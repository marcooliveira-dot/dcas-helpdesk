from pathlib import Path
from zoneinfo import ZoneInfo
from django.utils import timezone
import re
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods
from .models import Equipamento
from .views import perfis_permitidos
from .termo_pdf import gerar_pdf

def equipamentos_do_colaborador(colaborador_id, principal_id=None):
    if not colaborador_id:
        return Equipamento.objects.none()
    return Equipamento.objects.filter(
        colaborador_id=colaborador_id, ativo=True, status="em_uso",
    ).exclude(pk=principal_id)


class EquipamentosAdicionaisField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, equipamento):
        return str(equipamento)


class TermoForm(forms.Form):
    nome = forms.CharField(label='Nome completo do colaborador', max_length=150)
    cpf = forms.CharField(label='CPF do colaborador', max_length=14, widget=forms.TextInput(attrs={'placeholder':'000.000.000-00','inputmode':'numeric','autocomplete':'off'}))
    acessorios = forms.CharField(label='Acessórios entregues', max_length=150, required=False)
    conservacao = forms.CharField(label='Estado de conservação', max_length=150, required=False)
    equipamentos_adicionais = EquipamentosAdicionaisField(
        queryset=Equipamento.objects.none(),
        label="Equipamentos adicionais",
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 5}),
        help_text="Selecione até 50 itens já entregues ao mesmo colaborador. O equipamento principal já está incluído.",
    )
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

    def __init__(self, *args, colaborador_id=None, principal_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["equipamentos_adicionais"].queryset = equipamentos_do_colaborador(
            colaborador_id, principal_id,
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_equipamentos_adicionais(self):
        equipamentos = list(self.cleaned_data["equipamentos_adicionais"])
        if len(equipamentos) > 50:
            raise forms.ValidationError("Selecione até 50 equipamentos adicionais.")
        return equipamentos


def descricao_equipamento(equipamento, acessorios="", conservacao=""):
    partes = [str(equipamento.nome)]
    for rotulo, valor in (
        ('Marca', equipamento.marca), ('Modelo', equipamento.modelo),
        ('Série', equipamento.numero_serie), ('Acessórios', acessorios),
        ('Conservação', conservacao),
    ):
        if valor:
            partes.append(f'{rotulo}: {valor}')
    return ' | '.join(partes)


def preparar_termo(equipamento, dados):
    descricao = descricao_equipamento(equipamento, dados["acessorios"], dados["conservacao"])
    adicionais = dados["equipamentos_adicionais"]
    itens = []
    if adicionais:
        itens = [(equipamento.patrimonio, descricao)] + [
            (item.patrimonio, descricao_equipamento(item)) for item in adicionais
        ]
        descricao = f"{len(itens)} equipamentos relacionados no Anexo A, que integra este termo."
    return gerar_pdf(
        Path(settings.BASE_DIR) / 'chamados/documentos/termo_modelo.pdf',
        dados['nome'], str(equipamento.patrimonio), descricao,
        cpf=dados['cpf'],
        data=timezone.now().astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y'),
        itens=itens,
    )


def resposta_termo(equipamento, data, disposicao='attachment'):
    response = HttpResponse(data, content_type='application/pdf')
    response['Content-Disposition'] = f'{disposicao}; filename="termo-equipamento-{equipamento.pk}.pdf"'
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
@perfis_permitidos('admin','tecnico')
@never_cache
@require_GET
def opcoes_termo(request):
    colaborador = request.GET.get("colaborador", "")
    if not re.fullmatch(r"[0-9]{1,18}", colaborador):
        return JsonResponse({"equipamentos": []})
    equipamentos = equipamentos_do_colaborador(int(colaborador))
    return JsonResponse({
        "equipamentos": [{"id": item.pk, "rotulo": str(item)} for item in equipamentos],
    })


@login_required
@perfis_permitidos('admin','tecnico')
@never_cache
@require_http_methods(['GET','POST'])
def termo_equipamento(request, pk):
    equipamento=get_object_or_404(Equipamento.objects.select_related('colaborador'),pk=pk)
    nome= equipamento.colaborador.get_full_name() if equipamento.colaborador else ''
    form = TermoForm(
        request.POST if request.method == 'POST' else None, initial={'nome': nome},
        colaborador_id=equipamento.colaborador_id, principal_id=equipamento.pk,
    )
    if request.method=='POST' and form.is_valid():
        try:
            data = preparar_termo(equipamento, form.cleaned_data)
        except ValueError as error:
            form.add_error(None,str(error))
        except OSError:
            form.add_error(None, "Não foi possível abrir o modelo do termo. Tente novamente.")
        else:
            return resposta_termo(equipamento, data)
    return render(request,'chamados/equipamentos/termo.html',{'equipamento':equipamento,'form':form})
