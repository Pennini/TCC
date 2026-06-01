import json
from pathlib import Path

import pandas as pd

PORTE_MAP = {
    "Micro Empresário Individual (MEI)": "MEI",
    "Microempresa (ME)": "ME",
    "Empresa de Pequeno Porte (EPP)": "EPP",
    "Outros": "Outros",
}
PME_PORTES = ["MEI", "ME", "EPP"]
SAM_SETORES = ["Comércio", "Serviços", "Indústria"]


def load_raw(path):
    """Lê o JSON de coleta do Sebrae."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def to_df(raw, key):
    """Extrai o bloco `data` de um dataset como DataFrame."""
    if key not in raw:
        raise KeyError(f"Dataset '{key}' não encontrado. Disponíveis: {list(raw)}")
    return pd.DataFrame(raw[key]["data"])
