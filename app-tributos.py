import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import numpy as np
from datetime import datetime

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(
    page_title="Dashboard Tributário",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS PERSONALIZADO ==========
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# ========== HEADER PRINCIPAL ==========
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard Tributário Municipal</h1>
    <p>Análise Completa da Arrecadação e Receita Própria</p>
</div>
""", unsafe_allow_html=True)

# ========== FUNÇÃO PARA FORMATAR EM PADRÃO BR ==========
def formatar_moeda_br(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    # Seleção de arquivo
    arquivo_escolhido = st.selectbox(
        "📁 Arquivo de Dados",
        options=["Arrecadacao Tributos.xlsx", "Arrecadacao Bancos.xlsx"],
        help="Selecione o arquivo principal para análise"
    )
    
    # Filtro de anos
    st.markdown("### 📅 Filtros")
    
    # Carrega dados para obter anos disponíveis
    try:
        df_temp = pd.read_excel(arquivo_escolhido, header=2)
        df_temp = df_temp.loc[:, ~df_temp.columns.str.contains("^Unnamed")]
        df_temp.columns = df_temp.columns.str.strip().str.upper()
        anos_disponiveis = df_temp["ANO"].astype(str).tolist()
        
        anos_selecionados = st.multiselect(
            "Anos para análise",
            options=anos_disponiveis,
            default=anos_disponiveis,
            help="Selecione os anos que deseja analisar"
        )
    except:
        anos_selecionados = []
        st.error("Erro ao carregar anos disponíveis")
    
    # Configurações de gráficos
    st.markdown("### 📈 Configurações")
    tipo_grafico = st.selectbox(
        "Tipo de gráfico principal",
        ["Barras", "Linha", "Área", "Pizza"],
        help="Escolha o tipo de visualização principal"
    )
    
    tema_grafico = st.selectbox(
        "Tema do gráfico",
        ["plotly", "plotly_white", "plotly_dark", "simple_white"],
        help="Escolha o tema visual dos gráficos"
    )

# ========== CARREGAMENTO DE DADOS ==========
@st.cache_data
def carregar_dados(arquivo):
    try:
        df = pd.read_excel(arquivo, header=2)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df.columns = df.columns.str.strip().str.upper()
        df["ANO"] = df["ANO"].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df = carregar_dados(arquivo_escolhido)

if df is None:
    st.error("Não foi possível carregar os dados. Verifique se o arquivo existe.")
    st.stop()

# Filtrar por anos selecionados
if anos_selecionados:
    df = df[df["ANO"].isin(anos_selecionados)]

# ========== MÉTRICAS PRINCIPAIS ==========
st.markdown("## 📊 Métricas Principais")

# Calcular métricas
ultimo_ano = df["ANO"].max()
penultimo_ano = df["ANO"].iloc[-2] if len(df) > 1 else ultimo_ano

ultimo_total = df[df["ANO"] == ultimo_ano]["TOTAL"].iloc[0] if "TOTAL" in df.columns else 0
penultimo_total = df[df["ANO"] == penultimo_ano]["TOTAL"].iloc[0] if "TOTAL" in df.columns else 0

crescimento = ((ultimo_total - penultimo_total) / penultimo_total * 100) if penultimo_total > 0 else 0

# Layout de métricas em colunas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{formatar_moeda_br(ultimo_total)}</div>
        <div class="metric-label">Arrecadação {ultimo_ano}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{formatar_moeda_br(penultimo_total)}</div>
        <div class="metric-label">Arrecadação {penultimo_ano}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{crescimento:.1f}%</div>
        <div class="metric-label">Crescimento Anual</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    media_anual = df["TOTAL"].mean() if "TOTAL" in df.columns else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{formatar_moeda_br(media_anual)}</div>
        <div class="metric-label">Média Anual</div>
    </div>
    """, unsafe_allow_html=True)

# ========== GRÁFICO PRINCIPAL ==========
st.markdown("## 📈 Análise Temporal")

# Lista de tributos
tributos = [col for col in df.columns if col not in ["ANO", "TOTAL"]]

