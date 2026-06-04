# Análise PME SP + TAM/SAM/SOM — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir módulo Python testável + notebook que caracteriza o ecossistema PME de São Paulo (dados Sebrae) e dimensiona o mercado em funil TAM/SAM/SOM (nº de empresas e R$).

**Architecture:** Lógica pura e testável em `src/sebrae.py` (carga/parse) e `src/market_sizing.py` (cálculo). O notebook `notebooks/3. Dados Sebrae.ipynb` importa essas funções, gera os gráficos descritivos, calcula o funil e persiste tabelas em `data/interim/`. Sem acesso à rede no módulo — opera sobre `data/raw/sebrae.json` já coletado.

**Tech Stack:** Python, pandas, matplotlib, pytest.

---

## Contexto de dados (referência para todas as tasks)

`data/raw/sebrae.json` é um dict com 12 chaves. Cada valor tem `["data"]` = lista de registros. Chaves usadas neste plano:

- `RF__Establishments__Open Activity Year,Company Size Sebrae` — cols: `Company Size Sebrae`, `Open Activity Year`, `Establishments`
- `RF__Establishments__Grande Sector,Company Size Sebrae` — cols: `Grande Sector`, `Company Size Sebrae`, `Establishments`
- `RF__Establishments__Sebrae Client Indicator,Grande Sector` — cols: `Grande Sector`, `Sebrae Client Indicator`, `Establishments`
- `RF__Establishments__Legal Nature` — cols: `Type Legal Nature`, `Legal Nature`, `Establishments`
- `CAGED_movements__Movement Balance,Admissions,Resignations__Grande Sector` — cols: `Grande Sector`, `Admissions`, `Movement Balance`, `Resignations`
- `RAIS_workers__Remuneration Avg Nominal,Workers__Grande Sector,Year` — cols: `Grande Sector`, `Year`, `Remuneration Avg Nominal`, `Workers`
- `IBGE_Censo_Sexo_Faixa_Etaria__Population__Age Group,Sex` — cols: `Age Group`, `Sex`, `Population`
- `IBGE_Censo_Pop_Sit__Population__Year,Municipality` — cols: `Year`, `Municipality`, `Population`
- `PNUD_Atlas_IDHM__Gini__Year,Municipality` — cols: `Year`, `Gini`

Rótulos de porte (`Company Size Sebrae`): `Micro Empresário Individual (MEI)`, `Microempresa (ME)`, `Empresa de Pequeno Porte (EPP)`, `Outros`.
Rótulos de setor (`Grande Sector`): `Agricultura`, `Indústria`, `Comércio`, `Serviços`, `Administração pública`, `Não especificado`.
Dados estão em UTF-8 correto — não há tratamento de encoding.

---

## File Structure

- Create: `requirements.txt` — dependências
- Create: `src/sebrae.py` — carga, parse, constantes, normalização de porte
- Create: `src/market_sizing.py` — `compute_tam`, `compute_sam`, `compute_som`, `to_revenue`
- Create: `tests/__init__.py`
- Create: `tests/test_sebrae.py`
- Create: `tests/test_market_sizing.py`
- Modify: `notebooks/3. Dados Sebrae.ipynb` — adiciona blocos A (descritivo), B (funil), C (saídas)
- Output (geradas em runtime): `data/interim/pme_porte.csv`, `pme_porte_setor.csv`, `tam_sam_som.csv`, `contexto_socioecon.csv`

---

## Task 1: Setup de dependências

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Criar `requirements.txt`**

```
pandas>=2.0
matplotlib>=3.7
pytest>=8.0
requests>=2.31
jupyter
```

- [ ] **Step 2: Instalar**

Run: `pip install -r requirements.txt`
Expected: instala pytest e demais sem erro.

- [ ] **Step 3: Verificar pytest**

