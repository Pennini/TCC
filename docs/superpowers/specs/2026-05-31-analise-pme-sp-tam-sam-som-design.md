# Análise PME São Paulo (Sebrae) + Dimensionamento de Mercado TAM/SAM/SOM

**Data:** 2026-05-31
**Status:** Aprovado (design)
**Contexto do TCC:** Desenvolver um modelo de negócios para reduzir o impacto de quedas de
energia imprevisíveis em PMEs de São Paulo. Esta análise entrega o **contexto de mercado**
(caracterização descritiva do ecossistema PME) e o **dimensionamento da oportunidade**
(TAM/SAM/SOM) que fundamentam o capítulo de mercado/oportunidade.

A integração com os dados de interrupção de energia (`data/raw/interrupcoes-energia-*`)
fica para uma fase posterior — esta fase produz artefatos reaproveitáveis para ela.

---

## 1. Objetivo

1. **Caracterizar/diagnosticar** o ecossistema de PMEs (MEI, ME, EPP) da cidade de São Paulo
   a partir dos dados do Observatório Sebrae.
2. **Dimensionar o mercado** em funil TAM → SAM → SOM, expresso em **número de empresas**
   e em **R$ de receita potencial** (com premissas explícitas e análise de sensibilidade).

Escopo do município: São Paulo (código IBGE `3550308`).

Definição de **PME** nesta análise: `MEI + ME + EPP` (exclui a categoria "Outros" da RF,
que agrega médio e grande porte).

---

## 2. Fonte de dados

API do Observatório Sebrae (cubo Tesseract):
`https://apiv2-observatorio.sebrae.com.br/tesseract/data.jsonrecords`

Coleta feita no notebook `notebooks/3. Dados Sebrae.ipynb`, persistida em
`data/raw/sebrae.json`.

### 2.1 Correção aplicada (colisão de chave)

A versão original gerava a chave do dicionário como `f"{cube}_{measures}"`. Como três
queries usavam o cubo `RF` com a mesma measure `Establishments`, elas colidiam e apenas a
última sobrevivia — perdendo os recortes de setor×cliente e natureza jurídica.

**Correção:** chave única `f"{cube}__{measures}__{drilldowns}"`, extraindo e decodificando
os parâmetros da URL com uma função `get_param`. Resultado: 12 datasets distintos.

### 2.2 Query adicionada (porte × setor)

O cruzamento porte×setor não existia nos dados (havia porte×ano e setor×cliente, separados).
Esse cruzamento é o núcleo do SAM. Foi adicionada a query:

```
RF?drilldowns=Grande Sector,Company Size Sebrae&exclude=Company Size Sebrae:0
```

→ matriz exata de estabelecimentos por porte e Grande Setor (22 linhas). Evita a premissa
de distribuição de porte uniforme entre setores.

### 2.3 Inventário (12 datasets)

| Chave (resumida)                              | Linhas | Uso na análise |
|-----------------------------------------------|-------:|----------------|
| RF — porte × ano abertura                     | 188    | TAM, curva de aberturas, composição por porte |
| RF — porte × setor *(novo)*                    | 22     | **SAM** |
| RF — setor × cliente Sebrae                    | 8      | penetração Sebrae, contexto de alcance |
| RF — natureza jurídica                         | 72     | perfil jurídico das PMEs |
| CAGED — movimentação por setor 2026            | 5      | dinâmica recente de emprego |
| RAIS — setor × ano (MPE)                        | 36     | emprego e salário médio MPE |
| RAIS — subgrupo CBO 2023 vs 2024               | 395    | detalhe ocupacional (uso secundário) |
| IBGE — pirâmide etária 2022                     | 42     | contexto do mercado consumidor |
| IBGE — evolução populacional                    | 6      | contexto |
| PNUD — Gini 2000/2010                           | 2      | desigualdade (contexto) |
| INEP — distorção idade-série                    | 14     | capital humano (contexto) |
| INEP — abandono escolar                         | 14     | capital humano (contexto) |

### 2.4 Encoding

O JSON está em UTF-8 correto (`Indústria` = `0xfa`/ú, `São Paulo` = `0xe3`/ã). O `�` visto
em terminal é apenas artefato de exibição (console Windows), não corrupção dos dados.
**Nenhum tratamento de encoding é necessário.**

---

## 3. Arquitetura — Abordagem B (notebook + módulo)

Lógica reutilizável e testável em `src/`; o notebook importa, executa e visualiza.

```
src/
  __init__.py
  sebrae.py          # carga + parse + limpeza
  market_sizing.py   # cálculo TAM/SAM/SOM
tests/
  test_market_sizing.py
  test_sebrae.py
notebooks/
  3. Dados Sebrae.ipynb
data/
  raw/sebrae.json        # coleta (12 datasets)
  interim/               # tabelas limpas e resultados (saída)
```

