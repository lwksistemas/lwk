#!/usr/bin/env python
"""
Script para adicionar 'valor_estimado' nas colunas_leads de todas as lojas
que não possuem essa coluna configurada.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from crm_vendas.models_config import CRMConfig
from superadmin.models import Loja

def fix_colunas_leads():
    """Adiciona valor_estimado nas colunas_leads de todas as configurações."""
    print("🔧 Corrigindo colunas_leads em todas as lojas...")
    
    lojas = Loja.objects.filter(ativo=True)
    print(f"📊 Total de lojas ativas: {lojas.count()}")
    
    atualizadas = 0
    
    for loja in lojas:
        try:
            # Buscar ou criar configuração
            config, created = CRMConfig.objects.get_or_create(
                loja_id=loja.id,
                defaults={
                    'origens_leads': CRMConfig.get_default_origens(),
                    'etapas_pipeline': CRMConfig.get_default_etapas(),
                    'colunas_leads': CRMConfig.get_default_colunas_leads(),
                    'modulos_ativos': CRMConfig.get_default_modulos(),
                }
            )
            
            if created:
                print(f"✅ Loja {loja.slug} ({loja.nome}): Configuração criada com colunas padrão")
                atualizadas += 1
                continue
            
            # Verificar se valor_estimado está nas colunas
            if 'valor_estimado' not in config.colunas_leads:
                # Adicionar valor_estimado
                config.colunas_leads.append('valor_estimado')
                config.save(update_fields=['colunas_leads', 'updated_at'])
                print(f"✅ Loja {loja.slug} ({loja.nome}): valor_estimado adicionado")
                atualizadas += 1
            else:
                print(f"ℹ️  Loja {loja.slug} ({loja.nome}): já possui valor_estimado")
                
        except Exception as e:
            print(f"❌ Erro na loja {loja.slug}: {e}")
    
    print(f"\n✅ Processo concluído! {atualizadas} lojas atualizadas.")

if __name__ == '__main__':
    fix_colunas_leads()