# Criar gráfico baseado na seleção
if tipo_grafico == "Barras":
    fig_principal = px.bar(
        df, x="ANO", y="TOTAL" if "TOTAL" in df.columns else tributos[0],
        title="Evolução da Arrecadação Total",
        color_discrete_sequence=["#1f77b4"],
        template=tema_grafico
    )
elif tipo_grafico == "Linha":
    fig_principal = px.line(
        df, x="ANO", y="TOTAL" if "TOTAL" in df.columns else tributos[0],
        title="Evolução da Arrecadação Total",
        markers=True,
        template=tema_grafico
    )
elif tipo_grafico == "Área":
    fig_principal = px.area(
        df, x="ANO", y="TOTAL" if "TOTAL" in df.columns else tributos[0],
        title="Evolução da Arrecadação Total",
        template=tema_grafico
    )
else:  # Pizza
    fig_principal = px.pie(
        df, values="TOTAL" if "TOTAL" in df.columns else tributos[0], names="ANO",
        title="Distribuição da Arrecadação por Ano",
        template=tema_grafico
    )

fig_principal.update_layout(
    height=500,
    showlegend=True,
    title_x=0.5
)

st.plotly_chart(fig_principal, use_container_width=True)

# ========== GRÁFICOS COMPARATIVOS ==========
st.markdown("## 🔍 Análise Comparativa")

# Gráfico de barras empilhadas para todos os tributos
if len(tributos) > 0:
    fig_empilhado = go.Figure()
    
    for tributo in tributos:
        fig_empilhado.add_trace(go.Bar(
            name=tributo,
            x=df["ANO"],
            y=df[tributo],
            text=[formatar_moeda_br(val) for val in df[tributo]],
            textposition="auto",
        ))
    
    fig_empilhado.update_layout(
        title="Composição da Arrecadação por Tributo",
        barmode="stack",
        height=500,
        template=tema_grafico,
        title_x=0.5
    )
    
    st.plotly_chart(fig_empilhado, use_container_width=True)

# ========== GRÁFICO DE CALOR ==========
st.markdown("## 🌡️ Mapa de Calor")

# Preparar dados para o mapa de calor
heatmap_data = df.set_index("ANO")[tributos].T

fig_heatmap = px.imshow(
    heatmap_data,
    title="Mapa de Calor - Arrecadação por Tributo e Ano",
    aspect="auto",
    color_continuous_scale="Viridis",
    template=tema_grafico
)

