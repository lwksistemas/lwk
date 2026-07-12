from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Verifica dados após exclusão de lojas'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("🔍 VERIFICAÇÃO DE DADOS APÓS EXCLUSÃO")
        self.stdout.write("=" * 70 + "\n")

        # Lojas
        lojas = Loja.objects.all()
        self.stdout.write(f"📊 Lojas: {lojas.count()}")
        if lojas.exists():
            for loja in lojas:
                self.stdout.write(f"   - {loja.nome} (ID: {loja.id})")

        # Usuários
        users = User.objects.all()
        superusers = User.objects.filter(is_superuser=True)
        regulares = User.objects.filter(is_superuser=False)

        self.stdout.write(f"\n👤 Usuários:")
        self.stdout.write(f"   Total: {users.count()}")
        self.stdout.write(f"   Superusuários: {superusers.count()}")
        self.stdout.write(f"   Regulares: {regulares.count()}")

        if regulares.exists():
            self.stdout.write("\n   Usuários regulares:")
            for user in regulares:
                lojas_owned = Loja.objects.filter(owner=user).count()
                status = "⚠️ ÓRFÃO" if lojas_owned == 0 else f"✅ {lojas_owned} loja(s)"
                self.stdout.write(f"   - {user.username} ({user.email}) - {status}")

        # Apps ativos
        self.stdout.write("\n📦 Dados dos Apps:")

        try:
            from crm_vendas.models import Vendedor
            self.stdout.write(f"\n   CRM Vendas:")
            self.stdout.write(f"   - Vendedores: {Vendedor.objects.count()}")
        except Exception as e:
            self.stdout.write(f"   CRM Vendas: Erro - {e}")

        try:
            from clinica_beleza.models import Patient, Professional, Appointment
            self.stdout.write(f"\n   Clínica da Beleza:")
            self.stdout.write(f"   - Pacientes: {Patient.objects.count()}")
            self.stdout.write(f"   - Profissionais: {Professional.objects.count()}")
            self.stdout.write(f"   - Agendamentos: {Appointment.objects.count()}")
        except Exception as e:
            self.stdout.write(f"   Clínica da Beleza: Erro - {e}")

        try:
            from hotel.models import Hospede, Quarto
            self.stdout.write(f"\n   Hotel:")
            self.stdout.write(f"   - Hóspedes: {Hospede.objects.count()}")
            self.stdout.write(f"   - Quartos: {Quarto.objects.count()}")
        except Exception as e:
            self.stdout.write(f"   Hotel: Erro - {e}")

        self.stdout.write("\n" + "=" * 70 + "\n")
