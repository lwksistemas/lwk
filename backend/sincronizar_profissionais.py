#!/usr/bin/env python
"""
Script para forçar sincronização de Funcionários → Profissionais
Executa o método save() de todos os funcionários com funcao='profissional'
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from cabeleireiro.models import Funcionario, Profissional

def sincronizar_profissionais():
    """Sincroniza todos os funcionários profissionais"""
    
    # Buscar todos os funcionários com função 'profissional'
    funcionarios_profissionais = Funcionario.objects.filter(funcao='profissional')
    
    total = funcionarios_profissionais.count()
    print(f"\n📋 Encontrados {total} funcionários profissionais")
    print("=" * 60)
    
    sincronizados = 0
    erros = 0
    
    for func in funcionarios_profissionais:
        try:
            print(f"\n🔄 Sincronizando: {func.nome} (Loja ID: {func.loja_id})")
            
            # Forçar save para executar sincronização
            func.save()
            
            # Verificar se profissional foi criado
            profissional = Profissional.objects.filter(
                loja_id=func.loja_id,
                nome=func.nome
            ).first()
            
            if profissional:
                print(f"   ✅ Profissional criado/atualizado (ID: {profissional.id})")
                print(f"   📧 Email: {profissional.email or '(vazio)'}")
                print(f"   📱 Telefone: {profissional.telefone}")
                print(f"   ✂️  Especialidade: {profissional.especialidade or '(vazio)'}")
                sincronizados += 1
            else:
                print(f"   ⚠️  Profissional não encontrado após save")
                erros += 1
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            erros += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Sincronizados: {sincronizados}")
    print(f"❌ Erros: {erros}")
    print(f"📊 Total: {total}")
    print("=" * 60)
    
    # Listar todos os profissionais por loja
    print("\n📋 Profissionais por loja:")
    print("=" * 60)
    
    from django.db.models import Count
    lojas_com_profissionais = Profissional.objects.values('loja_id').annotate(
        total=Count('id')
    ).order_by('loja_id')
    
    for loja_info in lojas_com_profissionais:
        loja_id = loja_info['loja_id']
        total_prof = loja_info['total']
        
        print(f"\n🏪 Loja ID {loja_id}: {total_prof} profissional(is)")
        
        profissionais = Profissional.objects.filter(loja_id=loja_id)
        for prof in profissionais:
            status = "✅ Ativo" if prof.is_active else "❌ Inativo"
            print(f"   - {prof.nome} ({status})")

if __name__ == '__main__':
    sincronizar_profissionais()
