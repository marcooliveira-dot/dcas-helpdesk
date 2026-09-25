from pathlib import Path
from zoneinfo import ZoneInfo
from django.utils import timezone
import re
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from .models import Equipamento
from .views import perfis_permitidos
from .termo_pdf import gerar_pdf

class TermoForm(forms.Form):
    nome = forms.CharField(label='Nome completo do colaborador', max_length=150)
    cpf = forms.CharField(label='CPF do colaborador', max_length=14, widget=forms.TextInput(attrs={'placeholder':'000.000.000-00','inputmode':'numeric','autocomplete':'off'}))
    acessorios = forms.CharField(label='Acessórios entregues', max_length=150, required=False)
    conservacao = forms.CharField(label='Estado de conservação', max_length=150, required=False)
    def clean_cpf(self):
        valor=self.cleaned_data['cpf'].strip()
        if not re.fullmatch(r'(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})',valor):
            raise forms.ValidationError('Informe um CPF válido, com 11 dígitos.')
        digits=re.sub(r'[^0-9]','',valor)
        if len(set(digits))==1:
            raise forms.ValidationError('Informe um CPF válido.')
        for tamanho in (9,10):
            soma=sum(int(digits[i])*(tamanho+1-i) for i in range(tamanho))
            verificador=(soma*10)%11
            if verificador==10: verificador=0
            if verificador!=int(digits[tamanho]):
                raise forms.ValidationError('Informe um CPF válido.')
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

@login_required
@perfis_permitidos('admin','tecnico')
@require_http_methods(['GET','POST'])
def termo_equipamento(request, pk):
    equipamento=get_object_or_404(Equipamento.objects.select_related('colaborador'),pk=pk)
    nome= equipamento.colaborador.get_full_name() if equipamento.colaborador else ''
    form=TermoForm(request.POST if request.method=='POST' else None,initial={'nome':nome})
    if request.method=='POST' and form.is_valid():
        partes=[str(equipamento.nome)]
        for label,valor in [('Marca',equipamento.marca),('Modelo',equipamento.modelo),('Série',equipamento.numero_serie),('Acessórios',form.cleaned_data['acessorios']),('Conservação',form.cleaned_data['conservacao'])]:
            if valor: partes.append(f'{label}: {valor}')
        try:
            data=gerar_pdf(Path(settings.BASE_DIR)/'chamados/documentos/termo_modelo.pdf',form.cleaned_data['nome'],str(equipamento.patrimonio),' | '.join(partes),cpf=form.cleaned_data['cpf'],data=timezone.now().astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y'))
        except ValueError as error:
            form.add_error(None,str(error))
        else:
            response=HttpResponse(data,content_type='application/pdf')
            response['Content-Disposition']=f'attachment; filename="termo-equipamento-{equipamento.pk}.pdf"'
            response['Cache-Control']='private, no-store'
            return response
    return render(request,'chamados/equipamentos/termo.html',{'equipamento':equipamento,'form':form})
