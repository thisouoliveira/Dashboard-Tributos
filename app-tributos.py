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
    .tab-content {
        padding: 1rem 0;
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

# ========== FUNÇÃO PARA CARREGAR DADOS ==========
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

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    # Filtros globais
    st.markdown("### 📅 Filtros Globais")
    
    # Carregar dados para obter anos disponíveis de todos os arquivos
    anos_disponiveis = set()
    tributos_disponiveis = set()
    
    # Verificar anos disponíveis em todos os arquivos
    arquivos = ["Arrecadacao Tributos.xlsx", "Arrecadacao Ensino.xlsx", "Arrecadacao Bancos.xlsx", "Receita Propria Consolidado.xlsx", "Arrecadacao Divida Ativa.xlsx"]
    
    for arquivo in arquivos:
        try:
            df_temp = pd.read_excel(arquivo, header=2)
            df_temp = df_temp.loc[:, ~df_temp.columns.str.contains("^Unnamed")]
            df_temp.columns = df_temp.columns.str.strip().str.upper()
            if "ANO" in df_temp.columns:
                anos_disponiveis.update(df_temp["ANO"].astype(str).tolist())
                # Para tributos, apenas do arquivo principal
                if arquivo == "Arrecadacao Tributos.xlsx":
                    tributos_cols = [col for col in df_temp.columns if col not in ["ANO", "TOTAL"]]
                    tributos_disponiveis.update(tributos_cols)
        except:
            continue
    
    anos_disponiveis = sorted(list(anos_disponiveis))
    tributos_disponiveis = sorted(list(tributos_disponiveis))
    
    # Filtro de anos global
    anos_selecionados = st.multiselect(
        "📅 Anos para análise",
        options=anos_disponiveis,
        default=anos_disponiveis,
        help="Selecione os anos que deseja analisar em todas as abas"
    )
    
    # Filtro de tributos (apenas para a aba de tributos)
    if tributos_disponiveis:
        tributos_selecionados = st.multiselect(
            "🏛️ Tributos específicos",
            options=tributos_disponiveis,
            default=tributos_disponiveis,
            help="Selecione os tributos específicos para análise"
        )
    else:
        tributos_selecionados = []
    
    # Botão para limpar filtros
    if st.button("🔄 Limpar Todos os Filtros", help="Restaura todos os filtros para os valores padrão"):
        st.rerun()
    
    # Informações sobre os filtros
    st.markdown("### ℹ️ Sobre os Filtros")
    st.markdown("""
    - **📅 Anos:** Aplicado em todas as abas
    - **🏛️ Tributos:** Aplicado apenas na aba de Tributos
    - Os filtros são aplicados automaticamente em todas as visualizações
    """)
    
    st.markdown("---")
    
    # Configurações de gráficos
    st.markdown("### 📈 Configurações de Gráficos")
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
    
    # Configurações específicas para gráficos de tributos
    st.markdown("### 📊 Configurações de Gráficos por Tributo")
    num_colunas_tributos = st.slider(
        "Número de colunas nos gráficos por tributo",
        min_value=1,
        max_value=4,
        value=2,
        help="Define quantas colunas serão usadas para exibir os gráficos individuais por tributo"
    )
    
    tipo_grafico_tributos = st.selectbox(
        "Tipo de gráfico por tributo",
        ["Barras Verticais", "Barras Horizontais", "Linha", "Área"],
        help="Escolha o tipo de visualização para os gráficos individuais por tributo"
    )
    
    mostrar_valores = st.checkbox(
        "Mostrar valores nos gráficos",
        value=True,
        help="Exibe os valores monetários diretamente nos gráficos"
    )

# ========== SISTEMA DE ABAS ==========
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏛️ Arrecadação Tributos", 
    "🎓 Arrecadação Ensino", 
    "🏦 Arrecadação Bancos",
    "💰 Receita Própria",
    "📈 Evolução Arrecadação",
    "💳 Arrecadação Dívida Ativa"
])

