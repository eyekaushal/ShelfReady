from io import BytesIO

import pytest
from django.core.management import call_command
from PIL import Image

from catalog.models import LookalikePair, Product
from catalog.tasks import analyze_product
from services.embedding_service import EmbeddingService
from services.image_service import ImageService
from services.lookalike_service import LookalikeService
from tests.ai_fakes import png_bytes

LIST = "/api/lookalikes/"
# 64-bit fingerprints: SAME_LOOK differs from BASE in 2 bits, OTHER_LOOK in many.
BASE, SAME_LOOK, OTHER_LOOK = "ffff0000ffff0000", "ffff0000ffff0003", "0000ffff0000ffff"


@pytest.fixture(autouse=True)
def trigram_mode(settings):
    # The mode Render uses. It needs no model, so tests stay fast.
    settings.EMBEDDINGS_ENABLED = False


@pytest.fixture
def make_product(user, categories):
    def make(name, brand="Parle", category="biscuits", owner=user, **fields):
        return Product.objects.create(
            name=name,
            brand=brand,
            category=categories[category],
            description="x",
            price=10,
            created_by=owner,
            **fields,
        )

    return make


def pair_of(first, second):
    return LookalikePair.objects.filter(
        product_a=min(first.id, second.id), product_b=max(first.id, second.id)
    ).first()


class TestSmallHelpers:
    def test_hamming_counts_differing_bits(self):
        assert LookalikeService.hamming(BASE, BASE) == 0
        assert LookalikeService.hamming(BASE, SAME_LOOK) == 2


class TestMeasure:
    def test_measures_size_and_hash(self):
        result = ImageService.measure(png_bytes(320, 200))

        assert (result["image_width"], result["image_height"]) == (320, 200)
        assert len(result["image_phash"]) == 16

    def test_sharp_edges_score_higher_than_a_flat_image(self):
        checker = Image.new("L", (64, 64))
        checker.putdata([255 if (x // 4 + y // 4) % 2 else 0 for y in range(64) for x in range(64)])
        output = BytesIO()
        checker.save(output, format="PNG")

        assert (
            ImageService.measure(output.getvalue())["blur_score"]
            > ImageService.measure(png_bytes())["blur_score"]
        )


@pytest.mark.django_db
class TestPairDetection:
    def test_similar_names_without_a_size_are_an_unresolved_twin(self, make_product):
        first = make_product("Parle-G", pack_size="90 g")
        second = make_product("Parle-G Biscuit")

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second).status == LookalikePair.UNRESOLVED

    def test_different_pack_sizes_are_automatically_distinct(self, make_product):
        first = make_product("Parle-G", pack_size="90 g")
        second = make_product("Parle-G", pack_size="250 g")

        LookalikeService.refresh_pairs(second)

        pair = pair_of(first, second)
        assert pair.status == LookalikePair.RESOLVED_DISTINCT and pair.resolved_by is None

    def test_identical_attributes_stay_unresolved(self, make_product):
        first = make_product("Good Day", pack_size="50 G", variant="Cashew")
        second = make_product("Good Day", pack_size="50 g", variant=" cashew ")

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second).status == LookalikePair.UNRESOLVED

    def test_similar_photos_flag_a_pair_even_with_different_names(self, make_product):
        first = make_product("Monaco", image_phash=BASE)
        second = make_product("Krackjack", image_phash=SAME_LOOK)

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second).image_distance == 2

    def test_unrelated_products_are_not_flagged(self, make_product):
        first = make_product("Monaco", image_phash=BASE)
        second = make_product("Krackjack", image_phash=OTHER_LOOK)

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second) is None

    def test_other_brands_are_not_candidates(self, make_product):
        first = make_product("Marie Gold", brand="Britannia")
        second = make_product("Marie Gold", brand="Parle")

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second) is None

    def test_other_top_level_categories_are_not_candidates(self, make_product):
        first = make_product("Frooti", category="biscuits")
        second = make_product("Frooti", category="beverages")

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second) is None

    def test_sub_categories_of_the_same_tree_are_candidates(self, make_product):
        first = make_product("Parle-G", category="biscuits")
        second = make_product("Parle-G", category="cream")

        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second) is not None

    def test_filling_a_size_resolves_the_twin_by_itself(self, make_product):
        first = make_product("Parle-G", pack_size="90 g")
        second = make_product("Parle-G")
        LookalikeService.refresh_pairs(second)

        second.pack_size = "250 g"
        second.save()
        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second).status == LookalikePair.RESOLVED_DISTINCT

    def test_pair_is_removed_when_no_longer_similar(self, make_product):
        first = make_product("Parle-G")
        second = make_product("Parle-G")
        LookalikeService.refresh_pairs(second)

        second.name = "Krackjack"
        second.save()
        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second) is None

    def test_a_persons_decision_survives_a_recheck(self, make_product, user):
        first = make_product("Parle-G")
        second = make_product("Parle-G")
        LookalikeService.refresh_pairs(second)
        LookalikeService.resolve(pair_of(first, second), LookalikePair.DUPLICATE, user)

        LookalikeService.refresh_pairs(second)
        second.name = "Krackjack"
        second.save()
        LookalikeService.refresh_pairs(second)

        assert pair_of(first, second).status == LookalikePair.DUPLICATE


