# Rockbuzz Pay – Calculadora de Cachê (Versão Aprimorada)
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
# CSS Customizado
# =========================
st.markdown("""
<style>
    /* Estilo do footer */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #0E1117;
        color: #FAFAFA;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
        border-top: 1px solid #262730;
        z-index: 999;
    }
    
    .footer a {
        color: #FF4B4B;
        text-decoration: none;
        font-weight: 600;
    }
    
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Ajuste para evitar sobreposição do conteúdo com o footer */
    .main .block-container {
        padding-bottom: 60px;
    }
    
    /* Melhorias visuais */
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #3D3D3D;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    
    h1 {
        color: #FF4B4B;
        padding-bottom: 10px;
        border-bottom: 2px solid #FF4B4B;
    }
    
    h2 {
        color: #FAFAFA;
        margin-top: 20px;
    }
    
    .success-box {
        background-color: #1F4D2E;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 10px 0;
    }
    
    .info-box {
        background-color: #1E3A5F;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# Helpers & Defaults
# =========================
def brl(x: float) -> str:
    """Formata valor em Real Brasileiro"""
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def default_rows():
    """Retorna template padrão de itens do orçamento"""
    return [
        {"Item": "1. Músicos",              "Descrição": "Pagamento músicos",                                "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "2. Ajudantes/Staff",      "Descrição": "Pagamento de ajudantes (roadies)",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "3. Transporte",           "Descrição": "Aluguel/combustível de carros próprios",           "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "4. Pedágio",              "Descrição": "Custos com pedágios (ida e volta)",                "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "5. Combustível",          "Descrição": "Estimativa ida/volta (média 13 km/L)",             "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "6. Alimentação",          "Descrição": "Refeição completa para equipe",                    "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "7. Hospedagem",           "Descrição": "Caso haja necessidade de pernoite",                "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "8. Som/Luz Kiko",         "Descrição": "PA até 100 pessoas + Monitoramento + Luz",         "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "9. PA Guilherme",         "Descrição": "PA para eventos acima de 100 pessoas",             "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "10. Estrutura Evento",    "Descrição": "Palco, som, luz, telão, treliças",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "11. Técnico de Som",      "Descrição": "Palco/FOH",                                        "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
        {"Item": "12. Outros Custos",       "Descrição": "Equipamentos extras, imprevistos",                 "Quantidade": 0, "Custo Unitário (R$)": 0.00, "Incluir": True},
    ]

def ensure_state():
    """Inicializa estado da sessão"""
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame(default_rows())
    if "history" not in st.session_state:
        st.session_state.history = []

ensure_state()

# =========================
# Sidebar – Configurações
# =========================
with st.sidebar:
    st.image("https://github.com/murillomartins101/Rockbuzz-Pay/blob/65be9ca11db1977a1154e215ba2954bb537a4a6f/LOGO%20DEFINITIVO%20FUNDO%20ESCURO.png", use_container_width=True)
    st.markdown("---")
    
    # Parâmetros Gerais
    with st.expander("⚙️ Parâmetros Gerais", expanded=True):
        margem_pct = st.number_input("Margem de Lucro (%)", min_value=0.0, max_value=200.0, value=30.0, step=5.0)
    
    # Dados do Evento
    with st.expander("📅 Dados do Evento", expanded=True):
        nome_evento = st.text_input("Evento/Cliente", value="", placeholder="Ex: Festa Corporativa XYZ")
        data_evento = st.date_input("Data do evento", value=datetime.today())
        cidade = st.text_input("Cidade/Local", value="", placeholder="Ex: Jundiaí/SP")
    
    # Orçamento
    with st.expander("📄 Informações do Orçamento", expanded=False):
        numero_proposta = st.text_input("Nº da Proposta", value=datetime.now().strftime("RB-%Y%m%d-%H%M"))
        validade_dias = st.number_input("Validade (dias)", min_value=1, max_value=90, value=7, step=1)
        forma_pagto = st.text_input("Condições de Pagamento", value="50% na assinatura + 50% no dia do evento")
        observacoes = st.text_area("Observações", value="", height=100)
        enviado = st.checkbox("✅ Marcar como ENVIADO", value=False)
    
    # Contratante
    with st.expander("👤 Dados do Contratante", expanded=False):
        contratante_nome = st.text_input("Nome/Razão Social", value="")
        contratante_doc = st.text_input("CNPJ/CPF", value="")
        contratante_email = st.text_input("E-mail", value="")
        contratante_tel = st.text_input("Telefone", value="")
        contratante_end = st.text_area("Endereço", value="", height=80)
    
    # Banda
    with st.expander("🎸 Dados da Banda", expanded=False):
        banda_razao = st.text_input("Razão Social", value="Aditivo Media Management")
        banda_cnpj = st.text_input("CNPJ", value="40.157.297/0001-18")
        banda_resp_legal = st.text_input("Representante Legal", value="")
        banda_resp_banda = st.text_input("Responsável pela Banda", value="")
    
    # Detalhes do Evento
    with st.expander("🎤 Detalhes do Evento", expanded=False):
        num_convidados = st.number_input("Número de Convidados", min_value=0, step=10, value=0)
        hora_montagem = st.text_input("Horário de Montagem", value="", placeholder="Ex: 18:00")
        hora_show = st.text_input("Horário do Show", value="", placeholder="Ex: 21:00")
        local_apresentacao = st.text_input("Local de Apresentação", value="")
    
    # Responsabilidades
    with st.expander("📋 Equipamentos e Responsabilidades", expanded=False):
        resp_banda = st.text_area("Responsabilidade da Banda", value="Sonorização e iluminação do show", height=80)
        resp_contratante = st.text_area("Responsabilidade da Contratante", value="Som mecânico para a festa", height=80)
    
    # Equipe
    with st.expander("👥 Composição da Equipe", expanded=False):
        num_integrantes = st.number_input("Integrantes", min_value=0, value=0)
        num_apoio = st.number_input("Equipe de Apoio", min_value=0, value=0)
        num_acomp = st.number_input("Acompanhantes", min_value=0, value=0)
    
    # Energia
    with st.expander("⚡ Requisitos de Energia (NBR 5410)", expanded=False):
        energia_tomada = st.text_input("Tomada", value="20A")
        energia_tensao = st.text_input("Tensão", value="220V")
        energia_aterramento = st.text_input("Aterramento", value="Adequado, conforme NBR 5410")
        energia_dist_max = st.text_input("Distância máx. do palco", value="10 metros")
    
    # Cláusulas Legais
    with st.expander("⚖️ Cláusulas Contratuais", expanded=False):
        multa_perc = st.number_input("Multa por descumprimento (%)", min_value=0, max_value=100, value=50)
        foro = st.text_input("Foro", value="Comarca de Jundiaí/SP")

# =========================
# Conteúdo Principal
# =========================
st.title("🎸 Rockbuzz Pay")
st.markdown("**Calculadora de Cachê e Gerador de Contratos Profissionais**")
st.markdown("---")

# Instruções
with st.expander("ℹ️ Como usar", expanded=False):
    st.markdown("""
    1. **Configure os parâmetros** na barra lateral (margem de lucro, dados do evento, etc.)
    2. **Edite a tabela abaixo** com as quantidades e valores dos itens
    3. **Marque "Incluir"** nos itens que devem ser considerados no cálculo
    4. **Visualize o resumo** com os valores calculados automaticamente
    5. **Baixe os PDFs** de Orçamento e Contrato separadamente
    6. **Salve no histórico** para consultas futuras
    """)

st.subheader("💼 Itens do Orçamento")
st.caption("Adicione, remova ou edite os itens conforme necessário. Marque 'Incluir' para considerar no cálculo.")

# Editor de itens
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    column_order=["Item", "Descrição", "Quantidade", "Custo Unitário (R$)", "Incluir"],
    column_config={
        "Item": st.column_config.TextColumn("Item", width="small"),
        "Descrição": st.column_config.TextColumn("Descrição", width="large"),
        "Quantidade": st.column_config.NumberColumn("Qtd", format="%.0f", step=1.0, min_value=0.0, width="small"),
        "Custo Unitário (R$)": st.column_config.NumberColumn("Valor Unit.", format="R$ %.2f", step=50.0, min_value=0.0, width="medium"),
        "Incluir": st.column_config.CheckboxColumn("Incluir", width="small"),
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
# Resumo Financeiro
# =========================
st.markdown("---")
st.subheader("💰 Resumo Financeiro")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Custo Total", brl(custo_total))
with col2:
    st.metric("Margem de Lucro", brl(margem_valor), f"{margem_pct:.0f}%")
with col3:
    st.metric("💵 Cachê Proposto", brl(cache_proposto))
with col4:
    st.metric("Validade", f"{validade_dias} dias", f"até {data_validade.strftime('%d/%m/%Y')}")

# Informações adicionais
info_cols = st.columns(3)
with info_cols[0]:
    st.info(f"**Evento:** {nome_evento or 'Não informado'}")
with info_cols[1]:
    st.info(f"**Data:** {data_evento.strftime('%d/%m/%Y')}")
with info_cols[2]:
    st.info(f"**Local:** {cidade or 'Não informado'}")

# =========================
# Geração de PDFs
# =========================
def _pdf_doc_setup():
    doc_kwargs = dict(pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    small = ParagraphStyle(name="small", parent=styles["Normal"], fontSize=9, leading=11)
    small_bold = ParagraphStyle(name="small_bold", parent=styles["Normal"], fontSize=9, leading=11, fontName="Helvetica-Bold")
    title_style = ParagraphStyle(name="title", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#FF4B4B"))
    return doc_kwargs, small, small_bold, title_style

def gerar_pdf_orcamento(df, custo_total, margem_valor, cache_proposto):
    buffer = BytesIO()
    doc_kwargs, small, small_bold, title_style = _pdf_doc_setup()
    doc = SimpleDocTemplate(buffer, **doc_kwargs)

    elementos = []
    elementos.append(Paragraph("<b>Rockbuzz Pay – Orçamento</b>", title_style))
    elementos.append(Spacer(1, 6))
    
    topo = (
        f"<b>Nº Proposta:</b> {numero_proposta} &nbsp;&nbsp; "
        f"<b>Status:</b> {'✅ ENVIADO' if enviado else '📝 RASCUNHO'}<br/>"
        f"<b>Evento:</b> {nome_evento or '—'} &nbsp;&nbsp; "
        f"<b>Data:</b> {data_evento.strftime('%d/%m/%Y')} &nbsp;&nbsp; "
        f"<b>Cidade:</b> {cidade or '—'}<br/>"
        f"<b>Validade:</b> {validade_dias} dia(s) (até {data_validade.strftime('%d/%m/%Y')})"
    )
    elementos.append(Paragraph(topo, small))
    elementos.append(Spacer(1, 10))

    dados = [[
        Paragraph("<b>Item</b>", small_bold),
        Paragraph("<b>Descrição</b>", small_bold),
        Paragraph("<b>Qtd</b>", small_bold),
        Paragraph("<b>Valor Unit.</b>", small_bold),
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
        ["", "", "", Paragraph("<b>Margem de Lucro ({:.0f}%)</b>".format(margem_pct), small_bold), Paragraph(brl(margem_valor), small_bold)],
        ["", "", "", Paragraph("<b>Cachê Proposto</b>", small_bold), Paragraph(brl(cache_proposto), small_bold)],
    ]

    col_widths = [60, 210, 40, 90, 90]
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF4B4B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.whitesmoke, colors.white]),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos += [tabela, Spacer(1, 12)]

    elementos.append(Paragraph(f"<b>Condições de Pagamento:</b> {forma_pagto or '—'}", small))
    if observacoes:
        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph(f"<b>Observações:</b> {observacoes}", small))
    
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("<i>Desenvolvido por Aditivo Media</i>", small))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_pdf_contrato():
    buffer = BytesIO()
    doc_kwargs, small, small_bold, title_style = _pdf_doc_setup()
    doc = SimpleDocTemplate(buffer, **doc_kwargs)

    elementos = []
    elementos.append(Paragraph("<b>Contrato de Prestação de Serviços Musicais</b>", title_style))
    elementos.append(Spacer(1, 8))

    partes = (
        f"<b>CONTRATANTE:</b> {contratante_nome or '—'} – CPF/CNPJ: {contratante_doc or '—'}<br/>"
        f"Endereço: {contratante_end or '—'}<br/>"
        f"E-mail: {contratante_email or '—'} – Telefone: {contratante_tel or '—'}<br/><br/>"
        f"<b>CONTRATADA:</b> {banda_razao} – CNPJ: {banda_cnpj}<br/>"
        f"Representante Legal: {banda_resp_legal or '—'}<br/>"
        f"Responsável pela Banda: {banda_resp_banda or '—'}"
    )
    elementos.append(Paragraph(partes, small))
    elementos.append(Spacer(1, 10))

    info_evento = (
        f"<b>INFORMAÇÕES DO EVENTO</b><br/>"
        f"Data: {data_evento.strftime('%d/%m/%Y')} | Local: {cidade or '—'} | Nº Convidados: {num_convidados}<br/>"
        f"Horário Montagem: {hora_montagem or '—'} | Horário Show: {hora_show or '—'}<br/>"
        f"Local de Apresentação: {local_apresentacao or '—'}"
    )
    elementos.append(Paragraph(info_evento, small))
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph("<b>EQUIPAMENTOS E RESPONSABILIDADES</b>", small_bold))
    elementos.append(Paragraph(f"<b>Responsabilidade da Banda:</b> {resp_banda}", small))
    elementos.append(Paragraph(f"<b>Responsabilidade da Contratante:</b> {resp_contratante}", small))
    elementos.append(Spacer(1, 8))

    equipe = (
        f"<b>COMPOSIÇÃO DA EQUIPE:</b> Integrantes: {num_integrantes} | "
        f"Apoio: {num_apoio} | Acompanhantes: {num_acomp}"
    )
    elementos.append(Paragraph(equipe, small))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("<b>CLÁUSULAS CONTRATUAIS</b>", small_bold))
    elementos.append(Spacer(1, 4))
    
    clausulas = [
        f"<b>1ª.</b> Valor total do serviço: <b>{brl(cache_proposto)}</b> – Pagamento: {forma_pagto or '—'}.",
        "<b>2ª.</b> Despesas de transporte: responsabilidade da Contratada.",
        "<b>3ª.</b> Alimentação de banda e equipe: responsabilidade da Contratante.",
        "<b>4ª.</b> Alteração de data: deve ser comunicada por escrito ao responsável indicado.",
        "<b>5ª.</b> O responsável que assina pela Contratante é fiador solidário.",
        "<b>6ª.</b> A Contratante responde por danos aos equipamentos ou integrantes por problemas no local.",
        (f"<b>7ª.</b> Energia elétrica conforme NBR 5410: tomada {energia_tomada}, {energia_tensao}, "
         f"aterramento {energia_aterramento}; distância máxima do palco: {energia_dist_max}."),
        f"<b>8ª.</b> Multa por descumprimento: {multa_perc}% do valor total.",
        f"<b>9ª.</b> Foro: {foro}.",
    ]
    
    for c in clausulas:
        elementos.append(Paragraph(c, small))
        elementos.append(Spacer(1, 3))
    
    elementos.append(Spacer(1, 15))

    assinatura_tbl = Table(
        [
            [Paragraph(f"<b>Contratante:</b><br/><br/>{contratante_nome or '________________________________'}<br/>{contratante_doc or ''}", small),
             Paragraph(f"<b>Banda RockBuzz / {banda_razao}:</b><br/><br/>{banda_resp_banda or '________________________________'}", small)]
        ],
        colWidths=[240, 240]
    )
    assinatura_tbl.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (0, 0), 1, colors.black),
        ("LINEABOVE", (1, 0), (1, 0), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elementos.append(assinatura_tbl)
    
    elementos.append(Spacer(1, 15))
    elementos.append(Paragraph("<i>Desenvolvido por Aditivo Media</i>", small))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# Botões de download
st.markdown("---")
st.subheader("📥 Gerar Documentos")

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    pdf_orc = gerar_pdf_orcamento(df_calc, custo_total, margem_valor, cache_proposto)
    st.download_button(
        label="📄 Baixar PDF – Orçamento",
        data=pdf_orc,
        file_name=f"Rockbuzz_Orcamento_{numero_proposta}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
with col_btn2:
    pdf_ctr = gerar_pdf_contrato()
    st.download_button(
        label="📝 Baixar PDF – Contrato",
        data=pdf_ctr,
        file_name=f"Rockbuzz_Contrato_{numero_proposta}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# =========================
# Histórico
# =========================
st.markdown("---")
st.subheader("📜 Histórico de Propostas")

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
        "validade_ate": str(data_validade),
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
        "responsabilidades": {"banda": resp_banda, "contratante": resp_contratante},
        "equipe": {"integrantes": num_integrantes, "apoio": num_apoio, "acompanhantes": num_acomp},
        "energia": {
            "tomada": energia_tomada, "tensao": energia_tensao,
            "aterramento": energia_aterramento, "dist_max": energia_dist_max
        },
        "multa_perc": multa_perc, "foro": foro,
        "itens": df_calc.to_dict(orient="records"),
    }

colA, colB, colC = st.columns([1,1,2])

if colA.button("💾 Salvar no Histórico", use_container_width=True):
    st.session_state.history.append(make_record())
    st.success("✅ Proposta salva com sucesso!")

hist_json = json.dumps(st.session_state.history, ensure_ascii=False, indent=2)
colB.download_button(
    "⬇️ Exportar Histórico",
    data=hist_json.encode("utf-8"),
    file_name="rockbuzz_historico.json",
    mime="application/json",
    use_container_width=True
)

uploaded = colC.file_uploader("📤 Importar Histórico (JSON)", type=["json"])
if uploaded:
    try:
        st.session_state.history = json.loads(uploaded.read().decode("utf-8"))
        st.success("✅ Histórico importado com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Falha ao importar: {e}")

st.markdown("---")

# Listagem do histórico
if st.session_state.history:
    hist_df = pd.DataFrame([{
        "Criado em": datetime.fromisoformat(r["created_at"]).strftime("%d/%m/%Y %H:%M"),
        "Nº Proposta": r["numero_proposta"],
        "Evento": r["evento"] or "—",
        "Data": datetime.fromisoformat(r["data_evento"]).strftime("%d/%m/%Y"),
        "Cidade": r["cidade"] or "—",
        "Status": "✅ Enviado" if r["enviado"] else "📝 Rascunho",
        "Custo Total": brl(r["custo_total"]),
        "Margem": f"{r['margem_pct']:.0f}%",
        "Cachê": brl(r["cache_proposto"]),
        "Validade": datetime.fromisoformat(r["validade_ate"]).strftime("%d/%m/%Y"),
        "id": r["id"],
    } for r in st.session_state.history]).sort_values("Criado em", ascending=False)

    st.dataframe(
        hist_df.drop(columns=["id"]), 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Criado em": st.column_config.TextColumn("Criado em", width="medium"),
            "Nº Proposta": st.column_config.TextColumn("Nº Proposta", width="medium"),
            "Evento": st.column_config.TextColumn("Evento", width="large"),
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Cidade": st.column_config.TextColumn("Cidade", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Custo Total": st.column_config.TextColumn("Custo Total", width="small"),
            "Margem": st.column_config.TextColumn("Margem", width="small"),
            "Cachê": st.column_config.TextColumn("Cachê", width="small"),
            "Validade": st.column_config.TextColumn("Validade", width="small"),
        }
    )

    st.markdown("#### Gerenciar Propostas")
    ids = hist_df["id"].tolist()
    escolha = st.selectbox(
        "Selecione uma proposta:",
        options=["— Selecione —"] + ids,
        format_func=lambda x: "— Selecione —" if x == "— Selecione —" else hist_df[hist_df["id"]==x]["Nº Proposta"].values[0] + f" - {hist_df[hist_df['id']==x]['Evento'].values[0]}"
    )
    
    ac1, ac2 = st.columns([1, 1])
    
    if escolha != "— Selecione —":
        if ac1.button("🔄 Carregar no Editor", use_container_width=True):
            rec = next((r for r in st.session_state.history if r["id"] == escolha), None)
            if rec:
                st.session_state.df = pd.DataFrame(rec["itens"]).drop(columns=["Total (R$)"], errors="ignore")
                st.session_state["__restore__"] = rec
                st.success("✅ Proposta carregada! Atualizando...")
                st.rerun()
        
        if ac2.button("🗑️ Apagar Proposta", use_container_width=True):
            st.session_state.history = [r for r in st.session_state.history if r["id"] != escolha]
            st.success("✅ Proposta removida do histórico!")
            st.rerun()
else:
    st.info("📝 Nenhuma proposta salva ainda. Crie um orçamento e clique em **Salvar no Histórico**.")

# =========================
# Restaurar dados ao carregar
# =========================
restore = st.session_state.pop("__restore__", None)
if restore:
    # Atualizar todas as variáveis da sidebar
    margem_pct = restore["margem_pct"]
    nome_evento = restore["evento"]
    data_evento = datetime.fromisoformat(restore["data_evento"]).date()
    cidade = restore["cidade"]
    numero_proposta = restore["numero_proposta"]
    forma_pagto = restore["cond_pagto"]
    observacoes = restore.get("observacoes", "")
    enviado = restore["enviado"]
    
    # Contratante
    contratante = restore["contratante"]
    contratante_nome = contratante.get("nome", "")
    contratante_doc = contratante.get("doc", "")
    contratante_email = contratante.get("email", "")
    contratante_tel = contratante.get("tel", "")
    contratante_end = contratante.get("end", "")
    
    # Banda
    banda = restore["banda"]
    banda_razao = banda.get("razao", "")
    banda_cnpj = banda.get("cnpj", "")
    banda_resp_legal = banda.get("resp_legal", "")
    banda_resp_banda = banda.get("resp_banda", "")
    
    # Evento info
    ev = restore["evento_info"]
    num_convidados = ev.get("num_convidados", 0)
    hora_montagem = ev.get("hora_montagem", "")
    hora_show = ev.get("hora_show", "")
    local_apresentacao = ev.get("local_apresentacao", "")
    
    # Responsabilidades
    resp = restore["responsabilidades"]
    resp_banda = resp.get("banda", "")
    resp_contratante = resp.get("contratante", "")
    
    # Equipe
    equipe = restore["equipe"]
    num_integrantes = equipe.get("integrantes", 0)
    num_apoio = equipe.get("apoio", 0)
    num_acomp = equipe.get("acompanhantes", 0)
    
    # Energia
    eng = restore["energia"]
    energia_tomada = eng.get("tomada", "20A")
    energia_tensao = eng.get("tensao", "220V")
    energia_aterramento = eng.get("aterramento", "Adequado, conforme NBR 5410")
    energia_dist_max = eng.get("dist_max", "10 metros")
    
    # Multa/foro
    multa_perc = restore.get("multa_perc", 50)
    foro = restore.get("foro", "Comarca de Jundiaí/SP")

# Manter estado de itens editados
st.session_state.df = edited_df

# =========================
# Footer
# =========================
st.markdown("""
<div class="footer">
    Desenvolvido por <a href="https://aditivomedia.com" target="_blank">Aditivo Media</a>
</div>
""", unsafe_allow_html=True)