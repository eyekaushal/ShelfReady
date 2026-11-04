import io
import socket

import httpx2
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.exceptions import ValidationError

from services.image_service import ImageService
from tests.ai_fakes import png_bytes

PUBLIC_IP = "93.184.216.34"


@pytest.fixture
def public_dns(monkeypatch):
    """Pretend every host name resolves to a public IP (no real DNS in tests)."""
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda host, port, **kw: [(socket.AF_INET, 0, 0, "", (PUBLIC_IP, 0))]
    )


@pytest.fixture
def fake_web(monkeypatch):
    """Route the image fetch through a handler instead of the network."""

    def use(handler):
        monkeypatch.setattr(ImageService, "transport", httpx2.MockTransport(handler))

    return use


def error_text(excinfo, field="image_url"):
    return str(excinfo.value.detail[field][0])


class TestUploads:
    def test_png_upload_is_accepted(self):
        upload = SimpleUploadedFile("pack.png", png_bytes(), content_type="image/png")

        data, media_type = ImageService.read_upload(upload)

        assert media_type == "image/png" and data.startswith(b"\x89PNG")

    def test_real_type_is_detected_not_the_file_name(self):
        upload = SimpleUploadedFile("pack.png", png_bytes(image_format="JPEG"), content_type="image/png")

        assert ImageService.read_upload(upload)[1] == "image/jpeg"

    def test_non_image_is_rejected(self):
        upload = SimpleUploadedFile("pack.png", b"<html>not an image</html>")

        with pytest.raises(ValidationError) as excinfo:
            ImageService.read_upload(upload)

        assert "not a readable image" in error_text(excinfo, "image")

    def test_gif_is_rejected(self):
        upload = SimpleUploadedFile("pack.gif", png_bytes(image_format="GIF"))

        with pytest.raises(ValidationError) as excinfo:
            ImageService.read_upload(upload)

        assert "JPEG, PNG or WebP" in error_text(excinfo, "image")

    def test_upload_over_5_mb_is_rejected(self):
        upload = SimpleUploadedFile("big.png", b"0" * (5 * 1024 * 1024 + 1))

        with pytest.raises(ValidationError) as excinfo:
            ImageService.read_upload(upload)

        assert "5 MB" in error_text(excinfo, "image")


class TestSsrfProtection:
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/pack.png",
            "http://localhost:8000/admin/",
            "http://10.0.0.5/pack.png",
            "http://192.168.1.10/pack.png",
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata service
            "http://[::1]/pack.png",
        ],
    )
    def test_private_addresses_are_blocked(self, url):
        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url(url)

        assert "private network" in error_text(excinfo)

    @pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/a.png", "gopher://x"])
    def test_only_http_and_https(self, url):
        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url(url)

        assert "http and https" in error_text(excinfo)

    def test_redirect_to_private_address_is_blocked(self, monkeypatch, fake_web):
        # The first host is public, but it redirects to the metadata service.
        def resolve(host, port, **kw):
            ip = "169.254.169.254" if host == "169.254.169.254" else PUBLIC_IP
            return [(socket.AF_INET, 0, 0, "", (ip, 0))]

        monkeypatch.setattr(socket, "getaddrinfo", resolve)
        fake_web(lambda request: httpx2.Response(302, headers={"location": "http://169.254.169.254/secret"}))

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://cdn.example.com/pack.png")

        assert "private network" in error_text(excinfo)

    def test_endless_redirects_stop(self, public_dns, fake_web):
        fake_web(lambda request: httpx2.Response(302, headers={"location": "/again"}))

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://cdn.example.com/pack.png")

        assert "too many times" in error_text(excinfo)


class TestFetch:
    def test_fetches_a_public_image(self, public_dns, fake_web):
        fake_web(
            lambda request: httpx2.Response(200, headers={"content-type": "image/png"}, content=png_bytes())
        )

        data, media_type = ImageService.fetch_url("https://cdn.example.com/pack.png")

        assert media_type == "image/png" and len(data) > 0

    def test_follows_a_safe_redirect(self, public_dns, fake_web):
        def handler(request):
            if request.url.path == "/old.png":
                return httpx2.Response(301, headers={"location": "/new.png"})
            return httpx2.Response(200, headers={"content-type": "image/png"}, content=png_bytes())

        fake_web(handler)

        assert ImageService.fetch_url("https://cdn.example.com/old.png")[1] == "image/png"

    def test_web_page_instead_of_image(self, public_dns, fake_web):
        fake_web(
            lambda request: httpx2.Response(200, headers={"content-type": "text/html"}, content=b"<html>")
        )

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://example.com/")

        assert "not an image" in error_text(excinfo)

    def test_http_error_status(self, public_dns, fake_web):
        fake_web(lambda request: httpx2.Response(404))

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://cdn.example.com/missing.png")

        assert "HTTP 404" in error_text(excinfo)

    def test_declared_size_over_limit(self, public_dns, fake_web):
        headers = {"content-type": "image/png", "content-length": str(6 * 1024 * 1024)}
        fake_web(lambda request: httpx2.Response(200, headers=headers, content=b"x"))

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://cdn.example.com/huge.png")

        assert "5 MB" in error_text(excinfo)

    def test_actual_size_over_limit_without_header(self, public_dns, fake_web, settings):
        settings.IMAGE_MAX_BYTES = 1000

        def handler(request):
            return httpx2.Response(200, headers={"content-type": "image/png"}, content=iter([b"x" * 800] * 3))

        fake_web(handler)

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://cdn.example.com/sneaky.png")

        assert "5 MB" in error_text(excinfo)

    def test_network_failure_is_a_clean_error(self, public_dns, fake_web):
        def handler(request):
            raise httpx2.ConnectTimeout("timed out")

        fake_web(handler)

        with pytest.raises(ValidationError) as excinfo:
            ImageService.fetch_url("https://cdn.example.com/slow.png")

        assert "Couldn't download" in error_text(excinfo)


class TestShrinkForAi:
    def test_large_image_is_scaled_to_1568_and_jpeg(self):
        data, media_type = ImageService.shrink_for_ai(png_bytes(3000, 1000), "image/png")

        with Image.open(io.BytesIO(data)) as image:
            assert max(image.size) == 1568
        assert media_type == "image/jpeg"

    def test_small_image_is_unchanged(self):
        original = png_bytes(400, 400)

        assert ImageService.shrink_for_ai(original, "image/png") == (original, "image/png")
