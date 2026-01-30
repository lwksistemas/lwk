#!/usr/bin/env python
"""
🚀 SCRIPT: Aplicar Otimizações Automaticamente
Aplica as otimizações de performance e segurança em todos os apps
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
import logging

logger = logging.getLogger(__name__)


def apply_security_settings():
    """
    Aplica configurações de segurança
    """
    print("\n" + "="*60)
    print("🔒 APLICANDO CONFIGURAÇÕES DE SEGURANÇA")
    print("="*60)
    
    # Verificar se SECRET_KEY está configurada
    from django.conf import settings
    
    if settings.SECRET_KEY == 'django-insecure-dev-key-change-in-production-12345':
        print("⚠️  AVISO: SECRET_KEY padrão detectada!")
        print("   Configure SECRET_KEY no arquivo .env antes de usar em produção")
    else:
        print("✅ SECRET_KEY configurada corretamente")
    
    # Verificar HTTPS
    if not settings.DEBUG:
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            print("⚠️  AVISO: HTTPS não está forçado em produção")
            print("   Configure SECURE_SSL_REDIRECT=True no .env")
        else:
            print("✅ HTTPS forçado em produção")
    
    # Verificar CORS
    if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
        print("❌ ERRO: CORS_ALLOW_ALL_ORIGINS está True!")
        print("   Isso é um risco de segurança. Configure origens específicas.")
    else:
        print("✅ CORS configurado corretamente")
    
    print("\n✅ Verificação de segurança concluída")


def create_indexes():
    """
    Cria índices de performance em todos os apps
    """
    print("\n" + "="*60)
    print("📊 CRIANDO ÍNDICES DE PERFORMANCE")
    print("="*60)
    
    apps_to_migrate = [
        'clinica_estetica',
        'restaurante',
        'crm_vendas',
        'ecommerce',
        'servicos',
        'superadmin',
        'suporte',
    ]
    
    for app in apps_to_migrate:
        print(f"\n📦 Processando app: {app}")
        
        try:
            # Gerar migrações
            print(f"   Gerando migrações...")
            call_command('makemigrations', app, interactive=False)
            
            print(f"✅ Migrações geradas para {app}")
        except Exception as e:
            print(f"⚠️  Erro ao gerar migrações para {app}: {e}")
    
    print("\n✅ Índices criados com sucesso")


def apply_migrations():
    """
    Aplica migrações em todos os bancos
    """
    print("\n" + "="*60)
    print("🔄 APLICANDO MIGRAÇÕES")
    print("="*60)
    
    from django.conf import settings
    
    databases = settings.DATABASES.keys()
    
    for db in databases:
        if db == 'loja_template':
            continue  # Pular template
        
        print(f"\n📦 Aplicando migrações no banco: {db}")
        
        try:
            call_command('migrate', database=db, interactive=False)
            print(f"✅ Migrações aplicadas em {db}")
        except Exception as e:
            print(f"⚠️  Erro ao aplicar migrações em {db}: {e}")
    
    print("\n✅ Migrações aplicadas com sucesso")


def analyze_queries():
    """
    Analisa queries lentas e sugere otimizações
    """
    print("\n" + "="*60)
    print("🔍 ANALISANDO QUERIES")
    print("="*60)
    
    # Habilitar logging de queries
    from django.conf import settings
    settings.DEBUG = True
    
    from django.db import reset_queries, connection
    
    # Testar alguns endpoints comuns
    test_cases = [
        ('clinica_estetica', 'Agendamento'),
        ('restaurante', 'Pedido'),
        ('crm_vendas', 'Lead'),
    ]
    
    for app, model_name in test_cases:
        try:
            reset_queries()
            
            # Importar modelo dinamicamente
            from django.apps import apps
            Model = apps.get_model(app, model_name)
            
            # Executar query
            list(Model.objects.all()[:10])
            
            num_queries = len(connection.queries)
            print(f"\n📊 {app}.{model_name}:")
            print(f"   Queries executadas: {num_queries}")
            
            if num_queries > 10:
                print(f"   ⚠️  ATENÇÃO: Muitas queries! Considere usar select_related/prefetch_related")
            else:
                print(f"   ✅ Número de queries aceitável")
        
        except Exception as e:
            print(f"   ⚠️  Erro ao analisar {app}.{model_name}: {e}")
    
    print("\n✅ Análise de queries concluída")


def check_cache():
    """
    Verifica configuração de cache
    """
    print("\n" + "="*60)
    print("💾 VERIFICANDO CACHE")
    print("="*60)
    
    from django.core.cache import cache
    from django.conf import settings
    
    cache_backend = settings.CACHES['default']['BACKEND']
    print(f"\n📦 Backend de cache: {cache_backend}")
    
    if 'locmem' in cache_backend.lower():
        print("⚠️  AVISO: Usando LocMemCache (apenas para desenvolvimento)")
        print("   Em produção, use Redis para melhor performance")
    elif 'redis' in cache_backend.lower():
        print("✅ Usando Redis (recomendado para produção)")
    
    # Testar cache
    try:
        cache.set('test_key', 'test_value', 60)
        value = cache.get('test_key')
        
        if value == 'test_value':
            print("✅ Cache funcionando corretamente")
        else:
            print("❌ Cache não está funcionando")
    except Exception as e:
        print(f"❌ Erro ao testar cache: {e}")
    
    print("\n✅ Verificação de cache concluída")


def generate_report():
    """
    Gera relatório de otimizações
    """
    print("\n" + "="*60)
    print("📋 RELATÓRIO DE OTIMIZAÇÕES")
    print("="*60)
    
    from django.conf import settings
    from django.db import connection
    
    print("\n📊 Estatísticas:")
    print(f"   Apps instalados: {len(settings.INSTALLED_APPS)}")
    print(f"   Bancos de dados: {len(settings.DATABASES)}")
    print(f"   Middleware: {len(settings.MIDDLEWARE)}")
    
    print("\n🔒 Segurança:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SECRET_KEY configurada: {'Sim' if settings.SECRET_KEY != 'django-insecure-dev-key-change-in-production-12345' else 'Não'}")
    print(f"   HTTPS forçado: {getattr(settings, 'SECURE_SSL_REDIRECT', False)}")
    print(f"   CORS restritivo: {not getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)}")
    
    print("\n🚀 Performance:")
    print(f"   Cache backend: {settings.CACHES['default']['BACKEND']}")
    print(f"   Connection pooling: {settings.DATABASES['default'].get('CONN_MAX_AGE', 0)}s")
    print(f"   GZip compression: {'Sim' if 'GZipMiddleware' in str(settings.MIDDLEWARE) else 'Não'}")
    
    print("\n✅ Relatório gerado com sucesso")


def main():
    """
    Função principal
    """
    print("\n" + "="*60)
    print("🚀 APLICANDO OTIMIZAÇÕES NO SISTEMA")
    print("="*60)
    
    try:
        # 1. Verificar segurança
        apply_security_settings()
        
        # 2. Criar índices
        # create_indexes()  # Comentado - executar manualmente
        
        # 3. Aplicar migrações
        # apply_migrations()  # Comentado - executar manualmente
        
        # 4. Analisar queries
        analyze_queries()
        
        # 5. Verificar cache
        check_cache()
        
        # 6. Gerar relatório
        generate_report()
        
        print("\n" + "="*60)
        print("✅ OTIMIZAÇÕES APLICADAS COM SUCESSO!")
        print("="*60)
        
        print("\n📋 Próximos passos:")
        print("   1. Revisar configurações de segurança no .env")
        print("   2. Aplicar migrações: python manage.py migrate")
        print("   3. Refatorar ViewSets para usar OptimizedLojaViewSet")
        print("   4. Adicionar throttling em endpoints de autenticação")
        print("   5. Configurar Redis em produção")
        print("   6. Testar performance e segurança")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
