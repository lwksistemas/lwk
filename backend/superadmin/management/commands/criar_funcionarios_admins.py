"""Comando para criar funcionários para administradores de lojas existentes

⚠️ ATENÇÃO: Este comando é apenas para CORREÇÃO de dados antigos!

Lojas novas já têm funcionários criados automaticamente pelo signal em:
backend/superadmin/signals.py -> create_funcionario_for_loja_owner()

Use este comando apenas se:
1. Você tem lojas antigas criadas antes do signal ser implementado
2. Houve algum erro na criação automática e precisa recriar

Uso:
    python manage.py criar_funcionarios_admins
"""
from django.core.management.base import BaseCommand

from superadmin.models import Loja


class Command(BaseCommand):
    help = "Cria funcionários para administradores de lojas existentes que ainda não têm"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Iniciando criação de funcionários para administradores..."))

        lojas = Loja.objects.all()
        total_lojas = lojas.count()
        criados = 0
        ja_existentes = 0
        ignorados = 0
        erros = 0

        for loja in lojas:
            try:
                tipo_loja_nome = loja.tipo_loja.nome
                owner = loja.owner

                self.stdout.write(f"\n📋 Processando loja: {loja.nome} ({tipo_loja_nome})")
                self.stdout.write(f"   Owner: {owner.username} ({owner.email})")

                funcionario_data = {
                    "nome": owner.get_full_name() or owner.username,
                    "email": owner.email,
                    "telefone": "",
                    "cargo": "Administrador",
                    "is_admin": True,
                    "loja_id": loja.id,
                }

                if tipo_loja_nome == "CRM Vendas":
                    self.stdout.write(
                        self.style.WARNING(
                            "   ⚠️ CRM Vendas: admin aparece como Administrador (não é Vendedor). "
                            "Cadastre gerentes/vendedores pela página de funcionários.",
                        ),
                    )
                    ignorados += 1
                    continue

                if tipo_loja_nome == "Clínica da Beleza":
                    from clinica_beleza.models import Professional, ProfissionalUsuario
                    if Professional.objects.filter(email=owner.email, loja_id=loja.id).exists():
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING("   ⚠️ Profissional já existe"))
                        continue
                    prof = Professional.objects.create(**funcionario_data)
                    ProfissionalUsuario.objects.create(loja=loja, professional=prof, user=owner)
                    criados += 1
                    self.stdout.write(self.style.SUCCESS("   ✅ Profissional criado com sucesso!"))
                    continue

                if tipo_loja_nome == "Hotel":
                    from hotel.models import Funcionario
                    if Funcionario.objects.filter(email=owner.email, loja_id=loja.id).exists():
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING("   ⚠️ Funcionário já existe"))
                        continue
                    Funcionario.objects.create(**funcionario_data)
                    criados += 1
                    self.stdout.write(self.style.SUCCESS("   ✅ Funcionário criado com sucesso!"))
                    continue

                self.stdout.write(self.style.WARNING(f"   ⚠️ Tipo de app não reconhecido: {tipo_loja_nome}"))
                ignorados += 1

            except Exception as e:
                erros += 1
                self.stdout.write(self.style.ERROR(f"   ❌ Erro ao processar loja {loja.nome}: {e}"))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Processamento concluído!"))
        self.stdout.write(f"📊 Total de lojas processadas: {total_lojas}")
        self.stdout.write(self.style.SUCCESS(f"✅ Funcionários criados: {criados}"))
        self.stdout.write(self.style.WARNING(f"⚠️ Já existentes: {ja_existentes}"))
        if ignorados > 0:
            self.stdout.write(self.style.WARNING(f"⚠️ Ignorados: {ignorados}"))
        if erros > 0:
            self.stdout.write(self.style.ERROR(f"❌ Erros: {erros}"))
        self.stdout.write("=" * 60)
