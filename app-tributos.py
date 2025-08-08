import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(page_title="Painel de Arrecadação", layout="wide")
st.title("📊 Painel Geral de Arrecadação Tributária")

# ========== FUNÇÃO PARA FORMATAR EM PADRÃO BR ==========


def formatar_moeda_br(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor


# ========== SELECIONAR O ARQUIVO ==========
arquivo_escolhido = st.selectbox(
    "Selecione o arquivo de dados",
    options=["Arrecadacao Tributos.xlsx", "Arrecadacao Bancos.xlsx"]
)

# Carrega o DataFrame com base na escolha
df = pd.read_excel(arquivo_escolhido, header=2)
# remove colunas automáticas
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
df.columns = df.columns.str.strip().str.upper()
df["ANO"] = df["ANO"].astype(str)

# ========== LISTA DE TRIBUTOS ==========
tributos = [col for col in df.columns if col not in ["ANO", "TOTAL"]]

# ========== TABELA FORMATADA ==========
df_formatado = df.copy()
for col in df_formatado.columns:
    if col != "ANO":
        df_formatado[col] = df_formatado[col].apply(formatar_moeda_br)

# Remove o índice numérico antes de exibir
df_formatado = df_formatado.reset_index(drop=True)

st.subheader("📋 Tabela de Arrecadação")
st.dataframe(df_formatado, use_container_width=True, hide_index=True)

# ========== BOTÃO PARA DOWNLOAD EM EXCEL ==========
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Arrecadação')
st.download_button(
    label="📥 Baixar dados em Excel",
    data=buffer,
    file_name="arrecadacao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ========== GRÁFICOS INDIVIDUAIS ==========
st.subheader("📈 Gráficos Individuais por Tributo")
for tributo in tributos:
    fig = px.bar(
        df,
        x="ANO",
        y=tributo,
        title=f"Arrecadação de {tributo}",
        labels={"ANO": "Ano", tributo: "Valor Arrecadado (R$)"},
        text=df[tributo].apply(formatar_moeda_br),
        color_discrete_sequence=["#2E8B57"]
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=16)
    )

    fig.update_layout(
        title=dict(
            text=f"Arrecadação de {tributo}",
            font=dict(size=20)
        ),
        font=dict(size=14),
        xaxis=dict(
            title=dict(
                text="Ano",
                font=dict(size=16)
            ),
            tickfont=dict(size=14),
            type='category'
        ),
        yaxis=dict(
            title=dict(
                text="Valor Arrecadado (R$)",
                font=dict(size=16)
            ),
            tickfont=dict(size=14),
            tickformat=".2f",
            tickprefix="R$ ",
            separatethousands=True,
        ),
        bargap=0.3,
        height=600  # Altura do gráfico
    )

    st.plotly_chart(fig, use_container_width=True)

# ========== GRÁFICO DE LINHA USANDO COLUNA F ==========
st.subheader("📈 Evolução dos Totais (Coluna F)")

# Carrega a planilha enviada
df = pd.read_excel(arquivo_escolhido, header=2)
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
df.columns = df.columns.str.strip().str.upper()

# Seleciona coluna F (índice 5) e coluna A (anos, índice 0)
coluna_total = df.columns[5]
coluna_ano = df.columns[0]

# Garante que ANO é string (evita problemas no eixo x)
df[coluna_ano] = df[coluna_ano].astype(str)

# Formata texto para exibir nos pontos
df["TEXTO_FORMATADO"] = df[coluna_total].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Gera gráfico de linha
fig = px.line(
    df,
    x=coluna_ano,
    y=coluna_total,
    title="Totais por Ano",
    labels={coluna_ano: "Ano", coluna_total: "Total (R$)"},
    text="TEXTO_FORMATADO",
    markers=True
)

# Atualiza layout e fonte
fig.update_traces(
    textposition="top center",
    textfont=dict(size=12)
)
fig.update_layout(
    title=dict(text="Totais por Ano", font=dict(size=20)),
    font=dict(size=14),
    xaxis=dict(
        title=dict(text="Ano", font=dict(size=16)),
        tickfont=dict(size=14),
        type='category'
    ),
    yaxis=dict(
        title=dict(text="Total (R$)", font=dict(size=16)),
        tickfont=dict(size=14),
        tickformat=".2f",
        tickprefix="R$ ",
        separatethousands=True,
        range=[0, None]
    ),
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# ========== ARRECADAÇÃO POR TRIBUTOS ÚLTIMOS 5 ANOS - Ensino regular pré-escolar, fundamental, médio e superior  Iten 8.01  Lista de Serviços ==========
st.subheader("📊 Arrecadação Ensino")

try:
    # Tenta carregar o arquivo
    df_ensino = pd.read_excel("Arrecadacao Ensino.xlsx", header=2)
    df_ensino = df_ensino.loc[:, ~df_ensino.columns.str.contains("^Unnamed")]
    df_ensino.columns = df_ensino.columns.str.strip().str.upper()
    df_ensino["ANO"] = df_ensino["ANO"].astype(str)

    if "ANO" not in df_ensino.columns:
        st.error("A coluna 'ANO' não foi encontrada no arquivo 'Arrecadacao Ensino.xlsx'.")
    else:
        coluna_valor_extra = [col for col in df_ensino.columns if col != "ANO"][0]
        df_ensino["TEXTO_FORMATADO"] = df_ensino[coluna_valor_extra].apply(formatar_moeda_br)

        fig_extra = px.bar(
            df_ensino,
            x="ANO",
            y=coluna_valor_extra,
            title="ARRECADAÇÃO POR TRIBUTOS ÚLTIMOS 5 ANOS - Ensino regular pré-escolar, fundamental, médio e superior  Iten 8.01  Lista de Serviços",
            labels={"ANO": "Ano", coluna_valor_extra: "Valor Arrecadado (R$)"},
            text="TEXTO_FORMATADO",
            color_discrete_sequence=["#4682B4"]
        )

        fig_extra.update_traces(textposition="outside")
        fig_extra.update_layout(
            yaxis=dict(
                tickformat=".2f",
                tickprefix="R$ ",
                separatethousands=True,
            ),
            yaxis_title="Valor Arrecadado (R$)",
            bargap=0.3
        )
        fig_extra.update_xaxes(type='category')

        st.plotly_chart(fig_extra, use_container_width=True)

except FileNotFoundError:
    st.warning("📁 O arquivo 'Arrecadacao Ensino.xlsx' não foi encontrado. Pule esta seção ou carregue o arquivo.")
except Exception as e:
    st.error(f"❌ Erro ao carregar ou processar o arquivo 'Arrecadacao Ensino.xlsx': {e}")


# ========== NOVO GRÁFICO A PARTIR DE OUTRO ARQUIVO ==========
st.subheader("📊 Arrecadação Própria Total")

try:
    # Tenta carregar o arquivo
    df_extra = pd.read_excel("Receita Propria Consolidado.xlsx", header=2)
    df_extra = df_extra.loc[:, ~df_extra.columns.str.contains("^Unnamed")]
    df_extra.columns = df_extra.columns.str.strip().str.upper()
    df_extra["ANO"] = df_extra["ANO"].astype(str)

    # Verifica se 'ANO' está presente
    if "ANO" not in df_extra.columns:
        st.error("A coluna 'ANO' não foi encontrada no arquivo 'Receita Propria Consolidado.xlsx'.")
    else:
        coluna_valor_extra = [col for col in df_extra.columns if col != "ANO"][0]
        df_extra["TEXTO_FORMATADO"] = df_extra[coluna_valor_extra].apply(formatar_moeda_br)

        fig_extra = px.bar(
            df_extra,
            x="ANO",
            y=coluna_valor_extra,
            title="RECEITA TRIBUTÁRIA PRÓPRIA TOTAL ÚLTIMOS 5 ANOS",
            labels={"ANO": "Ano", coluna_valor_extra: "Valor Arrecadado (R$)"},
            text="TEXTO_FORMATADO",
            color_discrete_sequence=["#4682B4"]
        )

        fig_extra.update_traces(
            textposition="outside",
            textfont=dict(size=16)
        )

        fig_extra.update_layout(
            title=dict(
                text="RECEITA TRIBUTÁRIA PRÓPRIA TOTAL ÚLTIMOS 5 ANOS",
                font=dict(size=20)
            ),
            font=dict(size=14),
            xaxis=dict(
                title=dict(
                    text="Ano",
                    font=dict(size=16)
                ),
                tickfont=dict(size=14),
                type='category'
            ),
            yaxis=dict(
                title=dict(
                    text="Valor Arrecadado (R$)",
                    font=dict(size=16)
                ),
                tickfont=dict(size=14),
                tickformat=".2f",
                tickprefix="R$ ",
                separatethousands=True,
                range=[0, None]  # Trava o eixo Y para começar no zero
            ),
            bargap=0.3,
            height=500
        )

        st.plotly_chart(fig_extra, use_container_width=True)

except FileNotFoundError:
    st.warning("📁 O arquivo 'Receita Propria Consolidado.xlsx' não foi encontrado. Pule esta seção ou carregue o arquivo.")
except Exception as e:
    st.error(f"❌ Erro ao carregar ou processar o arquivo 'Receita Propria Consolidado.xlsx': {e}")
