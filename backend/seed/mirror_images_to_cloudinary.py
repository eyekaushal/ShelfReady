"""
Copies the seed product images from Open Food Facts to Cloudinary (run once, the JSON is committed).

Why: Open Food Facts' image servers can take many seconds per image, so a first-time visitor
saw blank tiles. Cloudinary is a fast CDN. Images are copied unchanged, so the deliberately
small demo image stays small. The original address is kept in `source_image_url` for attribution.

    cd backend
    CLOUD_NAME=xxx UPLOAD_PRESET=yyy python -m seed.mirror_images_to_cloudinary

Safe to re-run: images already on Cloudinary are skipped. Run it again after re-fetching
products.json with fetch_open_food_facts.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx2

SEED_FILE = Path(__file__).parent / "products.json"
CLOUDINARY_HOST = "res.cloudinary.com"
WORKERS = 6  # a few at a time: fast enough, and polite to Open Food Facts
ATTEMPTS = 3


class SeedImageMirror:
    def __init__(self, cloud_name: str, upload_preset: str):
        self.upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
        self.upload_preset = upload_preset

    def run(self) -> None:
        data = json.loads(SEED_FILE.read_text())
        pending = [p for p in data["products"] if CLOUDINARY_HOST not in p["image_url"]]
        print(f"{len(pending)} images to copy")

        failed = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            jobs = {pool.submit(self._copy, product): product for product in pending}
            for done, job in enumerate(as_completed(jobs), start=1):
                product = jobs[job]
                try:
                    product["source_image_url"] = product["image_url"]
                    product["image_url"] = job.result()
                except (httpx2.HTTPError, ValueError) as error:
                    failed += 1
                    product.pop("source_image_url", None)
                    print(f"  failed {product['gtin']}: {error}")
                self._save(data)  # after each image, so an interrupted run keeps its progress
                if done % 10 == 0:
                    print(f"  {done}/{len(pending)}", flush=True)

        print(f"Done. {len(pending) - failed} copied, {failed} failed (re-run to retry those).")

    def _copy(self, product: dict) -> str:
        """Ask Cloudinary to fetch the image itself. Returns its new https address."""
        error = None
        for _ in range(ATTEMPTS):
            try:
                response = httpx2.post(
                    self.upload_url,
                    data={
                        "file": product["image_url"],
                        "upload_preset": self.upload_preset,
                        "public_id": f"seed-{product['gtin']}",
                    },
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()["secure_url"]
            except httpx2.HTTPError as caught:  # Open Food Facts is sometimes too slow: try again
                error = caught
        raise error

    @staticmethod
    def _save(data: dict) -> None:
        SEED_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    SeedImageMirror(os.environ["CLOUD_NAME"], os.environ["UPLOAD_PRESET"]).run()
