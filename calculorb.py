# Rockbuzz Pay – Calculadora de Cachê (com download em PDF)
# ----------------------------------------------------------
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

st.set_page_config(
    page_title="Rockbuzz Pay | Calculadora de Cachê",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- helpers ----------
def brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def default_rows():
    return [
        {"Item": "1. Músicos",              "Descrição": "Pagamento músicos",                                "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "2. Ajudantes/Staff",      "Descrição": "Pagamento de ajudantes (roadies)",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "3. Transporte",           "Descrição": "Aluguel/combustível de carros próprios (3 ou 4)",  "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "4. Pedágio",              "Descrição": "Custos com pedágios (ida e volta)",                "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "5. Combustível",          "Descrição": "Estimativa ida/volta (média de 200 km, por carro)","Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "6. Alimentação",          "Descrição": "Refeição completa para 8 pessoas",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "7. Hospedagem (opcional)","Descrição": "Caso haja necessidade de pernoite",                "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "8. Som/Luz Kiko",         "Descrição": "PA até 100 pessoas/Monitoramento Banda/Luz",       "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "9. PA Guilherme",         "Descrição": "PA para eventos acima de 100 pessoas",             "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "10. Estrutura Evento",    "Descrição": "Palco, som, luz, telão, treliças",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "11. Técnico de Som",      "Descrição": "Palco/FOH",                                        "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
        {"Item": "12. Outros Custos",       "Descrição": "Equipamentos extras, imprevistos",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00,   "Incluir": True},
    ]

# ---------- estado ----------
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(default_rows())

# ---------- sidebar ----------
st.sidebar.header("Parâmetros")
margem_pct = st.sidebar.number_input("Margem de Lucro (%)", min_value=0.0, max_value=200.0, value=30.0, step=1.0)
nome_evento = st.sidebar.text_input("Evento/Cliente", value="")
data_evento = st.sidebar.date_input("Data do evento", value=datetime.today())
cidade = st.sidebar.text_input("Cidade/Local", value="")

# ---------- título ----------
st.title("Rockbuzz Pay")
st.write("Edite as quantidades/valores, marque **Incluir** e veja o resultado em tempo real.")

# ---------- editor ----------
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

# ---------- métricas ----------
st.subheader("Resumo")
col1, col2, col3 = st.columns(3)
col1.metric("Custo Total", brl(custo_total))
col2.metric("Margem de Lucro", brl(margem_valor), f"{margem_pct:.0f}%")
col3.metric("Cachê Proposto", brl(cache_proposto))

# ---------- função PDF ----------
def gerar_pdf(df, custo_total, margem_valor, cache_proposto):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("<b>Rockbuzz Pay – Calculadora de Cachê</b>", styles["Title"])
    info = Paragraph(
        f"<b>Evento:</b> {nome_evento or '—'}<br/>"
        f"<b>Data:</b> {data_evento.strftime('%d/%m/%Y')}<br/>"
        f"<b>Cidade:</b> {cidade or '—'}<br/><br/>",
        styles["Normal"],
    )
    elementos += [titulo, Spacer(1, 12), info]

    dados = [["Item", "Descrição", "Qtd", "Custo Unitário", "Total"]]
    for _, row in df[df["Incluir"]].iterrows():
        dados.append([
            row["Item"],
            row["Descrição"],
            f"{row['Quantidade']:.0f}",
            brl(row["Custo Unitário (R$)"]),
            brl(row["Total (R$)"]),
        ])
    dados.append(["", "", "", "Custo Total", brl(custo_total)])
    dados.append(["", "", "", "Margem de Lucro", brl(margem_valor)])
    dados.append(["", "", "", "Cachê Proposto", brl(cache_proposto)])

    tabela = Table(dados, colWidths=[60, 190, 50, 80, 80])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elementos.append(tabela)
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ---------- botão PDF ----------
pdf_buffer = gerar_pdf(df_calc, custo_total, margem_valor, cache_proposto)
st.download_button(
    label="⬇️ Baixar PDF",
    data=pdf_buffer,
    file_name=f"Rockbuzz_Pay_{datetime.now().strftime('%Y%m%d')}.pdf",
    mime="application/pdf",
)

# ---------- manter estado ----------
st.session_state.df = edited_df


