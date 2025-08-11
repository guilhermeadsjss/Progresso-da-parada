import streamlit as st
import pandas as pd
from pathlib import Path
import unicodedata
import re

st.set_page_config(
    page_title="Dashboard de Controle de Atividades",
    page_icon="📊",
    layout="wide"
)

# --- Logo ---
logo_candidates = ["images (1).png", "Sem título.png", "logo_empresa.png", "logo.png"]
base_path = Path(__file__).parent
logo_path = None
for cand in logo_candidates:
    p = base_path / cand
    if p.is_file():
        logo_path = p
        break

if logo_path:
    st.image(str(logo_path), width=180)

st.title("📊 Dashboard de Controle de Atividades")
st.markdown("---")

DATA_FILE = base_path / "Banco_Dashboard.xlsx"

def _normalize_col_name(s):
    s = str(s).strip()
    s = unicodedata.normalize('NFKD', s).encode('ASCII','ignore').decode()
    s = re.sub(r'\W+', '_', s)
    s = re.sub(r'_+', '_', s).strip('_').lower()
    return s

def find_col(df, keywords):
    for c in df.columns:
        for k in keywords:
            if k in c:
                return c
    return None

@st.cache_data(ttl=5)
def carregar_dados():
    if not DATA_FILE.is_file():
        st.error(f"Arquivo '{DATA_FILE.name}' não encontrado!")
        return pd.DataFrame()

    try:
        df = pd.read_excel(DATA_FILE, sheet_name="dados_corrigidos")
    except Exception:
        df = pd.read_excel(DATA_FILE)

    # Normalizar nomes das colunas
    original_cols = list(df.columns)
    normalized = [_normalize_col_name(c) for c in original_cols]
    mapping = dict(zip(original_cols, normalized))
    df = df.rename(columns=mapping)

    # Detectar colunas principais
    col_area = find_col(df, ['area', 'sistema'])
    col_desc = find_col(df, ['descricao', 'desc', 'atividade', 'description'])
    col_status = find_col(df, ['status'])
    col_tipo = find_col(df, ['tipo', 'medicao'])
    col_m2_prev = find_col(df, ['m2_previsto', 'm2_prev', 'previsto'])
    col_m2_real = find_col(df, ['m2_realizado', 'm2_real', 'realizado'])
    col_pct = find_col(df, ['conclusao', 'percent', 'porcent'])

    # Criar colunas padrão se não existirem
    if col_area is None:
        df['area_sistema'] = 'Sem Área'
        col_area = 'area_sistema'
    if col_desc is None:
        df['descricao'] = ''
        col_desc = 'descricao'
    if col_status is None:
        df['status'] = ''
        col_status = 'status'
    if col_m2_prev is None:
        df['m2_previsto'] = 0
        col_m2_prev = 'm2_previsto'
    if col_m2_real is None:
        df['m2_realizado'] = 0
        col_m2_real = 'm2_realizado'
    if col_pct is None:
        df['porcent_conclusao'] = 0
        col_pct = 'porcent_conclusao'

    # Garantir tipos numéricos
    for c in [col_m2_prev, col_m2_real, col_pct]:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # Inserir ID
    df.insert(0, 'id', range(len(df)))

    # Armazenar metadados
    df.attrs['col_area'] = col_area
    df.attrs['col_desc'] = col_desc
    df.attrs['col_status'] = col_status
    df.attrs['col_tipo'] = col_tipo
    df.attrs['col_m2_prev'] = col_m2_prev
    df.attrs['col_m2_real'] = col_m2_real
    df.attrs['col_pct'] = col_pct

    return df

df = carregar_dados()

if df.empty:
    st.warning("Não foi possível carregar os dados. Verifique se o arquivo está na pasta correta.")
