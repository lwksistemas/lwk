from django.contrib import admin
from .models import (
    Cliente, Profissional, Servico, Agendamento, Produto, Venda,
    Funcionario, HorarioFuncionamento, BloqueioAgenda
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['nome', 'telefone', 'email', 'cpf']


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ['nome', 'especialidade', 'telefone', 'is_active']
    list_filter = ['is_active', 'especialidade']
    search_fields = ['nome', 'telefone', 'email']


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'preco', 'duracao', 'is_active']
    list_filter = ['categoria', 'is_active']
    search_fields = ['nome', 'descricao']


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'profissional', 'servico', 'data', 'horario', 'status']
    list_filter = ['status', 'data']
    search_fields = ['cliente__nome', 'profissional__nome', 'servico__nome']
    date_hierarchy = 'data'


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'marca', 'preco_venda', 'estoque_atual', 'is_active']
    list_filter = ['categoria', 'is_active']
    search_fields = ['nome', 'marca']


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['id', 'produto', 'cliente', 'quantidade', 'valor_total', 'forma_pagamento', 'data_venda']
    list_filter = ['forma_pagamento', 'data_venda']
    search_fields = ['produto__nome', 'cliente__nome']
    date_hierarchy = 'data_venda'


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cargo', 'telefone', 'data_admissao', 'is_active']
    list_filter = ['is_active', 'cargo', 'data_admissao']
    search_fields = ['nome', 'cpf', 'telefone']


@admin.register(HorarioFuncionamento)
class HorarioFuncionamentoAdmin(admin.ModelAdmin):
    list_display = ['dia_semana', 'horario_abertura', 'horario_fechamento', 'is_active']
    list_filter = ['dia_semana', 'is_active']


@admin.register(BloqueioAgenda)
class BloqueioAgendaAdmin(admin.ModelAdmin):
    list_display = ['profissional', 'data_inicio', 'data_fim', 'motivo']
    list_filter = ['data_inicio', 'data_fim']
    search_fields = ['profissional__nome', 'motivo']
