import json
import pytest
from src import sebrae


def _raw_fixture(tmp_path):
    raw = {
        "RF__Establishments__Grande Sector,Company Size Sebrae": {
            "data": [
                {"Grande Sector": "Comércio", "Company Size Sebrae": "Microempresa (ME)", "Establishments": 10.0},
                {"Grande Sector": "Serviços", "Company Size Sebrae": "Outros", "Establishments": 5.0},
            ]
        }
    }
    p = tmp_path / "sebrae.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    return p


def test_load_raw_le_dict(tmp_path):
    p = _raw_fixture(tmp_path)
    raw = sebrae.load_raw(p)
    assert "RF__Establishments__Grande Sector,Company Size Sebrae" in raw


def test_to_df_extrai_data(tmp_path):
    raw = sebrae.load_raw(_raw_fixture(tmp_path))
    df = sebrae.to_df(raw, "RF__Establishments__Grande Sector,Company Size Sebrae")
    assert list(df.columns) == ["Grande Sector", "Company Size Sebrae", "Establishments"]
    assert len(df) == 2


def test_to_df_chave_ausente_erro_claro(tmp_path):
    raw = sebrae.load_raw(_raw_fixture(tmp_path))
    with pytest.raises(KeyError, match="não encontrado"):
        sebrae.to_df(raw, "chave_inexistente")


import pandas as pd


def test_clean_portes_normaliza_rotulos():
    df = pd.DataFrame({
        "Company Size Sebrae": [
            "Micro Empresário Individual (MEI)",
            "Microempresa (ME)",
            "Empresa de Pequeno Porte (EPP)",
            "Outros",
        ],
        "Establishments": [1, 2, 3, 4],
    })
    out = sebrae.clean_portes(df)
    assert list(out["porte"]) == ["MEI", "ME", "EPP", "Outros"]
    assert "porte" not in df.columns