else:
    # Debug para verificar colunas detectadas
    with st.expander("🔎 Colunas detectadas e mapeamento (debug)"):
        st.write("Colunas:", list(df.columns))
        st.write({
            "col_area": df.attrs.get('col_area'),
            "col_desc": df.attrs.get('col_desc'),
            "col_status": df.attrs.get('col_status'),
            "col_tipo": df.attrs.get('col_tipo'),
            "col_m2_prev": df.attrs.get('col_m2_prev'),
            "col_m2_real": df.attrs.get('col_m2_real'),
            "col_pct": df.attrs.get('col_pct'),
        })

    col_area = df.attrs.get('col_area')
    col_desc = df.attrs.get('col_desc')
    col_status = df.attrs.get('col_status')
    col_tipo = df.attrs.get('col_tipo')
    col_m2_prev = df.attrs.get('col_m2_prev')
    col_m2_real = df.attrs.get('col_m2_real')
    col_pct = df.attrs.get('col_pct')

    # --- Filtros ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        areas = st.multiselect("Filtrar por Área/Sistema", options=sorted(df[col_area].dropna().unique().tolist()))
    with col_f2:
        status = st.multiselect("Filtrar por Status", options=sorted(df[col_status].dropna().unique().tolist()))

    df_filtrado = df.copy()
    if areas:
        df_filtrado = df_filtrado[df_filtrado[col_area].isin(areas)]
    if status:
        df_filtrado = df_filtrado[df_filtrado[col_status].isin(status)]

    # --- KPIs ---
    total_atividades = len(df_filtrado)
    concluidas = df_filtrado[col_status].astype(str).str.contains('concl', case=False, na=False).sum()
    em_andamento = df_filtrado[col_status].astype(str).str.contains('andam', case=False, na=False).sum()
    nao_iniciadas = total_atividades - int(concluidas) - int(em_andamento)

    if col_tipo:
        df_m2 = df_filtrado[df_filtrado[col_tipo].astype(str).str.contains('m', case=False, na=False)]
    else:
        df_m2 = df_filtrado.copy()

    m2_previsto = df_m2[col_m2_prev].sum()
    m2_realizado = df_m2[col_m2_real].sum()
    progresso_m2 = (m2_realizado / m2_previsto * 100) if m2_previsto > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Atividades", f"{total_atividades}")
    col2.metric("✅ Concluídas", f"{int(concluidas)} ({(int(concluidas)/total_atividades):.1%})" if total_atividades else "0")
    col3.metric("▶️ Em Andamento", f"{int(em_andamento)} ({(int(em_andamento)/total_atividades):.1%})" if total_atividades else "0")
    col4.metric("⏰ Não Iniciadas", f"{int(nao_iniciadas)} ({(int(nao_iniciadas)/total_atividades):.1%})" if total_atividades else "0")

    st.markdown("##### Progresso Físico (m²)")
    st.progress(min(max(progresso_m2/100, 0), 1))
    st.write(f"**Previsto:** {m2_previsto:,.2f} m² | **Realizado:** {m2_realizado:,.2f} m²")

    st.markdown("---")

    # --- Gráficos ---
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("##### Avanço por Área (m² Realizado)")
        progresso_area = df_m2.groupby(col_area)[col_m2_real].sum()
        st.bar_chart(progresso_area)

    with col_chart2:
        st.markdown("##### Distribuição de Status das Atividades")
        status_counts = df_filtrado[col_status].value_counts()
        st.bar_chart(status_counts)

    # --- Visualização detalhada ---
    st.markdown("### 📋 Detalhes das Atividades")
    for _, row in df_filtrado.iterrows():
        area_val = row[col_area] if col_area in row else "N/A"
        desc_val = row[col_desc] if col_desc in row else ""
        status_val = row[col_status] if col_status in row else ""
        tipo_val = row[col_tipo] if (col_tipo and col_tipo in row) else ""
        m2_prev_val = row[col_m2_prev] if col_m2_prev in row else 0
        m2_real_val = row[col_m2_real] if col_m2_real in row else 0
        pct_val = row[col_pct] if col_pct in row else 0

        with st.expander(f"🔹 {area_val} - {desc_val}"):
            st.write(f"**Status:** {status_val}")
            st.write(f"**Tipo de Medição:** {tipo_val}")
            st.write(f"**M2 Previsto:** {m2_prev_val}")
            st.write(f"**M2 Realizado:** {m2_real_val}")
            st.write(f"**% Conclusão:** {pct_val}%")
            st.dataframe(row.to_frame().T)

