from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from submission_pipeline import matching


class Catalog:
    def __init__(self, match_rows, ingredient=None):
        self.match_rows = match_rows
        self.ingredient = ingredient

    def rpc(self, name, params):
        assert name == "match_ingredient"
        assert params["input"]
        rows = (
            self.match_rows.get(params["input"], [])
            if isinstance(self.match_rows, dict)
            else self.match_rows
        )
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=rows))

    def table(self, name):
        assert name == "ingredients"
        query = SimpleNamespace()
        query.select = lambda *_: query
        query.eq = lambda *_: query
        query.single = lambda: query
        query.execute = lambda: SimpleNamespace(data=self.ingredient)
        return query


def test_remote_exact_match_is_synced_and_supersedes_local_fuzzy(monkeypatch):
    ingredient_id = "01c3c5a5-0c55-4b55-a241-ca833039563f"
    local = Catalog(
        [
            {
                "ingredient_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "match_type": "canonical_fuzzy",
                "confidence": 0.7,
            }
        ]
    )
    remote = Catalog(
        [
            {
                "ingredient_id": ingredient_id,
                "match_type": "canonical_exact",
                "confidence": 1.0,
            }
        ],
        {"id": ingredient_id, "inci_name": "GLYCERIN", "slug": "glycerin"},
    )
    synced = []
    monkeypatch.setattr(matching.db, "client", lambda: local)
    monkeypatch.setattr(matching, "remote_client", lambda: remote)
    monkeypatch.setattr(
        matching.db,
        "sync_remote_catalog_ingredient",
        lambda ingredient: synced.append(ingredient) or ingredient["id"],
    )

    result = matching.match_token("glycerin")

    assert str(result.ingredient_id) == ingredient_id
    assert result.match_type == "canonical_exact"
    assert result.confidence == 1.0
    assert synced == [{"id": ingredient_id, "inci_name": "GLYCERIN", "slug": "glycerin"}]


def test_remote_fuzzy_match_is_not_synced_or_automatically_selected(monkeypatch):
    local_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    local = Catalog(
        [
            {
                "ingredient_id": local_id,
                "match_type": "canonical_fuzzy",
                "confidence": 0.7,
            }
        ]
    )
    remote = Catalog(
        [
            {
                "ingredient_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "match_type": "alias_fuzzy",
                "confidence": 0.9,
            }
        ]
    )
    monkeypatch.setattr(matching.db, "client", lambda: local)
    monkeypatch.setattr(matching, "remote_client", lambda: remote)
    sync_mock = Mock(side_effect=lambda ingredient: ingredient["id"])
    monkeypatch.setattr(matching.db, "sync_remote_catalog_ingredient", sync_mock)

    result = matching.match_token("glycern")

    assert str(result.ingredient_id) == local_id
    assert result.match_type == "canonical_fuzzy"
    sync_mock.assert_not_called()


def test_parenthetical_common_name_can_resolve_to_exact_remote_inci(monkeypatch):
    ingredient_id = "2ed67a3e-7ef0-4126-b05f-3ef756ca9444"
    token = "Ananas Sativus (Pineapple) Fruit Extract"
    canonical = "Ananas Sativus Fruit Extract"
    local = Catalog({token: [], canonical: []})
    remote = Catalog(
        {
            token: [
                {
                    "ingredient_id": ingredient_id,
                    "match_type": "canonical_fuzzy",
                    "confidence": 0.73,
                }
            ],
            canonical: [
                {
                    "ingredient_id": ingredient_id,
                    "match_type": "canonical_exact",
                    "confidence": 1.0,
                }
            ],
        },
        {"id": ingredient_id, "inci_name": "ANANAS SATIVUS FRUIT EXTRACT", "slug": "ananas"},
    )
    monkeypatch.setattr(matching.db, "client", lambda: local)
    monkeypatch.setattr(matching, "remote_client", lambda: remote)
    sync_mock = Mock(side_effect=lambda ingredient: ingredient["id"])
    monkeypatch.setattr(matching.db, "sync_remote_catalog_ingredient", sync_mock)

    result = matching.match_token(token)

    assert str(result.ingredient_id) == ingredient_id
    assert result.match_type == "canonical_exact"
    sync_mock.assert_called_once()
