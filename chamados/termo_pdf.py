from io import BytesIO
from xml.sax.saxutils import escape
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth


def anexar_equipamentos(writer, tamanho, nome, patrimonio, data, itens):
    anexo = BytesIO()
    largura, _ = tamanho
    corpo = ParagraphStyle('corpo', fontName='Helvetica', fontSize=10, leading=14)
    titulo = ParagraphStyle('titulo', parent=corpo, fontName='Helvetica-Bold', fontSize=17, leading=22)
    cabecalho = ParagraphStyle('cabecalho', parent=corpo, fontName='Helvetica-Bold', textColor=colors.white)
    linhas = [[Paragraph('Patrimônio', cabecalho), Paragraph('Equipamento', cabecalho)]]
    linhas += [[Paragraph(escape(str(codigo)), corpo), Paragraph(escape(texto), corpo)] for codigo, texto in itens]
    tabela = LongTable(linhas, colWidths=[112, largura - 208], repeatRows=1, hAlign='LEFT')
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16243c')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f1f5f9'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    def rodape(pagina, documento):
        pagina.setFont('Helvetica', 9)
        pagina.setFillColor(colors.HexColor('#40516d'))
        pagina.drawString(42, 30, 'DCAS Group | Anexo A - Termo de responsabilidade')
        pagina.drawRightString(largura - 42, 30, f'Página {documento.page + 1}')

    documento = SimpleDocTemplate(anexo, pagesize=tamanho, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=48)
    documento.build([
        Paragraph('Anexo A - Relação de equipamentos', titulo),
        Spacer(1, 12),
        Paragraph(f'<b>Colaborador:</b> {escape(nome)}', corpo),
        Paragraph(f'<b>Data:</b> {escape(data)} | <b>Patrimônio de referência:</b> {escape(patrimonio)}', corpo),
        Spacer(1, 8),
        Paragraph('Os itens desta relação fazem parte do termo de responsabilidade da página inicial.', corpo),
        Spacer(1, 16),
        tabela,
    ], onFirstPage=rodape, onLaterPages=rodape)
    anexo.seek(0)
    writer.append(PdfReader(anexo))


def gerar_pdf(modelo, nome, patrimonio, descricao, cpf='', data='', itens=()):
    reader = PdfReader(str(modelo))
    page = reader.pages[0]
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    layer = BytesIO()
    c = canvas.Canvas(layer, pagesize=(w,h))
    def linha(texto, x, y, largura):
        size = 11
        while stringWidth(texto, 'Helvetica', size) > largura and size > 8:
            size -= .25
        if stringWidth(texto, 'Helvetica', size) > largura:
            raise ValueError('Nome ou patrimônio muito longo para o espaço do modelo.')
        c.setFillColorRGB(1,1,1); c.rect(x,y-3,largura,16,fill=1,stroke=0)
        c.setFillColorRGB(0,0,0); c.setFont('Helvetica',size); c.drawString(x,y,texto)
    if cpf: linha(cpf,120,226.5,230)
    if data: linha(data,123,169.5,150)
    linha(nome,132,255,316)
    linha(patrimonio,166,283.5,280)
    for size in [11,10,9,8]:
        p=Paragraph(escape(descricao),ParagraphStyle('equipamento',fontName='Helvetica',fontSize=size,leading=size+2))
        _, altura=p.wrap(410,46)
        if altura<=46: break
    if altura>46:
        raise ValueError('A descrição está longa demais para o modelo. Reduza os complementos ou o cadastro do equipamento.')
    p.drawOn(c,93,367-altura)
    c.save(); layer.seek(0)
    page.merge_page(PdfReader(layer).pages[0])
    writer=PdfWriter(); writer.add_page(page)
    if itens:
        anexar_equipamentos(writer, (w, h), nome, patrimonio, data, itens)
    writer.add_metadata({'/Title':'Termo de Ciência e Responsabilidade','/Author':'DCAS Group'})
    output=BytesIO(); writer.write(output)
    return output.getvalue()