### 3.1 `src/sebrae.py`

Sem acesso à rede — opera sobre o JSON já salvo (reprodutível offline). Interface entre
funções é DataFrame do pandas.

| Função | Responsabilidade |
|--------|------------------|
| `load_raw(path) -> dict`          | lê `sebrae.json` |
| `to_df(raw, key) -> DataFrame`    | extrai `data` de um dataset; erro claro se chave ausente |
| `clean_portes(df) -> DataFrame`   | normaliza rótulo de porte → `MEI / ME / EPP / Outros` |
| `SECTOR_MAP`, `PORTE_MAP`         | constantes de mapeamento de IDs/rótulos |

### 3.2 `src/market_sizing.py`

Premissas (taxas, preços) entram como **parâmetros**, nunca hardcoded.

| Função | Responsabilidade |
|--------|------------------|
| `compute_tam(df_porte) -> dict`                 | TAM = soma MEI+ME+EPP (nº); "Outros" reportado à parte |
| `compute_sam(df_porte_setor, setores) -> DataFrame` | filtra setores-alvo × PME → SAM (nº) |
| `compute_som(sam_n, taxas) -> DataFrame`        | SOM = SAM × taxa, por cenário |
| `to_revenue(n, precos_mensais) -> dict`         | nº × preço × 12 → R$/ano; aceita lista de preços (sensibilidade) |

---

## 4. Fluxo do notebook

### Bloco A — Caracterização descritiva (contexto de mercado)

| Análise | Dataset | Visual |
|---------|---------|--------|
| Composição por porte           | RF porte×ano        | barras MEI/ME/EPP + % |
| Curva de aberturas 1980–2026   | RF porte×ano        | linha por porte |
| Distribuição setorial          | RF porte×setor      | barras empilhadas porte×setor |
| Perfil jurídico                | RF natureza jurídica| top-10 naturezas |
| Penetração Sebrae              | RF setor×cliente    | % cliente por setor |
| Emprego & salário MPE          | RAIS setor×ano      | linha workers + salário |
| Dinâmica recente de emprego    | CAGED 2026          | saldo por setor |
| Contexto consumidor            | IBGE pop/idade, Gini, INEP | pirâmide, série populacional |

### Bloco B — TAM/SAM/SOM

- **TAM** = MEI+ME+EPP ativas em SP (nº + R$).
- **SAM** = PME em Comércio + Serviços + Indústria (nº + R$).
- **SOM** = SAM × {pessimista, base, otimista} (nº + R$).
- Visual: funil/cascata + tabela de cenários.
- R$: análise de sensibilidade — grade de preço/PME/mês × taxa de penetração.

### Bloco C — Saídas persistidas em `data/interim/`

| Arquivo | Conteúdo |
|---------|----------|
| `pme_porte.csv`          | composição por porte |
| `pme_porte_setor.csv`    | matriz porte×setor (base do SAM) |
| `tam_sam_som.csv`        | funil em nº e R$, todos os cenários |
| `contexto_socioecon.csv` | consolidado IBGE/RAIS/CAGED |

Reaproveitáveis na fase de integração com energia, sem re-rodar a API.

---

## 5. Premissas (placeholders — a calibrar pelo autor)

Marcadas no notebook e no módulo como `# TODO calibrar`. **Não há valores fixos travados.**

- **Preço/PME/mês** da solução: placeholder, calibrar (entram como lista para sensibilidade).
- **Taxas de penetração SOM**: placeholder para pessimista/base/otimista (% do SAM).
- **Definição de PME**: `MEI + ME + EPP` (exclui "Outros" = médio/grande).
- **Setores do SAM**: Comércio + Serviços + Indústria (exclui Agricultura e Adm. pública).

---

## 6. Testes & robustez (TDD)

`market_sizing.py` escrito test-first.

| Teste | Verifica |
|-------|----------|
| `test_tam_soma_portes`    | TAM = MEI+ME+EPP, exclui "Outros" |
| `test_sam_filtra_setores` | SAM só setores-alvo; soma ≤ TAM |
| `test_som_cenarios`       | SOM = SAM×taxa; pess < base < otim |
| `test_to_revenue`         | nº×preço×12; sensibilidade retorna grade |
| `test_funil_monotonico`   | invariante TAM ≥ SAM ≥ SOM |
| `test_to_df_*` / `test_clean_portes` | parse extrai `data`; rótulos de porte normalizados (fixture mini-JSON) |

**Robustez adicional:**
- `to_df` levanta erro claro para chave ausente.
- Sanity check no notebook: soma do SAM por setor ≈ totais de RF setor.

---

## 7. Fora de escopo (esta fase)

- Integração com dados de interrupção de energia (fase seguinte).
- Cálculo de "dor" quantificada (frequência/duração de quedas × PME).
- Calibração final de preços e taxas (autor define depois).
