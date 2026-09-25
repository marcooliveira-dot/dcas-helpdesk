from io import BytesIO
from xml.sax.saxutils import escape
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth


def gerar_pdf(modelo, nome, patrimonio, descricao, cpf='', data=''):
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
    writer.add_metadata({'/Title':'Termo de Ciência e Responsabilidade','/Author':'DCAS Group'})
    output=BytesIO(); writer.write(output)
    return output.getvalue()

