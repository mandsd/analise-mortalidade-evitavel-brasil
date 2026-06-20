import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
CLUSTER_COLORS_LIST = ["#ef4444", "#f97316", "#3b82f6", "#22c55e"]

REGIOES_NOMES = {"N": "Norte", "NE": "Nordeste", "CO": "Centro-Oeste", "SE": "Sudeste", "S": "Sul"}

# Coordenadas aproximadas dos centróides das 5 macrorregiões do Brasil
REGIAO_COORDS = {
    "N":  {"lat": -4.5, "lon": -62.0, "nome": "Norte"},
    "NE": {"lat": -8.5, "lon": -39.5, "nome": "Nordeste"},
    "CO": {"lat": -15.5, "lon": -52.0, "nome": "Centro-Oeste"},
    "SE": {"lat": -20.0, "lon": -44.0, "nome": "Sudeste"},
    "S":  {"lat": -28.0, "lon": -52.0, "nome": "Sul"},
}

DESCRICOES_CID = {
    "I64": "AVC (tipo não especificado)",
    "I63": "Infarto cerebral (AVC isquêmico)",
    "I61": "Hemorragia intracerebral",
    "I67": "Outras doenças cerebrovasculares",
    "I21": "Infarto agudo do miocárdio",
    "I25": "Doença isquêmica crônica do coração",
    "I10": "Hipertensão essencial",
    "I50": "Insuficiência cardíaca",
    "I20": "Angina pectoris",
    "B57": "Doença de Chagas",
    "B65": "Esquistossomose",
    "A09": "Diarreia e gastroenterite infecciosa",
    "A90": "Dengue clássico",
    "A39": "Meningite meningocócica",
    "B24": "HIV/AIDS",
    "A15": "Tuberculose respiratória",
    "B18": "Hepatite viral crônica",
    "A41": "Septicemia",
    "E11": "Diabetes mellitus tipo 2",
    "E14": "Diabetes mellitus não especificado",
    "J18": "Pneumonia por microrganismo NE",
    "J43": "Enfisema pulmonar",
    "J44": "DPOC (doença pulmonar obstrutiva crônica)",
    "J45": "Asma",
    "C44": "Neoplasia maligna da pele",
    "C50": "Câncer de mama",
    "C53": "Câncer do colo do útero",
    "C34": "Câncer de pulmão / brônquios",
    "C16": "Câncer de estômago",
    "C18": "Câncer de cólon",
    "C22": "Câncer do fígado",
    "C67": "Câncer da bexiga",
    "C25": "Câncer do pâncreas",
    "C61": "Câncer de próstata",
    "F10": "Transtornos por uso de álcool",
    "K70": "Doença alcoólica do fígado",
    "K74": "Fibrose e cirrose hepática",
    "N18": "Insuficiência renal crônica",
    "G40": "Epilepsia",
    "E40": "Kwashiorkor",
    "E43": "Desnutrição proteico-calórica grave",
    "E46": "Desnutrição proteico-calórica NE",
    "O15": "Eclâmpsia",
    "O14": "Pré-eclâmpsia",
    "O03": "Aborto espontâneo",
    "P07": "Transtornos RN por gestação curta / baixo peso",
    "P22": "Angústia respiratória do recém-nascido",
}

FEATURE_LABELS = {
    "const":                "Constante",
    "LOG_PIB_PER_CAPITA":   "PIB per capita (log R$)",
    "LOG_DESPESA_SAUDE_PC": "Despesa saúde p.c. (log R$)",
    "LOG_POPULACAO":        "Tamanho populacional (log)",
    "IDHM":                 "IDH Municipal (IDHM)",
    "GINI":                 "Índice de Gini (desigualdade)",
    "RDPC":                 "Renda domiciliar per capita",
    "PMPOB":                "% pop. em extrema pobreza",
    "ESPVIDA":              "Esperança de vida (anos)",
    "T_ANALF15M":           "Analfabetismo 15+ (%)",
    "T_AGUA":               "Acesso à água encanada (%)",
    "REG_N":                "Região Norte",
    "REG_NE":               "Região Nordeste",
    "REG_S":                "Região Sul",
    "REG_SE":               "Região Sudeste",
    "ANO_2023":             "Ano 2023",
    "ANO_2024":             "Ano 2024",
}

CLUSTER_NARRATIVAS = {
    0: (
        "Municípios do Norte e Nordeste com estrutura sanitária mais frágil. "
        "Doença de Chagas (B57), alcoolismo (F10) e AVC (I64) são as causas mais distintivas — "
        "doenças ligadas a condições ambientais e determinantes sociais historicamente negligenciados."
    ),
    1: (
        "Interior do Brasil em transição. Esquistossomose (B65) e Doença de Chagas (B57) "
        "marcam o perfil — parasitoses dependentes de saneamento básico e contato com água "
        "contaminada, ainda prevalentes em áreas rurais do Nordeste e Norte."
    ),
    2: (
        "Municípios de porte médio no Sul e Sudeste com IDH intermediário. "
        "Dengue (A90) é o principal diferencial, refletindo a expansão do Aedes aegypti "
        "em cidades médias com urbanização acelerada e saneamento parcial."
    ),
    3: (
        "Grandes centros urbanos com maior IDH. Apesar do maior desenvolvimento, prevalecem "
        "causas cardiovasculares urbanas (I63 — AVC isquêmico, I25 — isquemia coronariana) "
        "e meningite meningocócica (A39), característica de aglomerados populacionais densos."
    ),
}

