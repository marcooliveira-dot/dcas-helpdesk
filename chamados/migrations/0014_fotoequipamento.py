import django.db.models.deletion
from django.db import migrations, models

import chamados.models


class Migration(migrations.Migration):
    dependencies = [
        ("chamados", "0013_equipamento_imagem_pc_perfil_foto_perfil"),
    ]

    operations = [
        migrations.CreateModel(
            name="FotoEquipamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("imagem", models.ImageField(storage=chamados.models.armazenamento_fotos_equipamento, upload_to="equipamentos/")),
                ("equipamento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fotos_pc", to="chamados.equipamento")),
            ],
            options={"ordering": ["pk"]},
        ),
    ]