# ========== ABA 1: ARRECADAÇÃO TRIBUTOS ==========
with tab1:
    st.markdown("## 🏛️ Arrecadação Tributos")
    
    # Carregar dados
    df = carregar_dados("Arrecadacao Tributos.xlsx")
    
    # Mostrar filtros aplicados
    if anos_selecionados or tributos_selecionados:
        st.markdown("### 🔍 Filtros Aplicados")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            if anos_selecionados:
                st.info(f"📅 **Anos selecionados:** {', '.join(anos_selecionados)}")
        
        with col_filtro2:
            if tributos_selecionados:
                st.info(f"🏛️ **Tributos selecionados:** {', '.join(tributos_selecionados)}")
    
    if df is None:
        st.error("Não foi possível carregar os dados. Verifique se o arquivo existe.")
    else:
        # Filtrar por anos selecionados (filtro global)
        if anos_selecionados:
            df = df[df["ANO"].isin(anos_selecionados)]
        
        # Filtrar por tributos selecionados (filtro global)
        if tributos_selecionados:
            colunas_para_manter = ["ANO"] + tributos_selecionados
            if "TOTAL" in df.columns:
                colunas_para_manter.append("TOTAL")
            df = df[colunas_para_manter]
        
        # Verificar se há dados após filtros
        if df.empty:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados. Tente ajustar os filtros na sidebar.")
        else:
            # Métricas principais
            st.markdown("### 📊 Métricas Principais")
        
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
        
        # Gráfico principal
        st.markdown("### 📈 Análise Temporal")
        
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
        
        # Gráficos de barra vertical por tributo
        st.markdown(f"### 📊 Gráficos de {tipo_grafico_tributos} por Tributo")
        
        # Criar gráficos individuais para cada tributo
        if len(tributos) > 0:
            # Determinar o número de colunas baseado na configuração da sidebar
            num_colunas = min(num_colunas_tributos, len(tributos))
            num_linhas = (len(tributos) + num_colunas - 1) // num_colunas
            
            # Informações sobre a configuração
            st.info(f"""
            📋 **Configuração atual:** {num_colunas_tributos} gráficos por linha
            - Total de tributos: {len(tributos)}
            - Layout: {num_linhas} linha(s) × {num_colunas} coluna(s)
            - Use o controle na sidebar para ajustar o número de colunas
            """)
            
            # Criar subplots
            fig_tributos = make_subplots(
                rows=num_linhas,
                cols=num_colunas,
                subplot_titles=tributos,
                vertical_spacing=0.15,
                horizontal_spacing=0.08
            )
            
            # Cores para os gráficos
            cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for i, tributo in enumerate(tributos):
                linha = (i // num_colunas) + 1
                coluna = (i % num_colunas) + 1
                
                # Preparar texto para os valores
                texto_valores = [formatar_moeda_br(val) for val in df[tributo]] if mostrar_valores else None
                
                # Criar gráfico baseado no tipo selecionado
                if tipo_grafico_tributos == "Barras Verticais":
                    trace = go.Bar(
                        x=df["ANO"],
                        y=df[tributo],
                        name=tributo,
                        marker_color=cores[i % len(cores)],
                        text=texto_valores,
                        textposition="outside",
                        textfont=dict(size=10),
                        showlegend=False
                    )
                elif tipo_grafico_tributos == "Barras Horizontais":
                    trace = go.Bar(
                        x=df[tributo],
                        y=df["ANO"],
                        name=tributo,
                        marker_color=cores[i % len(cores)],
                        text=texto_valores,
                        textposition="outside",
                        textfont=dict(size=10),
                        showlegend=False,
                        orientation='h'
                    )
                elif tipo_grafico_tributos == "Linha":
                    trace = go.Scatter(
                        x=df["ANO"],
                        y=df[tributo],
                        name=tributo,
                        mode='lines+markers',
                        line=dict(color=cores[i % len(cores)], width=3),
                        marker=dict(size=8),
                        text=texto_valores,
                        textposition="top center",
                        textfont=dict(size=10),
                        showlegend=False
                    )
                else:  # Área
                    trace = go.Scatter(
                        x=df["ANO"],
                        y=df[tributo],
                        name=tributo,
                        fill='tonexty',
                        line=dict(color=cores[i % len(cores)]),
                        text=texto_valores,
                        textposition="top center",
                        textfont=dict(size=10),
                        showlegend=False
                    )
                
                fig_tributos.add_trace(trace, row=linha, col=coluna)
                
                # Configurar eixos baseado no tipo de gráfico
                if tipo_grafico_tributos == "Barras Horizontais":
                    # Para barras horizontais, inverter os eixos
                    fig_tributos.update_xaxes(
                        title_text="Valor (R$)",
                        row=linha,
                        col=coluna,
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                        title_font=dict(size=12),
                        tickfont=dict(size=10)
                    )
                    
                    fig_tributos.update_yaxes(
                        title_text="Ano",
                        row=linha,
                        col=coluna,
                        title_font=dict(size=12),
                        tickfont=dict(size=10)
                    )
                else:
                    # Para outros tipos de gráfico
                    fig_tributos.update_yaxes(
                        title_text="Valor (R$)",
                        row=linha,
                        col=coluna,
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                        title_font=dict(size=12),
                        tickfont=dict(size=10)
                    )
                    
                    fig_tributos.update_xaxes(
                        title_text="Ano",
                        row=linha,
                        col=coluna,
                        title_font=dict(size=12),
                        tickfont=dict(size=10)
                    )
            
            fig_tributos.update_layout(
                title=f"Gráficos de {tipo_grafico_tributos} por Tributo",
                height=350 * num_linhas,
                template=tema_grafico,
                title_x=0.5,
                showlegend=False,
                margin=dict(l=50, r=50, t=80, b=50),
                title_font=dict(size=18)
            )
            
            # Ajustar tamanho dos títulos dos subplots
            fig_tributos.update_annotations(font_size=14)
            
            st.plotly_chart(fig_tributos, use_container_width=True)
        
        # Gráficos comparativos
        st.markdown("### 🔍 Análise Comparativa")
        
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
        
        # Tabela interativa
        st.markdown("### 📋 Dados Detalhados")
        
        # Formatar dados para exibição
        df_formatado = df.copy()
        for col in df_formatado.columns:
            if col != "ANO":
                df_formatado[col] = df_formatado[col].apply(formatar_moeda_br)
        
        st.dataframe(
            df_formatado,
            use_container_width=True,
            hide_index=True
        )

# ========== ABA 2: ARRECADAÇÃO ENSINO ==========
with tab2:
    st.markdown("## 🎓 Arrecadação Ensino")
    
    try:
        # Carregar dados de ensino
        df_ensino = carregar_dados("Arrecadacao Ensino.xlsx")
        
        if df_ensino is None:
            st.error("Não foi possível carregar os dados de ensino.")
        else:
            # Mostrar filtros aplicados
            if anos_selecionados:
                st.info(f"📅 **Anos selecionados:** {', '.join(anos_selecionados)}")
            
            # Filtrar por anos selecionados (filtro global)
            if anos_selecionados:
                df_ensino = df_ensino[df_ensino["ANO"].isin(anos_selecionados)]
            
            # Verificar se há dados após filtros
            if df_ensino.empty:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados. Tente ajustar os filtros na sidebar.")
            elif "ANO" not in df_ensino.columns:
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
                
                # Gráfico de área
                st.markdown("### 📈 Evolução Temporal")
                fig_ensino_area = px.area(
                    df_ensino,
                    x="ANO",
                    y=coluna_valor_ensino,
                    title="Evolução da Arrecadação Ensino (Área)",
                    template=tema_grafico
                )
                
                fig_ensino_area.update_layout(
                    height=400,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    )
                )
                
                st.plotly_chart(fig_ensino_area, use_container_width=True)
                
                # Tabela de dados
                st.markdown("### 📋 Dados Detalhados - Ensino")
                df_ensino_formatado = df_ensino.copy()
                df_ensino_formatado[coluna_valor_ensino] = df_ensino_formatado[coluna_valor_ensino].apply(formatar_moeda_br)
                
                st.dataframe(
                    df_ensino_formatado,
                    use_container_width=True,
                    hide_index=True
                )
    
    except FileNotFoundError:
        st.warning("📁 O arquivo 'Arrecadacao Ensino.xlsx' não foi encontrado.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de ensino: {e}")

