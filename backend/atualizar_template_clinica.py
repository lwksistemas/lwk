#!/usr/bin/env python3
"""
Script para atualizar o template padrão da Clínica de Estética
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import TipoLoja

def atualizar_template_clinica():
    """Atualiza o template padrão da Clínica de Estética"""
    print("🏥 Atualizando Template - Clínica de Estética")
    print("=" * 50)
    
    try:
        # Buscar o tipo de loja Clínica de Estética
        tipo_clinica = TipoLoja.objects.filter(nome='Clínica de Estética').first()
        
        if not tipo_clinica:
            print("❌ Tipo de loja 'Clínica de Estética' não encontrado")
            return
        
        print(f"✅ Tipo de loja encontrado: {tipo_clinica.nome}")
        print(f"   ID: {tipo_clinica.id}")
        print(f"   Descrição atual: {tipo_clinica.descricao}")
        
        # Atualizar descrição com as melhorias
        nova_descricao = """Dashboard completo para clínicas de estética com:

🚀 AÇÕES RÁPIDAS COM CORES ESPECÍFICAS:
• 📅 Agendamento (Azul) - Gerenciar consultas
• 🗓️ Calendário (Verde) - Visualização mensal/semanal  
• 🏥 Consultas (Roxo) - Sistema completo de consultas
• 👤 Cliente (Amarelo) - Cadastro de pacientes
• 👨‍⚕️ Profissional (Vermelho) - Equipe médica
• 💆 Procedimentos (Ciano) - Tratamentos disponíveis
• 📋 Protocolos (Marrom) - Protocolos padronizados
• 📊 Evolução (Vermelho escuro) - Acompanhamento do paciente
• 📝 Anamnese (Roxo escuro) - Histórico médico
• 📈 Relatórios (Verde escuro) - Análises e estatísticas

✨ RECURSOS AVANÇADOS:
• Sistema completo de consultas com evolução do paciente
• Calendário interativo com visualização por dia/semana/mês
• Protocolos de procedimentos estéticos
• Anamnese digital personalizada
• Dashboard responsivo e intuitivo
• Interface otimizada para clínicas de estética

🎨 DESIGN MELHORADO:
• Cabeçalho com gradiente e informações contextuais
• Cores específicas para cada funcionalidade
• Sombras e animações suaves
• Layout responsivo para todos os dispositivos
• Legenda explicativa das cores

Este template é automaticamente aplicado a todas as novas lojas do tipo 'Clínica de Estética'."""
        
        tipo_clinica.descricao = nova_descricao
        tipo_clinica.save()
        
        print("✅ Template atualizado com sucesso!")
        print("\n📋 Nova descrição salva:")
        print(nova_descricao[:200] + "...")
        
        # Verificar quantas lojas existem deste tipo
        lojas_clinica = tipo_clinica.lojas.all()
        print(f"\n📊 Lojas afetadas: {lojas_clinica.count()}")
        
        for loja in lojas_clinica:
            print(f"   • {loja.nome} (slug: {loja.slug})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar template: {e}")
        return False

def criar_documentacao_cores():
    """Cria documentação das cores do dashboard"""
    print("\n🎨 Documentação das Cores - Dashboard Clínica")
    print("=" * 50)
    
    cores_dashboard = {
        "Agendamento": {"cor": "#3B82F6", "nome": "Azul", "emoji": "📅"},
        "Calendário": {"cor": "#10B981", "nome": "Verde", "emoji": "🗓️"},
        "Consultas": {"cor": "#8B5CF6", "nome": "Roxo", "emoji": "🏥"},
        "Cliente": {"cor": "#F59E0B", "nome": "Amarelo", "emoji": "👤"},
        "Profissional": {"cor": "#EF4444", "nome": "Vermelho", "emoji": "👨‍⚕️"},
        "Procedimentos": {"cor": "#06B6D4", "nome": "Ciano", "emoji": "💆"},
        "Protocolos": {"cor": "#8B5A2B", "nome": "Marrom", "emoji": "📋"},
        "Evolução": {"cor": "#DC2626", "nome": "Vermelho escuro", "emoji": "📊"},
        "Anamnese": {"cor": "#7C3AED", "nome": "Roxo escuro", "emoji": "📝"},
        "Relatórios": {"cor": "#059669", "nome": "Verde escuro", "emoji": "📈"}
    }
    
    print("Cores padronizadas para o dashboard:")
    for funcao, info in cores_dashboard.items():
        print(f"   {info['emoji']} {funcao}: {info['cor']} ({info['nome']})")
    
    return cores_dashboard

def main():
    print("🏥 Atualização do Template - Clínica de Estética")
    print("=" * 55)
    
    # Atualizar template
    sucesso = atualizar_template_clinica()
    
    # Criar documentação
    cores = criar_documentacao_cores()
    
    if sucesso:
        print("\n🎯 Resultado:")
        print("✅ Template da Clínica de Estética atualizado")
        print("✅ Cores padronizadas definidas")
        print("✅ Melhorias salvas como padrão")
        print("\n📱 Todas as novas lojas 'Clínica de Estética' terão:")
        print("• Dashboard com cores específicas")
        print("• Cabeçalho melhorado")
        print("• Layout responsivo")
        print("• Sistema completo de consultas")
        
        print(f"\n🔗 Teste em: https://lwksistemas.com.br/loja/felix/dashboard")
    else:
        print("\n❌ Falha na atualização do template")

if __name__ == "__main__":
    main()