import logging
from unittest.mock import Mock

import pytest

from inci_pipeline import db
from inci_pipeline.stages import enrich_pubchem


@pytest.mark.parametrize("success", [True, False])
def test_pubchem_stage_logs_result_without_audit_table(monkeypatch, caplog, success):
    caplog.set_level(logging.INFO)
    client = Mock()
    query = client.table.return_value.select.return_value.not_.is_.return_value.range.return_value
    query.execute.return_value.data = []
    monkeypatch.setattr(db, "client", lambda: client)

    if success:
        enrich_pubchem.run()
        assert "pubchem_enrich completed:" in caplog.text
    else:
        query.execute.side_effect = RuntimeError("database unavailable")
        with pytest.raises(RuntimeError, match="database unavailable"):
            enrich_pubchem.run()
        assert "pubchem_enrich failed:" in caplog.text

    assert "'rows_in': 0, 'rows_upserted': 0" in caplog.text
    client.table.assert_called_once_with("ingredient_information")
