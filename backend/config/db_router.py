"""
Database Router para Multi-Tenant com 3 bancos isolados:
1. default - Super Admin (schema: public)
2. suporte - Sistema de Suporte (schema: suporte)
3. loja_* - Bancos dinâmicos por loja (schemas: loja_*)

Com PostgreSQL, usa schemas isolados no mesmo banco.
Com SQLite local, usa arquivos separados.
"""

class MultiTenantRouter:
    """
    Router que direciona queries para o banco correto baseado no app/model
    """
    
    # Apps que usam o banco de suporte
    suporte_apps = {'suporte'}
    
    # Apps que usam bancos de loja (schema isolado por loja)
    loja_apps = {
        'stores',
        'products',
        'clinica_estetica',
        'clinica_beleza',  # Clínica da Beleza - tabelas isoladas por schema
        'cabeleireiro',
        'ecommerce',
        'restaurante',
        'servicos',
        'whatsapp',  # Config e log WhatsApp isolados por loja (1 tabela por schema)
        'crm_vendas',  # CRM Vendas - leads, contas, oportunidades no schema da loja
        'nfse_integration',  # NFS-e emitidas no schema da loja (alinhado ao LojaIsolationManager)
    }
    
    def db_for_read(self, model, **hints):
        """Direciona leitura para o banco correto"""
        if model._meta.app_label in self.suporte_apps:
            return 'suporte'
        
        # Usar get_current_tenant_db do middleware (mesmo storage de thread)
        from tenants.middleware import get_current_tenant_db
        tenant_db = get_current_tenant_db()
        if tenant_db and tenant_db != 'default' and model._meta.app_label in self.loja_apps:
            return tenant_db
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Direciona escrita para o banco correto"""
        if model._meta.app_label in self.suporte_apps:
            return 'suporte'
        
        from tenants.middleware import get_current_tenant_db
        tenant_db = get_current_tenant_db()
        if tenant_db and tenant_db != 'default' and model._meta.app_label in self.loja_apps:
            return tenant_db
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Permite relações apenas dentro do mesmo banco"""
        db1 = self.db_for_read(obj1.__class__)
        db2 = self.db_for_read(obj2.__class__)
        return db1 == db2
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Controla quais apps podem migrar em quais bancos"""
        if app_label in self.suporte_apps:
            return db == 'suporte'
        
        if app_label in self.loja_apps:
            # Permite migração em qualquer banco de loja
            return db.startswith('loja_') or db == 'loja_template'
        
        # Apps padrão (auth, admin, etc) vão para todos os bancos
        return True
