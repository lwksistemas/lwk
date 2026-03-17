from django.core.management.base import BaseCommand
from django.conf import settings
from cabeleireiro.models import Funcionario, Profissional
from superadmin.models import Loja


def _ensure_loja_db(loja):
    """Garante que o banco da loja está em settings.DATABASES. Retorna alias ou None."""
    from core.db_config import ensure_loja_database_config
    db_name = getattr(loja, 'database_name', None)
    if not db_name:
        return None
    return db_name if ensure_loja_database_config(db_name, conn_max_age=0) else None


class Command(BaseCommand):
    help = 'Migra funcionários profissionais para tabela de profissionais (por loja, no schema da loja)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default=None,
            help='Slug da loja (opcional). Se informado, usa o schema da loja; senão usa default (legado).',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔄 Iniciando migração...\n')
        slug = options.get('slug')
        db_alias = None
        if slug:
            loja = Loja.objects.filter(slug=slug, is_active=True).first()
            if not loja:
                self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada.'))
                return
            db_alias = _ensure_loja_db(loja)
            if not db_alias:
                self.stdout.write(self.style.WARNING(f'Loja sem database_name ou não PostgreSQL; usando default.'))
            else:
                self.stdout.write(f'📋 Usando schema da loja: {loja.nome} (alias={db_alias})\n')

        base = Funcionario.objects.filter(funcao='profissional')
        if db_alias:
            base = base.using(db_alias)
        funcionarios = list(base)
        self.stdout.write(f'📋 Encontrados {len(funcionarios)} funcionários profissionais\n')

        migrados = 0
        ja_existentes = 0
        prof_qs = Profissional.objects
        if db_alias:
            prof_qs = prof_qs.using(db_alias)

        for func in funcionarios:
            existe = prof_qs.filter(loja_id=func.loja_id, email=func.email).first()
            if existe:
                self.stdout.write(f'⚠️  Já existe: {func.nome} (ID: {existe.id})')
                ja_existentes += 1
                continue
            prof = prof_qs.create(
                loja_id=func.loja_id,
                nome=func.nome,
                email=func.email,
                telefone=func.telefone,
                especialidade=func.especialidade or 'Geral',
                comissao_percentual=func.comissao_percentual,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Criado: {func.nome} (ID: {prof.id})'))
            migrados += 1

        self.stdout.write('\n📊 Resumo:')
        self.stdout.write(self.style.SUCCESS(f'   ✅ Migrados: {migrados}'))
        self.stdout.write(f'   ⚠️  Já existentes: {ja_existentes}')
        self.stdout.write(f'   📋 Total: {len(funcionarios)}')
        self.stdout.write(self.style.SUCCESS('\n✅ Migração concluída!'))
