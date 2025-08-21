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
        # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
        df.columns = df.columns.astype(str).str.strip().str.upper()
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
    arquivos = ["Arrecadacao Tributos.xlsx", "Receita Propria Consolidado.xlsx", "Arrecadacao Divida Ativa.xlsx"]
    
    for arquivo in arquivos:
        try:
            df_temp = pd.read_excel(arquivo, header=2)
            df_temp = df_temp.loc[:, ~df_temp.columns.str.contains("^Unnamed")]
            # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
            df_temp.columns = df_temp.columns.astype(str).str.strip().str.upper()
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
    
    # Filtro de meses (para abas de Evolução e Dívida Ativa)
    st.markdown("### 📅 Filtros de Meses")
    meses_disponiveis = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    meses_selecionados = st.multiselect(
        "📅 Meses para análise",
        options=meses_disponiveis,
        default=meses_disponiveis,
        help="Selecione os meses que deseja analisar nas abas de Evolução e Dívida Ativa"
    )
    
    # Botão para limpar filtros
    if st.button("🔄 Limpar Todos os Filtros", help="Restaura todos os filtros para os valores padrão"):
        st.rerun()
    
    # Informações sobre os filtros
    st.markdown("### ℹ️ Sobre os Filtros")
    st.markdown("""
    - **📅 Anos:** Aplicado em todas as abas automaticamente
    - **🏛️ Tributos:** Aplicado em todas as abas que possuem dados de tributos
    - **📅 Meses:** Aplicado nas abas de Evolução e Dívida Ativa para filtrar dados mensais
    - Os filtros são aplicados automaticamente em todas as visualizações
    - Use o botão "Limpar Todos os Filtros" para restaurar os valores padrão
    - Se um ano/tributo/mês não existir em uma aba específica, será ignorado
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
tab1, tab2, tab3, tab4 = st.tabs([
    "🏛️ Arrecadação Tributos", 
    "💰 Receita Própria",
    "📈 Evolução Arrecadação",
    "💳 Arrecadação Dívida Ativa"
])

# ========== ABA 1: ARRECADAÇÃO TRIBUTOS ==========
with tab1:
    st.markdown("## 🏛️ Arrecadação Tributos")
    
    # Informações sobre o arquivo fonte
    st.markdown("### 📁 Arquivo Fonte dos Dados")
    col_info1, col_info2 = st.columns([2, 1])
    
    with col_info1:
        st.info("""
        **📊 Fonte:** `Arrecadacao Tributos.xlsx`
        
        **📋 Descrição:** Dados consolidados de arrecadação tributária municipal, 
        contendo valores anuais por tipo de tributo.
        
        **📅 Período:** Dados históricos de arrecadação por ano
        **🏛️ Tributos:** IPTU, ISS, ITBI, Taxas, Multas e outros tributos municipais
        """)
    
    with col_info2:
        # Verificar se o arquivo existe e mostrar informações
        try:
            import os
            arquivo_info = "Arrecadacao Tributos.xlsx"
            if os.path.exists(arquivo_info):
                stat_info = os.stat(arquivo_info)
                tamanho_mb = stat_info.st_size / (1024 * 1024)
                data_modificacao = datetime.fromtimestamp(stat_info.st_mtime)
                
                st.success(f"""
                ✅ **Arquivo encontrado**
                
                📏 **Tamanho:** {tamanho_mb:.2f} MB
                📅 **Última modificação:** {data_modificacao.strftime('%d/%m/%Y %H:%M')}
                """)
            else:
                st.error("❌ Arquivo não encontrado")
        except Exception as e:
            st.warning(f"⚠️ Erro ao verificar arquivo: {e}")
    
    st.markdown("---")
    
    # Botão para download do arquivo original
    st.markdown("### 💾 Download do Arquivo Original")
    try:
        with open("Arrecadacao Tributos.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Arrecadacao Tributos.xlsx",
                data=file.read(),
                file_name="Arrecadacao Tributos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.warning("⚠️ Arquivo não disponível para download")
    except Exception as e:
        st.error(f"❌ Erro ao preparar download: {e}")
    
    st.markdown("---")
    
    # Carregar dados
    df = carregar_dados("Arrecadacao Tributos.xlsx")
    
    # Mostrar prévia dos dados
    if df is not None and not df.empty:
        st.markdown("### 👀 Prévia dos Dados")
        st.info(f"""
        **📊 Estrutura dos dados:**
        - **Linhas:** {len(df)} registros
        - **Colunas:** {len(df.columns)} campos
        - **Colunas disponíveis:** {', '.join(df.columns.tolist())}
        """)
        
        # Mostrar primeiras linhas dos dados
        with st.expander("📋 Ver primeiras linhas dos dados", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)
    else:
        st.warning("⚠️ Não foi possível carregar os dados para mostrar a prévia")
    
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





# ========== ABA 2: RECEITA PRÓPRIA ==========
with tab2:
    st.markdown("## 💰 Receita Própria Consolidada")
    
    # Informações sobre o arquivo fonte
    st.markdown("### 📁 Arquivo Fonte dos Dados")
    col_info1, col_info2 = st.columns([2, 1])
    
    with col_info1:
        st.info("""
        **📊 Fonte:** `Receita Propria Consolidado.xlsx`
        
        **📋 Descrição:** Dados consolidados de receita própria municipal, 
        contendo valores anuais de receitas próprias.
        
        **📅 Período:** Dados históricos de receita própria por ano
        **💰 Tipo:** Receitas próprias consolidadas do município
        """)
    
    with col_info2:
        # Verificar se o arquivo existe e mostrar informações
        try:
            import os
            arquivo_info = "Receita Propria Consolidado.xlsx"
            if os.path.exists(arquivo_info):
                stat_info = os.stat(arquivo_info)
                tamanho_mb = stat_info.st_size / (1024 * 1024)
                data_modificacao = datetime.fromtimestamp(stat_info.st_mtime)
                
                st.success(f"""
                ✅ **Arquivo encontrado**
                
                📏 **Tamanho:** {tamanho_mb:.2f} MB
                📅 **Última modificação:** {data_modificacao.strftime('%d/%m/%Y %H:%M')}
                """)
            else:
                st.error("❌ Arquivo não encontrado")
        except Exception as e:
            st.warning(f"⚠️ Erro ao verificar arquivo: {e}")
    
    st.markdown("---")
    
    # Botão para download do arquivo original
    st.markdown("### 💾 Download do Arquivo Original")
    try:
        with open("Receita Propria Consolidado.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Receita Propria Consolidado.xlsx",
                data=file.read(),
                file_name="Receita Propria Consolidado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.warning("⚠️ Arquivo não disponível para download")
    except Exception as e:
        st.error(f"❌ Erro ao preparar download: {e}")
    
    st.markdown("---")
    
    try:
        # Carregar dados de receita própria
        df_receita = carregar_dados("Receita Propria Consolidado.xlsx")
        
        # Mostrar prévia dos dados
        if df_receita is not None and not df_receita.empty:
            st.markdown("### 👀 Prévia dos Dados")
            st.info(f"""
            **📊 Estrutura dos dados:**
            - **Linhas:** {len(df_receita)} registros
            - **Colunas:** {len(df_receita.columns)} campos
            - **Colunas disponíveis:** {', '.join(df_receita.columns.tolist())}
            """)
            
            # Mostrar primeiras linhas dos dados
            with st.expander("📋 Ver primeiras linhas dos dados", expanded=False):
                st.dataframe(df_receita.head(10), use_container_width=True)
        else:
            st.warning("⚠️ Não foi possível carregar os dados para mostrar a prévia")
        
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

# ========== ABA 3: EVOLUÇÃO ARRECADAÇÃO ==========
with tab3:
    st.markdown("## 📈 Evolução Arrecadação")
    
    # Informações sobre o arquivo fonte
    st.markdown("### 📁 Arquivo Fonte dos Dados")
    col_info1, col_info2 = st.columns([2, 1])
    
    with col_info1:
        st.info("""
        **📊 Fonte:** `Evolucao Arrecadacao.xlsx`
        
        **📋 Descrição:** Dados detalhados de evolução mensal da arrecadação, 
        contendo orçado, arrecadado e metas por tributo e mês.
        
        **📅 Período:** Dados mensais organizados por ano em abas separadas
        **📊 Métricas:** Orçado, Arrecadado, Meta, Superávit/Déficit
        """)
    
    with col_info2:
        # Verificar se o arquivo existe e mostrar informações
        try:
            import os
            arquivo_info = "Evolucao Arrecadacao.xlsx"
            if os.path.exists(arquivo_info):
                stat_info = os.stat(arquivo_info)
                tamanho_mb = stat_info.st_size / (1024 * 1024)
                data_modificacao = datetime.fromtimestamp(stat_info.st_mtime)
                
                st.success(f"""
                ✅ **Arquivo encontrado**
                
                📏 **Tamanho:** {tamanho_mb:.2f} MB
                📅 **Última modificação:** {data_modificacao.strftime('%d/%m/%Y %H:%M')}
                """)
            else:
                st.error("❌ Arquivo não encontrado")
        except Exception as e:
            st.warning(f"⚠️ Erro ao verificar arquivo: {e}")
    
    st.markdown("---")
    
    # Botão para download do arquivo original
    st.markdown("### 💾 Download do Arquivo Original")
    try:
        with open("Evolucao Arrecadacao.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Evolucao Arrecadacao.xlsx",
                data=file.read(),
                file_name="Evolucao Arrecadacao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.warning("⚠️ Arquivo não disponível para download")
    except Exception as e:
        st.error(f"❌ Erro ao preparar download: {e}")
    
    st.markdown("---")
    
    # Informação sobre o cálculo de superávit/déficit
    st.info("""
    💡 **Cálculo de Superávit/Déficit:** 
    - **Superávit:** Quando ARRECADADO > ORÇADO (valor positivo)
    - **Déficit:** Quando ARRECADADO < ORÇADO (valor negativo)
    - **Fórmula:** SALDO = ARRECADADO - ORÇADO
    """)
    
    # Mostrar filtros globais aplicados
    if anos_selecionados or tributos_selecionados or meses_selecionados:
        st.markdown("### 🔍 Filtros Globais Aplicados")
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            if anos_selecionados:
                st.info(f"📅 **Anos selecionados:** {', '.join(anos_selecionados)}")
        
        with col_filtro2:
            if tributos_selecionados:
                st.info(f"🏛️ **Tributos selecionados:** {', '.join(tributos_selecionados)}")
        
        with col_filtro3:
            if meses_selecionados:
                st.info(f"📅 **Meses selecionados:** {', '.join(meses_selecionados)}")
    
    try:
        # Carregar dados de evolução
        xl = pd.ExcelFile('Evolucao Arrecadacao.xlsx')
        anos_disponiveis_evolucao = xl.sheet_names
        
        # Verificar se há abas no arquivo
        if not anos_disponiveis_evolucao:
            st.error("❌ O arquivo 'Evolucao Arrecadacao.xlsx' não possui abas.")
            st.stop()
        
        st.success(f"✅ Arquivo carregado com sucesso! Encontradas {len(anos_disponiveis_evolucao)} abas: {', '.join(anos_disponiveis_evolucao)}")
        
        # Mostrar prévia dos dados
        st.markdown("### 👀 Prévia dos Dados")
        st.info(f"""
        **📊 Estrutura do arquivo:**
        - **Total de abas:** {len(anos_disponiveis_evolucao)} anos
        - **Abas disponíveis:** {', '.join(anos_disponiveis_evolucao)}
        - **Formato:** Dados mensais organizados por ano
        """)
        
        # Mostrar prévia da primeira aba
        if anos_disponiveis_evolucao:
            try:
                df_previa = pd.read_excel('Evolucao Arrecadacao.xlsx', sheet_name=anos_disponiveis_evolucao[0])
                # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
                df_previa.columns = df_previa.columns.astype(str)
                with st.expander(f"📋 Ver primeiras linhas da aba '{anos_disponiveis_evolucao[0]}'", expanded=False):
                    st.dataframe(df_previa.head(10), use_container_width=True)
            except Exception as e:
                st.warning(f"⚠️ Não foi possível mostrar prévia da aba {anos_disponiveis_evolucao[0]}: {e}")
        
        # Usar filtros globais se disponíveis, senão usar todos os anos
        # Filtrar apenas anos que existem no arquivo de evolução
        anos_evolucao_selecionados = [ano for ano in (anos_selecionados if anos_selecionados else anos_disponiveis_evolucao) if ano in anos_disponiveis_evolucao]
        
        if not anos_evolucao_selecionados:
            st.warning("⚠️ Nenhum dos anos selecionados globalmente existe no arquivo de evolução.")
            anos_evolucao_selecionados = anos_disponiveis_evolucao
        
        # Carregar um ano para obter os tributos disponíveis
        tributos_evolucao = []
        if anos_evolucao_selecionados:
            try:
                df_temp = pd.read_excel('Evolucao Arrecadacao.xlsx', sheet_name=anos_evolucao_selecionados[0])
                # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
                df_temp.columns = df_temp.columns.astype(str)
                
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
            except Exception as e:
                st.error(f"❌ Erro ao carregar aba {anos_evolucao_selecionados[0]}: {e}")
        
        # Usar filtros globais de tributos se disponíveis, senão usar todos os tributos
        tributos_evolucao_selecionados = tributos_selecionados if tributos_selecionados else tributos_evolucao
        
        # Mapear meses selecionados para números
        meses_para_numero = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
            "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }
        
        # Usar filtros globais de meses se disponíveis, senão usar todos os meses
        meses_evolucao_selecionados = [meses_para_numero[mes] for mes in meses_selecionados] if meses_selecionados else list(range(1, 13))
        
        if not anos_evolucao_selecionados:
            st.warning("⚠️ Nenhum ano selecionado para análise.")
        else:
            # Carregar e processar dados
            dados_evolucao = []
            erros_processamento = []
            
            for ano in anos_evolucao_selecionados:
                try:
                    df_ano = pd.read_excel('Evolucao Arrecadacao.xlsx', sheet_name=ano)
                    # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
                    df_ano.columns = df_ano.columns.astype(str)
                    
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
                        
                        # Processar colunas de meses (colunas 1-12) - apenas meses selecionados
                        for i in meses_evolucao_selecionados:
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
                                            'NOME_MES': list(meses_para_numero.keys())[list(meses_para_numero.values()).index(i)],
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
                
                # Calcular métricas para todos os anos selecionados (não apenas o último)
                # Somatória total dos valores mensais para todos os anos selecionados
                total_valor_mensal = df_evolucao['VALOR_MENSAL'].sum()
                
                # Calcular orçado e arrecadado totais para todos os anos selecionados
                df_orcado_arrecadado = df_evolucao.groupby(['ANO', 'TRIBUTO']).agg({
                    'ORCADO': 'first',      # Pegar apenas uma vez por tributo/ano
                    'ARRECADADO': 'first'   # Pegar apenas uma vez por tributo/ano
                }).reset_index()
                
                # Somar orçado e arrecadado para todos os anos selecionados
                total_orcado = df_orcado_arrecadado['ORCADO'].sum()
                total_arrecadado = df_orcado_arrecadado['ARRECADADO'].sum()
                
                # Layout de métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(total_arrecadado)}</div>
                        <div class="metric-label">Arrecadado</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(total_orcado)}</div>
                        <div class="metric-label">Orçado</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    meta_alcancada = (total_arrecadado / total_orcado * 100) if total_orcado > 0 else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{meta_alcancada:.1f}%</div>
                        <div class="metric-label">Meta Atingida</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    superavit_deficit = total_arrecadado - total_orcado
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
                    # Preparar dados com ordenação correta dos meses
                    df_evol_mensal = df_evolucao.copy()
                    
                    # Criar mapeamento de meses para ordenação
                    ordem_meses = {
                        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
                        "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                    }
                    
                    # Adicionar coluna de ordenação
                    df_evol_mensal['ORDEM_MES'] = df_evol_mensal['NOME_MES'].map(ordem_meses)
                    
                    # Ordenar por tributo, ano e ordem do mês
                    df_evol_mensal = df_evol_mensal.sort_values(['TRIBUTO', 'ANO', 'ORDEM_MES'])
                    
                    fig_evol_mensal = px.line(
                        df_evol_mensal,
                        x='NOME_MES',
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
                
                # Gráfico comparativo entre anos
                st.markdown("### 🔍 Comparativo Entre Anos")
                
                # Criar gráfico comparativo por mês entre anos
                # Preparar dados com ordenação correta dos meses
                df_comparativo = df_evolucao.groupby(['ANO', 'NOME_MES'])['VALOR_MENSAL'].sum().reset_index()
                
                # Criar mapeamento de meses para ordenação
                ordem_meses = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
                    "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                
                # Adicionar coluna de ordenação
                df_comparativo['ORDEM_MES'] = df_comparativo['NOME_MES'].map(ordem_meses)
                
                # Ordenar por ano e ordem do mês
                df_comparativo = df_comparativo.sort_values(['ANO', 'ORDEM_MES'])
                
                fig_comparativo_anos = px.line(
                    df_comparativo,
                    x='NOME_MES',
                    y='VALOR_MENSAL',
                    color='ANO',
                    title='Comparativo de Arrecadação Mensal Entre Anos',
                    template=tema_grafico
                )
                
                fig_comparativo_anos.update_layout(
                    height=500,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    ),
                    xaxis_title="Mês",
                    yaxis_title="Valor Total (R$)"
                )
                
                st.plotly_chart(fig_comparativo_anos, use_container_width=True)
                
                # Gráfico de barras comparativo por tributo entre anos
                fig_comparativo_tributos = px.bar(
                    df_evolucao.groupby(['ANO', 'TRIBUTO'])['VALOR_MENSAL'].sum().reset_index(),
                    x='TRIBUTO',
                    y='VALOR_MENSAL',
                    color='ANO',
                    title='Comparativo de Arrecadação por Tributo Entre Anos',
                    template=tema_grafico,
                    barmode='group'
                )
                
                fig_comparativo_tributos.update_layout(
                    height=500,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    ),
                    xaxis_title="Tributo",
                    yaxis_title="Valor Total (R$)"
                )
                
                st.plotly_chart(fig_comparativo_tributos, use_container_width=True)
                
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



# ========== ABA 4: ARRECADAÇÃO DÍVIDA ATIVA ==========
with tab4:
    st.markdown("## 💳 Arrecadação Dívida Ativa")
    
    # Informações sobre o arquivo fonte
    st.markdown("### 📁 Arquivo Fonte dos Dados")
    col_info1, col_info2 = st.columns([2, 1])
    
    with col_info1:
        st.info("""
        **📊 Fonte:** `Arrecadacao Divida Ativa.xlsx`
        
        **📋 Descrição:** Dados de arrecadação de dívida ativa municipal, 
        contendo valores mensais de orçado, arrecadado e metas por tributo.
        
        **📅 Período:** Dados mensais organizados por ano em abas separadas
        **💳 Tipo:** Arrecadação de dívida ativa por tributo
        """)
    
    with col_info2:
        # Verificar se o arquivo existe e mostrar informações
        try:
            import os
            arquivo_info = "Arrecadacao Divida Ativa.xlsx"
            if os.path.exists(arquivo_info):
                stat_info = os.stat(arquivo_info)
                tamanho_mb = stat_info.st_size / (1024 * 1024)
                data_modificacao = datetime.fromtimestamp(stat_info.st_mtime)
                
                st.success(f"""
                ✅ **Arquivo encontrado**
                
                📏 **Tamanho:** {tamanho_mb:.2f} MB
                📅 **Última modificação:** {data_modificacao.strftime('%d/%m/%Y %H:%M')}
                """)
            else:
                st.error("❌ Arquivo não encontrado")
        except Exception as e:
            st.warning(f"⚠️ Erro ao verificar arquivo: {e}")
    
    st.markdown("---")
    
    # Botão para download do arquivo original
    st.markdown("### 💾 Download do Arquivo Original")
    try:
        with open("Arrecadacao Divida Ativa.xlsx", "rb") as file:
            st.download_button(
                label="📥 Download Arrecadacao Divida Ativa.xlsx",
                data=file.read(),
                file_name="Arrecadacao Divida Ativa.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.warning("⚠️ Arquivo não disponível para download")
    except Exception as e:
        st.error(f"❌ Erro ao preparar download: {e}")
    
    st.markdown("---")
    
    # Informação sobre o cálculo de superávit/déficit
    st.info("""
    💡 **Cálculo de Superávit/Déficit:** 
    - **Superávit:** Quando ARRECADADO > ORÇADO (valor positivo)
    - **Déficit:** Quando ARRECADADO < ORÇADO (valor negativo)
    - **Fórmula:** SALDO = ARRECADADO - ORÇADO
    """)
    
    # Mostrar filtros globais aplicados
    if anos_selecionados or tributos_selecionados or meses_selecionados:
        st.markdown("### 🔍 Filtros Globais Aplicados")
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            if anos_selecionados:
                st.info(f"📅 **Anos selecionados:** {', '.join(anos_selecionados)}")
        
        with col_filtro2:
            if tributos_selecionados:
                st.info(f"🏛️ **Tributos selecionados:** {', '.join(tributos_selecionados)}")
        
        with col_filtro3:
            if meses_selecionados:
                st.info(f"📅 **Meses selecionados:** {', '.join(meses_selecionados)}")
    
    try:
        # Carregar dados de dívida ativa
        xl_divida = pd.ExcelFile('Arrecadacao Divida Ativa.xlsx')
        anos_disponiveis_divida = xl_divida.sheet_names
        
        # Verificar se há abas no arquivo
        if not anos_disponiveis_divida:
            st.error("❌ O arquivo 'Arrecadacao Divida Ativa.xlsx' não possui abas.")
            st.stop()
        
        st.success(f"✅ Arquivo carregado com sucesso! Encontradas {len(anos_disponiveis_divida)} abas: {', '.join(anos_disponiveis_divida)}")
        
        # Mostrar prévia dos dados
        st.markdown("### 👀 Prévia dos Dados")
        st.info(f"""
        **📊 Estrutura do arquivo:**
        - **Total de abas:** {len(anos_disponiveis_divida)} anos
        - **Abas disponíveis:** {', '.join(anos_disponiveis_divida)}
        - **Formato:** Dados mensais de dívida ativa organizados por ano
        """)
        
        # Mostrar prévia da primeira aba
        if anos_disponiveis_divida:
            try:
                df_previa = pd.read_excel('Arrecadacao Divida Ativa.xlsx', sheet_name=anos_disponiveis_divida[0])
                # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
                df_previa.columns = df_previa.columns.astype(str)
                with st.expander(f"📋 Ver primeiras linhas da aba '{anos_disponiveis_divida[0]}'", expanded=False):
                    st.dataframe(df_previa.head(10), use_container_width=True)
            except Exception as e:
                st.warning(f"⚠️ Não foi possível mostrar prévia da aba {anos_disponiveis_divida[0]}: {e}")
        
        # Usar filtros globais se disponíveis, senão usar todos os anos
        # Filtrar apenas anos que existem no arquivo de dívida ativa
        anos_divida_selecionados = [ano for ano in (anos_selecionados if anos_selecionados else anos_disponiveis_divida) if ano in anos_disponiveis_divida]
        
        if not anos_divida_selecionados:
            st.warning("⚠️ Nenhum dos anos selecionados globalmente existe no arquivo de dívida ativa.")
            anos_divida_selecionados = anos_disponiveis_divida
        
        # Carregar um ano para obter os tributos disponíveis
        tributos_divida = []
        if anos_divida_selecionados:
            try:
                df_temp = pd.read_excel('Arrecadacao Divida Ativa.xlsx', sheet_name=anos_divida_selecionados[0])
                # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
                df_temp.columns = df_temp.columns.astype(str)
                
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
            except Exception as e:
                st.error(f"❌ Erro ao carregar aba {anos_divida_selecionados[0]}: {e}")
        
        # Usar filtros globais de tributos se disponíveis, senão usar todos os tributos
        tributos_divida_selecionados = tributos_selecionados if tributos_selecionados else tributos_divida
        
        # Mapear meses selecionados para números
        meses_para_numero = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
            "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }
        
        # Usar filtros globais de meses se disponíveis, senão usar todos os meses
        meses_divida_selecionados = [meses_para_numero[mes] for mes in meses_selecionados] if meses_selecionados else list(range(1, 13))
        
        if not anos_divida_selecionados:
            st.warning("⚠️ Nenhum ano selecionado para análise.")
        else:
            # Carregar e processar dados
            dados_divida = []
            erros_processamento = []
            
            for ano in anos_divida_selecionados:
                try:
                    df_ano = pd.read_excel('Arrecadacao Divida Ativa.xlsx', sheet_name=ano)
                    # Converter todos os nomes de colunas para string para evitar warning de tipos mistos
                    df_ano.columns = df_ano.columns.astype(str)
                    
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
                        
                        # Processar colunas de meses (colunas 1-12) - apenas meses selecionados
                        for i in meses_divida_selecionados:
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
                                            'NOME_MES': list(meses_para_numero.keys())[list(meses_para_numero.values()).index(i)],
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
                
                # Calcular métricas para todos os anos selecionados (não apenas o último)
                # Somatória total dos valores mensais para todos os anos selecionados
                total_valor_mensal_divida = df_divida['VALOR_MENSAL'].sum()
                
                # Calcular orçado e arrecadado totais para todos os anos selecionados
                df_orcado_arrecadado = df_divida.groupby(['ANO', 'TRIBUTO']).agg({
                    'ORCADO': 'first',      # Pegar apenas uma vez por tributo/ano
                    'ARRECADADO': 'first'   # Pegar apenas uma vez por tributo/ano
                }).reset_index()
                
                # Somar orçado e arrecadado para todos os anos selecionados
                total_orcado_divida = df_orcado_arrecadado['ORCADO'].sum()
                total_arrecadado_divida = df_orcado_arrecadado['ARRECADADO'].sum()
                
                # Layout de métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(total_arrecadado_divida)}</div>
                        <div class="metric-label">Dívida Ativa</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatar_moeda_br(total_orcado_divida)}</div>
                        <div class="metric-label">Orçado</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    meta_alcancada = (total_arrecadado_divida / total_orcado_divida * 100) if total_orcado_divida > 0 else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{meta_alcancada:.1f}%</div>
                        <div class="metric-label">Meta Atingida</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    superavit_deficit = total_arrecadado_divida - total_orcado_divida
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
                    # Preparar dados com ordenação correta dos meses
                    df_divida_mensal = df_divida.copy()
                    
                    # Criar mapeamento de meses para ordenação
                    ordem_meses = {
                        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
                        "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                    }
                    
                    # Adicionar coluna de ordenação
                    df_divida_mensal['ORDEM_MES'] = df_divida_mensal['NOME_MES'].map(ordem_meses)
                    
                    # Ordenar por tributo, ano e ordem do mês
                    df_divida_mensal = df_divida_mensal.sort_values(['TRIBUTO', 'ANO', 'ORDEM_MES'])
                    
                    fig_divida_mensal = px.line(
                        df_divida_mensal,
                        x='NOME_MES',
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
                
                # Gráfico comparativo entre anos
                st.markdown("### 🔍 Comparativo Entre Anos")
                
                # Criar gráfico comparativo por mês entre anos
                # Preparar dados com ordenação correta dos meses
                df_comparativo_divida = df_divida.groupby(['ANO', 'NOME_MES'])['VALOR_MENSAL'].sum().reset_index()
                
                # Criar mapeamento de meses para ordenação
                ordem_meses = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
                    "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                
                # Adicionar coluna de ordenação
                df_comparativo_divida['ORDEM_MES'] = df_comparativo_divida['NOME_MES'].map(ordem_meses)
                
                # Ordenar por ano e ordem do mês
                df_comparativo_divida = df_comparativo_divida.sort_values(['ANO', 'ORDEM_MES'])
                
                fig_comparativo_anos_divida = px.line(
                    df_comparativo_divida,
                    x='NOME_MES',
                    y='VALOR_MENSAL',
                    color='ANO',
                    title='Comparativo de Dívida Ativa Mensal Entre Anos',
                    template=tema_grafico
                )
                
                fig_comparativo_anos_divida.update_layout(
                    height=500,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    ),
                    xaxis_title="Mês",
                    yaxis_title="Valor Total (R$)"
                )
                
                st.plotly_chart(fig_comparativo_anos_divida, use_container_width=True)
                
                # Gráfico de barras comparativo por tributo entre anos
                fig_comparativo_tributos_divida = px.bar(
                    df_divida.groupby(['ANO', 'TRIBUTO'])['VALOR_MENSAL'].sum().reset_index(),
                    x='TRIBUTO',
                    y='VALOR_MENSAL',
                    color='ANO',
                    title='Comparativo de Dívida Ativa por Tributo Entre Anos',
                    template=tema_grafico,
                    barmode='group'
                )
                
                fig_comparativo_tributos_divida.update_layout(
                    height=500,
                    title_x=0.5,
                    yaxis=dict(
                        tickformat=".2f",
                        tickprefix="R$ ",
                        separatethousands=True,
                    ),
                    xaxis_title="Tributo",
                    yaxis_title="Valor Total (R$)"
                )
                
                st.plotly_chart(fig_comparativo_tributos_divida, use_container_width=True)
                
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
