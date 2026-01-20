"""
Admin para integração com Asaas
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AsaasCustomer, AsaasPayment, LojaAssinatura

@admin.register(AsaasCustomer)
class AsaasCustomerAdmin(admin.ModelAdmin):
    """Admin para clientes Asaas"""
    
    list_display = ['name', 'email', 'cpf_cnpj', 'city', 'state', 'external_reference', 'created_at']
    list_filter = ['state', 'created_at']
    search_fields = ['name', 'email', 'cpf_cnpj', 'external_reference']
    readonly_fields = ['asaas_id', 'created_at', 'updated_at', 'raw_data_display']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('asaas_id', 'name', 'email', 'cpf_cnpj', 'phone', 'external_reference')
        }),
        ('Endereço', {
            'fields': ('address', 'address_number', 'complement', 'province', 'city', 'state', 'postal_code')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at', 'raw_data_display'),
            'classes': ('collapse',)
        })
    )
    
    def raw_data_display(self, obj):
        """Exibe dados brutos formatados"""
        if obj.raw_data:
            import json
            return format_html('<pre>{}</pre>', json.dumps(obj.raw_data, indent=2, ensure_ascii=False))
        return '-'
    raw_data_display.short_description = 'Dados Brutos do Asaas'

@admin.register(AsaasPayment)
class AsaasPaymentAdmin(admin.ModelAdmin):
    """Admin para cobranças Asaas"""
    
    list_display = ['asaas_id', 'customer_name', 'value', 'status', 'billing_type', 'due_date', 'payment_date', 'actions']
    list_filter = ['status', 'billing_type', 'due_date', 'created_at']
    search_fields = ['asaas_id', 'customer__name', 'customer__email', 'external_reference', 'description']
    readonly_fields = ['asaas_id', 'created_at', 'updated_at', 'raw_data_display', 'payment_links']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('asaas_id', 'customer', 'external_reference')
        }),
        ('Cobrança', {
            'fields': ('billing_type', 'status', 'value', 'net_value', 'description')
        }),
        ('Datas', {
            'fields': ('due_date', 'payment_date')
        }),
        ('Links de Pagamento', {
            'fields': ('payment_links', 'invoice_url', 'bank_slip_url')
        }),
        ('PIX', {
            'fields': ('pix_qr_code', 'pix_copy_paste'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at', 'raw_data_display'),
            'classes': ('collapse',)
        })
    )
    
    def customer_name(self, obj):
        return obj.customer.name
    customer_name.short_description = 'Cliente'
    
    def payment_links(self, obj):
        """Exibe links de pagamento"""
        links = []
        if obj.invoice_url:
            links.append(f'<a href="{obj.invoice_url}" target="_blank">Fatura</a>')
        if obj.bank_slip_url:
            links.append(f'<a href="{obj.bank_slip_url}" target="_blank">Boleto</a>')
        return mark_safe(' | '.join(links)) if links else '-'
    payment_links.short_description = 'Links'
    
    def actions(self, obj):
        """Ações disponíveis"""
        actions = []
        if obj.asaas_id:
            # Link para baixar PDF
            actions.append(f'<a href="/api/asaas/payments/{obj.id}/download_pdf/" target="_blank">PDF</a>')
        return mark_safe(' | '.join(actions)) if actions else '-'
    actions.short_description = 'Ações'
    
    def raw_data_display(self, obj):
        """Exibe dados brutos formatados"""
        if obj.raw_data:
            import json
            return format_html('<pre>{}</pre>', json.dumps(obj.raw_data, indent=2, ensure_ascii=False))
        return '-'
    raw_data_display.short_description = 'Dados Brutos do Asaas'

@admin.register(LojaAssinatura)
class LojaAssinaturaAdmin(admin.ModelAdmin):
    """Admin para assinaturas das lojas"""
    
    list_display = ['loja_nome', 'plano_nome', 'plano_valor', 'ativa', 'data_vencimento', 'payment_status', 'actions']
    list_filter = ['ativa', 'plano_nome', 'data_vencimento', 'created_at']
    search_fields = ['loja_nome', 'loja_slug', 'asaas_customer__name', 'asaas_customer__email']
    readonly_fields = ['created_at', 'updated_at', 'payment_history']
    
    fieldsets = (
        ('Loja', {
            'fields': ('loja_slug', 'loja_nome')
        }),
        ('Assinatura', {
            'fields': ('plano_nome', 'plano_valor', 'ativa', 'data_ativacao', 'data_vencimento')
        }),
        ('Asaas', {
            'fields': ('asaas_customer', 'current_payment')
        }),
        ('Histórico', {
            'fields': ('payment_history',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def payment_status(self, obj):
        """Status do pagamento atual"""
        if obj.current_payment:
            status = obj.current_payment.status
            if obj.current_payment.is_paid:
                color = 'green'
            elif obj.current_payment.is_overdue:
                color = 'red'
            else:
                color = 'orange'
            return format_html('<span style="color: {};">{}</span>', color, obj.current_payment.get_status_display())
        return '-'
    payment_status.short_description = 'Status Pagamento'
    
    def actions(self, obj):
        """Ações disponíveis"""
        actions = []
        if obj.current_payment:
            # Link para ver pagamento
            actions.append(f'<a href="/admin/asaas_integration/asaaspayment/{obj.current_payment.id}/change/">Ver Pagamento</a>')
            # Link para baixar PDF
            actions.append(f'<a href="/api/asaas/payments/{obj.current_payment.id}/download_pdf/" target="_blank">PDF</a>')
        return mark_safe(' | '.join(actions)) if actions else '-'
    actions.short_description = 'Ações'
    
    def payment_history(self, obj):
        """Histórico de pagamentos"""
        payments = obj.get_all_payments()[:10]  # Últimos 10
        if not payments:
            return 'Nenhum pagamento encontrado'
        
        history = []
        for payment in payments:
            status_color = 'green' if payment.is_paid else ('red' if payment.is_overdue else 'orange')
            history.append(
                f'<div style="margin: 5px 0;">'
                f'<strong>{payment.asaas_id}</strong> - '
                f'R$ {payment.value} - '
                f'<span style="color: {status_color};">{payment.get_status_display()}</span> - '
                f'{payment.due_date}'
                f'</div>'
            )
        
        return mark_safe(''.join(history))
    payment_history.short_description = 'Histórico de Pagamentos'