# ========== ABA 3: ARRECADAÇÃO BANCOS ==========
with tab3:
    st.markdown("## 🏦 Arrecadação Bancos")
    
    try:
        # Carregar dados de bancos
        df_bancos = carregar_dados("Arrecadacao Bancos.xlsx")
        
        if df_bancos is None:
            st.error("Não foi possível carregar os dados de bancos.")
        else:
            # Mostrar filtros aplicados
            if anos_selecionados:
                st.info(f"📅 **Anos selecionados:** {', '.join(anos_selecionados)}")
            
            # Filtrar por anos selecionados (filtro global)
            if anos_selecionados:
                df_bancos = df_bancos[df_bancos["ANO"].isin(anos_selecionados)]
            
            # Verificar se há dados após filtros
            if df_bancos.empty:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados. Tente ajustar os filtros na sidebar.")
            elif "ANO" not in df_bancos.columns:
                st.error("A coluna 'ANO' não foi encontrada no arquivo 'Arrecadacao Bancos.xlsx'.")
            else:
                coluna_valor_bancos = [col for col in df_bancos.columns if col != "ANO"][0]
                
                # Métricas de bancos
                ultimo_ano_bancos = df_bancos["ANO"].max()
                penultimo_ano_bancos = df_bancos["ANO"].iloc[-2] if len(df_bancos) > 1 else ultimo_ano_bancos
                
                ultimo_valor_bancos = df_bancos[df_bancos["ANO"] == ultimo_ano_bancos][coluna_valor_bancos].iloc[0]
                penultimo_valor_bancos = df_bancos[df_bancos["ANO"] == penultimo_ano_bancos][coluna_valor_bancos].iloc[0]
                
                crescimento_bancos = ((ultimo_valor_bancos - penultimo_valor_bancos) / penultimo_valor_bancos * 100) if penultimo_valor_bancos > 0 else 0
                media_bancos = df_bancos[coluna_valor_bancos].mean()
                
                # Layout de métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(ultimo_valor_bancos)}</div>
                        <div class="metric-label">Bancos {ultimo_ano_bancos}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(penultimo_valor_bancos)}</div>
                        <div class="metric-label">Bancos {penultimo_ano_bancos}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{crescimento_bancos:.1f}%</div>
                        <div class="metric-label">Crescimento Bancos</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(media_bancos)}</div>
                        <div class="metric-label">Média Anual Bancos</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gráficos de bancos
                col_bancos1, col_bancos2 = st.columns(2)
                
                with col_bancos1:
                    # Gráfico de barras
                    df_bancos["TEXTO_FORMATADO"] = df_bancos[coluna_valor_bancos].apply(formatar_moeda_br)
                    
                    fig_bancos_bar = px.bar(
                        df_bancos,
                        x="ANO",
                        y=coluna_valor_bancos,
                        title="Arrecadação Bancos por Ano",
                        labels={"ANO": "Ano", coluna_valor_bancos: "Valor Arrecadado (R$)"},
                        text="TEXTO_FORMATADO",
                        color_discrete_sequence=["#FF6B6B"],
                        template=tema_grafico
                    )
                    
                    fig_bancos_bar.update_traces(
                        textposition="outside",
                        textfont=dict(size=12)
                    )
                    
                    fig_bancos_bar.update_layout(
                        height=400,
                        title_x=0.5,
                        yaxis=dict(
                            tickformat=".2f",
                            tickprefix="R$ ",
                            separatethousands=True,
                        ),
                        bargap=0.3
                    )
                    
                    st.plotly_chart(fig_bancos_bar, use_container_width=True)
                
                with col_bancos2:
                    # Gráfico de linha
                    fig_bancos_line = px.line(
                        df_bancos,
                        x="ANO",
                        y=coluna_valor_bancos,
                        title="Evolução da Arrecadação Bancos",
                        markers=True,
                        template=tema_grafico
                    )
                    
                    fig_bancos_line.update_layout(
                        height=400,
                        title_x=0.5,
                        yaxis=dict(
                            tickformat=".2f",
                            tickprefix="R$ ",
                            separatethousands=True,
                        )
                    )
                    
                    st.plotly_chart(fig_bancos_line, use_container_width=True)
                
                # Gráfico de área
                st.markdown("### 📈 Evolução Temporal")
                fig_bancos_area = px.area(
                    df_bancos,
                    x="ANO",
                    y=coluna_valor_bancos,
                    title="Evolução da Arrecadação Bancos (Área)",
                    template=tema_grafico
                )
                
                fig_bancos_area.update_layout(
                    height=400,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    )
                )
                
                st.plotly_chart(fig_bancos_area, use_container_width=True)
                
                # Tabela de dados
                st.markdown("### 📋 Dados Detalhados - Bancos")
                df_bancos_formatado = df_bancos.copy()
                df_bancos_formatado[coluna_valor_bancos] = df_bancos_formatado[coluna_valor_bancos].apply(formatar_moeda_br)
                
                st.dataframe(
                    df_bancos_formatado,
                    use_container_width=True,
                    hide_index=True
                )
    
    except FileNotFoundError:
        st.warning("📁 O arquivo 'Arrecadacao Bancos.xlsx' não foi encontrado.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de bancos: {e}")

# ========== ABA 4: RECEITA PRÓPRIA ==========
with tab4:
    st.markdown("## 💰 Receita Própria Consolidada")
    
    try:
        # Carregar dados de receita própria
        df_receita = carregar_dados("Receita Propria Consolidado.xlsx")
        
        if df_receita is None:
            st.error("Não foi possível carregar os dados de receita própria.")
        else:
            # Mostrar filtros aplicados
            if anos_selecionados:
                st.info(f"📅 **Anos selecionados:** {', '.join(anos_selecionados)}")
            
            # Filtrar por anos selecionados (filtro global)
            if anos_selecionados:
                df_receita = df_receita[df_receita["ANO"].isin(anos_selecionados)]
            
            # Verificar se há dados após filtros
            if df_receita.empty:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados. Tente ajustar os filtros na sidebar.")
            elif "ANO" not in df_receita.columns:
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
                
                # Gráfico de linha
                st.markdown("### 📈 Evolução Temporal")
                fig_receita_line = px.line(
                    df_receita,
                    x="ANO",
                    y=coluna_valor_receita,
                    title="Evolução da Receita Própria (Linha)",
                    markers=True,
                    template=tema_grafico
                )
                
                fig_receita_line.update_layout(
                    height=400,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    )
                )
                
                st.plotly_chart(fig_receita_line, use_container_width=True)
                
                # Tabela de dados
                st.markdown("### 📋 Dados Detalhados - Receita Própria")
                df_receita_formatado = df_receita.copy()
                df_receita_formatado[coluna_valor_receita] = df_receita_formatado[coluna_valor_receita].apply(formatar_moeda_br)
                
                st.dataframe(
                    df_receita_formatado,
                    use_container_width=True,
                    hide_index=True
                )
    
    except FileNotFoundError:
        st.warning("📁 O arquivo 'Receita Propria Consolidado.xlsx' não foi encontrado.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de receita própria: {e}")

