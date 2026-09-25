from django import forms

from .models import (
    Chamado,
    Equipamento,
)


# ==========================================================
# CHAMADOS
# ==========================================================

class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado

        fields = [
            "titulo",
            "descricao",
            "categoria",
            "prioridade",
            "anexo",
        ]

        labels = {
            "titulo": "Título do chamado",
            "descricao": "Descrição detalhada",
            "categoria": "Categoria",
            "prioridade": "Prioridade",
            "anexo": "Anexo",
        }

        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex.: Computador não liga",
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": (
                    "Descreva o problema, quando começou "
                    "e as mensagens de erro que aparecem."
                ),
            }),
            "categoria": forms.Select(attrs={
                "class": "form-select",
            }),
            "prioridade": forms.Select(attrs={
                "class": "form-select",
            }),
            "anexo": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = True
# ==========================================================
# EQUIPAMENTOS
# ==========================================================

class EquipamentoForm(forms.ModelForm):
    imagem_pc = forms.ImageField(label="Foto do computador", required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}))
    foto = forms.FileField(label="Arquivo (imagem ou PDF)", required=False,
        help_text="Envie uma imagem ou um documento PDF sem senha.",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*,.pdf,application/pdf"}))

    def clean_foto(self):
        arquivo = self.cleaned_data.get("foto")
        if not arquivo or not hasattr(arquivo, "content_type"):
            return arquivo
        try:
            if arquivo.name.lower().endswith('.pdf'):
                from pypdf import PdfReader
                reader = PdfReader(arquivo)
                if reader.is_encrypted or not len(reader.pages):
                    raise ValueError('PDF protegido ou vazio')
            else:
                from PIL import Image
                Image.open(arquivo).verify()
        except Exception:
            raise forms.ValidationError("Envie uma imagem válida ou um PDF sem senha.")
        finally:
            arquivo.seek(0)
        return arquivo


    class Meta:

        model = Equipamento

        fields = [

            "patrimonio",

            "numero_serie",

            "nome",

            "tipo",

            "categoria",

            "fabricante",

            "fornecedor",

            "departamento",

            "localizacao",

            "marca",

            "modelo",


            "memoria",

            "armazenamento",

            "sistema_operacional",



            "nota_fiscal",

            "data_compra",

            "garantia",


            "foto",
            "imagem_pc",

            "observacao",

        ]

        widgets = {

            "patrimonio": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "numero_serie": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "nome": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "tipo": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "categoria": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "fabricante": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "fornecedor": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "departamento": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "localizacao": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "marca": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "modelo": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "processador": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "memoria": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "armazenamento": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "sistema_operacional": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "endereco_mac": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "endereco_ip": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "nota_fiscal": forms.TextInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "data_compra": forms.DateInput(

                attrs={

                    "class": "form-control",

                    "type": "date"

                }

            ),

            "garantia": forms.DateInput(

                attrs={

                    "class": "form-control",

                    "type": "date"

                }

            ),

            "valor": forms.NumberInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "foto": forms.ClearableFileInput(

                attrs={

                    "class": "form-control"

                }

            ),

            "observacao": forms.Textarea(

                attrs={

                    "class": "form-control",

                    "rows": 4

                }

            ),

        }