"""
Builds backend/seed/products.json from Open Food Facts (run once, the JSON is committed).

    cd backend
    python -m seed.fetch_open_food_facts               # fetch live
    python -m seed.fetch_open_food_facts --cache /tmp/off  # keep raw responses (handy while tuning)

Data: Open Food Facts (https://openfoodfacts.org), licensed under the Open Database License,
images under CC BY-SA. See the README for attribution.

Open Food Facts has no prices, so `price` is an ILLUSTRATIVE estimate from pack size.
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from services.gtin_validator import GtinValidator

OUTPUT = Path(__file__).parent / "products.json"
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
USER_AGENT = "ShelfReady/1.0 (+https://github.com/eyekaushal/ShelfReady)"
FIELDS = "code,product_name,brands,quantity,image_front_url"

# One row per brand:
#   search words | brand name we store | word that must be in OFF "brands" | default category | skip words
# "skip words" drop rows whose brand or name contains them (OFF data has wrong brands and odd items).
BRAND_QUERIES = [
    ("parle biscuit", "Parle", "parle", "cookies", ["agro"]),
    ("britannia", "Britannia", "britannia", "cookies", []),
    ("sunfeast", "Sunfeast", "sunfeast", "cookies", []),
    ("parle agro", "Parle Agro", "parle", "juices", ["drinking water"]),
    ("haldiram", "Haldiram's", "haldiram", "namkeen", []),
    ("bikaji", "Bikaji", "bikaji", "namkeen", ["rasgulla"]),
    ("kurkure", "Kurkure", "kurkure", "chips-crisps", []),
    ("lays india", "Lay's", "lay", "chips-crisps", ["pepsico"]),
    ("bingo", "Bingo", "bingo", "chips-crisps", []),
    ("maggi", "Maggi", "maggi", "instant-noodles", ["ketchup"]),
    ("cadbury india", "Cadbury", "cadbury", "chocolates", ["cranberry"]),
    ("amul", "Amul", "amul", "milk-drinks", ["chocominis"]),
    ("nestle india", "Nestlé", "nestl", "chocolates", ["maggi", "polo", "milkmaid", "noodle", "whitener"]),
    ("tata tea", "Tata Tea", "tata", "tea", []),
    ("red label", "Brooke Bond", "brooke", "tea", []),
    ("bru coffee", "Bru", "bru", "coffee", ["cold"]),
    ("nescafe", "Nescafé", "nescaf", "coffee", ["noodle"]),
    ("dabur", "Dabur", "dabur", "honey-spreads", ["hajmola"]),
    ("paper boat", "Paper Boat", "paper boat", "juices", ["chikki", "jamun"]),
    ("mtr", "MTR", "mtr", "ready-mixes", ["vermicelli", "vemicelli", "badam", "powder"]),
]
MAX_PER_BRAND = 7

# Category tree: (slug, name, parent slug). Parents are listed before their children.
CATEGORIES = [
    ("food", "Food", None),
    ("biscuits", "Biscuits", "food"),
    ("glucose-biscuits", "Glucose Biscuits", "biscuits"),
    ("cream-biscuits", "Cream Biscuits", "biscuits"),
    ("cookies", "Cookies", "biscuits"),
    ("crackers", "Crackers", "biscuits"),
    ("snacks", "Snacks", "food"),
    ("namkeen", "Namkeen", "snacks"),
    ("chips-crisps", "Chips & Crisps", "snacks"),
    ("instant-food", "Instant Food", "food"),
    ("instant-noodles", "Instant Noodles", "instant-food"),
    ("ready-mixes", "Ready Mixes", "instant-food"),
    ("chocolates", "Chocolates", "food"),
    ("dairy", "Dairy", "food"),
    ("butter-cheese", "Butter & Cheese", "dairy"),
    ("milk-drinks", "Milk & Milk Drinks", "dairy"),
    ("ghee", "Ghee", "dairy"),
    ("pantry", "Pantry", "food"),
    ("honey-spreads", "Honey & Spreads", "pantry"),
    ("beverages", "Beverages", None),
    ("tea", "Tea", "beverages"),
    ("coffee", "Coffee", "beverages"),
    ("juices", "Juices & Fruit Drinks", "beverages"),
    ("soft-drinks", "Soft Drinks", "beverages"),
]

# Checked against the product NAME, first match wins; otherwise the brand's default is used.
# Order matters: "Dairy Milk" is a chocolate, "buttermilk" is a drink, not butter.
CATEGORY_RULES = [
    (["bourbon", "jim jam", "jimjam", "oreo", "cream biscuit"], "cream-biscuits"),
    (["parle-g", "parle g", "glucose", "marie", "tiger"], "glucose-biscuits"),
    (["krackjack", "monaco", "cracker"], "crackers"),
    (["cookie", "good day", "hide & seek", "20-20", "dark fantasy", "happy happy", "mom"], "cookies"),
    (["noodle", "maggi", "yippee", "pazzta", "macaroni"], "instant-noodles"),
    (["poha", "upma", "idli", "dosa", "gulab jamun"], "ready-mixes"),
    (["chips", "potato", "mad angles", "tedhe medhe", "tedha medha", "curlz"], "chips-crisps"),
    (["bhujia", "sev", "moong dal", "chiwda", "mixture", "bhel", "kaju", "soya", "murmura"], "namkeen"),
    (["dairy milk", "kitkat", "kit kat", "5star", "5 star", "munch max"], "chocolates"),
    (["milkybar", "milky bar", "silk", "gems"], "chocolates"),
    (["ghee"], "ghee"),
    (["buttermilk", "chaas", "lassi", "smoodh"], "milk-drinks"),
    (["butter", "cheese", "paneer"], "butter-cheese"),
    (["milk"], "milk-drinks"),
    (["honey", "chyawanprash"], "honey-spreads"),
    (["coffee", "nescafe", "bru", "cappuccino"], "coffee"),
    (["tea", "red label"], "tea"),
    (["fizz", "sparkling", "soda"], "soft-drinks"),
    (["juice", "frooti", "swing", "nectar"], "juices"),
]

# Flavours / types that tell variants apart. Longer phrases first, so "cream & onion" wins over "onion".
VARIANT_WORDS = [
    "cream & onion", "cream and onion", "magic masala", "fruit and nut", "fruit & nut",
    "roast almond", "green apple", "mixed fruit", "hot n sweet chilli", "achaari", "masala",
    "chocolate", "cashew", "elaichi", "mango", "apple", "orange", "guava", "litchi", "strawberry",
    "vanilla", "pista", "tomato", "mint", "lemon", "salted", "chilli", "cheese", "caramel",
    "hazelnut", "classic", "original", "natural care", "chicken", "veg atta",
]

# Rough ₹ per gram (or per ml) for each leaf category, used ONLY for illustrative prices.
PRICE_PER_UNIT = {
    "glucose-biscuits": 0.11, "cream-biscuits": 0.3, "cookies": 0.3, "crackers": 0.2,
    "namkeen": 0.28, "chips-crisps": 0.45, "instant-noodles": 0.2, "ready-mixes": 0.35,
    "chocolates": 1.0, "butter-cheese": 0.55, "milk-drinks": 0.12, "ghee": 0.65,
    "honey-spreads": 0.5, "tea": 0.55, "coffee": 2.4, "juices": 0.1, "soft-drinks": 0.08,
}


class OpenFoodFactsFetcher:
    """Fetches, cleans and saves a demo catalog of Indian FMCG products."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir
        self.parents = {slug: parent for slug, _, parent in CATEGORIES}

    # --- main flow ---------------------------------------------------------------

    def run(self) -> None:
        products, seen_codes, seen_names = [], set(), set()
        for search, brand, must_have, default_category, skip_words in BRAND_QUERIES:
            try:
                raw_products = self._search(search)
            except RuntimeError as error:  # OFF is a free service and sometimes busy
                print(f"{brand:20} skipped ({error})")
                continue
            picked = 0
            for raw in raw_products:
                product = self._clean(raw, brand, must_have, default_category, skip_words)
                if product is None:
                    continue
                # Skip accidental repeats (same barcode, or same name + size). The demo adds
                # exactly one duplicate on purpose later, so the duplicate check has one clear case.
                name_key = (product["name"].lower(), product["pack_size"])
                if product["gtin"] in seen_codes or name_key in seen_names:
                    continue
                seen_codes.add(product["gtin"])
                seen_names.add(name_key)
                products.append(product)
                picked += 1
                if picked == MAX_PER_BRAND:
                    break
            print(f"{brand:20} {picked:2} products")

        self._add_demo_cases(products)
        data = {
            "source": "Open Food Facts (ODbL; images CC BY-SA) — prices are illustrative estimates",
            "categories": [{"slug": s, "name": n, "parent": p} for s, n, p in CATEGORIES],
            "products": products,
        }
        OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"\nSaved {len(products)} products → {OUTPUT}")

    # --- fetching ------------------------------------------------------------------

    def _search(self, terms: str) -> list[dict]:
        cache_file = self.cache_dir / f"{terms.replace(' ', '_')}.json" if self.cache_dir else None
        if cache_file and cache_file.exists():
            return json.loads(cache_file.read_text())["products"]

        params = {
            "search_terms": terms, "countries_tags_en": "india", "json": 1,
            "page_size": 60, "fields": FIELDS, "sort_by": "unique_scans_n",  # most-scanned first
        }
        url = f"{SEARCH_URL}?{urllib.parse.urlencode(params)}"
        body = self._get_with_retry(url)
        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(body)
        time.sleep(7)  # OFF allows ~10 search requests per minute
        return json.loads(body)["products"]

    @staticmethod
    def _get_with_retry(url: str, attempts: int = 4) -> str:
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    body = response.read().decode("utf-8")
                if body.lstrip().startswith("{"):
                    return body
            except OSError:
                pass
            # OFF sometimes answers with an HTML "temporarily unavailable" page: wait and retry.
            time.sleep(15 * attempt)
        raise RuntimeError(f"Open Food Facts did not answer: {url}")

    # --- cleaning ------------------------------------------------------------------

    def _clean(
        self, raw: dict, brand: str, must_have: str, default_category: str, skip_words: list[str]
    ) -> dict | None:
        code = (raw.get("code") or "").strip()
        brands = (raw.get("brands") or "").lower()
        image = raw.get("image_front_url") or ""
        if not (code and image and GtinValidator.is_valid(code)) or must_have not in brands:
            return None

        name = self._clean_name(raw.get("product_name") or "", brand)
        if name is None or any(word in f"{brands} {name.lower()}" for word in skip_words):
            return None

        pack_size = self._clean_quantity(raw.get("quantity") or "")
        category = self._pick_category(name) or default_category
        return {
            "gtin": code,
            "name": name,
            "brand": brand,
            "category": category,
            "pack_size": pack_size,
            "variant": self._pick_variant(name),
            "price": self._estimate_price(category, pack_size),
            "image_url": image,
            "description": self._describe(name, brand, pack_size, category),
            "tags": self._tags(category),
        }

    @staticmethod
    def _clean_quantity(quantity: str) -> str:
        """'45gm' → '45 g', '1 L' → '1 l', '300ML' → '300 ml'. Anything odd → ''."""
        pattern = r"^\s*(\d+(?:[.,]\d+)?)\s*(g|gm|gms|gr|gram|grams|kg|ml|l|ltr|litre)\b"
        match = re.match(pattern, quantity.lower())
        if not match:
            return ""
        number = match.group(1).replace(",", ".").removesuffix(".0")
        unit = {"gm": "g", "gms": "g", "gr": "g", "gram": "g", "grams": "g", "ltr": "l", "litre": "l"}
        return f"{number} {unit.get(match.group(2), match.group(2))}"

    @staticmethod
    def _clean_name(name: str, brand: str) -> str | None:
        name = re.sub(r"\s+-\s+.*$", "", name)  # "Happy happy - Parle - Parle" → "Happy happy"
        name = re.sub(r"\(.*?\)", "", name)  # "Jimjam (57)" → "Jimjam"
        # Drop sizes and shop jargon: "70Grm", "10rs", "Pc", "pet", "Pch".
        name = re.sub(r"\b\d+(?:[.,]\d+)?\s*(g|gm|gms|gr|grm|kg|ml|l|ltr|rs)\b", "", name, flags=re.I)
        name = re.sub(r"\b(pc|pch|pet|pouch|pack)\b\.?", "", name, flags=re.I)
        name = name.replace("Maggie", "Maggi")
        name = " ".join(name.replace("_", " ").split()).strip(" -,")
        if len(name) < 3 or name.isdigit() or name.lower() in {brand.lower(), "biscuit", "biscuits", "tea"}:
            return None
        if name.islower() or name.isupper():
            name = name.title().replace("'S", "'s")
        return name[:200]

    @staticmethod
    def _pick_category(name: str) -> str | None:
        lowered = name.lower()
        for keywords, slug in CATEGORY_RULES:
            # Whole words only: "lassi" must not match inside "classic".
            if any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in keywords):
                return slug
        return None

    @staticmethod
    def _pick_variant(name: str) -> str:
        lowered = name.lower()
        for phrase in VARIANT_WORDS:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                return phrase.title().replace(" And ", " & ")
        return ""

    @staticmethod
    def _estimate_price(category: str, pack_size: str) -> str:
        number, _, unit = pack_size.partition(" ")
        # Grams or ml; kg / l are ×1000. No pack size → assume a 100 g / 100 ml pack.
        amount = float(number) * (1000 if unit in {"kg", "l"} else 1) if number else 100.0
        price = max(5, round(amount * PRICE_PER_UNIT.get(category, 0.3) / 5) * 5)  # nearest ₹5, min ₹5
        return f"{price}.00"

    @staticmethod
    def _describe(name: str, brand: str, pack_size: str, category: str) -> str:
        label = next(n for slug, n, _ in CATEGORIES if slug == category).lower()
        size = f", {pack_size} pack" if pack_size else ""
        return f"{name} by {brand}{size}. Listed under {label}."

    def _tags(self, category: str) -> list[str]:
        tags, slug = [], category
        while slug:
            tags.append(slug.replace("-", " "))
            slug = self.parents.get(slug)
        return tags

    # --- deliberate data problems, so the demo has something to show -------------

    @staticmethod
    def _add_demo_cases(products: list[dict]) -> None:
        """
        Real catalogs are messy. These edits make sure every readiness check and the
        look-alike detector have at least one real example to flag.
        """
        def find(word):
            return next(p for p in products if word in p["name"].lower())

        # 1. A wrong barcode: last digit changed, so the GS1 check digit fails.
        bad = find("marie")
        bad["gtin"] = bad["gtin"][:-1] + str((int(bad["gtin"][-1]) + 1) % 10)
        bad["demo_note"] = "invalid GTIN check digit"

        # 2. A tiny reference photo (200 px instead of 400 px).
        small = find("krackjack")
        small["image_url"] = small["image_url"].replace(".400.", ".200.")
        small["demo_note"] = "image too small"

        # 3. Missing pack size on one twin: the camera can't tell it from its siblings.
        twin = find("parle-g")
        twin["pack_size"] = ""
        twin["demo_note"] = "missing pack size (look-alike twin)"

        # 4. A vague category: "Biscuits" instead of a leaf like "Cookies".
        vague = find("bourbon")
        vague["category"] = "biscuits"
        vague["tags"] = ["biscuits", "food"]
        vague["demo_note"] = "category not specific (not a leaf)"

        # 5. A duplicate entry: same brand + name + pack size, different (valid) barcode.
        original = find("good day")
        duplicate = {**original, "description": original["description"] + " (re-entered)"}
        body = original["gtin"][:-2] + str((int(original["gtin"][-2]) + 1) % 10)
        duplicate["gtin"] = body + str(GtinValidator.check_digit(body))
        duplicate["demo_note"] = "duplicate of another product"
        products.append(duplicate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--cache", type=Path, help="folder to cache raw OFF responses")
    OpenFoodFactsFetcher(cache_dir=parser.parse_args().cache).run()
