# Data Major — Mortalidade por Causas Evitáveis no Brasil

Projeto da disciplina **Tópicos em Banco de Dados** — IESB, 2026/01.

## Problema

A alta incidência de mortalidade por causas evitáveis no Brasil e sua correlação com desigualdades socioeconômicas municipais. Causas evitáveis são aquelas que poderiam ser prevenidas por ações do Sistema Único de Saúde — imunização, diagnóstico precoce, atenção básica, políticas de saúde pública.

## Objetivo

Construir um pipeline de dados completo (ETL) e aplicar técnicas de modelagem e mineração para (1) quantificar a associação entre condições socioeconômicas e a mortalidade evitável, (2) identificar perfis típicos de município e (3) caracterizar o padrão de causas de cada perfil. O painel cobre **2022–2024** (município × ano).

## Arquitetura

```
Extração (01)        Transformação (02 / 02b)      Análise (03 / 04 / 05 / 06)
─────────────        ────────────────────────      ──────────────────────────
SIM-DATASUS  ──┐                                    03 Regressão (OLS + RF + XGBoost)
IBGE Sidra   ──┤──► feature_matrix.parquet  ──────► 04 Clusterização (K-Means, k=4)
SICONFI      ──┤      (município × ano,             05 Mineração de causas (CID-10)
IPEA Data    ──┤       taxa bruta + padronizada)    06 Padronização etária da taxa
Censo p/idade──┘     microdados_evitaveis.parquet
                      (1 óbito por linha)
```

> **Taxa padronizada por idade:** a `feature_matrix` traz a taxa bruta e a **padronizada por idade** (padronização direta, denominador por faixa do Censo 2022). A padronizada é o desfecho principal da regressão — corrige o paradoxo de Sul/Sudeste aparecerem com mortalidade maior só por terem população mais envelhecida.

> Relatório final em `relatorio/relatorio_final.tex`.

## Fontes de Dados

| Fonte | Conteúdo | Acesso |
|---|---|---|
| [SIM-DATASUS](https://datasus.saude.gov.br/mortalidade-desde-1996-pela-cid-10) | Microdados de óbitos (CID-10) | FTP DATASUS |
| [IBGE Sidra Tab. 4714](https://sidra.ibge.gov.br) | População municipal (Censo 2022) | API |
| [IBGE Sidra Tab. 9514](https://sidra.ibge.gov.br) | População por faixa etária × município (denominador da padronização) | API |
| [IBGE Sidra Tab. 5938](https://sidra.ibge.gov.br) | PIB municipal | API |
| [SICONFI / Tesouro Nacional](https://apidatalake.tesouro.gov.br) | Despesa em saúde por município | API |
| [IPEA Data (Atlas DH)](http://www.ipeadata.gov.br) | IDH-M, Gini, renda por quinto, pobreza (Censo 2010) | API |
| [DATASUS — tabelas CID-10](https://ftp.datasus.gov.br) | Descrições oficiais dos códigos CID-10 (`CID10.DBF`) | FTP |

## Classificação de Causas Evitáveis

Baseada na **Lista Brasileira de Causas de Mortes Evitáveis** (5–74 anos), Malta et al. 2007 + atualização 2010 (SVS/MS). Implementada inline no notebook 02. A lista oficial tem 5 grupos; usamos **4** (o grupo de causas externas é definido mas **excluído** da análise — ver nota abaixo):

| Grupo | Descrição |
|---|---|
| `imunoprevencao` | Reduzíveis por vacinação |
| `doencas_infecciosas` | Tuberculose, HIV, hepatites, DSTs, infecções respiratórias |
| `doencas_nao_transmissiveis` | Neoplasias, doenças cardiovasculares, diabetes, DPOC |
| `morte_materna` | Gravidez, parto e puerpério |

> **Causas externas excluídas:** acidentes, quedas, agressões e suicídios respondem a fatores (segurança pública, infraestrutura viária, violência) ausentes do nosso conjunto de variáveis socioeconômicas. Incluí-las introduziria ruído sem ganho explicativo. O escopo é o das causas evitáveis sensíveis ao SUS e ao desenvolvimento socioeconômico.

## Features do Modelo

| Categoria | Variáveis |
|---|---|
| Target | `TAXA_PADRONIZADA_100K` (principal), `TAXA_EVITAVEL_100K` (bruta), `OBITOS_EVITAVEIS` |
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
| `01_extracao.ipynb` | Extract | Download de todas as fontes, idempotente, com cache local e *fallbacks* de ano |
| `02_transformacao.ipynb` | Transform + Load | LBCE inline, limpeza, agregação, feature matrix (município × ano) |
| `02b_transformacao_microdados.ipynb` | Transform | Dataset individualizado (1 óbito/linha) + estatística descritiva |
| `03_regressao.ipynb` | Mining | Painel *pooled*: OLS (cluster-robust), Random Forest, XGBoost |
| `04_clusterizacao.ipynb` | Mining | Estatística descritiva + K-Means (k=4) dos municípios |
| `05_mineracao.ipynb` | Mining | Top causas CID-10, *lift* e vocabulário distintivo por cluster |
| `06_taxa_padronizada_idade.ipynb` | Mining | Padronização etária da taxa; comparação bruta × padronizada e impacto na regressão |

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
dbfread>=2.0         # leitura DBF → DataFrame (SIM + tabelas CID-10)
pandas>=2.0
pyarrow>=14.0
numpy>=1.24
requests             # chamadas às APIs (IBGE, SICONFI, IPEA)
scikit-learn>=1.3    # K-Means, RandomForest, métricas
statsmodels>=0.14    # OLS com erros cluster-robust
xgboost>=2.0         # gradient boosting
scipy                # ANOVA
jupyter / ipykernel
matplotlib
seaborn
```

## Referências

- Malta DC et al. *Tabela Brasileira de Causas de Mortes Evitáveis.* Epidemiol. Serv. Saúde 16(4):233-244, 2007.
- Malta DC et al. *Atualização da lista de causas de mortes evitáveis* [Nota técnica]. Epidemiol. Serv. Saúde 19(2):173-176, 2010.
- DATASUS/SVS-MS. *Lista de Tabulação de Causas Evitáveis de 5 a 74 anos.* Disponível em: [drive.prefeitura.sp.gov.br](https://drive.prefeitura.sp.gov.br/cidade/secretarias/upload/saude/Anexo%202_MALTA_Atualizacao_da_lista_de_causas_de_mortes_2010.pdf)

## Alunos
Segue o grupo responsável pelo desenvolvimento do projeto.

| Nome | 
|------|
| Amanda Ferreira Dahm | 
| João Marcos Santos e Carvalho |
| Maria Clara Fontenele Silva |
| Vitor Mendonça Mendes|
