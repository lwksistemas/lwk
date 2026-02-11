"""
Script para verificar estado da Clínica da Beleza em produção
Verifica se o banco está limpo e se tipo de loja + planos existem
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_beleza.models import Payment, Appointment, Patient, Professional, Procedure
from superadmin.models import TipoLoja, PlanoAssinatura

def verificar_estado():
    print("=" * 60)
    print("🔍 VERIFICAÇÃO DO ESTADO DA CLÍNICA DA BELEZA")
    print("=" * 60)
    
    # 1. Verificar tipo de loja
    print("\n📋 1. TIPO DE LOJA:")
    try:
        tipo_loja = TipoLoja.objects.get(slug='clinica-da-beleza')
        print(f"   ✅ Tipo de loja encontrado:")
        print(f"      - ID: {tipo_loja.id}")
        print(f"      - Nome: {tipo_loja.nome}")
        print(f"      - Slug: {tipo_loja.slug}")
    except TipoLoja.DoesNotExist:
        print("   ❌ Tipo de loja NÃO encontrado!")
        return
    
    # 2. Verificar planos
    print("\n💳 2. PLANOS DE ASSINATURA:")
    planos = PlanoAssinatura.objects.filter(tipos_loja=tipo_loja)
    if planos.exists():
        print(f"   ✅ {planos.count()} planos encontrados:")
        for plano in planos:
            print(f"      - {plano.nome}: R$ {plano.preco_mensal}/mês")
    else:
        print("   ❌ Nenhum plano encontrado!")
    
    # 3. Verificar dados no banco
    print("\n📊 3. DADOS NO BANCO (devem estar ZERADOS):")
    
    pacientes = Patient.objects.count()
    profissionais = Professional.objects.count()
    procedimentos = Procedure.objects.count()
    agendamentos = Appointment.objects.count()
    pagamentos = Payment.objects.count()
    
    total = pacientes + profissionais + procedimentos + agendamentos + pagamentos
    
    if total == 0:
        print("   ✅ Banco LIMPO - Nenhum dado de teste encontrado")
    else:
        print("   ⚠️  Banco contém dados:")
    
    print(f"      - Pacientes: {pacientes}")
    print(f"      - Profissionais: {profissionais}")
    print(f"      - Procedimentos: {procedimentos}")
    print(f"      - Agendamentos: {agendamentos}")
    print(f"      - Pagamentos: {pagamentos}")
    
    # 4. Verificar lojas existentes
    print("\n🏪 4. LOJAS CLÍNICA DA BELEZA:")
    try:
        from tenants.models import Loja
        lojas = Loja.objects.filter(tipo_loja=tipo_loja)
        if lojas.exists():
            print(f"   ℹ️  {lojas.count()} loja(s) encontrada(s):")
            for loja in lojas:
                print(f"      - {loja.nome} (slug: {loja.slug})")
                print(f"        Status: {'Ativa' if loja.ativa else 'Inativa'}")
                if hasattr(loja, 'plano_assinatura') and loja.plano_assinatura:
                    print(f"        Plano: {loja.plano_assinatura.nome}")
        else:
            print("   ℹ️  Nenhuma loja criada ainda")
    except ImportError:
        print("   ℹ️  Modelo Loja não disponível (verificação pulada)")
    
    # 5. Resumo final
    print("\n" + "=" * 60)
    print("📝 RESUMO:")
    print("=" * 60)
    
    if tipo_loja and planos.exists() and total == 0:
        print("✅ TUDO PRONTO para criar nova loja!")
        print("   - Tipo de loja: OK")
        print("   - Planos: OK")
        print("   - Banco limpo: OK")
        print("\n👉 Você pode criar a loja em:")
        print("   https://lwksistemas.com.br/superadmin/tipos-loja")
    else:
        print("⚠️  Verificar pendências acima")
    
    print("=" * 60)

if __name__ == '__main__':
    verificar_estado()