Run: `pytest --version`
Expected: imprime versão (ex.: `pytest 8.x`).

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "build: add requirements.txt (pandas, matplotlib, pytest)"
```

---

## Task 2: `src/sebrae.py` — `load_raw` e `to_df`

**Files:**
- Create: `src/sebrae.py`
- Create: `tests/__init__.py`
- Test: `tests/test_sebrae.py`

- [ ] **Step 1: Criar `tests/__init__.py` vazio**

```python
```

- [ ] **Step 2: Escrever teste que falha**

`tests/test_sebrae.py`:

```python
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
```

- [ ] **Step 3: Rodar — deve falhar**

Run: `pytest tests/test_sebrae.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.sebrae'`.

- [ ] **Step 4: Implementar mínimo**

`src/sebrae.py`:

```python
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
```

- [ ] **Step 5: Rodar — deve passar**

Run: `pytest tests/test_sebrae.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add src/sebrae.py tests/__init__.py tests/test_sebrae.py
git commit -m "feat: load_raw e to_df para datasets Sebrae"
```

---

## Task 3: `src/sebrae.py` — `clean_portes`

**Files:**
- Modify: `src/sebrae.py`
- Test: `tests/test_sebrae.py`

- [ ] **Step 1: Adicionar teste que falha**

Acrescentar a `tests/test_sebrae.py`:

```python
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
    # não muta o input
    assert "porte" not in df.columns
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `pytest tests/test_sebrae.py::test_clean_portes_normaliza_rotulos -v`
Expected: FAIL com `AttributeError: module 'src.sebrae' has no attribute 'clean_portes'`.

- [ ] **Step 3: Implementar**

Acrescentar a `src/sebrae.py`:

```python
def clean_portes(df, col="Company Size Sebrae"):
    """Adiciona coluna `porte` normalizada (MEI/ME/EPP/Outros)."""
    out = df.copy()
    out["porte"] = out[col].map(PORTE_MAP)
    return out
```

- [ ] **Step 4: Rodar — deve passar**

Run: `pytest tests/test_sebrae.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/sebrae.py tests/test_sebrae.py
git commit -m "feat: clean_portes normaliza rótulos de porte"
```

---

## Task 4: `src/market_sizing.py` — `compute_tam`

**Files:**
- Create: `src/market_sizing.py`
- Test: `tests/test_market_sizing.py`

- [ ] **Step 1: Escrever teste que falha**

`tests/test_market_sizing.py`:

```python
import pandas as pd
from src import market_sizing as ms


def _df_porte():
    return pd.DataFrame({
        "porte": ["MEI", "ME", "EPP", "Outros", "MEI"],
        "Establishments": [100.0, 50.0, 10.0, 30.0, 5.0],
    })


def test_tam_soma_apenas_pme():
    res = ms.compute_tam(_df_porte())
    assert res["tam_pme"] == 165.0       # 100+5 (MEI) + 50 (ME) + 10 (EPP)
    assert res["outros"] == 30.0
    assert res["por_porte"]["MEI"] == 105.0
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `pytest tests/test_market_sizing.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.market_sizing'`.

- [ ] **Step 3: Implementar**

`src/market_sizing.py`:

```python
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
```

- [ ] **Step 4: Rodar — deve passar**

Run: `pytest tests/test_market_sizing.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/market_sizing.py tests/test_market_sizing.py
git commit -m "feat: compute_tam (PME = MEI+ME+EPP)"
```

---

## Task 5: `src/market_sizing.py` — `compute_sam`

**Files:**
- Modify: `src/market_sizing.py`
- Test: `tests/test_market_sizing.py`

- [ ] **Step 1: Adicionar teste que falha**

Acrescentar a `tests/test_market_sizing.py`:

