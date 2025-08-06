import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Dashboard de Controle de Atividades",
    page_icon="📊",
    layout="wide"
)

DATA_FILE = Path(__file__).parent / "Banco_Dashboard.xlsx"

@st.cache_data(ttl=5)
def carregar_dados():
    if not DATA_FILE.is_file():
        st.error(f"Arquivo '{DATA_FILE.name}' não encontrado!")
        return pd.DataFrame()

    df = pd.read_excel(DATA_FILE, sheet_name="dados_corrigidos")

    # Garantir tipos corretos
    df['M2_Previsto'] = pd.to_numeric(df['M2_Previsto'], errors='coerce').fillna(0)
    df['M2_Realizado'] = pd.to_numeric(df['M2_Realizado'], errors='coerce').fillna(0)
    df['%_Conclusão'] = pd.to_numeric(df['%_Conclusão'], errors='coerce').fillna(0)
    df['%_Conclusão_Ajustado'] = pd.to_numeric(df['%_Conclusão_Ajustado'], errors='coerce').fillna(0)

    # Adicionar ID único
    df.insert(0, 'id', range(len(df)))

    return df

df = carregar_dados()

st.title("📊 Dashboard de Controle de Atividades")
st.markdown("---")

if not df.empty:
    # --- Filtros ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        areas = st.multiselect("Filtrar por Área/Sistema", options=sorted(df['Área/Sistema'].unique()))
    with col_f2:
        status = st.multiselect("Filtrar por Status", options=sorted(df['Status'].unique()))

    df_filtrado = df.copy()
    if areas:
        df_filtrado = df_filtrado[df_filtrado['Área/Sistema'].isin(areas)]
    if status:
        df_filtrado = df_filtrado[df_filtrado['Status'].isin(status)]

    # --- KPIs ---
    total_atividades = len(df_filtrado)
    concluidas = len(df_filtrado[df_filtrado['Status'].str.contains('Concluído', case=False)])
    em_andamento = len(df_filtrado[df_filtrado['Status'].str.contains('Andamento', case=False)])
    nao_iniciadas = total_atividades - concluidas - em_andamento

    df_m2 = df_filtrado[df_filtrado['Tipo de Medição'].str.contains('m', case=False)]
    m2_previsto = df_m2['M2_Previsto'].sum()
    m2_realizado = df_m2['M2_Realizado'].sum()
    progresso_m2 = (m2_realizado / m2_previsto * 100) if m2_previsto > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Atividades", f"{total_atividades}")
    col2.metric("✅ Concluídas", f"{concluidas} ({concluidas/total_atividades:.1%})" if total_atividades else "0")
    col3.metric("▶️ Em Andamento", f"{em_andamento} ({em_andamento/total_atividades:.1%})" if total_atividades else "0")
    col4.metric("⏰ Não Iniciadas", f"{nao_iniciadas} ({nao_iniciadas/total_atividades:.1%})" if total_atividades else "0")

    st.markdown("##### Progresso Físico (m²)")
    st.progress(progresso_m2 / 100)
    st.write(f"**Previsto:** {m2_previsto:,.2f} m² | **Realizado:** {m2_realizado:,.2f} m²")

    st.markdown("---")

    # --- Gráficos ---
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("##### Avanço por Área (m² Realizado)")
        progresso_area = df_m2.groupby('Área/Sistema')['M2_Realizado'].sum()
        st.bar_chart(progresso_area)

    with col_chart2:
        st.markdown("##### Distribuição de Status das Atividades")
        status_counts = df_filtrado['Status'].value_counts()
        st.bar_chart(status_counts)

    # --- Visualização da Tabela ---
    with st.expander("Ver Tabela de Dados Filtrada"):
        st.dataframe(df_filtrado.drop(columns=['id']))
else:
    st.warning("Não foi possível carregar os dados. Verifique se o arquivo está na pasta correta.")
