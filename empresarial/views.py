from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, FileResponse
from django.db.models.functions import Concat
from django.db.models import Value
from exames.models import SolicitacaoExame
from .utils import gerar_pdf_exames, gerar_senha_aleatoria
from django.contrib.messages import constants
from django.contrib import messages


@staff_member_required       ## Permite que somente membros do Staff podem acessar
def gerenciar_clientes(request):
    clientes = User.objects.filter(is_staff=False)

    nome_completo = request.GET.get('nome')
    email = request.GET.get('email')

    if email:
        clientes = clientes.filter(email__contains=email)
    if nome_completo:
        clientes = clientes.annotate(full_name=Concat('first_name', Value(' '), 'last_name')).filter(full_name__contains=nome_completo)  ## Cria um campo chamado full_name e depois filtra pelo nome completo
    
    return render(request, 'gerenciar_clientes.html', {'clientes': clientes})


@staff_member_required 
def cliente(request, cliente_id):
    cliente = User.objects.get(id=cliente_id)
    exames = SolicitacaoExame.objects.filter(usuario=cliente)
    return render(request, 'cliente.html', {'cliente': cliente, 'exames': exames})


@staff_member_required
def exame_cliente(request, exame_id):
    exame = SolicitacaoExame.objects.get(id=exame_id)
    return render(request, 'exame_cliente.html', {'exame': exame})


@staff_member_required
def proxy_pdf(request, exame_id):
    exame = SolicitacaoExame.objects.get(id=exame_id)
    response = exame.resultado.open()
    return FileResponse(response)


@staff_member_required
def gerar_senha(request, exame_id):
    exame = SolicitacaoExame.objects.get(id=exame_id)
    if exame.senha:
        return FileResponse(gerar_pdf_exames(exame.exame.nome, exame.usuario.first_name, exame.senha), filename='token.pdf')
    
    exame.senha = gerar_senha_aleatoria(6)
    exame.save()

    return FileResponse(gerar_pdf_exames(exame.exame.nome, exame.usuario.first_name, exame.senha), filename='token.pdf')

@staff_member_required
def alterar_dados_exame(request, exame_id):
    exame = SolicitacaoExame.objects.get(id=exame_id)
    pdf = request.FILES.get('resultado')
    status = request.POST.get('status')
    requer_senha = request.POST.get('requer_senha')

    if requer_senha and (not exame.senha):
        messages.add_message(request, constants.ERROR, 'Para exigir a senha primeir é preciso criá-la.')
        return redirect(f'/empresarial/exame_cliente/{exame.id}')

    exame.requer_senha = True if requer_senha == True else False

    if pdf:
        exame.resultado = pdf

    exame.status = status

    exame.save()
    messages.add_message(request, constants.SUCCESS, 'Dados salvos!')
    return redirect(f'/empresarial/exame_cliente/{exame.id}')