```python
from src.sebrae import SAM_SETORES


def _df_porte_setor():
    return pd.DataFrame({
        "Grande Sector": ["Comércio", "Serviços", "Indústria", "Agricultura", "Comércio"],
        "porte": ["ME", "MEI", "EPP", "ME", "Outros"],
        "Establishments": [200.0, 300.0, 25.0, 50.0, 40.0],
    })


def test_sam_filtra_setores_e_pme():
    sam = ms.compute_sam(_df_porte_setor(), SAM_SETORES)
    # exclui Agricultura (setor fora) e Outros (porte fora)
    total = sam["sam"].sum()
    assert total == 525.0                      # 200 + 300 + 25
    assert set(sam["setor"]) == {"Comércio", "Serviços", "Indústria"}
    assert "Agricultura" not in set(sam["setor"])
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `pytest tests/test_market_sizing.py::test_sam_filtra_setores_e_pme -v`
Expected: FAIL com `AttributeError: module 'src.market_sizing' has no attribute 'compute_sam'`.

- [ ] **Step 3: Implementar**

Acrescentar a `src/market_sizing.py`:

```python
def compute_sam(df_porte_setor, setores, porte_col="porte",
                setor_col="Grande Sector", value_col="Establishments"):
    """SAM = PME (MEI/ME/EPP) nos setores-alvo, somado por setor."""
    mask = df_porte_setor[porte_col].isin(PME_PORTES) & df_porte_setor[setor_col].isin(setores)
    tab = df_porte_setor[mask].groupby(setor_col)[value_col].sum()
    return pd.DataFrame({"setor": tab.index, "sam": tab.values})
```

- [ ] **Step 4: Rodar — deve passar**

Run: `pytest tests/test_market_sizing.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/market_sizing.py tests/test_market_sizing.py
git commit -m "feat: compute_sam (PME em Comércio+Serviços+Indústria)"
```

---

## Task 6: `src/market_sizing.py` — `compute_som`

**Files:**
- Modify: `src/market_sizing.py`
- Test: `tests/test_market_sizing.py`

- [ ] **Step 1: Adicionar teste que falha**

Acrescentar a `tests/test_market_sizing.py`:

```python
def test_som_aplica_taxas_por_cenario():
    taxas = {"pessimista": 0.01, "base": 0.03, "otimista": 0.05}
    som = ms.compute_som(1000.0, taxas)
    d = dict(zip(som["cenario"], som["som"]))
    assert d["pessimista"] == 10.0
    assert d["base"] == 30.0
    assert d["otimista"] == 50.0
    # ordenado crescente por som
    assert list(som["som"]) == sorted(som["som"])
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `pytest tests/test_market_sizing.py::test_som_aplica_taxas_por_cenario -v`
Expected: FAIL com `AttributeError: ... 'compute_som'`.

- [ ] **Step 3: Implementar**

Acrescentar a `src/market_sizing.py`:

```python
def compute_som(sam_total, taxas):
    """SOM = SAM_total × taxa, um registro por cenário, ordenado crescente."""
    rows = [{"cenario": c, "taxa": t, "som": sam_total * t} for c, t in taxas.items()]
    return pd.DataFrame(rows).sort_values("som").reset_index(drop=True)
```

- [ ] **Step 4: Rodar — deve passar**

Run: `pytest tests/test_market_sizing.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/market_sizing.py tests/test_market_sizing.py
git commit -m "feat: compute_som (cenários pess/base/otim)"
```

---

## Task 7: `src/market_sizing.py` — `to_revenue`

**Files:**
- Modify: `src/market_sizing.py`
- Test: `tests/test_market_sizing.py`

- [ ] **Step 1: Adicionar teste que falha**

Acrescentar a `tests/test_market_sizing.py`:

```python
def test_to_revenue_anualiza_por_preco():
    rev = ms.to_revenue(100.0, [50.0, 100.0])
    assert rev[50.0] == 100.0 * 50.0 * 12     # 60_000
    assert rev[100.0] == 100.0 * 100.0 * 12   # 120_000
```

- [ ] **Step 2: Rodar — deve falhar**

Run: `pytest tests/test_market_sizing.py::test_to_revenue_anualiza_por_preco -v`
Expected: FAIL com `AttributeError: ... 'to_revenue'`.

- [ ] **Step 3: Implementar**

Acrescentar a `src/market_sizing.py`:

