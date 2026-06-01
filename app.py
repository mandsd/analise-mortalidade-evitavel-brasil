import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ─── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mortalidade por Causas Evitáveis — Brasil",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

CLUSTER_LABELS = {
    0: "Cluster 0 — Norte/NE Vulnerável",
    1: "Cluster 1 — Interior em Desenvolvimento",
    2: "Cluster 2 — Sul/SE Médio",
    3: "Cluster 3 — Grandes Centros",
}
CLUSTER_COLORS = {0: "#ef4444", 1: "#f97316", 2: "#3b82f6", 3: "#22c55e"}

# ─── Loaders ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_perfil():
    df = pd.read_csv(f"{MODELS_DIR}/perfil_clusters.csv")
    df["label"] = df["CLUSTER"].map(CLUSTER_LABELS)
    df["color"] = df["CLUSTER"].map(CLUSTER_COLORS)
    return df

@st.cache_data
def load_metricas():
    return pd.read_csv(f"{MODELS_DIR}/metricas_modelos.csv")

@st.cache_data
def load_coeficientes():
    return pd.read_csv(f"{MODELS_DIR}/coeficientes_ols.csv")

@st.cache_data
def load_importancia():
    return pd.read_csv(f"{MODELS_DIR}/importancia_features.csv")

@st.cache_data
def load_top_causas():
    return pd.read_csv(f"{MODELS_DIR}/top_causas_cluster.csv")

@st.cache_data
def load_lbce():
    df = pd.read_csv(f"{MODELS_DIR}/lbce_por_cluster.csv")
    df["label"] = df["CLUSTER"].map(CLUSTER_LABELS)
    return df

@st.cache_data
def load_lift():
    df = pd.read_csv(f"{MODELS_DIR}/lift_causas_cluster.csv")
    df["label"] = df["CLUSTER"].map(CLUSTER_LABELS)
    return df

@st.cache_data
def load_termos():
    df = pd.read_csv(f"{MODELS_DIR}/termos_distintivos_cluster.csv")
    df["label"] = df["CLUSTER"].map(CLUSTER_LABELS)
    return df

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("iesblogo.png", width=120)
    st.markdown("## 🏥 Mortalidade Evitável")
    st.markdown("**Tópicos em Banco de Dados**  \nIESB — 2026/01")
    st.divider()

    pagina = st.radio(
        "Navegação",
        [
            "📊 Visão Geral",
            "🗺️ Perfis de Cluster",
            "🔬 Causas de Óbito",
            "📈 Modelos Preditivos",
            "ℹ️ Sobre o Projeto",
        ],
    )
    st.divider()
    st.caption("Dados: SIM-DATASUS · IBGE · SICONFI · IPEA  \nPeríodo: 2022–2024")