fig_heatmap.update_layout(
    height=400,
    title_x=0.5,
    xaxis_title="Ano",
    yaxis_title="Tributo"
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# ========== GRÁFICO DE DISPERSÃO ==========
st.markdown("## 📊 Análise de Correlação")

if len(tributos) >= 2:
    # Criar gráfico de dispersão entre os dois maiores tributos
    tributo1, tributo2 = tributos[0], tributos[1] if len(tributos) > 1 else tributos[0]
    
    try:
        # Tentar criar gráfico com linha de tendência
        fig_scatter = px.scatter(
            df,
            x=tributo1,
            y=tributo2,
            title=f"Correlação: {tributo1} vs {tributo2}",
            template=tema_grafico,
            trendline="ols"
        )
    except ImportError:
        # Se statsmodels não estiver disponível, criar sem linha de tendência
        fig_scatter = px.scatter(
            df,
            x=tributo1,
            y=tributo2,
            title=f"Correlação: {tributo1} vs {tributo2}",
            template=tema_grafico
        )
        st.info("💡 Para ver a linha de tendência, instale: `pip install statsmodels`")
    
    fig_scatter.update_layout(
        height=400,
        title_x=0.5
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

# ========== GRÁFICOS INDIVIDUAIS ==========
st.markdown("## 📊 Gráficos Individuais por Tributo")

# Layout em colunas para os gráficos individuais
cols = st.columns(2)

for i, tributo in enumerate(tributos):
    col = cols[i % 2]
    
    with col:
        st.markdown(f"### {tributo}")
        
        # Gráfico de linha
        fig_individual = px.line(
            df,
            x="ANO",
            y=tributo,
            title=f"Evolução de {tributo}",
            markers=True,
            template=tema_grafico
        )
        
        fig_individual.update_layout(
            height=300,
            title_x=0.5,
            showlegend=False
        )
        
        st.plotly_chart(fig_individual, use_container_width=True)

# ========== TABELA INTERATIVA ==========
st.markdown("## 📋 Dados Detalhados")

# Formatar dados para exibição
df_formatado = df.copy()
for col in df_formatado.columns:
    if col != "ANO":
        df_formatado[col] = df_formatado[col].apply(formatar_moeda_br)

# Adicionar filtros interativos
col_filtro1, col_filtro2 = st.columns(2)

with col_filtro1:
    tributo_filtro = st.selectbox(
        "Filtrar por tributo",
        ["Todos"] + tributos,
        help="Selecione um tributo específico para filtrar"
    )

with col_filtro2:
    ano_filtro = st.selectbox(
        "Filtrar por ano",
        ["Todos"] + df["ANO"].tolist(),
        help="Selecione um ano específico para filtrar"
    )

# Aplicar filtros
df_filtrado = df_formatado.copy()
if tributo_filtro != "Todos":
    df_filtrado = df_filtrado[["ANO", tributo_filtro]]
if ano_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ANO"] == ano_filtro]

st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True
)

# ========== DOWNLOAD DE DADOS ==========
st.markdown("## 📥 Exportar Dados")

col_download1, col_download2 = st.columns(2)

with col_download1:
    # Download Excel
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
        df_formatado.to_excel(writer, index=False, sheet_name='Dados_Formatados')
    
    st.download_button(
        label="📊 Baixar Excel",
        data=buffer_excel.getvalue(),
        file_name=f"dashboard_tributario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col_download2:
    # Download CSV
    buffer_csv = io.BytesIO()
    df.to_csv(buffer_csv, index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📄 Baixar CSV",
        data=buffer_csv.getvalue(),
        file_name=f"dashboard_tributario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ========== GRÁFICOS ADICIONAIS ==========
st.markdown("## 📈 Gráficos Adicionais")

# Gráfico de radar para comparação de tributos
if len(tributos) > 2:
    st.markdown("### 🎯 Comparação de Tributos (Gráfico de Radar)")
    
    # Usar o último ano para comparação
    ultimo_ano_dados = df["ANO"].iloc[-1]
    dados_radar = df[df["ANO"] == ultimo_ano_dados][tributos].iloc[0]
    
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=dados_radar.values,
        theta=tributos,
        fill='toself',
        name=f'Arrecadação {ultimo_ano_dados}'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, dados_radar.max() * 1.1]
            )),
        showlegend=True,
        title=f"Comparação de Tributos - {ultimo_ano_dados}",
        template=tema_grafico
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

# Gráfico de boxplot para distribuição
st.markdown("### 📦 Distribuição dos Valores (Boxplot)")

fig_box = px.box(
    df.melt(id_vars=["ANO"], value_vars=tributos, var_name="Tributo", value_name="Valor"),
    x="Tributo",
    y="Valor",
    title="Distribuição dos Valores por Tributo",
    template=tema_grafico
)

fig_box.update_layout(
    height=400,
    title_x=0.5
)

st.plotly_chart(fig_box, use_container_width=True)

# ========== ANÁLISE ESTATÍSTICA ==========
st.markdown("## 📊 Análise Estatística")

col_stats1, col_stats2 = st.columns(2)

with col_stats1:
    st.markdown("### 📈 Estatísticas Descritivas")
    
    # Calcular estatísticas
    stats_df = df[tributos].describe()
    stats_df = stats_df.round(2)
    
    # Formatar valores monetários
    for col in stats_df.columns:
        stats_df[col] = stats_df[col].apply(lambda x: formatar_moeda_br(x) if pd.notna(x) else x)
    
    st.dataframe(stats_df, use_container_width=True)

with col_stats2:
    st.markdown("### 🏆 Ranking de Tributos")
    
    # Calcular total por tributo
    totais_tributos = df[tributos].sum().sort_values(ascending=False)
    
    # Criar gráfico de ranking
    fig_ranking = px.bar(
        x=totais_tributos.values,
        y=totais_tributos.index,
        orientation='h',
        title="Ranking de Tributos por Arrecadação Total",
        template=tema_grafico
    )
    
    fig_ranking.update_layout(
        height=400,
        title_x=0.5,
        xaxis_title="Arrecadação Total (R$)",
        yaxis_title="Tributo"
    )
    
    st.plotly_chart(fig_ranking, use_container_width=True)