# ─── Loaders ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_perfil():
    df = pd.read_csv(f"{MODELS_DIR}/perfil_clusters.csv")
    df["label"] = df["CLUSTER"].map(CLUSTER_LABELS)
    df["color"] = df["CLUSTER"].map(CLUSTER_COLORS)
    df["PIB_pc_real"] = np.expm1(df["PIB_pc"])
    df["desp_saude_pc_real"] = np.expm1(df["desp_saude_pc"])
    return df

@st.cache_data
def load_metricas():
    return pd.read_csv(f"{MODELS_DIR}/metricas_modelos.csv")

@st.cache_data
def load_coeficientes():
    df = pd.read_csv(f"{MODELS_DIR}/coeficientes_ols.csv")
    df["feature_label"] = df["feature"].map(FEATURE_LABELS).fillna(df["feature"])
    return df

@st.cache_data
def load_importancia():
    df = pd.read_csv(f"{MODELS_DIR}/importancia_features.csv")
    df["feature_label"] = df["feature"].map(FEATURE_LABELS).fillna(df["feature"])
    return df

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
def load_taxa_regiao():
    df = pd.read_csv(f"{MODELS_DIR}/taxa_regiao_comparacao.csv")
    df["regiao_nome"] = df["REGIAO"].map(REGIOES_NOMES)
    return df

@st.cache_data
def load_tendencia():
    return pd.read_csv(f"{MODELS_DIR}/tendencia_temporal.csv")

@st.cache_data
def load_elbow():
    return pd.read_csv(f"{MODELS_DIR}/elbow_silhouette.csv")

