"""Fotos de acompanhamento do paciente — envio via QR ou painel da consulta."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .consultas import Consulta
from .patients import Patient


class PacienteFotoAcompanhamento(LojaIsolationMixin, models.Model):
    """Foto do paciente vinculada à consulta em que foi enviada; visível em todas as consultas do paciente."""

    ORIGEM_CHOICES = (
        ('qr', 'Celular do profissional'),
        ('painel', 'Painel da consulta'),
    )

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='fotos_acompanhamento',
    )
    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE, related_name='fotos_paciente',
    )
    cloudinary_url = models.URLField(max_length=500)
    cloudinary_public_id = models.CharField(max_length=255, blank=True, default='')
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES, default='qr')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_paciente_fotos'
        ordering = ['-created_at']
        verbose_name = 'Foto de acompanhamento'
        verbose_name_plural = 'Fotos de acompanhamento'
        indexes = [
            models.Index(fields=['patient', 'created_at'], name='clin_cb_foto_pac_dt_idx'),
            models.Index(fields=['consulta'], name='clin_cb_foto_cons_idx'),
        ]

    def __str__(self):
        return f'Foto {self.patient_id} — consulta #{self.consulta_id}'
