#!/usr/bin/env python3
"""Gera o PDF do e-book 'Rotina básica por tipo de pele' (Produto Skincare).

Visual: creme + serif (padrão do site). Uso:
    $MIMO_PYTHON newsletter/build_ebook.py
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable,
)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "rotina-basica-por-tipo-de-pele.pdf")

# --- marca do site ---
CREME = colors.HexColor("#f9f7f2")
CREME_ESCURO = colors.HexColor("#f1ede2")
TINTA = colors.HexColor("#2b2822")     # texto principal, quase preto quente
TINTA_FRACA = colors.HexColor("#6b6459")
OURO = colors.HexColor("#b08d57")      # acento dourado
FILETE = colors.HexColor("#d8cfbc")

FDIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Georgia", os.path.join(FDIR, "georgia.ttf")))
pdfmetrics.registerFont(TTFont("Georgia-Bold", os.path.join(FDIR, "georgiab.ttf")))
pdfmetrics.registerFont(TTFont("Georgia-Italic", os.path.join(FDIR, "georgiai.ttf")))
pdfmetrics.registerFont(TTFont("Calibri", os.path.join(FDIR, "calibri.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-Bold", os.path.join(FDIR, "calibrib.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-Italic", os.path.join(FDIR, "calibrii.ttf")))

W, H = A4
MARGIN = 22 * mm

# --- estilos ---
st_capa_eyebrow = ParagraphStyle("capa_eyebrow", fontName="Calibri", fontSize=11,
    textColor=OURO, alignment=TA_CENTER, leading=16, spaceAfter=6)
st_capa_titulo = ParagraphStyle("capa_titulo", fontName="Georgia-Bold", fontSize=34,
    textColor=TINTA, alignment=TA_CENTER, leading=42)
st_capa_sub = ParagraphStyle("capa_sub", fontName="Georgia-Italic", fontSize=15,
    textColor=TINTA_FRACA, alignment=TA_CENTER, leading=22)
st_capa_marca = ParagraphStyle("capa_marca", fontName="Calibri", fontSize=11,
    textColor=TINTA_FRACA, alignment=TA_CENTER, leading=16)

st_h1 = ParagraphStyle("h1", fontName="Georgia-Bold", fontSize=19, textColor=TINTA,
    leading=26, spaceBefore=2, spaceAfter=8)
st_h2 = ParagraphStyle("h2", fontName="Georgia-Bold", fontSize=13.5, textColor=TINTA,
    leading=19, spaceBefore=10, spaceAfter=5)
st_body = ParagraphStyle("body", fontName="Calibri", fontSize=10.5, textColor=TINTA,
    leading=15.5, spaceAfter=6)
st_lead = ParagraphStyle("lead", fontName="Georgia-Italic", fontSize=11.5,
    textColor=TINTA_FRACA, leading=17, spaceAfter=8)
st_bullet = ParagraphStyle("bullet", parent=st_body, leftIndent=12, bulletIndent=2,
    spaceAfter=3)
st_small = ParagraphStyle("small", fontName="Calibri", fontSize=8.5,
    textColor=TINTA_FRACA, leading=12, spaceAfter=4)
st_disclaimer = ParagraphStyle("disclaimer", fontName="Calibri-Italic", fontSize=8.5,
    textColor=TINTA_FRACA, leading=12, spaceAfter=3)
st_tbl = ParagraphStyle("tbl", fontName="Calibri", fontSize=9.5, textColor=TINTA,
    leading=13)
st_tbl_head = ParagraphStyle("tbl_head", fontName="Calibri-Bold", fontSize=9.5,
    textColor=CREME, leading=13)
st_quote = ParagraphStyle("quote", fontName="Georgia-Italic", fontSize=11,
    textColor=TINTA, leading=16, leftIndent=10, rightIndent=10, spaceAfter=8)

def P(text, style=st_body):
    return Paragraph(text, style)

def bullets(items, style=st_bullet):
    return [Paragraph(f"• {it}", style) for it in items]

def tabela_cabecalho(dados, larguras):
    """Tabela com cabeçalho escuro e linhas alternadas creme."""
    linhas = [[Paragraph(c, st_tbl_head) for c in dados[0]]]
    for r in dados[1:]:
        linhas.append([Paragraph(c, st_tbl) for c in r])
    t = Table(linhas, colWidths=larguras, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TINTA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREME]),
        ("GRID", (0, 0), (-1, -1), 0.4, FILETE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

def rotina_tabela(linhas):
    dados = [["Passo", "O que usar", "Por quê"]] + linhas
    return tabela_cabecalho(dados, [22*mm, 52*mm, 92*mm])

def ativos_tabela(linhas):
    dados = [["Ativo", "O que faz", "Quando usar"]] + linhas
    return tabela_cabecalho(dados, [30*mm, 88*mm, 48*mm])

def box_aviso(texto):
    """Caixa de aviso com filete dourado à esquerda."""
    t = Table([[Paragraph(texto, st_quote)]], colWidths=[166*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREME),
        ("LINEBEFORE", (0, 0), (0, -1), 2, OURO),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t

# --- capa (canvas) ---
def desenhar_capa(c: rl_canvas.Canvas):
    c.setFillColor(CREME)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # filete superior
    c.setStrokeColor(OURO)
    c.setLineWidth(1.2)
    c.line(22*mm, H - 18*mm, W - 22*mm, H - 18*mm)
    # monograma
    c.setFillColor(TINTA)
    c.setFont("Georgia-Bold", 16)
    c.drawCentredString(W/2, H - 34*mm, "PS")
    c.setFont("Calibri", 9)
    c.setFillColor(TINTA_FRACA)
    c.drawCentredString(W/2, H - 41*mm, "PRODUTO SKINCARE")
    # eyebrow
    c.setFont("Calibri", 11)
    c.setFillColor(OURO)
    c.drawCentredString(W/2, H - 68*mm, "GUIA PRÁTICO  ·  EDIÇÃO 2026")
    # título
    c.setFillColor(TINTA)
    c.setFont("Georgia-Bold", 33)
    c.drawCentredString(W/2, H - 88*mm, "Rotina básica")
    c.drawCentredString(W/2, H - 103*mm, "por tipo de pele")
    # subtítulo
    c.setFont("Georgia-Italic", 13)
    c.setFillColor(TINTA_FRACA)
    c.drawCentredString(W/2, H - 118*mm, "O essencial, bem feito — de manhã e à noite,")
    c.drawCentredString(W/2, H - 126*mm, "para pele oleosa, seca, mista e normal.")
    # filete central
    c.setStrokeColor(FILETE)
    c.setLineWidth(0.8)
    c.line(W/2 - 30*mm, H - 142*mm, W/2 + 30*mm, H - 142*mm)
    # promessa
    c.setFont("Calibri", 10)
    c.setFillColor(TINTA_FRACA)
    c.drawCentredString(W/2, H - 154*mm, "Sem rotinas de dez passos. Sem promessas milagrosas.")
    c.drawCentredString(W/2, H - 161*mm, "Só os hábitos que fazem diferença, com base no que a ciência mostra.")
    # rodapé da capa
    c.setStrokeColor(OURO)
    c.setLineWidth(1.2)
    c.line(22*mm, 30*mm, W - 22*mm, 30*mm)
    c.setFont("Calibri", 9)
    c.setFillColor(TINTA_FRACA)
    c.drawCentredString(W/2, 22*mm, "produtoskincare.com.br  ·  Sua pele. Seu próprio ritual.")
    c.showPage()

# --- chrome: rodapé das páginas internas ---
def chrome(c: rl_canvas.Canvas, doc):
    c.saveState()
    # faixa de fundo sutil
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(FILETE)
    c.setLineWidth(0.6)
    c.line(MARGIN, 16*mm, W - MARGIN, 16*mm)
    c.setFont("Calibri", 8)
    c.setFillColor(TINTA_FRACA)
    c.drawString(MARGIN, 11*mm, "Produto Skincare · Rotina básica por tipo de pele")
    c.drawRightString(W - MARGIN, 11*mm, f"{doc.page}")
    c.restoreState()

# --- conteúdo ---
def construir_story():
    s = []
    A = s.append

    # Boas-vindas
    A(P("Boas-vindas", st_h1))
    A(P("Cuidar da pele não precisa ser complicado. A maior parte do resultado vem de "
        "três hábitos simples, repetidos todos os dias, com produtos adequados ao seu "
        "tipo de pele.", st_lead))
    A(P("Este guia mostra exatamente isso: a rotina básica — de manhã e à noite — para "
        "cada um dos quatro tipos de pele (oleosa, seca, mista e normal), com os erros "
        "mais comuns e os ingredientes que realmente têm evidência."))
    A(P("Sem rotinas de dez passos. Sem promessas milagrosas. Só o essencial, bem feito."))
    A(Spacer(1, 4*mm))
    A(box_aviso("Tipo de pele é uma classificação cosmética, não um diagnóstico médico. "
        "Se tem acne intensa, lesões, dor ou irritação persistente, procure um "
        "dermatologista."))
    A(PageBreak())

    # Descobrir o tipo de pele
    A(P("Antes de começar: qual é o seu tipo de pele?", st_h1))
    A(P("Não existe um teste padrão — e a oleosidade muda conforme a região do rosto e "
        "a estação do ano. Ainda assim, os sinais abaixo costumam dar uma boa ideia."))
    A(Spacer(1, 2*mm))
    A(tabela_cabecalho([
        ["Tipo de pele", "Sinais principais"],
        ["Oleosa", "Brilho constante na testa, nariz e queixo · Poros dilatados · "
                   "Cravos e espinhas com frequência · Maquiagem \"escorrega\" em poucas horas"],
        ["Seca", "Repuxa depois de lavar o rosto · Descama (nariz, ao redor da boca) · "
                 "Fosca, sem brilho natural · Linhas finas mais visíveis"],
        ["Mista", "Brilho na zona T, mas não nas bochechas · Poros mais abertos no nariz · "
                  "Bochechas normais ou secas · Cravos só no nariz"],
        ["Normal", "Brilho suave e uniforme · Poros finos · Sem descamação nem sebo "
                   "excessivo · Tolera bem a maioria dos produtos"],
    ], [26*mm, 140*mm]))
    A(Spacer(1, 4*mm))
    A(P("Em dúvida? O quiz gratuito do Produto Skincare responde em poucas perguntas: "
        "<b>produtoskincare.com.br/provador</b>"))
    A(Spacer(1, 6*mm))

    # Esqueleto universal
    A(P("O esqueleto de toda rotina básica", st_h1))
    A(P("Toda rotina básica tem quatro movimentos — e só o último é exclusivo da manhã:"))
    A(tabela_cabecalho([
        ["Movimento", "O que faz", "Manhã", "Noite"],
        ["1. Limpeza", "Remove sebo, poluição e resíduos", "Sim", "Sim"],
        ["2. Tratamento", "Atua em uma preocupação específica (brilho, manchas, linhas finas)",
         "Opcional", "Opcional"],
        ["3. Hidratação", "Mantém a barreira da pele funcionando", "Sim", "Sim"],
        ["4. Proteção", "Protetor solar FPS 50+ — o antienvelhecimento com melhor evidência",
         "Sim", "—"],
    ], [28*mm, 84*mm, 27*mm, 27*mm]))
    A(Spacer(1, 4*mm))
    A(P("<b>Três regras que valem para todo mundo:</b>"))
    for b in bullets([
        "Lave o rosto <b>2 vezes por dia</b>, com produto suave. Lavar mais não ajuda — e pode irritar.",
        "<b>Nunca pule o protetor solar.</b> Num ensaio de 4,5 anos, o uso diário reduziu o "
        "envelhecimento da pele.",
        "Mude <b>um produto por vez</b>. Assim você sabe o que funciona e o que irrita.",
    ]):
        A(b)
    A(PageBreak())

    # ---------- Capítulo 1: oleosa ----------
    A(P("Capítulo 1 — Pele oleosa", st_h1))
    A(P("A pele oleosa produz mais sebo. Isso dá brilho, deixa os poros mais aparentes e "
        "favorece cravos e espinhas. O segredo é <b>equilibrar, não atacar</b>: limpeza "
        "agressiva resseca e irrita, sem reduzir a oleosidade.", st_lead))
    A(P("Manhã", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Gel de limpeza suave, pH próximo ao da pele",
         "Remove o sebo noturno sem agredir a barreira"],
        ["Tratamento", "Niacinamida (com ou sem zinco)",
         "Reduziu o sebo em estudos e ajuda a uniformizar o tom"],
        ["Hidratação", "Gel hidratante oil-free",
         "Hidrata sem pesar — sim, pele oleosa precisa de hidratante"],
        ["Protetor", "Protetor toque seco FPS 50+", "Protege sem dar brilho extra"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Noite", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Gel de limpeza (dupla limpeza se usa maquiagem)",
         "Remove poluição, sebo e resíduos do dia"],
        ["Tratamento", "BHA (ácido salicílico 2%) ou retinol",
         "Desobstruem os poros; comece 2x por semana"],
        ["Hidratação", "Gel hidratante leve", "Mantém a barreira hidratada durante a noite"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Erros comuns", st_h2))
    for b in bullets([
        "Lavar o rosto mais de 2x por dia — não traz vantagem e pode irritar.",
        "Pular hidratante: a falta dele não reduz o sebo, e hidratar ajuda a pele a "
        "tolerar tratamentos para acne, que costumam ressecar.",
        "Tônicos com muito álcool, se ardem ou ressecam.",
        "Esfregar com esponja ou escova — o atrito irrita a pele.",
    ]):
        A(b)
    A(Spacer(1, 3*mm))
    A(P("Ativos que funcionam", st_h2))
    A(ativos_tabela([
        ["Niacinamida", "Reduz o sebo", "Manhã e noite"],
        ["Ácido salicílico (BHA)", "Desobstrui os poros", "Noite (comece 2x/semana)"],
        ["Retinol", "Recomendação forte nas diretrizes de acne (retinoides tópicos)",
         "Só à noite, comece devagar"],
        ["Argila", "Absorve o sebo da superfície (não muda a produção)",
         "Máscara 1–2x/semana, só zona T"],
    ]))
    A(PageBreak())

    # ---------- Capítulo 2: seca ----------
    A(P("Capítulo 2 — Pele seca", st_h1))
    A(P("A pele seca tem pouca oleosidade e segura menos água. Pode repuxar, descamar ou "
        "ficar áspera — especialmente no frio e com ar seco. O segredo é <b>hidratar bem "
        "e repor os lipídios da barreira</b>.", st_lead))
    A(P("Manhã", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Loção ou creme de limpeza suave",
         "Limpadores suaves agridem menos os lipídios da pele"],
        ["Tratamento", "Sérum de ácido hialurônico",
         "Atrai e retém água; aplique antes do hidratante"],
        ["Hidratação", "Creme com ceramidas e karité", "Repõe os lipídios da barreira"],
        ["Protetor", "Protetor solar hidratante FPS 50+", "Protege e mantém a hidratação"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Noite", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Água micelar ou óleo de limpeza", "Remove impurezas de forma suave"],
        ["Tratamento", "Retinol suave ou peptídeos",
         "O retinol melhorou rugas finas num ensaio; irrita menos que os de receita"],
        ["Hidratação", "Creme rico com ceramidas",
         "Quanto mais seca a pele, mais rica em lipídios deve ser a fórmula"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Erros comuns", st_h2))
    for b in bullets([
        "Sabonete comum no rosto — tende a agredir a barreira e alterar o pH da pele.",
        "Lavar com água quente: aumenta a irritação causada por detergentes.",
        "Esfregar com a toalha — seque com delicadeza.",
        "Pular hidratante no verão. A pele seca precisa o ano inteiro.",
    ]):
        A(b)
    A(Spacer(1, 3*mm))
    A(P("Ativos que funcionam", st_h2))
    A(ativos_tabela([
        ["Ceramidas", "Repõe lipídios da barreira", "Manhã e noite"],
        ["Ácido hialurônico", "Atrai e retém água", "Antes do hidratante"],
        ["Pantenol (B5)", "Hidrata e ajuda a barreira", "Manhã e noite"],
        ["Ureia", "Melhor evidência para pele muito ressecada", "Conforme o produto"],
        ["Ácido láctico (AHA)", "Esfolia e alisa, mas pode arder",
         "1–2x/semana, comece devagar"],
    ]))
    A(PageBreak())

    # ---------- Capítulo 3: mista ----------
    A(P("Capítulo 3 — Pele mista", st_h1))
    A(P("A pele mista combina duas zonas: mais oleosa na zona T (testa, nariz, queixo) e "
        "normal ou seca nas bochechas. É o tipo mais comum. A chave é <b>tratar cada "
        "região com o que ela precisa</b>.", st_lead))
    A(P("Manhã", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Gel de limpeza equilibrado",
         "Limpa a zona T sem ressecar as bochechas"],
        ["Tratamento", "Niacinamida", "Reduz o sebo e ajuda a barreira da pele"],
        ["Hidratação", "Gel hidratante leve", "Hidrata sem pesar"],
        ["Protetor", "Protetor toque seco FPS 50+", "Protege sem dar brilho na zona T"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Noite", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Gel de limpeza (dupla limpeza se usa maquiagem)",
         "Remove sebo e impurezas"],
        ["Tratamento", "BHA na zona T / peptídeos nas bochechas",
         "Cada região recebe o que precisa"],
        ["Hidratação", "Gel na zona T / creme leve nas bochechas",
         "Multi-hidratação por região"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Erros comuns", st_h2))
    for b in bullets([
        "Usar o mesmo produto no rosto inteiro quando as zonas têm necessidades diferentes.",
        "Argila no rosto inteiro — só na zona T.",
        "Ignorar as bochechas: elas precisam de hidratação.",
    ]):
        A(b)
    A(Spacer(1, 3*mm))
    A(P("Ativos que funcionam", st_h2))
    A(ativos_tabela([
        ["Niacinamida", "Reduz o sebo e melhora a barreira", "Manhã e noite"],
        ["Ácido hialurônico", "Ajuda a hidratar", "Manhã e noite"],
        ["BHA (ácido salicílico)", "Desobstrui os poros da zona T", "Noite, só na zona T"],
        ["Ceramidas", "Repõe lipídios nas bochechas", "Hidratante"],
        ["Argila", "Absorve o sebo da superfície", "Máscara 1x/semana, só zona T"],
    ]))
    A(PageBreak())

    # ---------- Capítulo 4: normal ----------
    A(P("Capítulo 4 — Pele normal", st_h1))
    A(P("A pele normal está equilibrada: nem muito oleosa, nem seca. Mesmo assim, vale "
        "manter os bons hábitos — e o protetor solar faz toda a diferença a longo prazo.",
        st_lead))
    A(P("Manhã", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Gel de limpeza suave", "Agridem menos a barreira"],
        ["Tratamento", "Vitamina C (antioxidante)",
         "Pode ajudar contra manchas e fotoenvelhecimento"],
        ["Hidratação", "Hidratante leve", "Mantém o equilíbrio"],
        ["Protetor", "Protetor solar FPS 50+",
         "O antienvelhecimento com melhor evidência"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Noite", st_h2))
    A(rotina_tabela([
        ["Limpeza", "Gel de limpeza suave", "Remove poluição e resíduos"],
        ["Tratamento", "Retinol 2–3x por semana", "Melhorou rugas finas num ensaio"],
        ["Hidratação", "Hidratante leve", "Mantém a pele hidratada durante a noite"],
    ]))
    A(Spacer(1, 3*mm))
    A(P("Erros comuns", st_h2))
    for b in bullets([
        "Trocar de produto toda hora. Pele equilibrada não precisa de muita coisa.",
        "Pular o protetor solar.",
        "Usar produtos muito potentes \"por prevenção\": ativos fortes podem causar "
        "vermelhidão, descamação e ressecamento.",
    ]):
        A(b)
    A(Spacer(1, 3*mm))
    A(P("Ativos que funcionam", st_h2))
    A(ativos_tabela([
        ["Vitamina C", "Antioxidante", "Manhã"],
        ["Retinol", "Melhora linhas finas", "Noite, 2–3x/semana"],
        ["Ácido hialurônico", "Mantém a hidratação", "Manhã e noite"],
        ["Niacinamida", "Melhora manchas, vermelhidão e linhas finas", "Manhã e noite"],
    ]))
    A(PageBreak())

    # ---------- Guia rápido de ingredientes ----------
    A(P("Guia rápido de ingredientes", st_h1))
    A(P("Uma tabela só, para consulta rápida:"))
    A(tabela_cabecalho([
        ["Ingrediente", "Melhor para", "Quando usar"],
        ["Niacinamida", "Oleosa, mista, normal", "Manhã e noite"],
        ["Ácido salicílico (BHA)", "Oleosa (poros, cravos), mista (zona T)", "Noite"],
        ["Retinol", "Todas (linhas finas, acne)", "Só à noite"],
        ["Ácido hialurônico", "Seca, mista, normal", "Antes do hidratante"],
        ["Ceramidas", "Seca, mista (bochechas)", "Manhã e noite"],
        ["Vitamina C", "Normal", "Manhã"],
        ["Pantenol (B5)", "Seca", "Manhã e noite"],
        ["Argila", "Oleosa, mista (zona T)", "Máscara 1–2x/semana"],
    ], [36*mm, 76*mm, 54*mm]))
    A(Spacer(1, 4*mm))
    A(box_aviso("Regra de ouro: <b>um ativo novo por vez</b>, comece com poucas aplicações "
        "por semana e observe a reação da pele."))
    A(Spacer(1, 8*mm))

    # Checklist
    A(P("Checklist da rotina básica", st_h1))
    A(P("Imprima ou salve esta página:"))
    A(P("Manhã", st_h2))
    for b in bullets([
        "□ Limpei o rosto com produto suave",
        "□ Apliquei tratamento (se usar)",
        "□ Apliquei hidratante",
        "□ Apliquei protetor solar FPS 50+",
    ]):
        A(b)
    A(P("Noite", st_h2))
    for b in bullets([
        "□ Limpei o rosto (dupla limpeza se usei maquiagem)",
        "□ Apliquei tratamento (se usar)",
        "□ Apliquei hidratante",
    ]):
        A(b)
    A(P("Semana", st_h2))
    for b in bullets([
        "□ Máscara de argila (pele oleosa/mista, zona T)",
        "□ Esfoliação suave 1–2x (se a pele tolerar)",
        "□ Revisitei a rotina: a pele mudou com a estação?",
    ]):
        A(b)
    A(PageBreak())

    # FAQ
    A(P("Perguntas que sempre aparecem", st_h1))
    faq = [
        ("Preciso mesmo usar hidratante com pele oleosa?",
         "Sim. Não há boa prova de que a falta de hidratante reduza o sebo, e hidratar "
         "ajuda a pele a tolerar tratamentos para acne. Escolha texturas em gel ou fluido, oil-free."),
        ("Quantas vezes por dia devo lavar o rosto?",
         "Duas: de manhã e à noite, com produto suave. Lavar 4 vezes não se mostrou melhor do que 2."),
        ("Posso exfoliar pele seca?",
         "Sim, com cuidado. AHAs como o ácido láctico podem arder; PHAs (como a "
         "gluconolactona) dão efeito parecido com menos irritação. Comece 1x por semana, "
         "nunca em pele irritada."),
        ("Por que minha pele muda no inverno?",
         "Frio e ar seco enfraquecem a barreira da pele. Use hidratante mais rico nessa "
         "época e, se puder, umidifique o ambiente."),
        ("Preciso de produtos diferentes para cada zona da pele mista?",
         "Depende. Se a diferença é pequena, um produto leve equilibrado resolve. Se a "
         "zona T é muito oleosa e as bochechas muito secas, vale fazer multi-hidratação."),
    ]
    for q, a in faq:
        A(P(f"<b>{q}</b>", st_body))
        A(P(a))
        A(Spacer(1, 2*mm))
    A(PageBreak())

    # Continue cuidando
    A(P("Continue cuidando", st_h1))
    A(P("Este guia é o começo. No Produto Skincare você encontra:", st_lead))
    for b in bullets([
        "<b>Provador gratuito</b> — descubra seu tipo de pele e monte uma rotina "
        "personalizada, com produtos reais e preço datado: "
        "<font color='#b08d57'>produtoskincare.com.br/provador</font>",
        "<b>Guias completos por tipo de pele</b> — com a ciência por trás de cada "
        "recomendação: <font color='#b08d57'>produtoskincare.com.br/pele</font>",
        "<b>Ferramentas</b> — comparar produtos, verificar ingredientes, tracker de "
        "rotina e mais: <font color='#b08d57'>produtoskincare.com.br/ferramentas</font>",
    ]):
        A(b)
    A(Spacer(1, 8*mm))
    A(P("Sua pele. Seu próprio ritual.", st_quote))
    A(Spacer(1, 12*mm))
    A(HRFlowable(width="100%", thickness=0.6, color=FILETE))
    A(Spacer(1, 4*mm))
    A(P("Este material é uma referência cosmética, não um diagnóstico médico. Se tem "
        "acne intensa, lesões, dor ou irritação persistente, procure um dermatologista.",
        st_disclaimer))
    A(P("As recomendações deste guia se baseiam em estudos publicados (consulte os guias "
        "completos do site para as referências). Contém menções a produtos disponíveis no "
        "mercado; o Produto Skincare pode conter links de afiliado.", st_disclaimer))
    A(P("© 2026 Produto Skincare — produtoskincare.com.br", st_disclaimer))
    return s

def main():
    # Capa
    c = rl_canvas.Canvas(os.path.join(BASE, "_capa_tmp.pdf"), pagesize=A4)
    c.setTitle("Rotina básica por tipo de pele")
    c.setAuthor("Produto Skincare")
    c.setSubject("Guia prático de rotina de skincare por tipo de pele")
    c.setKeywords(["skincare", "rotina", "tipo de pele", "oleosa", "seca", "mista", "normal"])
    desenhar_capa(c)
    c.save()

    # Corpo
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=20*mm, bottomMargin=22*mm,
        title="Rotina básica por tipo de pele",
        author="Produto Skincare",
    )
    doc.build(construir_story(), onFirstPage=chrome, onLaterPages=chrome)

    # Junta capa + corpo
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    for p in PdfReader(os.path.join(BASE, "_capa_tmp.pdf")).pages:
        writer.add_page(p)
    for p in PdfReader(OUT).pages:
        writer.add_page(p)
    writer.add_metadata({
        "/Title": "Rotina básica por tipo de pele",
        "/Author": "Produto Skincare",
        "/Subject": "Guia prático de rotina de skincare por tipo de pele",
    })
    with open(OUT, "wb") as fh:
        writer.write(fh)
    os.remove(os.path.join(BASE, "_capa_tmp.pdf"))
    print(f"OK: {OUT}")

if __name__ == "__main__":
    main()
