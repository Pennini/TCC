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


def compute_sam(df_porte_setor, setores, porte_col="porte",
                setor_col="Grande Sector", value_col="Establishments"):
    """SAM = PME (MEI/ME/EPP) nos setores-alvo, somado por setor."""
    mask = df_porte_setor[porte_col].isin(PME_PORTES) & df_porte_setor[setor_col].isin(setores)
    tab = df_porte_setor[mask].groupby(setor_col)[value_col].sum()
    return pd.DataFrame({"setor": tab.index, "sam": tab.values})
