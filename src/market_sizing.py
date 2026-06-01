import pandas as pd

from src.sebrae import PME_PORTES


def compute_tam(df_porte, porte_col="porte", value_col="Establishments"):
    """TAM = soma de MEI+ME+EPP. 'Outros' (médio/grande) reportado à parte."""
    g = df_porte.groupby(porte_col)[value_col].sum()
    por_porte = g.reindex(PME_PORTES).fillna(0.0)
    return {
        "tam_pme": float(por_porte.sum()),
        "outros": float(g.drop(index=PME_PORTES, errors="ignore").sum()),
        "por_porte": por_porte.to_dict(),
    }