```python
def to_revenue(n_empresas, precos_mensais):
    """Receita potencial anual = nº × preço/mês × 12, para cada preço (sensibilidade)."""
    return {p: n_empresas * p * 12 for p in precos_mensais}
```

- [ ] **Step 4: Rodar — deve passar**

Run: `pytest tests/test_market_sizing.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/market_sizing.py tests/test_market_sizing.py
git commit -m "feat: to_revenue (anualização + sensibilidade de preço)"
```

---

## Task 8: Invariante do funil (teste de integração)

**Files:**
- Test: `tests/test_market_sizing.py`

- [ ] **Step 1: Adicionar teste que falha**

Acrescentar a `tests/test_market_sizing.py`:

```python
def test_funil_monotonico_tam_maior_igual_sam_maior_igual_som():
    # mesmos dados: porte_setor agrega para o total de porte
    df_ps = _df_porte_setor()
    df_porte = df_ps.groupby("porte", as_index=False)["Establishments"].sum()

    tam = ms.compute_tam(df_porte)["tam_pme"]
    sam = ms.compute_sam(df_ps, SAM_SETORES)["sam"].sum()
    som = ms.compute_som(sam, {"base": 0.03})["som"].iloc[0]

    assert tam >= sam >= som
```

- [ ] **Step 2: Rodar — deve passar (funções já existem)**

Run: `pytest tests/test_market_sizing.py::test_funil_monotonico_tam_maior_igual_sam_maior_igual_som -v`
Expected: PASS. Se falhar, há erro de definição de TAM/SAM — investigar antes de prosseguir.

- [ ] **Step 3: Rodar suíte completa**

Run: `pytest -v`
Expected: 9 passed (4 em test_sebrae + 5 em test_market_sizing).

- [ ] **Step 4: Commit**

```bash
git add tests/test_market_sizing.py
git commit -m "test: invariante do funil TAM >= SAM >= SOM"
```

---

## Task 9: Notebook — Bloco A (caracterização descritiva)

**Files:**
- Modify: `notebooks/3. Dados Sebrae.ipynb`

Adicionar células **após** a célula de coleta existente. A coleta já gravou `data/raw/sebrae.json`.

- [ ] **Step 1: Célula de imports e carga**

```python
import sys, os
sys.path.append(os.path.abspath(".."))  # acesso a src/
import pandas as pd
import matplotlib.pyplot as plt
from src import sebrae
from src import market_sizing as ms

raw = sebrae.load_raw("../data/raw/sebrae.json")
```

- [ ] **Step 2: Composição por porte (barras)**

```python
df_porte_ano = sebrae.clean_portes(
    sebrae.to_df(raw, "RF__Establishments__Open Activity Year,Company Size Sebrae")
)
comp = df_porte_ano.groupby("porte")["Establishments"].sum().reindex(
    ["MEI", "ME", "EPP", "Outros"]
)
ax = comp.plot.bar(title="Estabelecimentos por porte — São Paulo")
ax.set_ylabel("Nº de estabelecimentos")
plt.tight_layout(); plt.show()
comp
```

- [ ] **Step 3: Curva de aberturas 1980–2026 (linha por porte)**

```python
curva = (df_porte_ano[df_porte_ano["porte"].isin(["MEI", "ME", "EPP"])]
         .pivot_table(index="Open Activity Year", columns="porte",
                      values="Establishments", aggfunc="sum"))
ax = curva.plot(title="Aberturas de empresas por ano e porte")
ax.set_ylabel("Nº de aberturas")
plt.tight_layout(); plt.show()
```

- [ ] **Step 4: Distribuição setorial (barras empilhadas porte×setor)**

```python
df_ps = sebrae.clean_portes(
    sebrae.to_df(raw, "RF__Establishments__Grande Sector,Company Size Sebrae")
)
pivot = df_ps[df_ps["porte"].isin(["MEI", "ME", "EPP"])].pivot_table(
    index="Grande Sector", columns="porte", values="Establishments", aggfunc="sum"
).fillna(0)
ax = pivot.plot.bar(stacked=True, title="PME por setor e porte")
ax.set_ylabel("Nº de estabelecimentos")
plt.tight_layout(); plt.show()
pivot
```

