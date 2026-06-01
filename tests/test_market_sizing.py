import pandas as pd
from src import market_sizing as ms


def _df_porte():
    return pd.DataFrame({
        "porte": ["MEI", "ME", "EPP", "Outros", "MEI"],
        "Establishments": [100.0, 50.0, 10.0, 30.0, 5.0],
    })


def test_tam_soma_apenas_pme():
    res = ms.compute_tam(_df_porte())
    assert res["tam_pme"] == 165.0
    assert res["outros"] == 30.0
    assert res["por_porte"]["MEI"] == 105.0


from src.sebrae import SAM_SETORES


def _df_porte_setor():
    return pd.DataFrame({
        "Grande Sector": ["Comércio", "Serviços", "Indústria", "Agricultura", "Comércio"],
        "porte": ["ME", "MEI", "EPP", "ME", "Outros"],
        "Establishments": [200.0, 300.0, 25.0, 50.0, 40.0],
    })


def test_sam_filtra_setores_e_pme():
    sam = ms.compute_sam(_df_porte_setor(), SAM_SETORES)
    total = sam["sam"].sum()
    assert total == 525.0
    assert set(sam["setor"]) == {"Comércio", "Serviços", "Indústria"}
    assert "Agricultura" not in set(sam["setor"])


def test_som_aplica_taxas_por_cenario():
    taxas = {"pessimista": 0.01, "base": 0.03, "otimista": 0.05}
    som = ms.compute_som(1000.0, taxas)
    d = dict(zip(som["cenario"], som["som"]))
    assert d["pessimista"] == 10.0
    assert d["base"] == 30.0
    assert d["otimista"] == 50.0
    assert list(som["som"]) == sorted(som["som"])
