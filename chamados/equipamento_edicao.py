from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.views.decorators.http import require_http_methods
from .views import perfis_permitidos
from .models import Equipamento, HistoricoEquipamento
from .forms import EquipamentoForm

@login_required
@perfis_permitidos('admin', 'tecnico')
@require_http_methods(['GET', 'POST'])
def editar_equipamento(request, pk):
    with transaction.atomic():
        equipamento = get_object_or_404(Equipamento.objects.select_for_update(), pk=pk)
        form = EquipamentoForm(request.POST if request.method == 'POST' else None, request.FILES if request.method == 'POST' else None, instance=equipamento)
        if request.method == 'POST' and form.is_valid():
            if form.has_changed():
                form.save()
                HistoricoEquipamento.objects.create(equipamento=equipamento, usuario=request.user, acao='Cadastro atualizado', descricao='Campos alterados: ' + ', '.join(str(form.fields[n].label or n) for n in form.changed_data))
            messages.success(request, 'Equipamento atualizado com sucesso.')
            return redirect('detalhe_equipamento', pk=pk)
    return render(request, 'chamados/equipamentos/editar.html', {'form': form, 'equipamento': equipamento})