- [ ] **Step 5: Perfil jurídico (top-10)**

```python
nat = sebrae.to_df(raw, "RF__Establishments__Legal Nature")
top = nat.groupby("Legal Nature")["Establishments"].sum().nlargest(10)
ax = top.sort_values().plot.barh(title="Top 10 naturezas jurídicas")
plt.tight_layout(); plt.show()
top
```

- [ ] **Step 6: Penetração Sebrae por setor**

```python
cli = sebrae.to_df(raw, "RF__Establishments__Sebrae Client Indicator,Grande Sector")
pen = cli.pivot_table(index="Grande Sector", columns="Sebrae Client Indicator",
                      values="Establishments", aggfunc="sum").fillna(0)
pen["% cliente"] = 100 * pen.get("Sim", 0) / pen.sum(axis=1)
pen
```

- [ ] **Step 7: Emprego & salário MPE (RAIS)**

```python
rais = sebrae.to_df(raw, "RAIS_workers__Remuneration Avg Nominal,Workers__Grande Sector,Year")
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
rais.pivot_table(index="Year", columns="Grande Sector", values="Workers", aggfunc="sum").plot(ax=ax[0], title="Vínculos MPE por setor")
rais.pivot_table(index="Year", columns="Grande Sector", values="Remuneration Avg Nominal", aggfunc="mean").plot(ax=ax[1], title="Remuneração média nominal")
plt.tight_layout(); plt.show()
```

- [ ] **Step 8: Dinâmica recente (CAGED 2026) e contexto socioeconômico**

```python
caged = sebrae.to_df(raw, "CAGED_movements__Movement Balance,Admissions,Resignations__Grande Sector")
ax = caged.set_index("Grande Sector")["Movement Balance"].plot.bar(title="Saldo de empregos por setor — 2026")
plt.tight_layout(); plt.show()

pop = sebrae.to_df(raw, "IBGE_Censo_Pop_Sit__Population__Year,Municipality")
pop.plot(x="Year", y="Population", title="População — São Paulo"); plt.tight_layout(); plt.show()
caged
```

- [ ] **Step 9: Rodar o notebook até aqui (sanity check)**

Run (na pasta `notebooks/`): `jupyter nbconvert --to notebook --execute --inplace "3. Dados Sebrae.ipynb"`
Expected: executa sem exceção; gráficos renderizados.

- [ ] **Step 10: Commit**

```bash
git add "notebooks/3. Dados Sebrae.ipynb"
git commit -m "feat: notebook Bloco A — caracterização descritiva PME"
```

---

## Task 10: Notebook — Bloco B (TAM/SAM/SOM) + Bloco C (saídas)

**Files:**
- Modify: `notebooks/3. Dados Sebrae.ipynb`

- [ ] **Step 1: Premissas (placeholders para calibrar)**

```python
# === PREMISSAS — TODO calibrar ===
PRECOS_MENSAIS = [None]            # TODO: ex. [50, 100, 200] R$/PME/mês
TAXAS_SOM = {"pessimista": None,   # TODO: ex. 0.01
             "base": None,         # TODO: ex. 0.03
             "otimista": None}     # TODO: ex. 0.05
```

- [ ] **Step 2: TAM e SAM**

```python
tam = ms.compute_tam(
    df_porte_ano.groupby("porte", as_index=False)["Establishments"].sum()
)
sam_df = ms.compute_sam(df_ps, sebrae.SAM_SETORES)
sam_total = sam_df["sam"].sum()
print("TAM (PME):", tam["tam_pme"])
print("SAM (Com+Serv+Ind):", sam_total)
sam_df
```

- [ ] **Step 3: SOM (executa só quando taxas calibradas)**

