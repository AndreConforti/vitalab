from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import constants
from .models import TiposExames, PedidosExames, SolicitacaoExame, AcessoMedico
from datetime import datetime, date

@login_required
def solicitar_exames(request):
    tipos_exames = TiposExames.objects.all()
    if request.method == 'GET':
        return render(request, 'solicitar_exames.html', {'tipos_exames': tipos_exames})
    elif request.method == 'POST':
        exames_id = request.POST.getlist('exames')
        solicitacao_exames = TiposExames.objects.filter(id__in=exames_id)  ## __ equivale ao WHERE no SQL e 'in' significa iterar sobre a lista
        # TODO Calcular preco dos dados disponíveis
        preco_total = 0
        for i in solicitacao_exames:
            if i.disponivel:
                preco_total += i.preco
        data=datetime.now()

        return render(request, 'solicitar_exames.html', {'tipos_exames': tipos_exames,
                                                         'solicitacao_exames': solicitacao_exames,
                                                         'preco_total': preco_total,
                                                         'data': data})
        

@login_required
def fechar_pedido(request):
    exames_id = request.POST.getlist('exames')
    solicitacao_exames = TiposExames.objects.filter(id__in=exames_id)

    pedido_exame = PedidosExames(
        usuario=request.user,
        data=datetime.now()
    )
    pedido_exame.save()

    for exame in solicitacao_exames:
        solicitacao_exames_temp = SolicitacaoExame(
            usuario=request.user,
            exame=exame,
            status='E'
        )
        solicitacao_exames_temp.save()
        pedido_exame.exames.add(solicitacao_exames_temp)
    
    pedido_exame.save()

    messages.add_message(request, constants.SUCCESS, 'Pedido de exame realizado com sucesso!')
    return redirect('/exames/gerenciar_pedidos/')


@login_required
def gerenciar_pedidos(request):
    pedidos_exames = PedidosExames.objects.filter(usuario=request.user)

    return render(request, 'gerenciar_pedidos.html', {'pedidos_exames': pedidos_exames})


@login_required
def cancelar_pedido(request, pedido_id):
    pedido = PedidosExames.objects.get(id=pedido_id)
    if not pedido.usuario == request.user:
        messages.add_message(request, constants.ERROR, 'Não é possível realizar esta ação.')
        return redirect('/exames/gerenciar_pedidos/')
    pedido.agendado = False
    pedido.save()
    messages.add_message(request, constants.SUCCESS, 'Pedido cancelado com sucesso!')
    return redirect('/exames/gerenciar_pedidos/')


@login_required
def gerenciar_exames(request):
    exames = SolicitacaoExame.objects.filter(usuario=request.user)

    return render(request, 'gerenciar_exames.html', {'exames': exames})


@login_required
def permitir_abrir_exame(request, exame_id):
    exame = SolicitacaoExame.objects.get(id=exame_id)

    if not exame.requer_senha:
        try:
            return redirect(exame.resultado.url)  ## Campos FileField permitem que possa ser acessada sua URL
        except:
            messages.add_message(request, constants.WARNING, 'Não foi possível encontrar o arquivo.')
            return redirect(f'/exames/gerenciar_exames')
    return redirect(f'/exames/solicitar_senha_exame/{exame_id}')


@login_required
def solicitar_senha_exame(request, exame_id):
    exame = SolicitacaoExame.objects.get(id=exame_id)
    if request.method == 'GET':
        return render(request, 'solicitar_senha_exame.html', {'exame': exame})
    elif request.method == 'POST':
        senha = request.POST.get('senha')  ## Pega e armazena a senha passada na página de solicitar senha
        if senha == exame.senha:
            try:
                return redirect(exame.resultado.url)  ## Campos FileField permitem que possa ser acessada sua URL
            except:
                messages.add_message(request, constants.WARNING, 'Não foi possível encontrar o arquivo.')
                return redirect(f'/exames/gerenciar_exames')
        else:
            messages.add_message(request, constants.ERROR, 'Senha incorreta.')
            return redirect(f'/exames/solicitar_senha_exame/{exame_id}')
        

@login_required
def gerar_acesso_medico(request):
    if request.method == 'GET':
        acessos_medicos = AcessoMedico.objects.filter(usuario=request.user)
        return render(request, 'gerar_acesso_medico.html', {'acessos_medicos': acessos_medicos})
    elif request.method == "POST":
        identificacao = request.POST.get('identificacao')
        tempo_de_acesso = request.POST.get('tempo_de_acesso')
        data_exame_inicial = request.POST.get("data_exame_inicial")
        data_exame_final = request.POST.get("data_exame_final")

        acesso_medico = AcessoMedico(
            usuario = request.user,
            identificacao = identificacao,
            tempo_de_acesso = tempo_de_acesso,
            data_exames_iniciais = data_exame_inicial,
            data_exames_finais = data_exame_final,
            criado_em = datetime.now()
        )

        acesso_medico.save()

        messages.add_message(request, constants.SUCCESS, 'Acesso gerado com sucesso')
        return redirect('/exames/gerar_acesso_medico')
    

def acesso_medico(request, token):
    acesso_medico = AcessoMedico.objects.get(token=token)
    if acesso_medico.status == 'Expirado':
        messages.add_message(request, constants.ERROR, 'Este token já expirou. Solicite novamente um novo.')
        return(redirect('/usuarios/login'))
    ## listar os pedidos de exames que são de um determinado usuário entre as datas iniciais e finais do exame (3 filter's)
    pedidos = PedidosExames.objects.filter(usuario=acesso_medico.usuario).filter(data__gte=acesso_medico.data_exames_iniciais).filter(data__lte=acesso_medico.data_exames_finais)

    return render(request, 'acesso_medico.html', {'pedidos': pedidos})