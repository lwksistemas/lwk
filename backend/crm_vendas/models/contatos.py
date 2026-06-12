from django.db import models

from core.mixins import LojaIsolationMixin, LojaIsolationManager

from .contas import Conta

class Contato(LojaIsolationMixin, models.Model):
    """Contato (pessoa) vinculado a uma conta."""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        related_name='contatos',
    )
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_contato'
        ordering = ['nome']
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        indexes = [
            models.Index(fields=['loja_id', 'conta'], name='crm_contato_loja_conta_idx'),
            models.Index(fields=['loja_id', 'email'], name='crm_contato_loja_email_idx'),
        ]

    def __str__(self):
        return self.nome