```python
if all(v is not None for v in TAXAS_SOM.values()):
    som_df = ms.compute_som(sam_total, TAXAS_SOM)
    display(som_df)
else:
    print("Defina TAXAS_SOM para calcular o SOM.")
    som_df = None
```

- [ ] **Step 4: Funil visual (nº de empresas)**

```python
estagios = {"TAM": tam["tam_pme"], "SAM": sam_total}
if som_df is not None:
    estagios["SOM (base)"] = float(som_df.set_index("cenario").loc["base", "som"])
ax = pd.Series(estagios).plot.barh(title="Funil de mercado (nº de empresas)")
ax.invert_yaxis(); plt.tight_layout(); plt.show()
estagios
```

- [ ] **Step 5: Conversão em R$ (sensibilidade — executa quando preços calibrados)**

```python
if all(p is not None for p in PRECOS_MENSAIS):
    rev = {
        "TAM": ms.to_revenue(tam["tam_pme"], PRECOS_MENSAIS),
        "SAM": ms.to_revenue(sam_total, PRECOS_MENSAIS),
    }
    rev_df = pd.DataFrame(rev).T  # linhas=estágio, colunas=preço → R$/ano
    display(rev_df)
else:
    print("Defina PRECOS_MENSAIS para converter em R$.")
    rev_df = None
```

- [ ] **Step 6: Bloco C — persistir saídas em `data/interim/`**

```python
import os
os.makedirs("../data/interim", exist_ok=True)

comp.to_frame("estabelecimentos").to_csv("../data/interim/pme_porte.csv")
pivot.to_csv("../data/interim/pme_porte_setor.csv")

funil = pd.DataFrame({"estagio": list(estagios), "n_empresas": list(estagios.values())})
funil.to_csv("../data/interim/tam_sam_som.csv", index=False)

contexto = rais.merge(caged[["Grande Sector", "Movement Balance"]], on="Grande Sector", how="left")
contexto.to_csv("../data/interim/contexto_socioecon.csv", index=False)
print("Saídas gravadas em data/interim/")
```

- [ ] **Step 7: Sanity check — SAM por setor ≈ totais RF setor**

```python
totais_setor = (df_ps[df_ps["porte"].isin(["MEI","ME","EPP"])]
                .groupby("Grande Sector")["Establishments"].sum())
check = sam_df.set_index("setor")["sam"]
assert (check.reindex(check.index) <= totais_setor.reindex(check.index) + 1e-6).all()
print("Sanity check OK: SAM por setor consistente com totais.")
```

- [ ] **Step 8: Rodar notebook completo**

Run (na pasta `notebooks/`): `jupyter nbconvert --to notebook --execute --inplace "3. Dados Sebrae.ipynb"`
Expected: executa sem exceção. Como premissas são `None`, blocos SOM/R$ imprimem aviso (esperado).

- [ ] **Step 9: Commit**

```bash
git add "notebooks/3. Dados Sebrae.ipynb"
git commit -m "feat: notebook Blocos B (TAM/SAM/SOM) e C (saídas interim)"
```

---

## Task 11: Verificação final

**Files:** nenhum (validação)

- [ ] **Step 1: Suíte completa de testes**

Run: `pytest -v`
Expected: todos os testes passam (sebrae + market_sizing).

- [ ] **Step 2: Confirmar artefatos gerados**

Run: `ls data/interim/`
Expected: `pme_porte.csv`, `pme_porte_setor.csv`, `tam_sam_som.csv`, `contexto_socioecon.csv` presentes.

- [ ] **Step 3: Commit final (se houver pendências)**

```bash
git add -A
git commit -m "chore: artefatos da análise PME em data/interim"
```

---

## Notas de calibração (pós-implementação, pelo autor)

- `PRECOS_MENSAIS` e `TAXAS_SOM` no notebook são placeholders `None`. Definir valores reais reativa os blocos SOM e R$ automaticamente (já há guarda `if`).
- Integração com `data/raw/interrupcoes-energia-*` é fase seguinte — fora do escopo deste plano.
