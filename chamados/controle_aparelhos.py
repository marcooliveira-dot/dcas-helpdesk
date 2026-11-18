from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Equipamento, HistoricoEquipamento, Localizacao
from .views import perfis_permitidos


ALTERACAO_BASE = "Alteração de base"


class BaseForm(forms.ModelForm):
    class Meta:
        model = Localizacao
        fields = ["nome", "endereco"]
        labels = {"nome": "Nome da base", "endereco": "Endereço (opcional)"}
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "endereco": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_nome(self):
        nome = self.cleaned_data["nome"]
        if Localizacao.objects.filter(nome__iexact=nome).exists():
            raise forms.ValidationError("Já existe uma base com esse nome.")
        return nome


class BaseAparelhoForm(forms.Form):
    base = forms.ModelChoiceField(
        queryset=Localizacao.objects.all(),
        label="Base do aparelho",
        required=False,
        empty_label="Sem base definida",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


@login_required
@perfis_permitidos("admin", "tecnico")
def controle_equipamentos(request):
    equipamentos = Equipamento.objects.select_related("localizacao", "colaborador").order_by("patrimonio")
    totais = equipamentos.aggregate(total=Count("pk"), sem_base=Count("pk", filter=Q(localizacao__isnull=True)))
    bases = list(Localizacao.objects.all())
    base = request.GET.get("base", "")
    busca = request.GET.get("busca", "").strip()[:150]
    base_id = next((item.pk for item in bases if str(item.pk) == base), None)
    if base == "sem-base":
        equipamentos = equipamentos.filter(localizacao__isnull=True)
    elif base_id is not None:
        equipamentos = equipamentos.filter(localizacao_id=base_id)
    else:
        base = ""
    if busca:
        equipamentos = equipamentos.filter(
            Q(nome__icontains=busca) | Q(patrimonio__icontains=busca) | Q(numero_serie__icontains=busca)
        )
    return render(request, "chamados/equipamentos/controle.html", {
        "pagina": Paginator(equipamentos, 25).get_page(request.GET.get("page")),
        "bases": bases,
        "base": base,
        "busca": busca,
        "total": totais["total"],
        "sem_base": totais["sem_base"],
        "com_base": totais["total"] - totais["sem_base"],
    })


@login_required
@perfis_permitidos("admin")
@require_http_methods(["GET", "POST"])
def nova_base(request):
    form = BaseForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Base cadastrada. Você já pode vincular aparelhos a ela.")
        return redirect("controle_equipamentos")
    return render(request, "chamados/equipamentos/base_form.html", {"form": form})


@login_required
@perfis_permitidos("admin", "tecnico")
@require_http_methods(["GET", "POST"])
def alterar_base_aparelho(request, pk):
    equipamento = get_object_or_404(Equipamento.objects.select_related("localizacao"), pk=pk)
    form = BaseAparelhoForm(
        request.POST if request.method == "POST" else None,
        initial={"base": equipamento.localizacao_id},
    )
    if request.method == "POST" and form.is_valid():
        destino = form.cleaned_data["base"]
        destino_id = destino.pk if destino else None
        with transaction.atomic():
            atual = get_object_or_404(Equipamento.objects.select_for_update(), pk=pk)
            if atual.localizacao_id != destino_id:
                origem = str(atual.localizacao) if atual.localizacao_id else "Sem base definida"
                atual.localizacao = destino
                atual.save(update_fields=["localizacao", "atualizado_em"])
                HistoricoEquipamento.objects.create(
                    equipamento=atual,
                    usuario=request.user,
                    acao=ALTERACAO_BASE,
                    descricao=f"{origem} → {destino or 'Sem base definida'}",
                )
        messages.success(request, "Base do aparelho atualizada.")
        return redirect("controle_equipamentos")
    historico = equipamento.historico.filter(acao=ALTERACAO_BASE).select_related("usuario").order_by("-data", "-pk")[:10]
    return render(request, "chamados/equipamentos/base_aparelho.html", {
        "form": form, "equipamento": equipamento, "historico": historico,
    })
