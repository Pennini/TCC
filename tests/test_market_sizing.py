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