# ========== ARRECADAÇÃO ENSINO ==========
st.markdown("## 🎓 Arrecadação Ensino")

try:
    # Carregar dados de ensino
    df_ensino = pd.read_excel("Arrecadacao Ensino.xlsx", header=2)
    df_ensino = df_ensino.loc[:, ~df_ensino.columns.str.contains("^Unnamed")]
    df_ensino.columns = df_ensino.columns.str.strip().str.upper()
    df_ensino["ANO"] = df_ensino["ANO"].astype(str)
    
    if "ANO" not in df_ensino.columns:
        st.error("A coluna 'ANO' não foi encontrada no arquivo 'Arrecadacao Ensino.xlsx'.")
    else:
        coluna_valor_ensino = [col for col in df_ensino.columns if col != "ANO"][0]
        
        # Métricas de ensino
        ultimo_ano_ensino = df_ensino["ANO"].max()
        penultimo_ano_ensino = df_ensino["ANO"].iloc[-2] if len(df_ensino) > 1 else ultimo_ano_ensino
        
        ultimo_valor_ensino = df_ensino[df_ensino["ANO"] == ultimo_ano_ensino][coluna_valor_ensino].iloc[0]
        penultimo_valor_ensino = df_ensino[df_ensino["ANO"] == penultimo_ano_ensino][coluna_valor_ensino].iloc[0]
        
        crescimento_ensino = ((ultimo_valor_ensino - penultimo_valor_ensino) / penultimo_valor_ensino * 100) if penultimo_valor_ensino > 0 else 0
        media_ensino = df_ensino[coluna_valor_ensino].mean()
        
        # Layout de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_moeda_br(ultimo_valor_ensino)}</div>
                <div class="metric-label">Ensino {ultimo_ano_ensino}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_moeda_br(penultimo_valor_ensino)}</div>
                <div class="metric-label">Ensino {penultimo_ano_ensino}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{crescimento_ensino:.1f}%</div>
                <div class="metric-label">Crescimento Ensino</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_moeda_br(media_ensino)}</div>
                <div class="metric-label">Média Anual Ensino</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráficos de ensino
        col_ensino1, col_ensino2 = st.columns(2)
        
        with col_ensino1:
            # Gráfico de barras
            df_ensino["TEXTO_FORMATADO"] = df_ensino[coluna_valor_ensino].apply(formatar_moeda_br)
            
            fig_ensino_bar = px.bar(
                df_ensino,
                x="ANO",
                y=coluna_valor_ensino,
                title="Arrecadação Ensino por Ano",
                labels={"ANO": "Ano", coluna_valor_ensino: "Valor Arrecadado (R$)"},
                text="TEXTO_FORMATADO",
                color_discrete_sequence=["#20B2AA"],
                template=tema_grafico
            )
            
            fig_ensino_bar.update_traces(
                textposition="outside",
                textfont=dict(size=12)
            )
            
            fig_ensino_bar.update_layout(
                height=400,
                title_x=0.5,
                yaxis=dict(
                    tickformat=".2f",
                    tickprefix="R$ ",
                    separatethousands=True,
                ),
                bargap=0.3
            )
            
            st.plotly_chart(fig_ensino_bar, use_container_width=True)
        
        with col_ensino2:
            # Gráfico de linha
            fig_ensino_line = px.line(
                df_ensino,
                x="ANO",
                y=coluna_valor_ensino,
                title="Evolução da Arrecadação Ensino",
                markers=True,
                template=tema_grafico
            )
            
            fig_ensino_line.update_layout(
                height=400,
                title_x=0.5,
                yaxis=dict(
                    tickformat=".2f",
                    tickprefix="R$ ",
                    separatethousands=True,
                )
            )
            
            st.plotly_chart(fig_ensino_line, use_container_width=True)

