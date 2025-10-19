# CV/Banda – Calculadora de Cachê
# Autor: Murillo Martins
# -----------------------------------------------
# Como rodar local:
#   pip install -r requirements.txt
#   streamlit run "C:\Users\muril\OneDrive\01 - Projetos\07 - Streamlit\calculorb\calculorb.py"
# -----------------------------------------------

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Rockbuzz Pay",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- util ----------
def brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def default_rows():
    # Valores pré-preenchidos iguais à imagem (edite livremente no app)
    return [
        {"Item": "1. Músicos",              "Descrição": "Pagamento dos 6 músicos",                          "Quantidade": 6, "Custo Unitário (R$)": 300.00, "Incluir": True},
        {"Item": "2. Ajudantes/Staff",      "Descrição": "Pagamento de ajudantes (roadies)",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "3. Transporte",           "Descrição": "Aluguel/combustível de carros próprios (3 ou 4)",  "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "4. Pedágio",              "Descrição": "Custos com pedágios (ida e volta)",                "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "5. Combustível",          "Descrição": "Estimativa ida/volta (média de 200 km, por carro)", "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "6. Alimentação",          "Descrição": "Refeição completa para 8 pessoas",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00,  "Incluir": True},
        {"Item": "7. Hospedagem (opcional)","Descrição": "Caso haja necessidade de pernoite",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "8. Som/Luz Kiko",         "Descrição": "PA até 100 pessoas/Monitoramento Banda/Luz",       "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "9. PA Guilherme",         "Descrição": "PA para eventos acima de 100 pessoas",             "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "10. Estrutura Evento",    "Descrição": "Palco, som, luz, telão, treliças",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00,"Incluir": True},
        {"Item": "11. Técnico de Som",      "Descrição": "Palco/FOH",                                        "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "12. Outros Custos",       "Descrição": "Equipamentos extras, imprevistos",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "13. Taxa de Lucro*",      "Descrição": "Margem adicional para banda (20–30%)",             "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": False},
    ]

# ---------- estado inicial ----------
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(default_rows())

# ---------- sidebar (parâmetros) ----------
st.sidebar.header("Parâmetros")
margem_pct = st.sidebar.number_input(
    "Margem de Lucro (%)", min_value=0.0, max_value=200.0, value=30.0, step=1.0, help="Percentual aplicado sobre o Custo Total."
)
nome_evento = st.sidebar.text_input("Nome do evento / cliente", value="")
data_evento = st.sidebar.date_input("Data do evento", value=datetime.today())
cidade = st.sidebar.text_input("Cidade/Local", value="")
st.sidebar.caption("Dica: no celular, a tabela abaixo é rolável lateralmente.")

st.title("Rockbuzz Pay")
st.write("Edite as quantidades/valores, marque **Incluir** nos itens que contam para o cálculo e veja o resultado em tempo real.")

# ---------- editor de dados ----------
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    column_order=["Item", "Descrição", "Quantidade", "Custo Unitário (R$)", "Incluir"],
    column_config={
        "Quantidade": st.column_config.NumberColumn(format="%.2f", step=1.0, min_value=0.0),
        "Custo Unitário (R$)": st.column_config.NumberColumn(format="%.2f", step=1.0, min_value=0.0),
        "Incluir": st.column_config.CheckboxColumn(),
    },
    hide_index=True,
)

# ---------- cálculos ----------
df_calc = edited_df.copy()
df_calc["Total (R$)"] = df_calc["Quantidade"] * df_calc["Custo Unitário (R$)"]
df_calc["Total (R$)"] = df_calc["Total (R$)"].where(df_calc["Incluir"], 0.0)

custo_total = float(df_calc["Total (R$)"].sum())
margem_valor = custo_total * (margem_pct / 100.0)
cache_proposto = custo_total + margem_valor

# ---------- exibição ----------
# formatações apenas para exibir
df_view = edited_df.copy()
df_view["Total (R$)"] = (edited_df["Quantidade"] * edited_df["Custo Unitário (R$)"]).map(brl)
df_view["Custo Unitário (R$)"] = df_view["Custo Unitário (R$)"].map(brl)
df_view["Quantidade"] = df_view["Quantidade"].map(lambda x: f"{x:.0f}" if float(x).is_integer() else f"{x:.2f}")

st.subheader("Planilha")
st.dataframe(df_view, use_container_width=True, hide_index=True)

st.subheader("Resumo")
col1, col2, col3 = st.columns(3)
col1.metric("Custo Total", brl(custo_total))
col2.metric("Margem de Lucro", brl(margem_valor), f"{margem_pct:.0f}%")
col3.metric("Cachê Proposto", brl(cache_proposto))

st.divider()
st.write("**Detalhes do evento (opcional):**")
st.write(
    f"- **Evento/Cliente:** {nome_evento or '—'}  \n"
    f"- **Data:** {data_evento.strftime('%d/%m/%Y')}  \n"
    f"- **Local:** {cidade or '—'}"
)

# ---------- export ----------
csv = df_calc.drop(columns=["Incluir"]).to_csv(index=False, encoding="utf-8-sig")
dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
st.download_button(
    "⬇️ Baixar CSV (com valores numéricos)",
    data=csv,
    file_name=f"calculadora_cache_{dt_str}.csv",
    mime="text/csv",
)

st.caption(
    "Observação: a linha **13. Taxa de Lucro** está no grid apenas para manter a referência da sua planilha; "
    "o valor usado no cálculo vem do controle **Margem de Lucro (%)** na barra lateral."
)

# mantém o estado
st.session_state.df = edited_df
