# Data Major — Mortalidade por Causas Evitáveis no Brasil

Projeto final da disciplina **Tópicos em Banco de Dados** — IESB, 2026/01.

## Problema

A alta incidência de mortalidade por causas evitáveis no Brasil e sua correlação com desigualdades socioeconômicas municipais. Causas evitáveis são aquelas que poderiam ser prevenidas por ações do Sistema Único de Saúde — imunização, diagnóstico precoce, atenção básica, políticas de saúde pública.

## Objetivo

Construir um pipeline de dados completo (ETL) e um modelo de regressão multivariada capaz de estimar o número de mortes evitáveis por município em função de indicadores socioeconômicos, de investimento em saúde e de desenvolvimento humano.

## Arquitetura

```
Extração (01)          Transformação (02)        Modelagem (03 — em breve)
─────────────          ──────────────────        ────────────────────────
SIM-DATASUS   ──┐
IBGE Sidra    ──┤──► feature_matrix.parquet ──► Regressão XGBoost + Linear
SICONFI       ──┤      (município × ano)         Projeção contrafactual
IPEA Data     ──┘                                Feature importance (SHAP)
```

## Fontes de Dados

| Fonte | Conteúdo | Acesso |
|---|---|---|
| [SIM-DATASUS](https://datasus.saude.gov.br/mortalidade-desde-1996-pela-cid-10) | Microdados de óbitos (CID-10) | FTP DATASUS |
| [IBGE Sidra Tab. 4714](https://sidra.ibge.gov.br) | População municipal (Censo 2022) | API |
| [IBGE Sidra Tab. 5938](https://sidra.ibge.gov.br) | PIB municipal | API |
| [SICONFI / Tesouro Nacional](https://apidatalake.tesouro.gov.br) | Despesa em saúde por município | API |
| [IPEA Data (Atlas DH)](http://www.ipeadata.gov.br) | IDH-M, Gini, renda por quinto, pobreza | API |

## Classificação de Causas Evitáveis

Baseada na **Lista Brasileira de Causas de Mortes Evitáveis** (5–74 anos), Malta et al. 2007 + atualização 2010 (SVS/MS). Implementada inline no notebook 02 com 717 prefixos CID-10 organizados em 5 grupos:

| Grupo | Descrição |
|---|---|
| `imunoprevencao` | Reduzíveis por vacinação |
| `doencas_infecciosas` | Tuberculose, HIV, hepatites, DSTs, infecções respiratórias |
| `doencas_nao_transmissiveis` | Neoplasias, doenças cardiovasculares, diabetes, DPOC |
| `morte_materna` | Gravidez, parto e puerpério |
| `causas_externas` | Acidentes, agressões, suicídios |

## Features do Modelo

| Categoria | Variáveis |
|---|---|
| Target | `OBITOS_EVITAVEIS`, `TAXA_EVITAVEL_100K` |
| Economia | `PIB_PER_CAPITA`, `RDPC` |
| Saúde pública | `DESPESA_SAUDE_PC` (SICONFI) |
| Desigualdade | `GINI`, `THEIL`, `RDPC1`–`RDPC4` (renda média por quinto) |
| IDH | `IDHM`, `IDHM_E`, `IDHM_L`, `IDHM_R` |
| Pobreza | `PMPOB`, `PIND` |
| Social | `T_ANALF15M`, `ESPVIDA`, `T_AGUA` |
| Geográfica | `UF`, `REGIAO` |

## Notebooks

| Notebook | Etapa | Descrição |
|---|---|---|
| `01_extracao.ipynb` | Extract | Download de todas as fontes, idempotente, com cache local |
| `02_transformacao.ipynb` | Transform + Load | LBCE inline, limpeza, agregação, feature matrix |
| `03_regressao.ipynb` *(em breve)* | Mining | XGBoost, regressão linear, projeção contrafactual, SHAP |

## Setup

```bash
# Clone o repositório
git clone https://github.com/Skinnyopeats/Data-Major-IESB-2026-01-.git
cd Data-Major-IESB-2026-01-

# Instale as dependências (requer Python 3.11+)
pip install -r requirements.txt

# Registre o kernel no Jupyter
python -m ipykernel install --user --name topicos-bd --display-name "Python - Tópicos BD"

# Execute os notebooks em ordem
jupyter notebook
```

> **Nota:** A pasta `data/` não está no repositório (`.gitignore`). Ela é gerada automaticamente ao executar `01_extracao.ipynb`.

## Requisitos

```
datasus-dbc>=0.1.3   # conversão DBC→DBF (Windows, sem compilação)
dbfread>=2.0         # leitura DBF → DataFrame
pandas>=2.0
pyarrow>=14.0
numpy>=1.24
requests             # chamadas às APIs (IBGE, SICONFI, IPEA)
jupyter / ipykernel
matplotlib
seaborn
```

## Referências

- Malta DC et al. *Tabela Brasileira de Causas de Mortes Evitáveis.* Epidemiol. Serv. Saúde 16(4):233-244, 2007.
- Malta DC et al. *Atualização da lista de causas de mortes evitáveis* [Nota técnica]. Epidemiol. Serv. Saúde 19(2):173-176, 2010.
- DATASUS/SVS-MS. *Lista de Tabulação de Causas Evitáveis de 5 a 74 anos.* Disponível em: [drive.prefeitura.sp.gov.br](https://drive.prefeitura.sp.gov.br/cidade/secretarias/upload/saude/Anexo%202_MALTA_Atualizacao_da_lista_de_causas_de_mortes_2010.pdf)
