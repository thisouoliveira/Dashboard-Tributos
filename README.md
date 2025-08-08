# 📊 Dashboard Tributário Municipal

Um dashboard moderno e interativo para análise de dados tributários municipais, desenvolvido com Streamlit e Plotly.

## 🚀 Funcionalidades

### ✨ **Novos Recursos Visuais**
- **Design Moderno**: Header com gradiente profissional
- **Cards de Métricas**: Visualização clara dos principais indicadores
- **Layout Responsivo**: Adaptação para diferentes tamanhos de tela
- **Temas Personalizáveis**: Múltiplas opções de tema para gráficos

### 📈 **Novos Gráficos**
1. **Mapa de Calor**: Visualização matricial dos dados
2. **Gráfico de Radar**: Comparação de tributos
3. **Boxplot**: Análise de distribuição
4. **Gráfico de Dispersão**: Análise de correlação
5. **Gráficos Empilhados**: Composição da arrecadação
6. **Gráfico de Área**: Evolução temporal

### ⚙️ **Funcionalidades Avançadas**
- **Sidebar Interativa**: Controles de configuração
- **Filtros Dinâmicos**: Seleção de anos e tributos
- **Cache de Dados**: Carregamento otimizado
- **Exportação Múltipla**: Excel e CSV com timestamp
- **Análise Estatística**: Estatísticas descritivas completas

## 📁 Estrutura de Arquivos

```
Dashboard Tributos/
├── app-tributos.py              # Dashboard principal melhorado
├── README.md                    # Este arquivo
├── Arrecadacao Tributos.xlsx    # Dados principais
├── Arrecadacao Bancos.xlsx      # Dados bancários
├── Arrecadacao Ensino.xlsx      # Dados educacionais
└── Receita Propria Consolidado.xlsx  # Dados de receita própria
```

## 🛠️ Como Executar

### Pré-requisitos
```bash
pip install streamlit pandas plotly openpyxl
```

### Executar o Dashboard
```bash
streamlit run app-tributos.py
```

## 📊 Tipos de Gráficos Disponíveis

### Dashboard Principal
1. **Barras**: Gráfico de barras simples
2. **Linha**: Gráfico de linha com marcadores
3. **Área**: Gráfico de área preenchida
4. **Pizza**: Gráfico de pizza para distribuição

### Gráficos Especializados
- **Mapa de Calor**: Visualização matricial
- **Radar**: Comparação de múltiplas variáveis
- **Boxplot**: Análise de distribuição
- **Dispersão**: Análise de correlação
- **Empilhado**: Composição por categoria

## ⚙️ Configurações

### Sidebar
- **Arquivo de Dados**: Seleção entre diferentes fontes
- **Filtro de Anos**: Seleção múltipla de períodos
- **Tipo de Gráfico**: Escolha do tipo de visualização
- **Tema**: Personalização visual dos gráficos

### Filtros Interativos
- **Por Tributo**: Filtro específico por tipo de tributo
- **Por Ano**: Filtro temporal
- **Configurações de Exibição**: Controle de visibilidade

## 📈 Métricas Principais

### Indicadores Calculados
- **Arrecadação Atual**: Valor do último ano
- **Arrecadação Anterior**: Valor do penúltimo ano
- **Crescimento Anual**: Percentual de variação
- **Média Anual**: Valor médio do período

### Análise Estatística
- **Média**: Valor médio dos dados
- **Mediana**: Valor central
- **Mínimo/Máximo**: Extremos dos dados
- **Desvio Padrão**: Variabilidade dos dados

## 🎯 Recursos Avançados

### Exportação de Dados
- **Excel**: Múltiplas abas com dados formatados
- **CSV**: Arquivo de texto separado por vírgulas
- **Timestamp**: Nomes de arquivo com data/hora

### Análise Comparativa
- **Receita vs Ensino**: Comparação entre diferentes fontes
- **Ranking de Tributos**: Ordenação por arrecadação
- **Correlação**: Análise de relacionamento entre variáveis

### Personalização
- **Temas**: Múltiplas opções de tema visual
- **Cores**: Paletas de cores profissionais
- **Layout**: Organização responsiva dos elementos

## 🔧 Tecnologias Utilizadas

- **Streamlit**: Framework para aplicações web
- **Plotly**: Biblioteca de gráficos interativos
- **Pandas**: Manipulação e análise de dados
- **OpenPyXL**: Leitura de arquivos Excel

## 📝 Formato dos Dados

### Estrutura Esperada
- **Coluna ANO**: Anos dos dados
- **Colunas de Tributos**: Valores de arrecadação
- **Header na linha 3**: Configuração para leitura

### Arquivos Suportados
- **Excel (.xlsx)**: Formato principal
- **CSV**: Exportação de dados

## 🎨 Temas Disponíveis

1. **plotly**: Tema padrão
2. **plotly_white**: Tema claro
3. **plotly_dark**: Tema escuro
4. **simple_white**: Tema minimalista

## 📊 Exemplos de Uso

### Análise Temporal
1. Selecione o arquivo de dados
2. Escolha os anos de interesse
3. Visualize a evolução no gráfico principal

### Análise Comparativa
1. Use o mapa de calor para identificar padrões
2. Analise a correlação entre tributos
3. Compare composições com gráficos empilhados

### Exportação de Relatórios
1. Configure os filtros desejados
2. Use os botões de download
3. Arquivos são salvos com timestamp

## 🚀 Próximas Melhorias

- [ ] Gráficos 3D
- [ ] Análise preditiva
- [ ] Dashboards em tempo real
- [ ] Integração com APIs
- [ ] Relatórios automáticos
- [ ] Alertas e notificações

---

**Desenvolvido com ❤️ para análise tributária municipal** 