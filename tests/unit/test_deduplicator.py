"""Testes unitários para a classe Deduplicator."""

import pytest

from src.core.deduplicator import Deduplicator


class TestDeduplicator:
    """Testes para Deduplicator."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_init_default_dedup_days(self, db):
        """Inicializa com dedup_days padrão."""
        dedup = Deduplicator(db)
        assert dedup.dedup_days == 7

    @pytest.mark.unit
    def test_init_custom_dedup_days(self, db):
        """Inicializa com dedup_days customizado."""
        dedup = Deduplicator(db, dedup_days=30)
        assert dedup.dedup_days == 30

    @pytest.mark.unit
    def test_is_duplicate_new_product(self, db):
        """Produto novo não é duplicata."""
        dedup = Deduplicator(db, dedup_days=7)
        assert dedup.is_duplicate(999999, "-1001234567890") is False

    @pytest.mark.database
    @pytest.mark.unit
    def test_is_duplicate_sent_recently(self, db):
        """Produto enviado recentemente é duplicata."""
        from datetime import datetime, timedelta

        dedup = Deduplicator(db, dedup_days=7)
        item_id = 123456
        group_id = "-1001234567890"

        # Primeiro insere o produto em products_seen (FK requirement)
        db.upsert_product({
            "itemId": str(item_id),
            "productName": "Produto Teste",
            "priceMin": 100.0,
            "priceDiscountRate": 10,
            "commissionRate": 0.08,
        })

        # Marca como enviado
        db.mark_as_sent(item_id, group_id, "https://test.link", "batch1")

        assert dedup.is_duplicate(item_id, group_id) is True

    @pytest.mark.database
    @pytest.mark.unit
    def test_is_duplicate_old_product(self, db):
        """Produto enviado há muito tempo não é duplicata."""
        from datetime import datetime, timedelta

        dedup = Deduplicator(db, dedup_days=7)
        item_id = 789012
        group_id = "-1001234567890"

        # Primeiro insere o produto em products_seen (FK requirement)
        db.upsert_product({
            "itemId": str(item_id),
            "productName": "Produto Teste",
            "priceMin": 100.0,
            "priceDiscountRate": 10,
            "commissionRate": 0.08,
        })

        # Marca como enviado há 10 dias
        old_timestamp = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        db.conn.execute(
            """INSERT INTO sent_messages (item_id, group_id, short_link, batch_id, sent_at)
               VALUES (?, ?, ?, ?, ?)""",
            (item_id, group_id, "https://test.link", "batch_old", old_timestamp),
        )
        db.conn.commit()

        assert dedup.is_duplicate(item_id, group_id) is False

    @pytest.mark.smoke
    @pytest.mark.database
    @pytest.mark.unit
    def test_filter_duplicates_removes_sent(self, db):
        """Remove produtos já enviados da lista."""
        from datetime import datetime

        dedup = Deduplicator(db, dedup_days=7)
        group_id = "-1001234567890"

        # Primeiro insere o produto em products_seen (FK requirement)
        db.upsert_product({
            "itemId": "2",
            "productName": "Produto 2",
            "priceMin": 50.0,
            "priceDiscountRate": 10,
            "commissionRate": 0.08,
        })

        # Marca produto 2 como enviado
        db.mark_as_sent(2, group_id, "https://test.link", "batch1")

        products = [
            {"itemId": "1", "productName": "Produto 1"},
            {"itemId": "2", "productName": "Produto 2"},
            {"itemId": "3", "productName": "Produto 3"},
        ]

        filtered = dedup.filter_duplicates(products, group_id)

        assert len(filtered) == 2
        assert filtered[0]["itemId"] == "1"
        assert filtered[1]["itemId"] == "3"

    @pytest.mark.database
    @pytest.mark.unit
    def test_filter_duplicates_handles_missing_item_id(self, db):
        """Lida com produtos sem itemId."""
        dedup = Deduplicator(db, dedup_days=7)

        products = [
            {"itemId": "1", "productName": "Produto 1"},
            {"productName": "Sem ID"},  # Sem itemId
            {"itemId": "2", "productName": "Produto 2"},
        ]

        filtered = dedup.filter_duplicates(products, "-1001234567890")

        # Produto sem ID é ignorado, mas não causa erro
        assert len(filtered) == 2
        assert all("itemId" in p for p in filtered)

    @pytest.mark.database
    @pytest.mark.unit
    def test_filter_duplicates_empty_list(self, db):
        """Lida com lista vazia."""
        dedup = Deduplicator(db, dedup_days=7)
        filtered = dedup.filter_duplicates([], "-1001234567890")
        assert filtered == []

    @pytest.mark.database
    @pytest.mark.unit
    def test_mark_sent(self, db):
        """Marca produto como enviado."""
        dedup = Deduplicator(db, dedup_days=7)
        item_id = 555555
        group_id = "-1001234567890"
        short_link = "https://shope.ee/test"
        batch_id = "test_batch"

        # Primeiro insere o produto em products_seen (FK requirement)
        db.upsert_product({
            "itemId": str(item_id),
            "productName": "Produto Teste",
            "priceMin": 100.0,
            "priceDiscountRate": 10,
            "commissionRate": 0.08,
        })

        dedup.mark_sent(item_id, group_id, short_link, batch_id)

        # Verifica se foi marcado
        assert db.was_sent_recently(item_id, group_id, 7) is True

    @pytest.mark.database
    @pytest.mark.unit
    def test_mark_sent_then_is_duplicate(self, db):
        """Produto marcado como enviado é detectado como duplicata."""
        dedup = Deduplicator(db, dedup_days=7)
        item_id = 777777
        group_id = "-1001234567890"

        # Inicialmente não é duplicata
        assert dedup.is_duplicate(item_id, group_id) is False

        # Primeiro insere o produto em products_seen (FK requirement)
        db.upsert_product({
            "itemId": str(item_id),
            "productName": "Produto Teste",
            "priceMin": 100.0,
            "priceDiscountRate": 10,
            "commissionRate": 0.08,
        })

        # Marca como enviado
        dedup.mark_sent(item_id, group_id, "https://test.link", "batch1")

        # Agora é duplicata
        assert dedup.is_duplicate(item_id, group_id) is True
