from contextlib import contextmanager
from uuid import uuid4

from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from .forms import EquipamentoForm
from .models import FotoEquipamento


@contextmanager
def gravar_equipamento_com_fotos():
    gravadas = []
    try:
        with transaction.atomic():
            yield gravadas
    except Exception:
        for imagem in gravadas:
            imagem.storage.delete(imagem.name)
        raise


class ResponsavelEquipamentoForm(forms.Form):
    colaborador = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("first_name", "last_name", "username"),
        label="Vincular a um usuário",
        empty_label="Sem vínculo (estoque)",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["colaborador"].label_from_instance = (
            lambda user: f"{user.get_full_name()} ({user.username})"
            if user.get_full_name() else user.username
        )


class CadastroEquipamentoForm(EquipamentoForm):
    imagem_pc = None

    class Meta(EquipamentoForm.Meta):
        fields = [field for field in EquipamentoForm.Meta.fields if field != "imagem_pc"]


class SeletorFotos(forms.ClearableFileInput):
    allow_multiple_selected = True


class CampoFotos(forms.ImageField):
    formatos = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError("Selecione pelo menos uma foto.", code="required")
            return []
        arquivos = data if isinstance(data, (list, tuple)) else [data]
        if len(arquivos) > 10:
            raise forms.ValidationError("Selecione até 10 fotos por envio.")
        if sum(arquivo.size for arquivo in arquivos) > 32 * 1024 * 1024:
            raise forms.ValidationError("As fotos selecionadas devem somar até 32 MB.")
        fotos = []
        for arquivo in arquivos:
            if arquivo.size > 8 * 1024 * 1024:
                raise forms.ValidationError("Cada foto pode ter até 8 MB.")
            foto = super().clean(arquivo, initial)
            extensao = self.formatos.get(foto.image.format)
            if extensao is None:
                raise forms.ValidationError("Use fotos em JPEG, PNG ou WebP.")
            foto.name = uuid4().hex + extensao
            fotos.append(foto)
        return fotos


class FotosEquipamentoForm(forms.Form):
    fotos = CampoFotos(
        label="Fotos do computador",
        required=False,
        help_text="Selecione até 10 fotos por envio, em JPEG, PNG ou WebP. Até 8 MB por foto e 32 MB no total.",
        widget=SeletorFotos(attrs={"class": "form-control", "accept": "image/jpeg,image/png,image/webp"}),
    )

    def salvar(self, equipamento, gravadas):
        for imagem in self.cleaned_data["fotos"]:
            foto = FotoEquipamento(equipamento=equipamento)
            foto.imagem.save(imagem.name, imagem, save=False)
            gravadas.append(foto.imagem)
            foto.save()