# ─── Helpers ───────────────────────────────────────────────────────────────────
def metric_card(col, label, value, delta=None, help=None):
    col.metric(label, value, delta=delta, help=help)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Visão Geral
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "📊 Visão Geral":
    st.title("📊 Mortalidade por Causas Evitáveis no Brasil")
    st.markdown(
        "Análise de **2022–2024** sobre a relação entre desigualdades socioeconômicas "
        "municipais e mortalidade evitável sensível ao SUS."
    )
    st.divider()

    perfil = load_perfil()
    total_mun = perfil["n_municipios"].sum()
    total_pop = perfil["populacao_total"].sum()
    taxa_media_bruta = (perfil["taxa_bruta"] * perfil["%_pop_brasil"]).sum() / 100
    taxa_media_pad = (perfil["taxa_padronizada"] * perfil["%_pop_brasil"]).sum() / 100

    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, "Municípios analisados", f"{int(total_mun):,}".replace(",", "."), help="Total de municípios no painel 2022–2024")
    metric_card(c2, "População coberta", f"{total_pop/1e6:.1f} M", help="Soma da população total dos clusters")
    metric_card(c3, "Taxa bruta média", f"{taxa_media_bruta:.1f} /100k", help="Óbitos evitáveis por 100 mil hab. (bruta)")
    metric_card(c4, "Taxa padronizada média", f"{taxa_media_pad:.1f} /100k", help="Corrigida pelo envelhecimento populacional")

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Taxa padronizada por cluster")
        fig = px.bar(
            perfil,
            x="label",
            y="taxa_padronizada",
            color="label",
            color_discrete_map={v: CLUSTER_COLORS[k] for k, v in CLUSTER_LABELS.items()},
            labels={"taxa_padronizada": "Taxa padronizada /100k", "label": ""},
            text_auto=".1f",
        )
        fig.update_layout(showlegend=False, height=340)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("IDH × Taxa padronizada")
        fig2 = px.scatter(
            perfil,
            x="IDHM",
            y="taxa_padronizada",
            size="n_municipios",
            color="label",
            color_discrete_map={v: CLUSTER_COLORS[k] for k, v in CLUSTER_LABELS.items()},
            text="label",
            labels={"IDHM": "IDH Municipal", "taxa_padronizada": "Taxa padronizada /100k", "label": "Cluster"},
            hover_data=["n_municipios", "GINI", "PIB_pc"],
        )
        fig2.update_traces(textposition="top center", textfont_size=9)
        fig2.update_layout(showlegend=False, height=340)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Comparativo geral dos clusters")
    variaveis = {
        "Taxa padronizada (/100k)": "taxa_padronizada",
        "IDH Municipal": "IDHM",
        "Índice de Gini": "GINI",
        "PIB per capita (log R$)": "PIB_pc",
        "Desp. saúde per capita (log R$)": "desp_saude_pc",
        "Analfabetismo 15+ (%)": "ANALF15M",
        "Acesso à água (%)": "T_AGUA",
        "Esperança de vida": "ESPVIDA",
    }
    sel_var = st.selectbox("Selecione a variável", list(variaveis.keys()))
    col_var = variaveis[sel_var]

    fig3 = px.bar(
        perfil,
        x="label",
        y=col_var,
        color="label",
        color_discrete_map={v: CLUSTER_COLORS[k] for k, v in CLUSTER_LABELS.items()},
        text_auto=".2f",
        labels={col_var: sel_var, "label": ""},
    )
    fig3.update_layout(showlegend=False, height=300)
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Perfis de Cluster
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🗺️ Perfis de Cluster":
    st.title("🗺️ Perfis de Cluster de Municípios")
    st.markdown(
        "K-Means (k=4) aplicado sobre a **feature matrix** município × ano. "
        "Cada cluster agrupa municípios com perfis socioeconômicos e de mortalidade semelhantes."
    )
    st.divider()

    perfil = load_perfil()
    lbce = load_lbce()

    cluster_sel = st.selectbox(
        "Selecione um cluster para detalhar",
        options=list(CLUSTER_LABELS.keys()),
        format_func=lambda x: CLUSTER_LABELS[x],
    )
    row = perfil[perfil["CLUSTER"] == cluster_sel].iloc[0]
    cor = CLUSTER_COLORS[cluster_sel]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Municípios", f"{int(row['n_municipios']):,}".replace(",", "."))
    c2.metric("% pop. Brasil", f"{row['%_pop_brasil']}%")
    c3.metric("IDH-M", f"{row['IDHM']:.2f}")
    c4.metric("Gini", f"{row['GINI']:.2f}")
    c5.metric("Taxa padronizada", f"{row['taxa_padronizada']:.1f} /100k")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Indicadores socioeconômicos")
        indicadores = {
            "PIB per capita (log R$)": row["PIB_pc"],
            "Desp. saúde p.c. (log R$)": row["desp_saude_pc"],
            "Analfabetismo 15+ (%)": row["ANALF15M"],
            "Acesso à água (%)": row["T_AGUA"],
            "Esperança de vida (anos)": row["ESPVIDA"],
        }
        df_ind = pd.DataFrame({"Indicador": indicadores.keys(), "Valor": indicadores.values()})
        fig = px.bar(
            df_ind, x="Valor", y="Indicador", orientation="h",
            color_discrete_sequence=[cor], text_auto=".2f"
        )
        fig.update_layout(height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Composição por grupo de causas evitáveis (LBCE)")
        row_lbce = lbce[lbce["CLUSTER"] == cluster_sel].iloc[0]
        labels_lbce = ["D. Infecciosas", "D. Não Transmissíveis", "Imunopreveníveis", "Morte Materna"]
        vals_lbce = [
            row_lbce["doencas_infecciosas"],
            row_lbce["doencas_nao_transmissiveis"],
            row_lbce["imunoprevencao"],
            row_lbce["morte_materna"],
        ]
        fig2 = px.pie(
            names=labels_lbce, values=vals_lbce,
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Comparação entre todos os clusters — radar")

    cats = ["taxa_padronizada", "IDHM", "GINI", "T_AGUA", "ESPVIDA"]
    cats_label = ["Taxa padronizada", "IDH-M", "Gini", "Água (%)", "Esp. de vida"]

    def norm(col):
        mn, mx = perfil[col].min(), perfil[col].max()
        return (perfil[col] - mn) / (mx - mn + 1e-9)

    fig3 = go.Figure()
    for _, r in perfil.iterrows():
        vals = [norm(c).iloc[int(r["CLUSTER"])] for c in cats]
        vals += [vals[0]]
        fig3.add_trace(go.Scatterpolar(
            r=vals,
            theta=cats_label + [cats_label[0]],
            name=r["label"],
            fill="toself",
            line_color=CLUSTER_COLORS[int(r["CLUSTER"])],
            opacity=0.6,
        ))
    fig3.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=420,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Causas de Óbito
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🔬 Causas de Óbito":
    st.title("🔬 Análise de Causas de Óbito por CID-10")
    st.markdown("Top causas, lift e termos distintivos de cada cluster.")
    st.divider()

    top_causas = load_top_causas()
    lift = load_lift()
    termos = load_termos()

    DESCRICOES_CID = {
        "I64": "AVC (tipo não especificado)",
        "F10": "Transtornos por uso de álcool",
        "E11": "Diabetes mellitus tipo 2",
        "B57": "Doença de Chagas",
        "A09": "Diarreia e gastroenterite infecciosa",
        "K70": "Doença alcoólica do fígado",
        "G40": "Epilepsia",
        "C44": "Neoplasia maligna da pele",
        "C53": "Câncer do colo do útero",
        "N18": "Insuficiência renal crônica",
        "I21": "Infarto agudo do miocárdio",
        "E14": "Diabetes mellitus NE",
        "J18": "Pneumonia por microrganismo NE",
        "I10": "Hipertensão essencial",
        "C34": "Câncer de pulmão / brônquios",
        "I50": "Insuficiência cardíaca",
        "J44": "DPOC",
        "A41": "Septicemia",
        "I61": "Hemorragia intracerebral",
        "C50": "Câncer de mama",
        "C16": "Câncer de estômago",
        "C18": "Câncer de cólon",
        "I25": "Doença isquêmica crônica do coração",
        "I67": "Outras doenças cerebrovasculares",
        "I20": "Angina pectoris",
        "J45": "Asma",
        "B24": "HIV/AIDS",
        "A15": "Tuberculose respiratória",
    }

    tab1, tab2, tab3 = st.tabs(["📋 Top causas", "📐 Lift por CID-10", "🔤 Termos distintivos"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            cluster_tc = st.selectbox(
                "Cluster",
                options=list(CLUSTER_LABELS.keys()),
                format_func=lambda x: CLUSTER_LABELS[x],
                key="tc",
            )
            n_top = st.slider("Nº de causas", 5, 15, 10)
        with c2:
            df_tc = top_causas[top_causas["CLUSTER"] == cluster_tc].head(n_top).copy()
            df_tc["descricao_legivel"] = df_tc.apply(
                lambda r: DESCRICOES_CID.get(r["CID_CAT3"], r["descricao"].title()), axis=1
            )
            fig = px.bar(
                df_tc.sort_values("pct"),
                x="pct", y="descricao_legivel", orientation="h",
                color_discrete_sequence=[CLUSTER_COLORS[cluster_tc]],
                text="pct",
                labels={"pct": "% dos óbitos do cluster", "descricao_legivel": ""},
                hover_data={"CID_CAT3": True, "descricao": True, "n": True, "descricao_legivel": False},
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(height=max(300, n_top * 35), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        cluster_lift = st.selectbox(
            "Cluster",
            options=list(CLUSTER_LABELS.keys()),
            format_func=lambda x: CLUSTER_LABELS[x],
            key="lift",
        )

        df_lift = lift[lift["CLUSTER"] == cluster_lift].copy()
        df_lift = df_lift.sort_values("lift", ascending=False).head(10)
        df_lift["descricao_legivel"] = df_lift.apply(
            lambda r: DESCRICOES_CID.get(r["CID_CAT3"], r["descricao"].title()), axis=1
        )

        fig = px.bar(
            df_lift.sort_values("lift"),
            x="lift", y="descricao_legivel", orientation="h",
            color="lift",
            color_continuous_scale="RdYlGn",
            text="lift",
            labels={"lift": "Lift (razão vs. média nacional)", "descricao_legivel": ""},
            hover_data={"CID_CAT3": True, "descricao": True, "n": True, "descricao_legivel": False},
        )
        fig.add_vline(x=1.0, line_dash="dash", line_color="gray", annotation_text="Média nacional")
        fig.update_traces(texttemplate="%{text:.2f}x", textposition="outside")
        fig.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**Lift > 1**: causa mais frequente neste cluster do que na média nacional. Quanto maior, mais distintiva.")

    with tab3:
        cluster_ter = st.selectbox(
            "Cluster",
            options=list(CLUSTER_LABELS.keys()),
            format_func=lambda x: CLUSTER_LABELS[x],
            key="termos",
        )
        df_ter = termos[termos["CLUSTER"] == cluster_ter].copy()
        fig = px.bar(
            df_ter.sort_values("score", ascending=False).head(12),
            x="termo", y="score",
            color_discrete_sequence=[CLUSTER_COLORS[cluster_ter]],
            labels={"score": "Score TF-IDF", "termo": "Termo"},
            text_auto=".1f",
        )
        fig.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Termos extraídos das descrições de causas com maior peso TF-IDF neste cluster vs. os demais.")

    st.divider()
    st.subheader("Composição LBCE por cluster — comparativo")
    lbce = load_lbce()
    lbce_melt = lbce.melt(
        id_vars=["CLUSTER", "label"],
        value_vars=["doencas_infecciosas", "doencas_nao_transmissiveis", "imunoprevencao", "morte_materna"],
        var_name="Grupo", value_name="Percentual"
    )
    lbce_melt["Grupo"] = lbce_melt["Grupo"].map({
        "doencas_infecciosas": "D. Infecciosas",
        "doencas_nao_transmissiveis": "D. Não Transmissíveis",
        "imunoprevencao": "Imunopreveníveis",
        "morte_materna": "Morte Materna",
    })
    fig_lbce = px.bar(
        lbce_melt, x="label", y="Percentual", color="Grupo",
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"label": "", "Percentual": "% dos óbitos evitáveis"},
        text_auto=".1f",
    )
    fig_lbce.update_layout(height=380)
    st.plotly_chart(fig_lbce, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Modelos Preditivos
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📈 Modelos Preditivos":
    st.title("📈 Modelos Preditivos")
    st.markdown(
        "Regressão OLS painel (cluster-robust), Random Forest e XGBoost para "
        "prever a **taxa padronizada de mortalidade evitável** por 100k hab."
    )
    st.divider()

    metricas = load_metricas()
    coefs = load_coeficientes()
    imp = load_importancia()

    st.subheader("Desempenho dos modelos")
    c1, c2, c3 = st.columns(3)
    for col, (_, row) in zip([c1, c2, c3], metricas.iterrows()):
        col.metric(row["modelo"], f"R² = {row['R2']:.3f}", f"RMSE {row['RMSE']:.1f} | MAE {row['MAE']:.1f}")

    fig_met = px.bar(
        metricas, x="modelo", y=["R2", "RMSE", "MAE"],
        barmode="group",
        labels={"value": "Valor", "variable": "Métrica", "modelo": ""},
        color_discrete_sequence=["#3b82f6", "#ef4444", "#f97316"],
        text_auto=".2f",
    )
    fig_met.update_layout(height=320)
    st.plotly_chart(fig_met, use_container_width=True)

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Coeficientes OLS (excl. constante)")
        df_coef = coefs[coefs["feature"] != "const"].copy()
        df_coef["cor"] = df_coef["coef"].apply(lambda x: "#ef4444" if x > 0 else "#22c55e")
        df_coef_sorted = df_coef.sort_values("coef")
        fig_coef = go.Figure()
        fig_coef.add_trace(go.Bar(
            x=df_coef_sorted["coef"],
            y=df_coef_sorted["feature"],
            orientation="h",
            marker_color=df_coef_sorted["cor"],
            text=df_coef_sorted["sig"].fillna(""),
            textposition="outside",
        ))
        fig_coef.add_vline(x=0, line_color="gray", line_dash="dash")
        fig_coef.update_layout(height=480, showlegend=False,
                                xaxis_title="Coeficiente", yaxis_title="")
        st.plotly_chart(fig_coef, use_container_width=True)
        st.caption("🔴 aumenta mortalidade · 🟢 reduz mortalidade · *** p<0.001 · ** p<0.01 · * p<0.05")

    with col_b:
        st.subheader("Importância de features (RF vs XGBoost)")
        modelo_imp = st.radio("Modelo", ["Random Forest", "XGBoost"], horizontal=True, key="imp_model")
        col_imp = "imp_rf" if modelo_imp == "Random Forest" else "imp_xgb"
        df_imp = imp.sort_values(col_imp, ascending=False)
        fig_imp = px.bar(
            df_imp.sort_values(col_imp),
            x=col_imp, y="feature", orientation="h",
            color=col_imp,
            color_continuous_scale="Blues",
            text_auto=".3f",
            labels={col_imp: "Importância", "feature": ""},
        )
        fig_imp.update_layout(height=480, coloraxis_showscale=False)
        st.plotly_chart(fig_imp, use_container_width=True)

    st.divider()
    st.subheader("Intervalo de confiança — coeficientes OLS significativos")
    df_sig = coefs[(coefs["sig"].notna()) & (coefs["sig"] != "") & (coefs["feature"] != "const")].copy()
    df_sig = df_sig.sort_values("coef")
    fig_ci = go.Figure()
    for _, r in df_sig.iterrows():
        cor = "#ef4444" if r["coef"] > 0 else "#22c55e"
        fig_ci.add_trace(go.Scatter(
            x=[r["ci_low"], r["ci_high"]],
            y=[r["feature"], r["feature"]],
            mode="lines",
            line=dict(color=cor, width=3),
            showlegend=False,
        ))
        fig_ci.add_trace(go.Scatter(
            x=[r["coef"]],
            y=[r["feature"]],
            mode="markers",
            marker=dict(color=cor, size=10),
            showlegend=False,
        ))
    fig_ci.add_vline(x=0, line_dash="dash", line_color="gray")
    fig_ci.update_layout(height=420, xaxis_title="Coeficiente (95% IC)", yaxis_title="")
    st.plotly_chart(fig_ci, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Sobre
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "ℹ️ Sobre o Projeto":
    st.title("ℹ️ Sobre o Projeto")

    st.markdown("""
    ## Data Major — Mortalidade por Causas Evitáveis no Brasil

    Projeto da disciplina **Tópicos em Banco de Dados** — IESB, 2026/01.

    ### Problema
    A alta incidência de mortalidade por causas evitáveis no Brasil e sua correlação com
    desigualdades socioeconômicas municipais. Causas evitáveis são aquelas que poderiam ser
    prevenidas por ações do SUS — imunização, diagnóstico precoce, atenção básica e políticas de saúde.

    ### Período coberto
    **2022–2024** (painel município × ano)

    ### Pipeline
    | Etapa | Notebook |
    |---|---|
    | Extração | `01_extracao.ipynb` |
    | Transformação | `02_transformacao.ipynb` + `02b` |
    | Regressão | `03_regressao.ipynb` |
    | Clusterização K-Means | `04_clusterizacao.ipynb` |
    | Mineração CID-10 | `05_mineracao.ipynb` |
    | Padronização etária | `06_taxa_padronizada_idade.ipynb` |

    ### Fontes de dados
    - **SIM-DATASUS** — microdados de óbitos (CID-10)
    - **IBGE Sidra** — população municipal, PIB
    - **SICONFI / Tesouro Nacional** — despesa municipal em saúde
    - **IPEA Data (Atlas DH)** — IDH-M, Gini, renda, pobreza

    ### Grupos de causas evitáveis (LBCE)
    Baseados na Lista Brasileira de Causas de Mortes Evitáveis — Malta et al. 2007 + atualização 2010 (SVS/MS):

    | Grupo | Descrição |
    |---|---|
    | `imunoprevencao` | Reduzíveis por vacinação |
    | `doencas_infecciosas` | Tuberculose, HIV, hepatites, infecções respiratórias |
    | `doencas_nao_transmissiveis` | Neoplasias, cardiovasculares, diabetes, DPOC |
    | `morte_materna` | Gravidez, parto e puerpério |

    > Causas externas (acidentes, violências) foram **excluídas** por dependerem de fatores
    > ausentes do conjunto de variáveis socioeconômicas utilizadas.

    ### Referências
    - Malta DC et al. *Tabela Brasileira de Causas de Mortes Evitáveis.* Epidemiol. Serv. Saúde 16(4):233-244, 2007.
    - Malta DC et al. *Atualização da lista de causas de mortes evitáveis.* Epidemiol. Serv. Saúde 19(2):173-176, 2010.
    """)