# ========== ABA 5: EVOLUÇÃO ARRECADAÇÃO ==========
with tab5:
    st.markdown("## 📈 Evolução Arrecadação")
    
    # Informação sobre o cálculo de superávit/déficit
    st.info("""
    💡 **Cálculo de Superávit/Déficit:** 
    - **Superávit:** Quando ARRECADADO > ORÇADO (valor positivo)
    - **Déficit:** Quando ARRECADADO < ORÇADO (valor negativo)
    - **Fórmula:** SALDO = ARRECADADO - ORÇADO
    """)
    
    try:
        # Carregar dados de evolução
        xl = pd.ExcelFile('Evolucao Arrecadacao.xlsx')
        anos_disponiveis_evolucao = xl.sheet_names
        
        # Verificar se há abas no arquivo
        if not anos_disponiveis_evolucao:
            st.error("❌ O arquivo 'Evolucao Arrecadacao.xlsx' não possui abas.")
            st.stop()
        
        st.success(f"✅ Arquivo carregado com sucesso! Encontradas {len(anos_disponiveis_evolucao)} abas: {', '.join(anos_disponiveis_evolucao)}")
        
        # Filtros específicos para evolução
        st.markdown("### 🔍 Filtros de Análise")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            anos_evolucao_selecionados = st.multiselect(
                "📅 Anos para análise",
                options=anos_disponiveis_evolucao,
                default=anos_disponiveis_evolucao[-2:] if len(anos_disponiveis_evolucao) >= 2 else anos_disponiveis_evolucao,
                help="Selecione os anos que deseja analisar"
            )
        
        with col_filtro2:
            # Carregar um ano para obter os tributos disponíveis
            if anos_evolucao_selecionados:
                try:
                    df_temp = pd.read_excel('Evolucao Arrecadacao.xlsx', sheet_name=anos_evolucao_selecionados[0])
                    
                    # Verificar se a coluna existe (pode ser 'TRIBUTO/MÊS/ANO' ou 'TRIBUTO')
                    coluna_tributo = None
                    if 'TRIBUTO/MÊS/ANO' in df_temp.columns:
                        coluna_tributo = 'TRIBUTO/MÊS/ANO'
                    elif 'TRIBUTO' in df_temp.columns:
                        coluna_tributo = 'TRIBUTO'
                    
                    if coluna_tributo:
                        tributos_evolucao = df_temp[coluna_tributo].unique().tolist()
                        st.success(f"✅ Encontrados {len(tributos_evolucao)} tributos na aba {anos_evolucao_selecionados[0]} (coluna: {coluna_tributo})")
                    else:
                        st.error(f"❌ Coluna de tributo não encontrada na aba {anos_evolucao_selecionados[0]}")
                        st.write("Colunas disponíveis:", list(df_temp.columns))
                        tributos_evolucao = []
                except Exception as e:
                    st.error(f"❌ Erro ao carregar aba {anos_evolucao_selecionados[0]}: {e}")
                    tributos_evolucao = []
            else:
                tributos_evolucao = []
            
            if tributos_evolucao:
                tributos_evolucao_selecionados = st.multiselect(
                    "🏛️ Tributos para análise",
                    options=tributos_evolucao,
                    default=tributos_evolucao,
                    help="Selecione os tributos que deseja analisar"
                )
            else:
                tributos_evolucao_selecionados = []
        
        if not anos_evolucao_selecionados:
            st.warning("⚠️ Selecione pelo menos um ano para análise.")
        else:
            # Carregar e processar dados
            dados_evolucao = []
            erros_processamento = []
            
            for ano in anos_evolucao_selecionados:
                try:
                    df_ano = pd.read_excel('Evolucao Arrecadacao.xlsx', sheet_name=ano)
                    
                    # Verificar se a coluna necessária existe (pode ser 'TRIBUTO/MÊS/ANO' ou 'TRIBUTO')
                    coluna_tributo = None
                    if 'TRIBUTO/MÊS/ANO' in df_ano.columns:
                        coluna_tributo = 'TRIBUTO/MÊS/ANO'
                    elif 'TRIBUTO' in df_ano.columns:
                        coluna_tributo = 'TRIBUTO'
                    
                    if not coluna_tributo:
                        erros_processamento.append(f"Coluna de tributo não encontrada na aba {ano}")
                        continue
                    
                    # Filtrar tributos selecionados
                    if tributos_evolucao_selecionados:
                        df_ano = df_ano[df_ano[coluna_tributo].isin(tributos_evolucao_selecionados)]
                    
                    # Verificar se há dados após filtro
                    if df_ano.empty:
                        erros_processamento.append(f"Nenhum dado encontrado na aba {ano} após aplicar filtros")
                        continue
                    
                    # Processar dados mensais
                    for _, row in df_ano.iterrows():
                        tributo = row[coluna_tributo]
                        
                        # Verificar se as colunas necessárias existem
                        colunas_necessarias = ['ORÇADO', 'ARRECADADO', 'META']
                        if not all(col in df_ano.columns for col in colunas_necessarias):
                            erros_processamento.append(f"Colunas necessárias não encontradas na aba {ano}")
                            continue
                        
                        # Processar colunas de meses (colunas 1-12)
                        for i in range(1, 13):
                            if i < len(df_ano.columns):
                                col_mes = df_ano.columns[i]
                                if pd.notna(row[col_mes]) and row[col_mes] != 0:
                                    try:
                                        # Calcular superávit/déficit usando a fórmula ARRECADADO - ORÇADO
                                        saldo = row['ARRECADADO'] - row['ORÇADO']
                                        superavit = saldo if saldo > 0 else 0
                                        deficit = abs(saldo) if saldo < 0 else 0
                                        
                                        dados_evolucao.append({
                                            'ANO': ano,
                                            'TRIBUTO': tributo,
                                            'MES': i,
                                            'VALOR_MENSAL': row[col_mes],
                                            'ORCADO': row['ORÇADO'],
                                            'ARRECADADO': row['ARRECADADO'],
                                            'META': row['META'],
                                            'SALDO': saldo,
                                            'SUPERAVIT': superavit,
                                            'DEFICIT': deficit
                                        })
                                    except Exception as e:
                                        erros_processamento.append(f"Erro ao processar linha do tributo {tributo} na aba {ano}: {e}")
                
                except Exception as e:
                    erros_processamento.append(f"Erro ao carregar aba {ano}: {e}")
            
            # Mostrar erros se houver
            if erros_processamento:
                st.warning("⚠️ Alguns erros foram encontrados durante o processamento:")
                for erro in erros_processamento[:5]:  # Mostrar apenas os primeiros 5 erros
                    st.write(f"• {erro}")
                if len(erros_processamento) > 5:
                    st.write(f"• ... e mais {len(erros_processamento) - 5} erros")
            
            if dados_evolucao:
                df_evolucao = pd.DataFrame(dados_evolucao)
                st.success(f"✅ Processados {len(dados_evolucao)} registros de dados")
                
                # Métricas principais
                st.markdown("### 📊 Métricas Principais")
                
                # Calcular métricas por ano
                metricas_por_ano = df_evolucao.groupby('ANO').agg({
                    'ARRECADADO': 'sum',
                    'ORCADO': 'sum',
                    'VALOR_MENSAL': 'sum'
                }).reset_index()
                
                # Layout de métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    ultimo_ano_evol = metricas_por_ano['ANO'].max()
                    ultimo_arrecadado = metricas_por_ano[metricas_por_ano['ANO'] == ultimo_ano_evol]['ARRECADADO'].iloc[0]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(ultimo_arrecadado)}</div>
                        <div class="metric-label">Arrecadado {ultimo_ano_evol}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    ultimo_orcado = metricas_por_ano[metricas_por_ano['ANO'] == ultimo_ano_evol]['ORCADO'].iloc[0]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(ultimo_orcado)}</div>
                        <div class="metric-label">Orçado {ultimo_ano_evol}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    meta_alcancada = (ultimo_arrecadado / ultimo_orcado * 100) if ultimo_orcado > 0 else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{meta_alcancada:.1f}%</div>
                        <div class="metric-label">Meta Atingida</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    superavit_deficit = ultimo_arrecadado - ultimo_orcado
                    status = "SUPERÁVIT" if superavit_deficit > 0 else "DÉFICIT"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(abs(superavit_deficit))}</div>
                        <div class="metric-label">{status}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gráficos de evolução
                st.markdown("### 📈 Análise Temporal")
                
                # Gráfico 1: Evolução mensal por tributo
                col_evol1, col_evol2 = st.columns(2)
                
                with col_evol1:
                    # Gráfico de linha para evolução mensal
                    fig_evol_mensal = px.line(
                        df_evolucao,
                        x='MES',
                        y='VALOR_MENSAL',
                        color='TRIBUTO',
                        title='Evolução Mensal por Tributo',
                        template=tema_grafico
                    )
                    
                    fig_evol_mensal.update_layout(
                        height=400,
                        title_x=0.5,
                        yaxis=dict(
                            tickformat=".2f",
                            tickprefix="R$ ",
                            separatethousands=True,
                        ),
                        xaxis=dict(
                            tickmode='linear',
                            tick0=1,
                            dtick=1
                        )
                    )
                    
                    st.plotly_chart(fig_evol_mensal, use_container_width=True)
                
                with col_evol2:
                    # Gráfico de barras para comparação orçado vs arrecadado
                    df_comparacao = df_evolucao.groupby(['ANO', 'TRIBUTO']).agg({
                        'ORCADO': 'first',
                        'ARRECADADO': 'first'
                    }).reset_index()
                    
                    # Criar gráfico de barras agrupadas
                    fig_comparacao = go.Figure()
                    
                    for tributo in df_comparacao['TRIBUTO'].unique():
                        df_tributo = df_comparacao[df_comparacao['TRIBUTO'] == tributo]
                        
                        # Barras para orçado
                        fig_comparacao.add_trace(go.Bar(
                            name=f'{tributo} - Orçado',
                            x=df_tributo['ANO'],
                            y=df_tributo['ORCADO'],
                            marker_color='lightblue',
                            opacity=0.7
                        ))
                        
                        # Barras para arrecadado
                        fig_comparacao.add_trace(go.Bar(
                            name=f'{tributo} - Arrecadado',
                            x=df_tributo['ANO'],
                            y=df_tributo['ARRECADADO'],
                            marker_color='darkblue',
                            opacity=0.9
                        ))
                    
                    fig_comparacao.update_layout(
                        title='Orçado vs Arrecadado por Tributo e Ano',
                        barmode='group',
                        height=400,
                        template=tema_grafico,
                        title_x=0.5,
                        yaxis=dict(
                            tickformat=".2f",
                            tickprefix="R$ ",
                            separatethousands=True,
                        )
                    )
                    
                    st.plotly_chart(fig_comparacao, use_container_width=True)
                
                # Gráfico 2: Análise de metas
                st.markdown("### 🎯 Análise de Metas")
                
                # Calcular percentual de meta por tributo e ano
                df_metas = df_evolucao.groupby(['ANO', 'TRIBUTO']).agg({
                    'META': 'first'
                }).reset_index()
                
                fig_metas = px.bar(
                    df_metas,
                    x='ANO',
                    y='META',
                    color='TRIBUTO',
                    title='Percentual de Meta Atingida por Tributo',
                    template=tema_grafico
                )
                
                fig_metas.update_layout(
                    height=400,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".1f",
                        ticksuffix="%",
                        title="Meta (%)"
                    )
                )
                
                st.plotly_chart(fig_metas, use_container_width=True)
                
                # Gráfico 3: Análise de superávit/déficit
                st.markdown("### 💰 Análise de Superávit/Déficit")
                
                # Calcular superávit/déficit por tributo e ano usando a fórmula ARRECADADO - ORÇADO
                df_superavit = df_evolucao.groupby(['ANO', 'TRIBUTO']).agg({
                    'ARRECADADO': 'first',
                    'ORCADO': 'first',
                    'SALDO': 'first'
                }).reset_index()
                
                # Calcular status baseado no saldo
                df_superavit['STATUS'] = df_superavit['SALDO'].apply(lambda x: 'SUPERÁVIT' if x > 0 else 'DÉFICIT')
                
                # Criar gráfico com cores diferentes para superávit e déficit
                fig_superavit = go.Figure()
                
                for tributo in df_superavit['TRIBUTO'].unique():
                    df_tributo = df_superavit[df_superavit['TRIBUTO'] == tributo]
                    
                    # Separar superávit e déficit
                    superavit_data = df_tributo[df_tributo['SALDO'] > 0]
                    deficit_data = df_tributo[df_tributo['SALDO'] < 0]
                    
                    # Adicionar barras de superávit (verde)
                    if not superavit_data.empty:
                        fig_superavit.add_trace(go.Bar(
                            name=f'{tributo} - Superávit',
                            x=superavit_data['ANO'],
                            y=superavit_data['SALDO'],
                            marker_color='green',
                            opacity=0.8,
                            showlegend=True
                        ))
                    
                    # Adicionar barras de déficit (vermelho)
                    if not deficit_data.empty:
                        fig_superavit.add_trace(go.Bar(
                            name=f'{tributo} - Déficit',
                            x=deficit_data['ANO'],
                            y=deficit_data['SALDO'],
                            marker_color='red',
                            opacity=0.8,
                            showlegend=True
                        ))
                
                fig_superavit.update_layout(
                    title='Superávit/Déficit por Tributo e Ano (ARRECADADO - ORÇADO)',
                    height=400,
                    template=tema_grafico,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                        title="Saldo (R$)"
                    ),
                    barmode='group'
                )
                
                # Adicionar linha de referência em zero
                fig_superavit.add_hline(y=0, line_dash="dash", line_color="black", line_width=2)
                
                st.plotly_chart(fig_superavit, use_container_width=True)
                
                # Análise detalhada de superávit/déficit
                st.markdown("### 📊 Análise Detalhada de Superávit/Déficit")
                
                # Criar métricas por status
                col_analise1, col_analise2, col_analise3 = st.columns(3)
                
                with col_analise1:
                    total_superavit = df_superavit[df_superavit['SALDO'] > 0]['SALDO'].sum()
                    st.metric(
                        label="💰 Total Superávit",
                        value=formatar_moeda_br(total_superavit),
                        delta=f"{len(df_superavit[df_superavit['SALDO'] > 0])} registros"
                    )
                
                with col_analise2:
                    total_deficit = abs(df_superavit[df_superavit['SALDO'] < 0]['SALDO'].sum())
                    st.metric(
                        label="📉 Total Déficit",
                        value=formatar_moeda_br(total_deficit),
                        delta=f"{len(df_superavit[df_superavit['SALDO'] < 0])} registros"
                    )
                
                with col_analise3:
                    saldo_geral = df_superavit['SALDO'].sum()
                    st.metric(
                        label="⚖️ Saldo Geral",
                        value=formatar_moeda_br(saldo_geral),
                        delta="Superávit" if saldo_geral > 0 else "Déficit"
                    )
                
                # Tabela de dados consolidados
                st.markdown("### 📋 Dados Consolidados")
                
                # Criar tabela consolidada usando a fórmula ARRECADADO - ORÇADO
                df_consolidado = df_evolucao.groupby(['ANO', 'TRIBUTO']).agg({
                    'ORCADO': 'first',
                    'ARRECADADO': 'first',
                    'META': 'first',
                    'SALDO': 'first'
                }).reset_index()
                
                # Calcular status baseado no saldo
                df_consolidado['STATUS'] = df_consolidado['SALDO'].apply(lambda x: 'SUPERÁVIT' if x > 0 else 'DÉFICIT')
                
                # Adicionar coluna de percentual de realização
                df_consolidado['PERCENTUAL_REALIZACAO'] = (df_consolidado['ARRECADADO'] / df_consolidado['ORCADO'] * 100).round(1)
                
                # Formatar dados para exibição
                df_consolidado_formatado = df_consolidado.copy()
                df_consolidado_formatado['ORCADO'] = df_consolidado_formatado['ORCADO'].apply(formatar_moeda_br)
                df_consolidado_formatado['ARRECADADO'] = df_consolidado_formatado['ARRECADADO'].apply(formatar_moeda_br)
                df_consolidado_formatado['META'] = df_consolidado_formatado['META'].apply(lambda x: f"{x:.1f}%")
                df_consolidado_formatado['SALDO'] = df_consolidado_formatado['SALDO'].apply(formatar_moeda_br)
                df_consolidado_formatado['PERCENTUAL_REALIZACAO'] = df_consolidado_formatado['PERCENTUAL_REALIZACAO'].apply(lambda x: f"{x:.1f}%")
                
                # Selecionar colunas para exibição
                colunas_exibicao = ['ANO', 'TRIBUTO', 'ORCADO', 'ARRECADADO', 'PERCENTUAL_REALIZACAO', 'META', 'SALDO', 'STATUS']
                df_exibicao = df_consolidado_formatado[colunas_exibicao]
                
                # Explicação das colunas da tabela
                st.markdown("""
                **📋 Legenda da Tabela:**
                - **ANO:** Ano de referência
                - **TRIBUTO:** Tipo de tributo
                - **ORÇADO:** Valor orçado para o ano
                - **ARRECADADO:** Valor efetivamente arrecadado
                - **% REALIZAÇÃO:** Percentual de realização (ARRECADADO/ORÇADO × 100)
                - **META:** Meta estabelecida (%)
                - **SALDO:** Saldo calculado (ARRECADADO - ORÇADO)
                - **STATUS:** Superávit (saldo > 0) ou Déficit (saldo < 0)
                """)
                
                st.dataframe(
                    df_exibicao,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download dos dados
                st.markdown("### 💾 Download dos Dados")
                
                # Preparar dados para download
                df_download = df_consolidado.copy()
                df_download['ORCADO'] = df_download['ORCADO'].apply(lambda x: f"R$ {x:,.2f}")
                df_download['ARRECADADO'] = df_download['ARRECADADO'].apply(lambda x: f"R$ {x:,.2f}")
                df_download['META'] = df_download['META'].apply(lambda x: f"{x:.1f}%")
                df_download['SALDO'] = df_download['SALDO'].apply(lambda x: f"R$ {x:,.2f}")
                df_download['PERCENTUAL_REALIZACAO'] = df_download['PERCENTUAL_REALIZACAO'].apply(lambda x: f"{x:.1f}%")
                
                # Criar arquivo CSV para download
                csv = df_download.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"evolucao_arrecadacao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                if erros_processamento:
                    st.error("❌ Verifique os erros acima para entender por que nenhum dado foi processado.")
    
    except FileNotFoundError:
        st.warning("📁 O arquivo 'Evolucao Arrecadacao.xlsx' não foi encontrado.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de evolução: {e}")
        st.write("Detalhes do erro:", str(e))



# ========== ABA 6: ARRECADAÇÃO DÍVIDA ATIVA ==========
with tab6:
    st.markdown("## 💳 Arrecadação Dívida Ativa")
    
    try:
        # Carregar dados de dívida ativa
        xl_divida = pd.ExcelFile('Arrecadacao Divida Ativa.xlsx')
        anos_disponiveis_divida = xl_divida.sheet_names
        
        # Verificar se há abas no arquivo
        if not anos_disponiveis_divida:
            st.error("❌ O arquivo 'Arrecadacao Divida Ativa.xlsx' não possui abas.")
            st.stop()
        
        st.success(f"✅ Arquivo carregado com sucesso! Encontradas {len(anos_disponiveis_divida)} abas: {', '.join(anos_disponiveis_divida)}")
        
        # Filtros específicos para dívida ativa
        st.markdown("### 🔍 Filtros de Análise")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            anos_divida_selecionados = st.multiselect(
                "📅 Anos para análise",
                options=anos_disponiveis_divida,
                default=anos_disponiveis_divida[-2:] if len(anos_disponiveis_divida) >= 2 else anos_disponiveis_divida,
                help="Selecione os anos que deseja analisar"
            )
        
        with col_filtro2:
            # Carregar um ano para obter os tributos disponíveis
            if anos_divida_selecionados:
                try:
                    df_temp = pd.read_excel('Arrecadacao Divida Ativa.xlsx', sheet_name=anos_divida_selecionados[0])
                    
                    # Verificar se a coluna existe (pode ser 'TRIBUTO/MÊS/ANO' ou 'TRIBUTO')
                    coluna_tributo = None
                    if 'TRIBUTO/MÊS/ANO' in df_temp.columns:
                        coluna_tributo = 'TRIBUTO/MÊS/ANO'
                    elif 'TRIBUTO' in df_temp.columns:
                        coluna_tributo = 'TRIBUTO'
                    
                    if coluna_tributo:
                        tributos_divida = df_temp[coluna_tributo].unique().tolist()
                        st.success(f"✅ Encontrados {len(tributos_divida)} tributos na aba {anos_divida_selecionados[0]} (coluna: {coluna_tributo})")
                    else:
                        st.error(f"❌ Coluna de tributo não encontrada na aba {anos_divida_selecionados[0]}")
                        st.write("Colunas disponíveis:", list(df_temp.columns))
                        tributos_divida = []
                except Exception as e:
                    st.error(f"❌ Erro ao carregar aba {anos_divida_selecionados[0]}: {e}")
                    tributos_divida = []
            else:
                tributos_divida = []
            
            if tributos_divida:
                tributos_divida_selecionados = st.multiselect(
                    "🏛️ Tributos para análise",
                    options=tributos_divida,
                    default=tributos_divida,
                    help="Selecione os tributos que deseja analisar"
                )
            else:
                tributos_divida_selecionados = []
        
        if not anos_divida_selecionados:
            st.warning("⚠️ Selecione pelo menos um ano para análise.")
        else:
            # Carregar e processar dados
            dados_divida = []
            erros_processamento = []
            
            for ano in anos_divida_selecionados:
                try:
                    df_ano = pd.read_excel('Arrecadacao Divida Ativa.xlsx', sheet_name=ano)
                    
                    # Verificar se a coluna necessária existe (pode ser 'TRIBUTO/MÊS/ANO' ou 'TRIBUTO')
                    coluna_tributo = None
                    if 'TRIBUTO/MÊS/ANO' in df_ano.columns:
                        coluna_tributo = 'TRIBUTO/MÊS/ANO'
                    elif 'TRIBUTO' in df_ano.columns:
                        coluna_tributo = 'TRIBUTO'
                    
                    if not coluna_tributo:
                        erros_processamento.append(f"Coluna de tributo não encontrada na aba {ano}")
                        continue
                    
                    # Filtrar tributos selecionados
                    if tributos_divida_selecionados:
                        df_ano = df_ano[df_ano[coluna_tributo].isin(tributos_divida_selecionados)]
                    
                    # Verificar se há dados após filtro
                    if df_ano.empty:
                        erros_processamento.append(f"Nenhum dado encontrado na aba {ano} após aplicar filtros")
                        continue
                    
                    # Processar dados mensais
                    for _, row in df_ano.iterrows():
                        tributo = row[coluna_tributo]
                        
                        # Verificar se as colunas necessárias existem
                        colunas_necessarias = ['ORÇADO', 'ARRECADADO', 'META']
                        if not all(col in df_ano.columns for col in colunas_necessarias):
                            erros_processamento.append(f"Colunas necessárias não encontradas na aba {ano}")
                            continue
                        
                        # Processar colunas de meses (colunas 1-12)
                        for i in range(1, 13):
                            if i < len(df_ano.columns):
                                col_mes = df_ano.columns[i]
                                if pd.notna(row[col_mes]) and row[col_mes] != 0:
                                    try:
                                        # Calcular superávit/déficit usando a fórmula ARRECADADO - ORÇADO
                                        saldo = row['ARRECADADO'] - row['ORÇADO']
                                        superavit = saldo if saldo > 0 else 0
                                        deficit = abs(saldo) if saldo < 0 else 0
                                        
                                        dados_divida.append({
                                            'ANO': ano,
                                            'TRIBUTO': tributo,
                                            'MES': i,
                                            'VALOR_MENSAL': row[col_mes],
                                            'ORCADO': row['ORÇADO'],
                                            'ARRECADADO': row['ARRECADADO'],
                                            'META': row['META'],
                                            'SALDO': saldo,
                                            'SUPERAVIT': superavit,
                                            'DEFICIT': deficit
                                        })
                                    except Exception as e:
                                        erros_processamento.append(f"Erro ao processar linha do tributo {tributo} na aba {ano}: {e}")
                
                except Exception as e:
                    erros_processamento.append(f"Erro ao carregar aba {ano}: {e}")
            
            # Mostrar erros se houver
            if erros_processamento:
                st.warning("⚠️ Alguns erros foram encontrados durante o processamento:")
                for erro in erros_processamento[:5]:  # Mostrar apenas os primeiros 5 erros
                    st.write(f"• {erro}")
                if len(erros_processamento) > 5:
                    st.write(f"• ... e mais {len(erros_processamento) - 5} erros")
            
            if dados_divida:
                df_divida = pd.DataFrame(dados_divida)
                st.success(f"✅ Processados {len(dados_divida)} registros de dados")
                
                # Métricas principais
                st.markdown("### 📊 Métricas Principais")
                
                # Calcular métricas por ano
                metricas_por_ano = df_divida.groupby('ANO').agg({
                    'ARRECADADO': 'sum',
                    'ORCADO': 'sum',
                    'VALOR_MENSAL': 'sum'
                }).reset_index()
                
                # Layout de métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    ultimo_ano_divida = metricas_por_ano['ANO'].max()
                    ultimo_arrecadado = metricas_por_ano[metricas_por_ano['ANO'] == ultimo_ano_divida]['ARRECADADO'].iloc[0]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(ultimo_arrecadado)}</div>
                        <div class="metric-label">Dívida Ativa {ultimo_ano_divida}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    ultimo_orcado = metricas_por_ano[metricas_por_ano['ANO'] == ultimo_ano_divida]['ORCADO'].iloc[0]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(ultimo_orcado)}</div>
                        <div class="metric-label">Orçado {ultimo_ano_divida}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    meta_alcancada = (ultimo_arrecadado / ultimo_orcado * 100) if ultimo_orcado > 0 else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{meta_alcancada:.1f}%</div>
                        <div class="metric-label">Meta Atingida</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    superavit_deficit = ultimo_arrecadado - ultimo_orcado
                    status = "SUPERÁVIT" if superavit_deficit > 0 else "DÉFICIT"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(abs(superavit_deficit))}</div>
                        <div class="metric-label">{status}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gráficos de dívida ativa
                st.markdown("### 📈 Análise Temporal")
                
                # Gráfico 1: Evolução mensal por tributo
                col_divida1, col_divida2 = st.columns(2)
                
                with col_divida1:
                    # Gráfico de linha para evolução mensal
                    fig_divida_mensal = px.line(
                        df_divida,
                        x='MES',
                        y='VALOR_MENSAL',
                        color='TRIBUTO',
                        title='Evolução Mensal Dívida Ativa por Tributo',
                        template=tema_grafico
                    )
                    
                    fig_divida_mensal.update_layout(
                        height=400,
                        title_x=0.5,
                        yaxis=dict(
                            tickformat=".2f",
                            tickprefix="R$ ",
                            separatethousands=True,
                        ),
                        xaxis=dict(
                            tickmode='linear',
                            tick0=1,
                            dtick=1
                        )
                    )
                    
                    st.plotly_chart(fig_divida_mensal, use_container_width=True)
                
                with col_divida2:
                    # Gráfico de barras para comparação orçado vs arrecadado
                    df_comparacao_divida = df_divida.groupby(['ANO', 'TRIBUTO']).agg({
                        'ORCADO': 'first',
                        'ARRECADADO': 'first'
                    }).reset_index()
                    
                    # Criar gráfico de barras agrupadas
                    fig_comparacao_divida = go.Figure()
                    
                    for tributo in df_comparacao_divida['TRIBUTO'].unique():
                        df_tributo = df_comparacao_divida[df_comparacao_divida['TRIBUTO'] == tributo]
                        
                        # Barras para orçado
                        fig_comparacao_divida.add_trace(go.Bar(
                            name=f'{tributo} - Orçado',
                            x=df_tributo['ANO'],
                            y=df_tributo['ORCADO'],
                            marker_color='lightcoral',
                            opacity=0.7
                        ))
                        
                        # Barras para arrecadado
                        fig_comparacao_divida.add_trace(go.Bar(
                            name=f'{tributo} - Arrecadado',
                            x=df_tributo['ANO'],
                            y=df_tributo['ARRECADADO'],
                            marker_color='darkred',
                            opacity=0.9
                        ))
                    
                    fig_comparacao_divida.update_layout(
                        title='Orçado vs Arrecadado Dívida Ativa por Tributo e Ano',
                        barmode='group',
                        height=400,
                        template=tema_grafico,
                        title_x=0.5,
                        yaxis=dict(
                            tickformat=".2f",
                            tickprefix="R$ ",
                            separatethousands=True,
                        )
                    )
                    
                    st.plotly_chart(fig_comparacao_divida, use_container_width=True)
                
                # Gráfico 2: Análise de metas
                st.markdown("### 🎯 Análise de Metas")
                
                # Calcular percentual de meta por tributo e ano
                df_metas_divida = df_divida.groupby(['ANO', 'TRIBUTO']).agg({
                    'META': 'first'
                }).reset_index()
                
                fig_metas_divida = px.bar(
                    df_metas_divida,
                    x='ANO',
                    y='META',
                    color='TRIBUTO',
                    title='Percentual de Meta Atingida Dívida Ativa por Tributo',
                    template=tema_grafico
                )
                
                fig_metas_divida.update_layout(
                    height=400,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".1f",
                        ticksuffix="%",
                        title="Meta (%)"
                    )
                )
                
                st.plotly_chart(fig_metas_divida, use_container_width=True)
                
                # Gráfico 3: Análise de superávit/déficit
                st.markdown("### 💰 Análise de Superávit/Déficit")
                
                # Calcular superávit/déficit por tributo e ano usando a fórmula ARRECADADO - ORÇADO
                df_superavit_divida = df_divida.groupby(['ANO', 'TRIBUTO']).agg({
                    'ARRECADADO': 'first',
                    'ORCADO': 'first',
                    'SALDO': 'first'
                }).reset_index()
                
                # Calcular status baseado no saldo
                df_superavit_divida['STATUS'] = df_superavit_divida['SALDO'].apply(lambda x: 'SUPERÁVIT' if x > 0 else 'DÉFICIT')
                
                # Criar gráfico com cores diferentes para superávit e déficit
                fig_superavit_divida = go.Figure()
                
                for tributo in df_superavit_divida['TRIBUTO'].unique():
                    df_tributo = df_superavit_divida[df_superavit_divida['TRIBUTO'] == tributo]
                    
                    # Separar superávit e déficit
                    superavit_data = df_tributo[df_tributo['SALDO'] > 0]
                    deficit_data = df_tributo[df_tributo['SALDO'] < 0]
                    
                    # Adicionar barras de superávit (verde)
                    if not superavit_data.empty:
                        fig_superavit_divida.add_trace(go.Bar(
                            name=f'{tributo} - Superávit',
                            x=superavit_data['ANO'],
                            y=superavit_data['SALDO'],
                            marker_color='green',
                            opacity=0.8,
                            showlegend=True
                        ))
                    
                    # Adicionar barras de déficit (vermelho)
                    if not deficit_data.empty:
                        fig_superavit_divida.add_trace(go.Bar(
                            name=f'{tributo} - Déficit',
                            x=deficit_data['ANO'],
                            y=deficit_data['SALDO'],
                            marker_color='red',
                            opacity=0.8,
                            showlegend=True
                        ))
                
                fig_superavit_divida.update_layout(
                    title='Superávit/Déficit Dívida Ativa por Tributo e Ano (ARRECADADO - ORÇADO)',
                    height=400,
                    template=tema_grafico,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                        title="Saldo (R$)"
                    ),
                    barmode='group'
                )
                
                # Adicionar linha de referência em zero
                fig_superavit_divida.add_hline(y=0, line_dash="dash", line_color="black", line_width=2)
                
                st.plotly_chart(fig_superavit_divida, use_container_width=True)
                
                # Análise detalhada de superávit/déficit
                st.markdown("### 📊 Análise Detalhada de Superávit/Déficit")
                
                # Criar métricas por status
                col_analise1, col_analise2, col_analise3 = st.columns(3)
                
                with col_analise1:
                    total_superavit_divida = df_superavit_divida[df_superavit_divida['SALDO'] > 0]['SALDO'].sum()
                    st.metric(
                        label="💰 Total Superávit Dívida Ativa",
                        value=formatar_moeda_br(total_superavit_divida),
                        delta=f"{len(df_superavit_divida[df_superavit_divida['SALDO'] > 0])} registros"
                    )
                
                with col_analise2:
                    total_deficit_divida = abs(df_superavit_divida[df_superavit_divida['SALDO'] < 0]['SALDO'].sum())
                    st.metric(
                        label="📉 Total Déficit Dívida Ativa",
                        value=formatar_moeda_br(total_deficit_divida),
                        delta=f"{len(df_superavit_divida[df_superavit_divida['SALDO'] < 0])} registros"
                    )
                
                with col_analise3:
                    saldo_geral_divida = df_superavit_divida['SALDO'].sum()
                    st.metric(
                        label="⚖️ Saldo Geral Dívida Ativa",
                        value=formatar_moeda_br(saldo_geral_divida),
                        delta="Superávit" if saldo_geral_divida > 0 else "Déficit"
                    )
                
                # Tabela de dados consolidados
                st.markdown("### 📋 Dados Consolidados")
                
                # Criar tabela consolidada usando a fórmula ARRECADADO - ORÇADO
                df_consolidado_divida = df_divida.groupby(['ANO', 'TRIBUTO']).agg({
                    'ORCADO': 'first',
                    'ARRECADADO': 'first',
                    'META': 'first',
                    'SALDO': 'first'
                }).reset_index()
                
                # Calcular status baseado no saldo
                df_consolidado_divida['STATUS'] = df_consolidado_divida['SALDO'].apply(lambda x: 'SUPERÁVIT' if x > 0 else 'DÉFICIT')
                
                # Adicionar coluna de percentual de realização
                df_consolidado_divida['PERCENTUAL_REALIZACAO'] = (df_consolidado_divida['ARRECADADO'] / df_consolidado_divida['ORCADO'] * 100).round(1)
                
                # Formatar dados para exibição
                df_consolidado_divida_formatado = df_consolidado_divida.copy()
                df_consolidado_divida_formatado['ORCADO'] = df_consolidado_divida_formatado['ORCADO'].apply(formatar_moeda_br)
                df_consolidado_divida_formatado['ARRECADADO'] = df_consolidado_divida_formatado['ARRECADADO'].apply(formatar_moeda_br)
                df_consolidado_divida_formatado['META'] = df_consolidado_divida_formatado['META'].apply(lambda x: f"{x:.1f}%")
                df_consolidado_divida_formatado['SALDO'] = df_consolidado_divida_formatado['SALDO'].apply(formatar_moeda_br)
                df_consolidado_divida_formatado['PERCENTUAL_REALIZACAO'] = df_consolidado_divida_formatado['PERCENTUAL_REALIZACAO'].apply(lambda x: f"{x:.1f}%")
                
                # Selecionar colunas para exibição
                colunas_exibicao = ['ANO', 'TRIBUTO', 'ORCADO', 'ARRECADADO', 'PERCENTUAL_REALIZACAO', 'META', 'SALDO', 'STATUS']
                df_exibicao_divida = df_consolidado_divida_formatado[colunas_exibicao]
                
                # Explicação das colunas da tabela
                st.markdown("""
                **📋 Legenda da Tabela:**
                - **ANO:** Ano de referência
                - **TRIBUTO:** Tipo de tributo
                - **ORÇADO:** Valor orçado para o ano
                - **ARRECADADO:** Valor efetivamente arrecadado
                - **% REALIZAÇÃO:** Percentual de realização (ARRECADADO/ORÇADO × 100)
                - **META:** Meta estabelecida (%)
                - **SALDO:** Saldo calculado (ARRECADADO - ORÇADO)
                - **STATUS:** Superávit (saldo > 0) ou Déficit (saldo < 0)
                """)
                
                st.dataframe(
                    df_exibicao_divida,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download dos dados
                st.markdown("### 💾 Download dos Dados")
                
                # Preparar dados para download
                df_download_divida = df_consolidado_divida.copy()
                df_download_divida['ORCADO'] = df_download_divida['ORCADO'].apply(lambda x: f"R$ {x:,.2f}")
                df_download_divida['ARRECADADO'] = df_download_divida['ARRECADADO'].apply(lambda x: f"R$ {x:,.2f}")
                df_download_divida['META'] = df_download_divida['META'].apply(lambda x: f"{x:.1f}%")
                df_download_divida['SALDO'] = df_download_divida['SALDO'].apply(lambda x: f"R$ {x:,.2f}")
                df_download_divida['PERCENTUAL_REALIZACAO'] = df_download_divida['PERCENTUAL_REALIZACAO'].apply(lambda x: f"{x:.1f}%")
                
                # Criar arquivo CSV para download
                csv_divida = df_download_divida.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Download CSV Dívida Ativa",
                    data=csv_divida,
                    file_name=f"divida_ativa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                if erros_processamento:
                    st.error("❌ Verifique os erros acima para entender por que nenhum dado foi processado.")
    
    except FileNotFoundError:
        st.warning("📁 O arquivo 'Arrecadacao Divida Ativa.xlsx' não foi encontrado.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de dívida ativa: {e}")
        st.write("Detalhes do erro:", str(e))

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>📊 Dashboard Tributário Municipal | Desenvolvido com Streamlit e Plotly</p>
    <p>Última atualização: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
