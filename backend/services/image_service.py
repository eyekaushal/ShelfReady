import io
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx2
import imagehash
import numpy as np
from django.conf import settings
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError


class ImageService:
    """
    Gets image bytes from a URL or an upload, safely, and checks they really are an image.

    Why the URL fetch is careful (SSRF protection): the server fetches whatever URL a user
    types. Without checks, someone could make our server call internal addresses such as
    http://127.0.0.1:5432 or the cloud metadata service at http://169.254.169.254.
    So we only allow http/https, resolve the host and refuse private / loopback / link-local
    IPs, re-check every redirect, cap time (5 s) and size (5 MB), and verify the bytes with Pillow.

    Known limit (fine for this project): the host is resolved once by us and once by the HTTP
    client, so a DNS server that changes its answer in between could slip past. Fully closing that
    needs connecting to the checked IP directly.
    """

    # Pillow format name → the media type Claude expects.
    ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    MAX_REDIRECTS = 3
    AI_MAX_SIDE = 1568  # Claude downsizes anything bigger, so we send at most this (fewer tokens)

    # Tests set a fake transport here so no real network is used.
    transport = None

    # --- public ------------------------------------------------------------------------

    @classmethod
    def fetch_url(cls, url: str, field: str = "image_url") -> tuple[bytes, str]:
        """Download an image from a user-supplied URL. Returns (bytes, media_type)."""
        try:
            data = cls._download(url)
        except ValidationError:
            raise
        except (httpx2.HTTPError, OSError) as error:
            raise ValidationError({field: ["Couldn't download this image. Check the URL."]}) from error
        except ValueError as error:  # our own checks below raise ValueError with a user message
            raise ValidationError({field: [str(error)]}) from error
        return data, cls._media_type(data, field)

    @classmethod
    def read_upload(cls, upload, field: str = "image") -> tuple[bytes, str]:
        """Read an uploaded file (Django UploadedFile). Returns (bytes, media_type)."""
        if upload.size > settings.IMAGE_MAX_BYTES:
            raise ValidationError({field: ["Image must be 5 MB or smaller."]})
        data = upload.read()
        return data, cls._media_type(data, field)

    @classmethod
    def shrink_for_ai(cls, data: bytes, media_type: str) -> tuple[bytes, str]:
        """If the longest side is over 1568 px, scale down and re-encode as JPEG."""
        with Image.open(io.BytesIO(data)) as image:
            if max(image.size) <= cls.AI_MAX_SIDE:
                return data, media_type
            image.thumbnail((cls.AI_MAX_SIDE, cls.AI_MAX_SIDE))
            output = io.BytesIO()
            image.convert("RGB").save(output, format="JPEG", quality=85)
            return output.getvalue(), "image/jpeg"

    @staticmethod
    def measure(data: bytes) -> dict:
        """
        What the catalog stores about a pack photo:
        - image_phash: a 64-bit fingerprint of how the image looks; similar images differ in few bits
        - image_width / image_height: pixels
        - blur_score: variance of the Laplacian, an edge filter. Sharp photos have strong edges,
          so a higher number means sharper.
        """
        with Image.open(io.BytesIO(data)) as image:
            rgb = image.convert("RGB")
            gray = np.asarray(rgb.convert("L"), dtype=np.float64)
            # Laplacian: 4 x each pixel minus its four neighbours, for all inner pixels.
            edges = (
                4 * gray[1:-1, 1:-1] - gray[:-2, 1:-1] - gray[2:, 1:-1] - gray[1:-1, :-2] - gray[1:-1, 2:]
            )
            return {
                "image_phash": str(imagehash.phash(rgb)),
                "image_width": rgb.width,
                "image_height": rgb.height,
                "blur_score": round(float(edges.var()), 2),
            }

    # --- fetching ----------------------------------------------------------------------

    @classmethod
    def _download(cls, url: str) -> bytes:
        timeout = settings.IMAGE_FETCH_TIMEOUT_SECONDS
        with httpx2.Client(timeout=timeout, follow_redirects=False, transport=cls.transport) as client:
            for _ in range(cls.MAX_REDIRECTS + 1):
                cls._check_url_is_public(url)
                with client.stream("GET", url, headers={"User-Agent": "ShelfReady/1.0"}) as response:
                    if response.is_redirect:
                        # Follow redirects ourselves, so every hop goes through the IP check.
                        url = urljoin(url, response.headers.get("location", ""))
                        continue
                    if response.status_code != 200:
                        raise ValueError(f"The image URL answered with HTTP {response.status_code}.")
                    content_type = response.headers.get("content-type", "").split(";")[0].strip()
                    if not content_type.startswith("image/"):
                        raise ValueError("That URL is not an image (it returned a web page or file).")
                    return cls._read_capped(response)
        raise ValueError("The image URL redirects too many times.")

    @staticmethod
    def _read_capped(response) -> bytes:
        limit = settings.IMAGE_MAX_BYTES
        declared = response.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > limit:
            raise ValueError("Image must be 5 MB or smaller.")
        chunks, total = [], 0
        for chunk in response.iter_bytes():
            total += len(chunk)
            if total > limit:  # don't trust content-length alone; stop reading once over
                raise ValueError("Image must be 5 MB or smaller.")
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _check_url_is_public(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Only http and https image URLs are allowed.")
        try:
            addresses = socket.getaddrinfo(parsed.hostname, parsed.port or None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as error:
            raise ValueError("That image host could not be found.") from error
        for *_, sockaddr in addresses:
            ip = ipaddress.ip_address(sockaddr[0])
            # is_global is False for private, loopback, link-local, reserved, multicast, etc.
            if not ip.is_global:
                raise ValueError("That image URL points to a private network address, which isn't allowed.")

    # --- checking the bytes ------------------------------------------------------------

    @classmethod
    def _media_type(cls, data: bytes, field: str) -> str:
        """Ask Pillow what the bytes really are (never trust the file name or header)."""
        try:
            with Image.open(io.BytesIO(data)) as image:
                image_format = image.format
                image.verify()  # catches truncated / corrupt files
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise ValidationError({field: ["This file is not a readable image."]}) from error
        if image_format not in cls.ALLOWED_FORMATS:
            raise ValidationError({field: ["Use a JPEG, PNG or WebP image."]})
        return cls.ALLOWED_FORMATS[image_format]