@st.cache_data
def load_composicao_regional():
    df = pd.read_csv(f"{MODELS_DIR}/composicao_regional_cluster.csv")
    df["label"] = df["CLUSTER"].map(CLUSTER_LABELS)
    return df

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("iesblogo.png", width=120)
    except Exception:
        pass
    st.markdown("## Mortalidade Evitável")
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

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Visão Geral
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "📊 Visão Geral":
    st.title("📊 Mortalidade por Causas Evitáveis no Brasil")
    st.markdown(
        "Análise de **5.571 municípios** entre **2022 e 2024**, investigando a relação entre "
        "desigualdades socioeconômicas e mortalidade evitável sensível ao SUS. "
        "Causas evitáveis classificadas pela **LBCE** — 344 prefixos CID-10, faixa etária 5–74 anos."
    )
    st.divider()

    perfil      = load_perfil()
    tendencia   = load_tendencia()
    regiao      = load_taxa_regiao()

    total_mun     = int(perfil["n_municipios"].sum())
    total_obitos  = int(tendencia["obitos_total"].sum())
    taxa_bruta_p  = (perfil["taxa_bruta"] * perfil["%_pop_brasil"]).sum() / 100
    taxa_pad_p    = (perfil["taxa_padronizada"] * perfil["%_pop_brasil"]).sum() / 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Municípios analisados", f"{total_mun:,}".replace(",", "."),
              help="Total de municípios no painel 2022–2024")
    c2.metric("Óbitos evitáveis (3 anos)", f"{total_obitos:,}".replace(",", "."),
              help="Total de óbitos LBCE acumulados em 2022, 2023 e 2024")
    c3.metric("Taxa bruta média", f"{taxa_bruta_p:.1f} /100k",
              help="Sem correção pela estrutura etária")
    c4.metric("Taxa padronizada média", f"{taxa_pad_p:.1f} /100k",
              help="Corrigida pelo Censo 2022 — métrica principal do projeto")

    st.divider()

    # ── Mapa regional ─────────────────────────────────────────────────────────
    st.subheader("Mapa: Taxa padronizada de mortalidade evitável por região")
    st.markdown(
        "Cada bolha representa uma das 5 macrorregiões brasileiras. "
        "Tamanho proporcional ao número de municípios; cor pela taxa padronizada."
    )

    regiao_ord = (
        regiao.set_index("REGIAO").reindex(["N", "NE", "CO", "SE", "S"]).reset_index()
    )
    map_df = regiao_ord.copy()
    map_df["lat"]  = map_df["REGIAO"].map(lambda r: REGIAO_COORDS[r]["lat"])
    map_df["lon"]  = map_df["REGIAO"].map(lambda r: REGIAO_COORDS[r]["lon"])
    map_df["nome"] = map_df["REGIAO"].map(REGIOES_NOMES)

    fig_map = px.scatter_geo(
        map_df,
        lat="lat",
        lon="lon",
        size="n_municipios",
        color="taxa_padronizada",
        color_continuous_scale="RdYlGn_r",
        hover_name="nome",
        hover_data={
            "taxa_padronizada": ":.1f",
            "taxa_bruta": ":.1f",
            "n_municipios": True,
            "lat": False,
            "lon": False,
        },
        text="nome",
        labels={"taxa_padronizada": "Taxa pad. /100k", "n_municipios": "Nº municípios"},
        size_max=60,
    )
    fig_map.update_traces(textposition="top center", textfont_size=12)
    fig_map.update_geos(
        scope="south america",
        showcountries=True,
        countrycolor="lightgray",
        showland=True,
        landcolor="#f8fafc",
        showcoastlines=True,
        coastlinecolor="gray",
        fitbounds="locations",
    )
    fig_map.update_layout(height=440, coloraxis_colorbar_title="Taxa pad.<br>/100k")
    st.plotly_chart(fig_map, width="stretch")
    st.caption(
        "Bolhas maiores = mais municípios. Vermelho = maior mortalidade evitável padronizada. "
        "Norte aparece menor (menos municípios), mas sua taxa padronizada supera a taxa bruta — "
        "o paradoxo corrigido pela padronização etária."
    )

    st.divider()

    # ── Paradoxo ──────────────────────────────────────────────────────────────
    st.subheader("O Paradoxo: Taxa Bruta vs. Padronizada por Região")
    st.markdown(
        "Pela taxa bruta, o Sul (256.5) parece ter a maior mortalidade. "
        "Após padronizar pela estrutura etária do Censo 2022, o Norte sobe de 158.9 → 227.7 "
        "e o Sul cai de 256.5 → 241.8 — revelando o gradiente socioeconômico real."
    )

    fig_par = go.Figure()
    fig_par.add_trace(go.Bar(
        name="Taxa bruta /100k",
        x=regiao_ord["regiao_nome"],
        y=regiao_ord["taxa_bruta"],
        marker_color="#94a3b8",
        text=regiao_ord["taxa_bruta"].round(1),
        textposition="outside",
    ))
    fig_par.add_trace(go.Bar(
        name="Taxa padronizada /100k",
        x=regiao_ord["regiao_nome"],
        y=regiao_ord["taxa_padronizada"],
        marker_color="#3b82f6",
        text=regiao_ord["taxa_padronizada"].round(1),
        textposition="outside",
    ))
    fig_par.update_layout(
        barmode="group", height=360,
        yaxis_title="Óbitos evitáveis por 100k hab.",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(range=[0, 290]),
    )
    st.plotly_chart(fig_par, width="stretch")
    st.info(
        "**Norte:** taxa bruta 158.9 (menor do país) → padronizada 227.7 (+68.8). "
        "**Sul:** taxa bruta 256.5 (maior) → padronizada 241.8 (−14.7). "
        "O gradiente correto após padronização: Norte/Nordeste com maior carga de mortalidade evitável."
    )

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Tendência temporal (2022–2024)")
        fig_tend = go.Figure()
        fig_tend.add_trace(go.Scatter(
            x=tendencia["ANO"].astype(str),
            y=tendencia["taxa_media"],
            mode="lines+markers+text",
            marker=dict(size=12, color="#3b82f6"),
            line=dict(width=3, color="#3b82f6"),
            text=tendencia["taxa_media"].round(2),
            textposition="top center",
        ))
        fig_tend.update_layout(
            height=300, yaxis_title="Taxa padronizada /100k",
            yaxis=dict(range=[216, 232]),
        )
        st.plotly_chart(fig_tend, width="stretch")
        delta = (
            tendencia.loc[tendencia["ANO"] == 2024, "taxa_media"].values[0]
            - tendencia.loc[tendencia["ANO"] == 2022, "taxa_media"].values[0]
        )
        obitos_24 = int(tendencia.loc[tendencia["ANO"] == 2024, "obitos_total"].values[0])
        tm1, tm2 = st.columns(2)
        tm1.metric("Óbitos 2024", f"{obitos_24:,}".replace(",", "."))
        tm2.metric("Variação 2022→2024", f"{delta:+.2f} /100k",
                   help="Alta em 2024 ligada a ondas de dengue e melhora no registro de óbitos")

    with col_b:
        st.subheader("Taxa padronizada por cluster")
        fig_cl = px.bar(
            perfil, x="label", y="taxa_padronizada", color="label",
            color_discrete_map={v: CLUSTER_COLORS[k] for k, v in CLUSTER_LABELS.items()},
            labels={"taxa_padronizada": "Taxa padronizada /100k", "label": ""},
            text_auto=".1f",
        )
        fig_cl.update_layout(showlegend=False, height=300)
        fig_cl.update_traces(textposition="outside")
        st.plotly_chart(fig_cl, width="stretch")

    st.divider()

    st.subheader("IDH-M × Taxa padronizada por cluster")
    fig_sc = px.scatter(
        perfil, x="IDHM", y="taxa_padronizada",
        size="n_municipios", color="label",
        color_discrete_map={v: CLUSTER_COLORS[k] for k, v in CLUSTER_LABELS.items()},
        text="label",
        labels={"IDHM": "IDH Municipal", "taxa_padronizada": "Taxa padronizada /100k",
                "label": "Cluster", "n_municipios": "Nº municípios"},
        hover_data={"n_municipios": True, "GINI": True, "PIB_pc_real": ":.0f"},
    )
    fig_sc.update_traces(textposition="top center", textfont_size=10)
    fig_sc.update_layout(showlegend=False, height=360)
    st.plotly_chart(fig_sc, width="stretch")

    st.divider()

    st.subheader("Comparativo geral dos clusters")
    variaveis = {
        "Taxa padronizada (/100k)": "taxa_padronizada",
        "IDH Municipal": "IDHM",
        "Índice de Gini": "GINI",
        "PIB per capita real (R$)": "PIB_pc_real",
        "Despesa saúde p.c. real (R$)": "desp_saude_pc_real",
        "Analfabetismo 15+ (%)": "ANALF15M",
        "Acesso à água (%)": "T_AGUA",
        "Esperança de vida (anos)": "ESPVIDA",
    }
    sel_var = st.selectbox("Selecione a variável", list(variaveis.keys()))
    col_var = variaveis[sel_var]
    fmt = ":.0f" if "real" in col_var else ".2f"
    fig_comp = px.bar(
        perfil, x="label", y=col_var, color="label",
        color_discrete_map={v: CLUSTER_COLORS[k] for k, v in CLUSTER_LABELS.items()},
        text_auto=fmt, labels={col_var: sel_var, "label": ""},
    )
    fig_comp.update_layout(showlegend=False, height=300)
    fig_comp.update_traces(textposition="outside")
    st.plotly_chart(fig_comp, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Perfis de Cluster
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🗺️ Perfis de Cluster":
    st.title("🗺️ Perfis de Cluster de Municípios")
    st.markdown(
        "**K-Means (k=4)** aplicado sobre 7 variáveis socioeconômicas padronizadas. "
        "A variável-alvo (taxa de mortalidade) **não entrou no clustering** — "
        "os perfis emergiram exclusivamente do contexto socioeconômico. "
        "Clusters ordenados por IDH-M crescente (0 = mais vulnerável → 3 = mais desenvolvido)."
    )
    st.divider()

    perfil      = load_perfil()
    lbce        = load_lbce()
    comp_reg    = load_composicao_regional()
    elbow       = load_elbow()

    cluster_sel = st.selectbox(
        "Selecione um cluster para detalhar",
        options=list(CLUSTER_LABELS.keys()),
        format_func=lambda x: CLUSTER_LABELS[x],
    )
    row = perfil[perfil["CLUSTER"] == cluster_sel].iloc[0]
    cor = CLUSTER_COLORS[cluster_sel]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Municípios", f"{int(row['n_municipios']):,}".replace(",", "."))
    c2.metric("% pop. Brasil", f"{row['%_pop_brasil']}%")
    c3.metric("IDH-M", f"{row['IDHM']:.2f}")
    c4.metric("Gini", f"{row['GINI']:.2f}")
    c5.metric("Taxa padronizada", f"{row['taxa_padronizada']:.1f} /100k")
    c6.metric("Esperança de vida", f"{row['ESPVIDA']:.1f} anos")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Indicadores socioeconômicos")
        indicadores = {
            "PIB per capita real (R$)": row["PIB_pc_real"],
            "Desp. saúde p.c. real (R$)": row["desp_saude_pc_real"],
            "Analfabetismo 15+ (%)": row["ANALF15M"],
            "Acesso à água (%)": row["T_AGUA"],
            "Esperança de vida (anos)": row["ESPVIDA"],
        }
        df_ind = pd.DataFrame({"Indicador": list(indicadores.keys()), "Valor": list(indicadores.values())})
        fig = px.bar(
            df_ind, x="Valor", y="Indicador", orientation="h",
            color_discrete_sequence=[cor], text_auto=".1f",
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, width="stretch")
        st.caption(
            f"PIB per capita: **R$ {row['PIB_pc_real']:,.0f}** &nbsp;|&nbsp; "
            f"Despesa saúde p.c.: **R$ {row['desp_saude_pc_real']:,.0f}**  \n"
            "*(valores reais: exp(log) dos dados originais em escala logarítmica)*"
        )

    with col_b:
        st.subheader("Composição geográfica do cluster")
        row_reg = comp_reg[comp_reg["CLUSTER"] == cluster_sel].iloc[0]
        regs = ["N", "NE", "CO", "SE", "S"]
        vals_reg = [row_reg[r] for r in regs]
        nomes_reg = [REGIOES_NOMES[r] for r in regs]
        df_reg_plot = pd.DataFrame({"Região": nomes_reg, "% municípios": vals_reg})
        df_reg_plot = df_reg_plot[df_reg_plot["% municípios"] > 0]
        fig_rp = px.pie(
            df_reg_plot, names="Região", values="% municípios",
            color_discrete_sequence=px.colors.qualitative.Set1, hole=0.4,
        )
        fig_rp.update_layout(height=300)
        st.plotly_chart(fig_rp, width="stretch")
        st.caption("Distribuição dos municípios do cluster entre as 5 macrorregiões brasileiras.")

    st.divider()

    # ── Composição regional comparativo ───────────────────────────────────────
    st.subheader("De onde são os municípios de cada cluster?")
    st.markdown(
        "Composição regional de cada cluster (% dos municípios do cluster por macrorregião). "
        "Revela a **geografia dos perfis de desenvolvimento**."
    )

    comp_melt = comp_reg.melt(
        id_vars=["CLUSTER", "label"],
        value_vars=["N", "NE", "CO", "SE", "S"],
        var_name="REGIAO", value_name="pct",
    )
    comp_melt["regiao_nome"] = comp_melt["REGIAO"].map(REGIOES_NOMES)

    fig_creg = px.bar(
        comp_melt, x="label", y="pct", color="regiao_nome",
        barmode="stack",
        color_discrete_sequence=["#0ea5e9", "#f97316", "#8b5cf6", "#22c55e", "#ef4444"],
        labels={"label": "", "pct": "% dos municípios do cluster", "regiao_nome": "Região"},
        text_auto=".0f",
    )
    fig_creg.update_layout(height=380)
    st.plotly_chart(fig_creg, width="stretch")
    st.info(
        "**Cluster 0** — 85.8% Nordeste + 11.5% Norte: quase exclusivamente as regiões mais pobres.  \n"
        "**Cluster 1** — 64.7% NE + 15.1% N: interior nordestino em transição.  \n"
        "**Cluster 2** — 43.2% Sudeste + 35.0% Sul + 16.9% Centro-Oeste: cidades médias do Centro-Sul.  \n"
        "**Cluster 3** — 43.9% SE + 37.0% Sul: grandes centros urbanos."
    )

    st.divider()

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Composição LBCE por cluster")
        row_lbce = lbce[lbce["CLUSTER"] == cluster_sel].iloc[0]
        labels_lbce = ["D. Infecciosas", "D. Não Transmissíveis", "Imunopreveníveis", "Morte Materna"]
        vals_lbce   = [
            row_lbce["doencas_infecciosas"],
            row_lbce["doencas_nao_transmissiveis"],
            row_lbce["imunoprevencao"],
            row_lbce["morte_materna"],
        ]
        fig2 = px.pie(
            names=labels_lbce, values=vals_lbce,
            color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4,
        )
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, width="stretch")

    with col_d:
        st.subheader("Radar comparativo — todos os clusters")
        cats = ["taxa_padronizada", "IDHM", "GINI", "T_AGUA", "ESPVIDA"]
        cats_label = ["Taxa padronizada", "IDH-M", "Gini", "Água (%)", "Esp. de vida"]

        def norm(col):
            mn, mx = perfil[col].min(), perfil[col].max()
            return (perfil[col] - mn) / (mx - mn + 1e-9)

        fig3 = go.Figure()
        for _, r in perfil.iterrows():
            idx = int(r["CLUSTER"])
            vals = [norm(c).iloc[idx] for c in cats] ; vals += [vals[0]]
            fig3.add_trace(go.Scatterpolar(
                r=vals, theta=cats_label + [cats_label[0]],
                name=r["label"], fill="toself",
                line_color=CLUSTER_COLORS[idx], opacity=0.6,
            ))
        fig3.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=300,
        )
        st.plotly_chart(fig3, width="stretch")

    st.info(
        "**Nota:** A composição LBCE é similar entre clusters (D. Não Transmissíveis ~81% em todos) "
        "porque a transição epidemiológica afetou todo o Brasil. O diferencial está nas causas "
        "específicas dentro de cada grupo — analisadas pela metodologia de lift (página Causas de Óbito). "
        "O gradiente mais claro: **Morte Materna** 0.65% (Cluster 0) → 0.31% (Cluster 3)."
    )

    st.divider()
    with st.expander("Como o k=4 foi escolhido? — Método do Cotovelo e Silhouette"):
        st.markdown(
            "Testamos k de 2 a 10. Dois critérios combinados justificam k=4:"
        )
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            fig_elbow = go.Figure()
            fig_elbow.add_trace(go.Scatter(
                x=elbow["k"], y=elbow["inertia"],
                mode="lines+markers", marker=dict(size=8, color="#3b82f6"),
                line=dict(width=2), name="Inertia (WCSS)",
            ))
            fig_elbow.add_vline(x=4, line_dash="dash", line_color="#ef4444",
                                annotation_text="k=4 escolhido")
            fig_elbow.update_layout(
                height=280, title="Método do Cotovelo",
                xaxis_title="k (número de clusters)",
                yaxis_title="Inertia (soma quadrática intra-cluster)",
            )
            st.plotly_chart(fig_elbow, width="stretch")

        with col_e2:
            fig_sil = go.Figure()
            fig_sil.add_trace(go.Scatter(
                x=elbow["k"], y=elbow["silhouette"],
                mode="lines+markers", marker=dict(size=8, color="#f97316"),
                line=dict(width=2), name="Silhouette",
            ))
            fig_sil.add_vline(x=4, line_dash="dash", line_color="#ef4444",
                              annotation_text="k=4 escolhido")
            fig_sil.update_layout(
                height=280, title="Silhouette Score",
                xaxis_title="k (número de clusters)",
                yaxis_title="Silhouette médio",
            )
            st.plotly_chart(fig_sil, width="stretch")

        st.markdown(
            "**Interpretação:** O cotovelo da inertia se forma em k=3–4 — adicionar mais clusters "
            "além de k=4 traz ganho marginal pequeno. O silhouette máximo absoluto é em k=2 (0.39), "
            "mas 2 clusters seria insuficiente para distinguir os perfis Norte/NE, interior, médios e grandes centros. "
            "**k=4 é escolhido pelo equilíbrio entre separação estatística e interpretabilidade geográfica** — "
            "4 perfis mapeiam diretamente as 4 realidades de desenvolvimento municipal no Brasil."
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Causas de Óbito
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🔬 Causas de Óbito":
    st.title("🔬 Análise de Causas de Óbito por CID-10")
    st.markdown(
        "Quais causas evitáveis são mais características de cada cluster? "
        "Analisamos por **frequência relativa** (top causas) e por **razão lift** (distintividade vs. média nacional)."
    )
    st.divider()

    top_causas = load_top_causas()
    lift       = load_lift()

    tab1, tab2 = st.tabs(["📋 Top causas por cluster", "📐 Análise de Lift (distintividade)"])

    with tab1:
        st.markdown(
            "Proporção de cada CID-10 no total de óbitos evitáveis do cluster. "
            "Doenças cardiovasculares e diabetes dominam em todos — transição epidemiológica brasileira."
        )
        col_tc1, col_tc2 = st.columns([1, 2])
        with col_tc1:
            cluster_tc = st.selectbox(
                "Cluster", options=list(CLUSTER_LABELS.keys()),
                format_func=lambda x: CLUSTER_LABELS[x], key="tc",
            )
            n_top = st.slider("Nº de causas", 5, 15, 10)
        with col_tc2:
            df_tc = top_causas[top_causas["CLUSTER"] == cluster_tc].head(n_top).copy()
            df_tc["descricao_legivel"] = df_tc.apply(
                lambda r: DESCRICOES_CID.get(
                    r["CID_CAT3"],
                    r.get("descricao", r["CID_CAT3"]).title()
                    if pd.notna(r.get("descricao", "")) else r["CID_CAT3"],
                ), axis=1,
            )
            fig_tc = px.bar(
                df_tc.sort_values("pct"),
                x="pct", y="descricao_legivel", orientation="h",
                color_discrete_sequence=[CLUSTER_COLORS[cluster_tc]],
                text="pct",
                labels={"pct": "% dos óbitos do cluster", "descricao_legivel": ""},
                hover_data={"CID_CAT3": True, "n": True, "descricao_legivel": False},
            )
            fig_tc.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_tc.update_layout(height=max(320, n_top * 38), showlegend=False)
            st.plotly_chart(fig_tc, width="stretch")

    with tab2:
        st.markdown(
            "**Lift** = frequência da causa neste cluster ÷ frequência nacional.  \n"
            "Lift = 2.0 → a causa é **2× mais frequente** aqui do que na média nacional. "
            "Lift < 1 → sub-representada. Revela o que torna cada cluster único epidemiologicamente."
        )
        cluster_lift = st.selectbox(
            "Cluster", options=list(CLUSTER_LABELS.keys()),
            format_func=lambda x: CLUSTER_LABELS[x], key="lift",
        )
        st.info(CLUSTER_NARRATIVAS[cluster_lift])

        df_lift = lift[lift["CLUSTER"] == cluster_lift].copy()
        df_lift = df_lift.sort_values("lift", ascending=False).head(10)
        df_lift["descricao_legivel"] = df_lift.apply(
            lambda r: DESCRICOES_CID.get(
                r["CID_CAT3"],
                r.get("descricao", r["CID_CAT3"]).title()
                if pd.notna(r.get("descricao", "")) else r["CID_CAT3"],
            ), axis=1,
        )
        df_lift["label_bar"] = df_lift.apply(
            lambda r: f"{r['CID_CAT3']} — {r['descricao_legivel']}", axis=1
        )
        fig_lift = px.bar(
            df_lift.sort_values("lift"),
            x="lift", y="label_bar", orientation="h",
            color="lift", color_continuous_scale="RdYlGn",
            text="lift",
            labels={"lift": "Lift (razão vs. média nacional)", "label_bar": ""},
            hover_data={"CID_CAT3": True, "n": True, "label_bar": False, "descricao_legivel": False},
        )
        fig_lift.add_vline(x=1.0, line_dash="dash", line_color="gray",
                           annotation_text="Média nacional (lift = 1)")
        fig_lift.update_traces(texttemplate="%{text:.2f}×", textposition="outside")
        fig_lift.update_layout(height=440, coloraxis_showscale=False)
        st.plotly_chart(fig_lift, width="stretch")
        st.caption(
            "Lift = (freq. no cluster) ÷ (freq. nacional). "
            "Top 10 causas com maior lift no cluster selecionado."
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Modelos Preditivos
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📈 Modelos Preditivos":
    st.title("📈 Modelos Preditivos")
    st.markdown(
        "Regressão **OLS painel** (erros HC3, cluster-robust por município), "
        "**Random Forest** e **XGBoost** com validação **GroupShuffleSplit** sem leakage temporal.  \n"
        "Alvo: taxa padronizada de mortalidade evitável por 100k hab."
    )
    st.divider()

    metricas = load_metricas()
    coefs    = load_coeficientes()
    imp      = load_importancia()

    # ── KPIs de desempenho ────────────────────────────────────────────────────
    st.subheader("Desempenho dos modelos")
    c1, c2, c3 = st.columns(3)
    for col, (_, row) in zip([c1, c2, c3], metricas.iterrows()):
        col.metric(row["modelo"], f"R² = {row['R2']:.3f}",
                   f"RMSE {row['RMSE']:.1f} | MAE {row['MAE']:.1f}")

    st.warning(
        "**R² ≈ 10% — por que é esperado e não é um problema:**  \n"
        "Variáveis socioeconômicas municipais capturam padrões estruturais mas não fatores locais "
        "(qualidade do registro de óbitos, gestão de UBS, comportamentos individuais, sazonalidade). "
        "O que importa é a **direção, magnitude e significância dos coeficientes** — "
        "todos os três modelos convergem para as mesmas features mais relevantes."
    )

    fig_met = px.bar(
        metricas.melt(id_vars="modelo", value_vars=["RMSE", "MAE"]),
        x="modelo", y="value", color="variable", barmode="group",
        labels={"value": "Erro (óbitos/100k)", "variable": "Métrica", "modelo": ""},
        color_discrete_sequence=["#ef4444", "#f97316"], text_auto=".1f",
    )
    fig_met.update_layout(height=260)
    st.plotly_chart(fig_met, width="stretch")

    st.divider()

    # ── Validação estatística dos clusters ────────────────────────────────────
    st.subheader("Validação estatística dos clusters")
    st.markdown(
        "ANOVA one-way testa se a taxa de mortalidade é significativamente diferente entre clusters "
        "(H₀: médias iguais). Confirma que o K-Means separou grupos com perfis de mortalidade distintos."
    )
    va1, va2 = st.columns(2)
    va1.metric(
        "ANOVA — Taxa bruta",
        "F = 290.09",
        "p = 5.97×10⁻¹⁷⁵ (***)",
        help="Diferença altamente significativa entre clusters na taxa bruta de mortalidade evitável",
    )
    va2.metric(
        "ANOVA — Taxa padronizada",
        "F = 28.02",
        "p = 5.62×10⁻¹⁸ (***)",
        help="Diferença significativa mesmo após controlar estrutura etária",
    )
    st.info(
        "Ambos os p-valores são virtualmente zero — os 4 clusters **não são arbitrários**: "
        "representam grupos de municípios com mortalidade evitável estatisticamente distinta, "
        "mesmo que o target não tivesse entrado na clusterização (K-Means usou apenas features socioeconômicas)."
    )

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Coeficientes OLS — variáveis socioeconômicas")
        df_coef = coefs[
            (coefs["feature"] != "const")
            & (~coefs["feature"].str.startswith("ANO_"))
            & (~coefs["feature"].str.startswith("REG_"))
        ].copy()
        df_coef["cor"] = df_coef["coef"].apply(lambda x: "#ef4444" if x > 0 else "#22c55e")
        df_coef_sorted = df_coef.sort_values("coef")
        fig_coef = go.Figure()
        fig_coef.add_trace(go.Bar(
            x=df_coef_sorted["coef"],
            y=df_coef_sorted["feature_label"],
            orientation="h",
            marker_color=df_coef_sorted["cor"].tolist(),
            text=df_coef_sorted["sig"].fillna(""),
            textposition="outside",
            customdata=df_coef_sorted["coef"].round(3),
            hovertemplate="<b>%{y}</b><br>Coeficiente: %{customdata}<extra></extra>",
        ))
        fig_coef.add_vline(x=0, line_color="gray", line_dash="dash")
        fig_coef.update_layout(
            height=420, showlegend=False,
            xaxis_title="Efeito na taxa padronizada /100k hab.", yaxis_title="",
        )
        st.plotly_chart(fig_coef, width="stretch")
        st.caption("🔴 aumenta mortalidade · 🟢 reduz mortalidade · *** p<0.001 · ** p<0.01 · * p<0.05")

        with st.expander("Interpretação dos principais coeficientes"):
            st.markdown(
                "- **Gini (+151):** o efeito mais forte — 1pp a mais de desigualdade → +151 óbitos/100k\n"
                "- **Esperança de vida (−4.2):** cada ano extra de expectativa → −4.2 óbitos/100k\n"
                "- **Tamanho pop. (+13):** municípios maiores têm melhor registro de óbitos (viés de sub-registro)\n"
                "- **Despesa saúde (+8.8):** endogeneidade — municípios com maior carga gastam mais\n"
                "- **Renda per capita (RDPC, −0.14):** efeito parcialmente capturado pelo IDH-M"
            )

    with col_b:
        st.subheader("Importância de features — ML")
        modelo_imp = st.radio("Modelo", ["Random Forest", "XGBoost"], horizontal=True, key="imp_model")
        col_imp = "imp_rf" if modelo_imp == "Random Forest" else "imp_xgb"
        df_imp = imp.sort_values(col_imp, ascending=False).copy()
        fig_imp = px.bar(
            df_imp.sort_values(col_imp),
            x=col_imp, y="feature_label", orientation="h",
            color=col_imp, color_continuous_scale="Blues",
            text_auto=".3f",
            labels={col_imp: "Importância (MDI)", "feature_label": ""},
        )
        fig_imp.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_imp, width="stretch")
        st.caption(
            "Importância por redução de impureza (MDI). "
            "Coerente com os coeficientes OLS — variáveis de renda/IDH dominam."
        )

    st.divider()
    st.subheader("Intervalos de confiança 95% — coeficientes OLS significativos")
    df_sig = coefs[
        (coefs["sig"].notna()) & (coefs["sig"] != "") & (coefs["feature"] != "const")
    ].copy()
    df_sig = df_sig.sort_values("coef")
    fig_ci = go.Figure()
    for _, r in df_sig.iterrows():
        cor = "#ef4444" if r["coef"] > 0 else "#22c55e"
        lbl = r["feature_label"]
        fig_ci.add_trace(go.Scatter(
            x=[r["ci_low"], r["ci_high"]], y=[lbl, lbl],
            mode="lines", line=dict(color=cor, width=4), showlegend=False,
        ))
        fig_ci.add_trace(go.Scatter(
            x=[r["coef"]], y=[lbl],
            mode="markers", marker=dict(color=cor, size=10),
            showlegend=False,
            hovertemplate=(
                f"<b>{lbl}</b><br>Coef: {r['coef']:.3f}<br>"
                f"IC 95%: [{r['ci_low']:.3f}, {r['ci_high']:.3f}]<extra></extra>"
            ),
        ))
    fig_ci.add_vline(x=0, line_dash="dash", line_color="gray")
    fig_ci.update_layout(height=420, xaxis_title="Coeficiente (IC 95%)", yaxis_title="")
    st.plotly_chart(fig_ci, width="stretch")
    st.caption(
        "Barras cruzando o zero → não significativo ao nível 5%. "
        "Erros-padrão robustos HC3 e clusterizados por município."
    )

    st.divider()

    # ── Contrafactual ─────────────────────────────────────────────────────────
    st.subheader("Simulação Contrafactual — e se o IDH-M subisse no quintil mais vulnerável?")
    st.markdown(
        "Simulamos elevar o IDH-M dos municípios do **1º quintil** ao nível do **2º quintil**, "
        "mantendo todos os outros fatores constantes — baseado nos coeficientes OLS estimados."
    )
    cf1, cf2, cf3, cf4 = st.columns(4)
    cf1.metric("Municípios afetados", "3.340",
               help="Municípios no 1º quintil de IDH-M, ~60% no Norte/Nordeste")
    cf2.metric("IDH-M antes → depois", "0,557 → 0,689",
               help="Média do quintil 1 elevada ao nível do quintil 2")
    cf3.metric("Taxa antes → depois", "240,4 → 238,0 /100k",
               delta="-2,4 /100k",
               help="Redução simulada na taxa padronizada")
    cf4.metric("Redução relativa", "−1,0%",
               help="Variação percentual na taxa padronizada média dos municípios afetados")
    st.info(
        "O efeito contrafactual é modesto (−1,0%) — consistente com o R² baixo e com a literatura: "
        "melhorias estruturais em IDH têm efeitos graduais e acumulados na mortalidade ao longo de anos. "
        "O resultado evidencia que a desigualdade estrutural (Gini) é o vetor mais relevante a atacar."
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Sobre o Projeto
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "ℹ️ Sobre o Projeto":
    st.title("ℹ️ Sobre o Projeto")

    st.markdown("""
## Plataforma de Análise de Mortalidade por Causas Evitáveis no Brasil

**Trabalho de Conclusão de Curso — Ciência da Computação — IESB, 2026/01**

**Autores:** João Marcos Santos e Carvalho · Maria Clara Fontenele Silva
**Orientador:** Prof. Cristiano Lehrer

---

### Pergunta de Pesquisa

> *Em que medida indicadores socioeconômicos municipais (IDH, Gini, renda, saneamento)
> explicam as taxas de mortalidade por causas evitáveis no Brasil entre 2022 e 2024?*

### Hipótese

Municípios com piores indicadores socioeconômicos apresentam taxas de mortalidade evitável
significativamente maiores, mesmo após controle por estrutura etária — evidenciando iniquidades
em saúde reduzíveis por políticas públicas de atenção básica.

---

### Pipeline Técnico

| Etapa | Descrição | Artefato |
|---|---|---|
| **Extração (ETL)** | FTP DATASUS (SIM) + APIs IBGE Sidra, SICONFI/STN, IPEA Data | `01_extracao.ipynb` |
| **Transformação** | Classificação LBCE, padronização etária direta, merge geoespacial, feature matrix | `02_transformacao.ipynb` |
| **Regressão** | OLS painel (HC3 + cluster-robust SE) + RF + XGBoost (GroupShuffleSplit) | `03_regressao.ipynb` |
| **Clusterização** | K-Means k=4 em 7 features socioeconômicas padronizadas (target excluído) | `04_clusterizacao.ipynb` |
| **Mineração** | Análise de lift por CID-10, TF-IDF lift-ponderado | `05_mineracao.ipynb` |
| **Padronização etária** | Comparação taxa bruta vs. padronizada; diagnóstico do paradoxo regional | `06_taxa_padronizada_idade.ipynb` |

---

### Fontes de Dados

| Fonte | Dado coletado | Granularidade |
|---|---|---|
| **SIM-DATASUS** | Microdados de óbitos com CID-10 (arquivos .dbc via FTP) | Municipal × ano |
| **IBGE Sidra** | Pop. por faixa etária (Censo 2022), PIB municipal | Municipal |
| **SICONFI / STN** | Despesas municipais em saúde (função orçamentária 10) | Municipal × ano |
| **IPEA Data / Atlas DH** | IDH-M, Gini, RDPC, PMPOB, ESPVIDA, T_ANALF15M, T_AGUA | Municipal |

**Período:** 2022–2024 &nbsp;·&nbsp; **Cobertura:** 5.571 municípios brasileiros

---

### Lista Brasileira de Causas Evitáveis (LBCE)

344 prefixos de CID-10 classificados em 4 grupos (Malta et al., 2007 e 2010):

| Grupo | Definição | Exemplos | % aprox. |
|---|---|---|---|
| **Imunopreveníveis** | Reduzíveis por vacinação | Sarampo, difteria | ~0.1% |
| **D. Infecciosas** | Diagnóstico/tratamento precoce | TB, HIV/AIDS, diarreia | ~17% |
| **D. Não Transmissíveis** | Prevenção e atenção básica | DCV, neoplasias, diabetes | ~81% |
| **Morte Materna** | Gravidez, parto, puerpério | Eclâmpsia, sepse puerperal | ~0.4% |

> **Faixa etária:** 5 a 74 anos. Causas externas deliberadamente excluídas.

---

### Principais Achados

1. **Paradoxo corrigido:** pela taxa bruta, o Norte apareceria como a região de menor mortalidade (158.9/100k).
   Após padronização etária, sobe para 227.7/100k. O Sul cai de 256.5 → 241.8/100k.

2. **Desigualdade supera pobreza absoluta:** Gini (+151) é o coeficiente mais forte —
   a distribuição da renda importa mais que o nível médio de PIB.

3. **4 perfis geográficos distintos:** Cluster 0/1 = Norte/Nordeste vulnerável e em transição;
   Cluster 2/3 = Centro-Sul médio e grandes centros. Clusters confirmados por ANOVA (p<10⁻¹⁷).

4. **Causas distintivas por cluster:** Chagas e esquistossomose marcam os vulneráveis;
   dengue diferencia municípios médios; DCV urbanas dominam os grandes centros.

5. **Contrafactual modesto (−1%):** efeitos estruturais de IDH são graduais — coerente com a literatura.

---

### Limitações

- Denominador do Censo 2022 para todos os anos (estrutura etária muda pouco mas não é estática)
- Sub-registro de óbitos heterogêneo entre regiões (mais crítico no Norte)
- Dados IDH-M/Gini com base no Atlas DH 2010 (defasagem reconhecida)
- Correlação ecológica: inferências valem ao nível municipal, não individual

---

### Referências

- MALTA, D.C. et al. *Lista de causas de mortes evitáveis por intervenções do SUS.*
  Epidemiol. Serv. Saúde, 16(4):233–244, 2007.
- MALTA, D.C. et al. *Atualização da lista de causas de mortes evitáveis.*
  Epidemiol. Serv. Saúde, 19(2):173–176, 2010.
- WORLD HEALTH ORGANIZATION. *World Health Statistics 2023.* Geneva: WHO, 2023.
- PNUD/IPEA/FJP. *Atlas do Desenvolvimento Humano no Brasil.* Brasília, 2013.
- DATASUS/MS. *Sistema de Informações sobre Mortalidade (SIM).* Brasília: MS, 2024.
- IBGE. *Censo Demográfico 2022.* Rio de Janeiro: IBGE, 2023.
- BREIMAN, L. *Random Forests.* Machine Learning, 45(1):5–32, 2001.
- CHEN, T.; GUESTRIN, C. *XGBoost: A Scalable Tree Boosting System.* KDD, 2016.
""")
