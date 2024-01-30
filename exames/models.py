from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from secrets import token_urlsafe  
from django.utils import timezone
from datetime import timedelta

class TiposExames(models.Model):
    TIPO_CHOICES = (
        ('I', 'Exame de Imagem'),
        ('S', 'Exame de Sangue'),
    )
    nome = models.CharField(max_length=70)
    preco = models.FloatField()
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    disponivel = models.BooleanField(default=True)
    horario_incial = models.IntegerField()
    horario_final = models.IntegerField()

    def __str__(self):
        return self.nome


class SolicitacaoExame(models.Model):
    choice_status = (
        ('E', 'Em análise'),
        ('F', 'Finalizado')
    )
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    exame = models.ForeignKey(TiposExames, on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=2, choices=choice_status)
    resultado = models.FileField(upload_to="resultados", null=True, blank=True)
    requer_senha = models.BooleanField(default=False)
    senha = models.CharField(max_length=6, null=True, blank=True)

    def __str__(self):
        return f'{self.usuario} | {self.exame.nome}'
    
    def badge_template(self):
        if self.status == 'E':
            classes = 'bg-warning text-dark'
            texto = 'Em análise'
        else:
            classes = 'bg-success'
            texto = 'Finalizado'
        return mark_safe(f'<span class="badge {classes}">{texto}</span>')


class PedidosExames(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    exames = models.ManyToManyField(SolicitacaoExame)
    agendado = models.BooleanField(default=True)
    data = models.DateField()

    def __str__(self):
        return f'{self.usuario} | {self.id} | {self.data}'
    

class AcessoMedico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    identificacao = models.CharField(max_length=50)
    tempo_de_acesso = models.IntegerField() # Em horas
    criado_em = models.DateTimeField()
    data_exames_iniciais = models.DateField()
    data_exames_finais = models.DateField()
    token = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.token
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = token_urlsafe(6)  ## Gera um token aleatório com 6 bites, porém sem os caracteres especiais reservados de URL

        super(AcessoMedico, self).save(*args, **kwargs)

    @property   ## Permite que eu possa acessar essemétodo como se fosse uma propredade da classe
    def status(self):
        return 'Expirado' if timezone.now() > (self.criado_em + timedelta(hours=self.tempo_de_acesso)) else 'Ativo'
    
    @property
    def url(self):
        return f'http://127.0.0.1:8000/exames/acesso_medico/{self.token}'