except FileNotFoundError:
    st.warning("📁 O arquivo 'Arrecadacao Ensino.xlsx' não foi encontrado.")
except Exception as e:
    st.error(f"❌ Erro ao carregar dados de ensino: {e}")

# ========== RECEITA PRÓPRIA ==========
st.markdown("## 💰 Receita Própria Total")

try:
    # Carregar dados de receita própria
    df_receita = pd.read_excel("Receita Propria Consolidado.xlsx", header=2)
    df_receita = df_receita.loc[:, ~df_receita.columns.str.contains("^Unnamed")]
    df_receita.columns = df_receita.columns.str.strip().str.upper()
    df_receita["ANO"] = df_receita["ANO"].astype(str)
    
    if "ANO" not in df_receita.columns:
        st.error("A coluna 'ANO' não foi encontrada no arquivo 'Receita Propria Consolidado.xlsx'.")
    else:
        coluna_valor_receita = [col for col in df_receita.columns if col != "ANO"][0]
        
        # Métricas de receita própria
        ultimo_ano_receita = df_receita["ANO"].max()
        penultimo_ano_receita = df_receita["ANO"].iloc[-2] if len(df_receita) > 1 else ultimo_ano_receita
        
        ultimo_valor_receita = df_receita[df_receita["ANO"] == ultimo_ano_receita][coluna_valor_receita].iloc[0]
        penultimo_valor_receita = df_receita[df_receita["ANO"] == penultimo_ano_receita][coluna_valor_receita].iloc[0]
        
        crescimento_receita = ((ultimo_valor_receita - penultimo_valor_receita) / penultimo_valor_receita * 100) if penultimo_valor_receita > 0 else 0
        media_receita = df_receita[coluna_valor_receita].mean()
        
        # Layout de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_moeda_br(ultimo_valor_receita)}</div>
                <div class="metric-label">Receita {ultimo_ano_receita}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_moeda_br(penultimo_valor_receita)}</div>
                <div class="metric-label">Receita {penultimo_ano_receita}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{crescimento_receita:.1f}%</div>
                <div class="metric-label">Crescimento Receita</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_moeda_br(media_receita)}</div>
                <div class="metric-label">Média Anual Receita</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráficos de receita própria
        col_receita1, col_receita2 = st.columns(2)
        
        with col_receita1:
            # Gráfico de barras
            df_receita["TEXTO_FORMATADO"] = df_receita[coluna_valor_receita].apply(formatar_moeda_br)
            
            fig_receita_bar = px.bar(
                df_receita,
                x="ANO",
                y=coluna_valor_receita,
                title="Receita Própria Total por Ano",
                labels={"ANO": "Ano", coluna_valor_receita: "Valor (R$)"},
                text="TEXTO_FORMATADO",
                color_discrete_sequence=["#4682B4"],
                template=tema_grafico
            )
            
            fig_receita_bar.update_traces(
                textposition="outside",
                textfont=dict(size=12)
            )
            
            fig_receita_bar.update_layout(
                height=400,
                title_x=0.5,
                yaxis=dict(
                    tickformat=".2f",
                    tickprefix="R$ ",
                    separatethousands=True,
                ),
                bargap=0.3
            )
            
            st.plotly_chart(fig_receita_bar, use_container_width=True)
        
        with col_receita2:
            # Gráfico de área
            fig_receita_area = px.area(
                df_receita,
                x="ANO",
                y=coluna_valor_receita,
                title="Evolução da Receita Própria",
                template=tema_grafico
            )
            
            fig_receita_area.update_layout(
                height=400,
                title_x=0.5,
                yaxis=dict(
                    tickformat=".2f",
                    tickprefix="R$ ",
                    separatethousands=True,
                )
            )
            
            st.plotly_chart(fig_receita_area, use_container_width=True)

except FileNotFoundError:
    st.warning("📁 O arquivo 'Receita Propria Consolidado.xlsx' não foi encontrado.")
except Exception as e:
    st.error(f"❌ Erro ao carregar dados de receita própria: {e}")

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>📊 Dashboard Tributário Municipal | Desenvolvido com Streamlit e Plotly</p>
    <p>Última atualização: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
