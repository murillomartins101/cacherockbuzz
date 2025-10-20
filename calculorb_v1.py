# Rockbuzz Pay – Calculadora de Cachê (Orçamento separado do Contrato + Histórico)
# -------------------------------------------------------------------------------
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import json
import uuid

# --- PDF (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

st.set_page_config(
    page_title="Rockbuzz Pay | Calculadora de Cachê + Contrato",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# Helpers & Defaults
# =========================
def brl(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def default_rows():
    return [
        {"Item": "1. Músicos",               "Descrição": "Pagamento músicos",                                "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "2. Ajudantes/Staff",      "Descrição": "Pagamento de ajudantes (roadies)",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "3. Transporte",           "Descrição": "Aluguel/combustível de carros próprios (3 ou 4)",  "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "4. Pedágio",              "Descrição": "Custos com pedágios (ida e volta)",                "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "5. Combustível",          "Descrição": "Estimativa ida/volta (média de 200 km, por carro)", "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "6. Alimentação",          "Descrição": "Refeição completa para 8 pessoas",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "7. Hospedagem (opcional)","Descrição": "Caso haja necessidade de pernoite",                "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "8. Som/Luz Kiko",         "Descrição": "PA até 100 pessoas/Monitoramento Banda/Luz",       "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "9. PA Guilherme",         "Descrição": "PA para eventos acima de 100 pessoas",             "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "10. Estrutura Evento",    "Descrição": "Palco, som, luz, telão, treliças",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "11. Técnico de Som",      "Descrição": "Palco/FOH",                                        "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "12. Outros Custos",       "Descrição": "Equipamentos extras, imprevistos",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
    ]

def ensure_state():
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame(default_rows())
    if "history" not in st.session_state:
        st.session_state.history = []

ensure_state()

# =========================
# Sidebar – Parâmetros
# =========================
st.sidebar.header("Parâmetros")
margem_pct = st.sidebar.number_input("Margem de Lucro (%)", min_value=0.0, max_value=200.0, value=30.0, step=1.0)

st.sidebar.header("Evento")
nome_evento = st.sidebar.text_input("Evento/Cliente", value="")
data_evento = st.sidebar.date_input("Data do evento", value=datetime.today())
cidade = st.sidebar.text_input("Cidade/Local", value="")

st.sidebar.header("Orçamento Enviado")
numero_proposta = st.sidebar.text_input("Nº da Proposta", value=datetime.now().strftime("RB-%Y%m%d-%H%M"))
validade_dias = st.sidebar.number_input("Validade (dias)", min_value=1, max_value=90, value=7, step=1)
forma_pagto = st.sidebar.text_input("Condições de Pagamento", value="50% na assinatura + 50% no dia do evento")
observacoes = st.sidebar.text_area("Observações (opcional)", value="")
enviado = st.sidebar.checkbox("Marcar como ENVIADO", value=False)

st.sidebar.header("Contratante")
contratante_nome = st.sidebar.text_input("Nome/Razão Social", value="")
contratante_doc = st.sidebar.text_input("CNPJ/CPF", value="")
contratante_email = st.sidebar.text_input("E-mail", value="")
contratante_tel = st.sidebar.text_input("Telefone", value="")
contratante_end = st.sidebar.text_area("Endereço", value="")

st.sidebar.header("Contrato – Dados da Banda")
banda_razao = st.sidebar.text_input("Contratada (Razão Social)", value="Aditivo Media Management")
banda_cnpj = st.sidebar.text_input("CNPJ", value="40.157.297/0001-18")
banda_resp_legal = st.sidebar.text_input("Representante Legal do CNPJ", value="")
banda_resp_banda = st.sidebar.text_input("Responsável pela Banda", value="")

st.sidebar.header("Contrato – Itens do Evento")
num_convidados = st.sidebar.number_input("Número de Convidados", min_value=0, step=10, value=0)
hora_montagem = st.sidebar.text_input("Horário de Montagem", value="")
hora_show = st.sidebar.text_input("Horário do Show", value="")
local_apresentacao = st.sidebar.text_input("Local de Apresentação", value="")

st.sidebar.header("Contrato – Equipamentos e Responsabilidades")
resp_banda = st.sidebar.text_area("Responsabilidade da Banda", value="Sonorização e iluminação do show")
resp_contratante = st.sidebar.text_area("Responsabilidade da Contratante", value="Som mecânico para a festa")

st.sidebar.header("Contrato – Equipe")
num_integrantes = st.sidebar.number_input("Integrantes", min_value=0, value=0)
num_apoio = st.sidebar.number_input("Equipe de Apoio", min_value=0, value=0)
num_acomp = st.sidebar.number_input("Acompanhantes", min_value=0, value=0)

st.sidebar.header("Contrato – Energia (NBR 5410)")
energia_tomada = st.sidebar.text_input("Tomada", value="20A")
energia_tensao = st.sidebar.text_input("Tensão", value="220V")
energia_aterramento = st.sidebar.text_input("Aterramento", value="Adequado, conforme NBR 5410")
energia_dist_max = st.sidebar.text_input("Distância máx. do palco", value="10 metros")

st.sidebar.header("Contrato – Multa & Foro")
multa_perc = st.sidebar.number_input("Multa por descumprimento (%)", min_value=0, max_value=100, value=50)
foro = st.sidebar.text_input("Foro", value="Comarca de Jundiaí/SP")

# =========================
# Título
# =========================
st.title("Rockbuzz Pay")
st.write("Edite as quantidades/valores, marque **Incluir** nos itens que contam para o cálculo e veja o resultado em tempo real.")

# =========================
# Editor de itens
# =========================
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

# =========================
# Cálculos
# =========================
df_calc = edited_df.copy()
df_calc["Total (R$)"] = df_calc["Quantidade"] * df_calc["Custo Unitário (R$)"]
df_calc["Total (R$)"] = df_calc["Total (R$)"].where(df_calc["Incluir"], 0.0)

custo_total = float(df_calc["Total (R$)"].sum())
margem_valor = custo_total * (margem_pct / 100.0)
cache_proposto = custo_total + margem_valor
data_validade = datetime.today().date() + timedelta(days=int(validade_dias))

# =========================
# Resumo
# =========================
st.subheader("Resumo")
c1, c2, c3 = st.columns(3)
c1.metric("Custo Total", brl(custo_total))
c2.metric("Margem de Lucro", brl(margem_valor), f"{margem_pct:.0f}%")
c3.metric("Cachê Proposto", brl(cache_proposto))
st.caption("A margem é controlada pela barra lateral; a planilha não tem linha de 'Taxa de Lucro'.")

# =========================
# PDFs separados (Orçamento e Contrato)
# =========================
def _pdf_doc_setup():
    doc_kwargs = dict(pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    small = ParagraphStyle(name="small", parent=styles["Normal"], fontSize=9, leading=11)
    small_bold = ParagraphStyle(name="small_bold", parent=styles["Normal"], fontSize=9, leading=11)
    title_style = ParagraphStyle(name="title", parent=styles["Title"], fontSize=18, leading=22)
    return doc_kwargs, small, small_bold, title_style

def gerar_pdf_orcamento(df, custo_total, margem_valor, cache_proposto):
    buffer = BytesIO()
    doc_kwargs, small, small_bold, title_style = _pdf_doc_setup()
    doc = SimpleDocTemplate(buffer, **doc_kwargs)

    elementos = []
    elementos.append(Paragraph("<b>Rockbuzz Pay – Orçamento</b>", title_style))
    elementos.append(Spacer(1, 4))
    topo = (
        f"<b>Nº Proposta:</b> {numero_proposta} &nbsp;&nbsp; "
        f"<b>Status:</b> {'ENVIADO' if enviado else 'RASCUNHO'}<br/>"
        f"<b>Evento:</b> {nome_evento or '—'} &nbsp;&nbsp; "
        f"<b>Data:</b> {data_evento.strftime('%d/%m/%Y')} &nbsp;&nbsp; "
        f"<b>Cidade:</b> {cidade or '—'}<br/>"
        f"<b>Validade:</b> {validade_dias} dia(s) (até {data_validade.strftime('%d/%m/%Y')})"
    )
    elementos.append(Paragraph(topo, small))
    elementos.append(Spacer(1, 8))

    dados = [[
        Paragraph("<b>Item</b>", small_bold),
        Paragraph("<b>Descrição</b>", small_bold),
        Paragraph("<b>Qtd</b>", small_bold),
        Paragraph("<b>Custo Unitário</b>", small_bold),
        Paragraph("<b>Total</b>", small_bold),
    ]]
    for _, row in df[df["Incluir"]].iterrows():
        dados.append([
            Paragraph(str(row["Item"]), small),
            Paragraph(str(row["Descrição"]), small),
            Paragraph(f"{row['Quantidade']:.0f}", small),
            Paragraph(brl(row["Custo Unitário (R$)"]), small),
            Paragraph(brl(row["Total (R$)"]), small),
        ])
    dados += [
        ["", "", "", Paragraph("<b>Custo Total</b>", small_bold), Paragraph(brl(custo_total), small_bold)],
        ["", "", "", Paragraph("<b>Margem de Lucro</b>", small_bold), Paragraph(brl(margem_valor), small_bold)],
        ["", "", "", Paragraph("<b>Cachê Proposto</b>", small_bold), Paragraph(brl(cache_proposto), small_bold)],
    ]

    col_widths = [60, 210, 40, 90, 90]  # 490pt (cabe na área útil do A4)
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.whitesmoke, colors.white]),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos += [tabela, Spacer(1, 8)]

    elementos.append(Paragraph(f"<b>Condições de Pagamento:</b> {forma_pagto or '—'}", small))
    if observacoes:
        elementos.append(Spacer(1, 4))
        elementos.append(Paragraph(f"<b>Observações:</b> {observacoes}", small))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_pdf_contrato():
    buffer = BytesIO()
    doc_kwargs, small, small_bold, title_style = _pdf_doc_setup()
    doc = SimpleDocTemplate(buffer, **doc_kwargs)

    elementos = []
    elementos.append(Paragraph("<b>Contrato de Prestação de Serviços Musicais</b>", title_style))
    elementos.append(Spacer(1, 6))

    partes = (
        f"<b>Contratante:</b> {contratante_nome or '—'} – CPF/CNPJ: {contratante_doc or '—'}<br/>"
        f"<b>Contratada:</b> {banda_razao} – CNPJ: {banda_cnpj}<br/>"
        f"<b>Representante Legal do CNPJ:</b> {banda_resp_legal or '—'}<br/>"
        f"<b>Responsável pela Banda:</b> {banda_resp_banda or '—'}"
    )
    elementos.append(Paragraph(partes, small))
    elementos.append(Spacer(1, 8))

    info_evento = (
        f"<b>Data:</b> {data_evento.strftime('%d/%m/%Y')} &nbsp;&nbsp; "
        f"<b>Local:</b> {cidade or '—'} &nbsp;&nbsp; "
        f"<b>Nº Convidados:</b> {num_convidados}<br/>"
        f"<b>Horário de Montagem:</b> {hora_montagem or '—'} &nbsp;&nbsp; "
        f"<b>Horário do Show:</b> {hora_show or '—'} &nbsp;&nbsp; "
        f"<b>Local de Apresentação:</b> {local_apresentacao or '—'}"
    )
    elementos.append(Paragraph("<b>Informações do Evento</b>", small_bold))
    elementos.append(Paragraph(info_evento, small))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("<b>Equipamentos e Responsabilidades</b>", small_bold))
    elementos.append(Paragraph(f"<b>Responsabilidade da Banda:</b> {resp_banda}", small))
    elementos.append(Paragraph(f"<b>Responsabilidade da Contratante:</b> {resp_contratante}", small))
    elementos.append(Spacer(1, 6))

    equipe = (
        f"<b>Composição da Equipe da Banda:</b> Integrantes: {num_integrantes}, "
        f"Apoio: {num_apoio}, Acompanhantes: {num_acomp}"
    )
    elementos.append(Paragraph(equipe, small))
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph("<b>Cláusulas</b>", small_bold))
    clausulas = [
        f"1ª. Valor total do serviço: <b>{brl(cache_proposto)}</b> – pagamento: {forma_pagto or '—'}.",
        "2ª. Despesas de transporte: responsabilidade da Contratada.",
        "3ª. Alimentação de banda e equipe: responsabilidade da Contratante.",
        "4ª. Alteração de data: deve ser comunicada por escrito ao responsável indicado.",
        "5ª. O responsável que assina pela Contratante é fiador solidário.",
        "6ª. A Contratante responde por danos aos equipamentos ou integrantes por problemas no local.",
        (f"7ª. Energia elétrica conforme NBR 5410: tomada {energia_tomada}, {energia_tensao}, "
         f"aterramento {energia_aterramento}; distância máxima do palco: {energia_dist_max}."),
        f"8ª. Multa por descumprimento: {multa_perc}% do valor total.",
        f"9ª. Foro: {foro}.",
    ]
    for c in clausulas:
        elementos.append(Paragraph(c, small))
    elementos.append(Spacer(1, 12))

    assinatura_tbl = Table(
        [
            [Paragraph(f"<b>Contratante:</b><br/>{contratante_nome or '______________________'}", small),
             Paragraph(f"<b>Banda RockBuzz / {banda_razao}:</b><br/>{banda_resp_banda or '______________________'}", small)]
        ],
        colWidths=[240, 240]
    )
    assinatura_tbl.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (0, 0), 0.5, colors.black),
        ("LINEABOVE", (1, 0), (1, 0), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elementos.append(assinatura_tbl)

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# Botões de download separados
col_orc, col_ctr = st.columns(2)
with col_orc:
    pdf_orc = gerar_pdf_orcamento(df_calc, custo_total, margem_valor, cache_proposto)
    st.download_button(
        label="⬇️ Baixar PDF — Orçamento",
        data=pdf_orc,
        file_name=f"Rockbuzz_Orcamento_{numero_proposta}.pdf",
        mime="application/pdf",
    )
with col_ctr:
    pdf_ctr = gerar_pdf_contrato()
    st.download_button(
        label="⬇️ Baixar PDF — Contrato",
        data=pdf_ctr,
        file_name=f"Rockbuzz_Contrato_{numero_proposta}.pdf",
        mime="application/pdf",
    )

# =========================
# Histórico (salvar / listar / carregar / apagar / exportar / importar)
# =========================
st.divider()
st.subheader("📜 Histórico de Propostas")

colA, colB, colC = st.columns([1,1,2])

def make_record():
    return {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "numero_proposta": numero_proposta,
        "enviado": enviado,
        "evento": nome_evento,
        "data_evento": str(data_evento),
        "cidade": cidade,
        "custo_total": custo_total,
        "margem_pct": float(margem_pct),
        "cache_proposto": cache_proposto,
        "validade_ate": str(datetime.today().date() + timedelta(days=int(validade_dias))),
        "cond_pagto": forma_pagto,
        "observacoes": observacoes,
        "contratante": {
            "nome": contratante_nome, "doc": contratante_doc,
            "email": contratante_email, "tel": contratante_tel, "end": contratante_end
        },
        "banda": {
            "razao": banda_razao, "cnpj": banda_cnpj,
            "resp_legal": banda_resp_legal, "resp_banda": banda_resp_banda
        },
        "evento_info": {
            "num_convidados": num_convidados, "hora_montagem": hora_montagem,
            "hora_show": hora_show, "local_apresentacao": local_apresentacao
        },
        "responsabilidades": {
            "banda": resp_banda, "contratante": resp_contratante
        },
        "equipe": {
            "integrantes": num_integrantes, "apoio": num_apoio, "acompanhantes": num_acomp
        },
        "energia": {
            "tomada": energia_tomada, "tensao": energia_tensao,
            "aterramento": energia_aterramento, "dist_max": energia_dist_max
        },
        "multa_perc": multa_perc, "foro": foro,
        "itens": df_calc.to_dict(orient="records"),
    }

# Salvar
if colA.button("💾 Salvar no Histórico"):
    st.session_state.history.append(make_record())
    st.success("Proposta salva no histórico.")

# Exportar
hist_json = json.dumps(st.session_state.history, ensure_ascii=False, indent=2)
colB.download_button("⬇️ Exportar Histórico (JSON)", data=hist_json.encode("utf-8"),
                     file_name="rockbuzz_historico.json", mime="application/json")

# Importar
uploaded = colC.file_uploader("Importar Histórico (JSON)", type=["json"])
if uploaded:
    try:
        st.session_state.history = json.loads(uploaded.read().decode("utf-8"))
        st.success("Histórico importado com sucesso.")
    except Exception as e:
        st.error(f"Falha ao importar: {e}")

# Listagem
if st.session_state.history:
    hist_df = pd.DataFrame([{
            "Criado em": r["created_at"],
            "Nº Proposta": r["numero_proposta"],
            "Evento": r["evento"],
            "Data": r["data_evento"],
            "Cidade": r["cidade"],
            "Enviado": "Sim" if r["enviado"] else "Não",
            "Custo Total": brl(r["custo_total"]),
            "Margem (%)": r["margem_pct"],
            "Cachê Proposto": brl(r["cache_proposto"]),
            "Validade até": r["validade_ate"],
            "id": r["id"],
        } for r in st.session_state.history]).sort_values("Criado em", ascending=False)

    st.dataframe(hist_df.drop(columns=["id"]), use_container_width=True, hide_index=True)

    ids = hist_df["id"].tolist()
    escolha = st.selectbox("Selecione uma proposta para carregar/apagar:", options=["—"] + ids)
    ac1, ac2 = st.columns([1,1])
    if escolha != "—":
        # Carregar
        if ac1.button("↩️ Carregar no editor"):
            rec = next((r for r in st.session_state.history if r["id"] == escolha), None)
            if rec:
                st.session_state.df = pd.DataFrame(rec["itens"]).drop(columns=["Total (R$)"], errors="ignore")
                st.session_state["__restore__"] = rec
                st.rerun()
        # Apagar
        if ac2.button("🗑️ Apagar selecionada"):
            st.session_state.history = [r for r in st.session_state.history if r["id"] != escolha]
            st.success("Proposta removida do histórico.")
            st.rerun()
else:
    st.info("Nenhuma proposta salva ainda. Gere um orçamento e clique em **Salvar no Histórico**.")

# Restaura parâmetros ao carregar do histórico
restore = st.session_state.pop("__restore__", None)
if restore:
    margem_pct = restore["margem_pct"]
    nome_evento = restore["evento"]
    data_evento = datetime.fromisoformat(restore["data_evento"]).date()
    cidade = restore["cidade"]
    numero_proposta = restore["numero_proposta"]
    forma_pagto = restore["cond_pagto"]
    observacoes = restore.get("observacoes", "")
    enviado = restore["enviado"]
    # contratante
    contratante = restore["contratante"]
    contratante_nome = contratante.get("nome", "")
    contratante_doc = contratante.get("doc", "")
    contratante_email = contratante.get("email", "")
    contratante_tel = contratante.get("tel", "")
    contratante_end = contratante.get("end", "")
    # banda
    banda = restore["banda"]
    banda_razao = banda.get("razao", "")
    banda_cnpj = banda.get("cnpj", "")
    banda_resp_legal = banda.get("resp_legal", "")
    banda_resp_banda = banda.get("resp_banda", "")
    # evento info
    ev = restore["evento_info"]
    num_convidados = ev.get("num_convidados", 0)
    hora_montagem = ev.get("hora_montagem", "")
    hora_show = ev.get("hora_show", "")
    local_apresentacao = ev.get("local_apresentacao", "")
    # responsabilidades
    resp = restore["responsabilidades"]
    resp_banda = resp.get("banda", "")
    resp_contratante = resp.get("contratante", "")
    # equipe
    equipe = restore["equipe"]
    num_integrantes = equipe.get("integrantes", 0)
    num_apoio = equipe.get("apoio", 0)
    num_acomp = equipe.get("acompanhantes", 0)
    # energia
    eng = restore["energia"]
    energia_tomada = eng.get("tomada", "20A")
    energia_tensao = eng.get("tensao", "220V")
    energia_aterramento = eng.get("aterramento", "Adequado, conforme NBR 5410")
    energia_dist_max = eng.get("dist_max", "10 metros")
    # multa/foro
    multa_perc = restore.get("multa_perc", 50)
    foro = restore.get("foro", "Comarca de Jundiaí/SP")
    st.rerun()

# manter estado de itens
st.session_state.df = edited_df