@pytest.mark.django_db
class TestAnalyze:
    def test_measures_the_image(self, make_product, monkeypatch):
        monkeypatch.setattr(ImageService, "fetch_url", lambda url: (png_bytes(), "image/png"))
        product = make_product("Parle-G", image_url="https://cdn.example.com/a.png")

        LookalikeService.analyze(product)

        product.refresh_from_db()
        assert product.image_width == 400 and len(product.image_phash) == 16

    def test_dead_image_link_is_not_an_error(self, make_product, monkeypatch):
        def fail(url):
            raise ValueError("dead link")

        monkeypatch.setattr(ImageService, "fetch_url", fail)
        product = make_product("Parle-G", image_url="https://cdn.example.com/a.png", image_phash=BASE)

        LookalikeService.analyze(product)

        product.refresh_from_db()
        assert product.image_phash == ""

    def test_removed_image_clears_measurements(self, make_product):
        product = make_product("Parle-G", image_phash=BASE, image_width=100)

        LookalikeService.analyze(product)

        product.refresh_from_db()
        assert product.image_phash == "" and product.image_width is None

    def test_task_never_raises(self, make_product, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(LookalikeService, "analyze", explode)

        analyze_product(make_product("Parle-G").id)  # must not raise

    def test_task_ignores_a_deleted_product(self, db):
        analyze_product(999999)

    def test_embeddings_stored_when_enabled(self, make_product, monkeypatch, settings):
        settings.EMBEDDINGS_ENABLED = True
        monkeypatch.setattr(EmbeddingService, "embed", classmethod(lambda cls, product: [0.1] * 384))
        product = make_product("Parle-G")

        LookalikeService.analyze(product, image_changed=False)

        product.refresh_from_db()
        assert len(product.name_embedding) == 384

    def test_embedding_similarity_uses_the_cosine_threshold(self, make_product, settings):
        settings.EMBEDDINGS_ENABLED = True
        close = [1.0] + [0.0] * 383
        far = [0.0, 1.0] + [0.0] * 382
        first = make_product("Alpha", name_embedding=close)
        same = make_product("Beta", name_embedding=close)
        make_product("Gamma", name_embedding=far)

        scores = EmbeddingService.similar_products(first, Product.objects.exclude(pk=first.pk))

        assert scores == {same.id: 1.0}

    def test_product_missing_an_embedding_gets_one_even_if_text_did_not_change(
        self, make_product, monkeypatch, settings
    ):
        settings.EMBEDDINGS_ENABLED = True
        monkeypatch.setattr(EmbeddingService, "embed", classmethod(lambda cls, product: [0.1] * 384))
        product = make_product("Parle-G")

        LookalikeService.analyze(product, image_changed=False, text_changed=False)

        product.refresh_from_db()
        assert product.name_embedding is not None

    def test_pairs_are_kept_while_other_products_have_no_embedding(self, make_product, monkeypatch, settings):
        first = make_product("Parle-G")
        second = make_product("Parle-G")
        LookalikeService.refresh_pairs(second)  # found in trigram mode

        settings.EMBEDDINGS_ENABLED = True
        monkeypatch.setattr(EmbeddingService, "embed", classmethod(lambda cls, product: [0.1] * 384))
        LookalikeService.analyze(second, image_changed=False, text_changed=False)

        assert pair_of(first, second) is not None

    def test_embed_does_nothing_when_disabled(self, make_product):
        assert EmbeddingService.embed(make_product("Parle-G")) is None


@pytest.mark.django_db
@pytest.mark.real_analysis
class TestSavingAProductTriggersAnalysis:
    def payload(self, categories, **extra):
        return {
            "name": "Parle-G",
            "brand": "Parle",
            "category": categories["biscuits"].id,
            "description": "Glucose biscuits.",
            "price": "10.00",
            **extra,
        }

    def test_create_runs_analysis_and_finds_the_twin(self, auth_client, categories, make_product):
        first = make_product("Parle-G", pack_size="90 g")

        response = auth_client.post("/api/products/", self.payload(categories), format="json")

        assert response.status_code == 201
        assert pair_of(first, Product.objects.get(pk=response.json()["id"])) is not None

    def test_update_only_redoes_what_changed(self, auth_client, make_product, monkeypatch):
        calls = []
        monkeypatch.setattr(
            LookalikeService, "analyze", classmethod(lambda cls, product, **flags: calls.append(flags))
        )
        product = make_product("Parle-G")

        auth_client.patch(f"/api/products/{product.id}/", {"price": "12.00"}, format="json")
        auth_client.patch(f"/api/products/{product.id}/", {"name": "Parle-G Gold"}, format="json")

        assert calls == [
            {"image_changed": False, "text_changed": False},
            {"image_changed": False, "text_changed": True},
        ]

    def test_failed_analysis_does_not_fail_the_save(self, auth_client, categories, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(LookalikeService, "analyze", explode)

        assert auth_client.post("/api/products/", self.payload(categories), format="json").status_code == 201


@pytest.mark.django_db
class TestLookalikeApi:
    @pytest.fixture
    def twin(self, make_product):
        first = make_product("Parle-G", pack_size="90 g")
        second = make_product("Parle-G Biscuit")
        LookalikeService.refresh_pairs(second)
        return pair_of(first, second)

    def test_anyone_can_list_with_status_filter(self, api_client, twin):
        assert api_client.get(LIST, {"status": "unresolved"}).json()["count"] == 1
        assert api_client.get(LIST, {"status": "duplicate"}).json()["count"] == 0

    def test_list_shows_both_products(self, api_client, twin):
        result = api_client.get(LIST).json()["results"][0]

        assert result["product_a"]["name"] == "Parle-G"
        assert result["product_b"]["name"] == "Parle-G Biscuit"
        assert result["differing_attributes"] == []

    def test_filter_by_product(self, api_client, twin, make_product):
        assert api_client.get(LIST, {"product": twin.product_b_id}).json()["count"] == 1
        assert api_client.get(LIST, {"product": make_product("Other").id}).json()["count"] == 0

    def test_resolve_needs_login(self, api_client, twin):
        response = api_client.post(f"{LIST}{twin.id}/resolve/", {"status": "duplicate"}, format="json")

        assert response.status_code == 401

    def test_owner_marks_duplicate(self, auth_client, twin, user):
        response = auth_client.post(f"{LIST}{twin.id}/resolve/", {"status": "duplicate"}, format="json")

        assert response.status_code == 200
        assert response.json()["status"] == "duplicate" and response.json()["resolved_by"] == user.username

    def test_any_logged_in_user_can_resolve(self, api_client, other_user, twin):
        api_client.force_authenticate(user=other_user)

        response = api_client.post(f"{LIST}{twin.id}/resolve/", {"status": "duplicate"}, format="json")

        assert response.status_code == 200
        assert response.json()["resolved_by"] == other_user.username

    def test_staff_can_resolve(self, api_client, staff_user, twin):
        api_client.force_authenticate(user=staff_user)

        assert (
            api_client.post(f"{LIST}{twin.id}/resolve/", {"status": "duplicate"}, format="json").status_code
            == 200
        )

    def test_distinct_needs_an_attribute_that_differs(self, auth_client, twin):
        response = auth_client.post(
            f"{LIST}{twin.id}/resolve/", {"status": "resolved_distinct"}, format="json"
        )

        assert response.status_code == 400
        assert "status" in response.json()["error"]["details"]

    def test_distinct_allowed_once_attributes_differ(self, auth_client, twin):
        Product.objects.filter(pk=twin.product_b_id).update(pack_size="250 g")

        response = auth_client.post(
            f"{LIST}{twin.id}/resolve/", {"status": "resolved_distinct"}, format="json"
        )

        assert response.status_code == 200

    def test_cannot_set_unresolved(self, auth_client, twin):
        response = auth_client.post(f"{LIST}{twin.id}/resolve/", {"status": "unresolved"}, format="json")

        assert response.status_code == 400

    def test_check_finds_similar_skus_of_the_brand(self, api_client, make_product):
        existing = make_product("Parle-G", pack_size="90 g")
        make_product("Parle-G", brand="Other")

        response = api_client.get(f"{LIST}check/", {"name": "parle g biscuit", "brand": "parle"})

        assert [item["id"] for item in response.json()] == [existing.id]

    def test_check_excludes_the_product_being_edited(self, api_client, make_product):
        existing = make_product("Parle-G")

        response = api_client.get(
            f"{LIST}check/", {"name": "Parle-G", "brand": "Parle", "exclude": existing.id}
        )

        assert response.json() == []

    @pytest.mark.parametrize(
        "params", [{"name": "x"}, {"brand": "x"}, {"name": "x", "brand": "y", "exclude": "1 OR 1=1"}]
    )
    def test_check_validates_input(self, api_client, db, params):
        assert api_client.get(f"{LIST}check/", params).status_code == 400


@pytest.mark.django_db
class TestAnalyzeCatalogCommand:
    def test_measures_what_is_missing_then_finds_pairs_in_any_order(self, make_product, monkeypatch):
        fetched = []

        def fetch(url):
            fetched.append(url)
            return png_bytes(), "image/png"

        monkeypatch.setattr(ImageService, "fetch_url", fetch)
        first = make_product("Monaco", image_url="https://cdn.example.com/a.png")
        second = make_product("Krackjack", image_url="https://cdn.example.com/a.png")

        call_command("analyze_catalog")

        assert pair_of(first, second).image_distance == 0
        assert len(fetched) == 2

    def test_does_not_download_again_when_already_measured(self, make_product, monkeypatch):
        monkeypatch.setattr(ImageService, "fetch_url", lambda url: pytest.fail("should not download"))
        make_product("Monaco", image_url="https://cdn.example.com/a.png", image_phash=BASE)

        call_command("analyze_catalog")
