"""
Ativa termo de consentimento em um procedimento da loja.

Uso:
    python manage.py ativar_termo_procedimento --slug beleza --nome "Botox"
    python manage.py ativar_termo_procedimento --slug beleza --id 5
"""
from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

from clinica_beleza.models import Procedure

TERMO_BOTOX = """TERMO DE CONSENTIMENTO ESCLARECIDO — APLICAÇÃO DE TOXINA BOTULÍNICA

Eu, {paciente_nome}, portador(a) do CPF {paciente_cpf}, declaro ter sido informado(a) de forma clara e adequada pela profissional {profissional_nome} ({profissional_conselho}), na clínica {clinica_nome}, sobre o procedimento de aplicação de toxina botulínica tipo A.

Fui esclarecido(a) sobre:
• Objetivo do tratamento: suavização de rugas de expressão e linhas dinâmicas.
• Benefícios esperados e limitações do resultado.
• Riscos e efeitos adversos possíveis: dor local, edema, equimose, assimetria temporária, ptose palpebral, cefaleia, reação alérgica e outros descritos em literatura médica.
• Contraindicações: gravidez, amamentação, doenças neuromusculares, infecção local ativa, hipersensibilidade conhecida ao produto, entre outras avaliadas na consulta.
• Alternativas terapêuticas disponíveis.
• Cuidados pré e pós-procedimento.

Declaro que tive oportunidade de esclarecer minhas dúvidas, que as respostas foram satisfatórias e que concordo voluntariamente com a realização do procedimento na data {data}.

Comprometo-me a informar imediatamente a clínica sobre qualquer intercorrência após o tratamento."""

TERMO_CRIOLIPOLISE = """TERMO DE CONSENTIMENTO ESCLARECIDO — CRIOLIPÓLISE

Eu, {paciente_nome}, portador(a) do CPF {paciente_cpf}, declaro ter sido informado(a) pela profissional {profissional_nome} ({profissional_conselho}), na clínica {clinica_nome}, sobre o procedimento de criolipólise para redução de gordura localizada.

Fui esclarecido(a) sobre objetivos, número de sessões recomendadas, resultados graduais, riscos (equimose, edema, dormência temporária, assimetria, paradoxical adipose hyperplasia em casos raros), contraindicações e cuidados pós-procedimento.

Concordo voluntariamente com a realização do tratamento na data {data}."""

TERMO_PREENCHIMENTO = """TERMO DE CONSENTIMENTO ESCLARECIDO — PREENCHIMENTO COM ÁCIDO HIALURÔNICO

Eu, {paciente_nome}, portador(a) do CPF {paciente_cpf}, declaro ter sido informado(a) pela profissional {profissional_nome} ({profissional_conselho}), na clínica {clinica_nome}, sobre o procedimento de preenchimento com ácido hialurônico.

Fui esclarecido(a) sobre indicação, material utilizado, duração esperada do resultado, riscos (edema, hematoma, assimetria, nódulos, reação alérgica, isquemia/vascular em casos raros), contraindicações e possibilidade de reversão com hialuronidase quando aplicável.

Concordo voluntariamente com a realização do procedimento na data {data}."""

TERMO_CARBOXITERAPIA = """TERMO DE CONSENTIMENTO ESCLARECIDO — CARBOXITERAPIA

Eu, {paciente_nome}, portador(a) do CPF {paciente_cpf}, declaro ter sido informado(a) pela profissional {profissional_nome} ({profissional_conselho}), na clínica {clinica_nome}, sobre o procedimento de carboxiterapia.

Fui esclarecido(a) sobre finalidade do tratamento, técnica de aplicação, sensações durante a sessão, riscos (dor local, equimose, crepitação subcutânea), contraindicações e número de sessões indicadas.

Concordo voluntariamente com a realização do procedimento na data {data}."""

TERMO_GENERICO = """TERMO DE CONSENTIMENTO ESCLARECIDO — {procedimento}

Eu, {paciente_nome}, portador(a) do CPF {paciente_cpf}, declaro ter sido informado(a) de forma clara e adequada pela profissional {profissional_nome} ({profissional_conselho}), na clínica {clinica_nome}, sobre o procedimento: {procedimentos}.

Fui esclarecido(a) sobre objetivos, benefícios, riscos, efeitos adversos, contraindicações, alternativas terapêuticas e cuidados necessários. Tive oportunidade de esclarecer minhas dúvidas e concordo voluntariamente com a realização do procedimento na data {data}."""


def _resolver_loja(slug_filter: str):
    slug_filter = slug_filter.strip().lower()
    for loja in Loja.objects.filter(is_active=True, database_created=True):
        if slug_filter in (
            (loja.slug or '').lower(),
            (getattr(loja, 'atalho', None) or '').lower(),
            str(loja.id),
        ):
            return loja
    return None


class Command(BaseCommand):
    help = 'Ativa termo de consentimento real em procedimento da loja.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, required=True, help='Slug, atalho ou id da loja')
        parser.add_argument('--nome', type=str, help='Nome (ou parte) do procedimento')
        parser.add_argument('--id', type=int, help='ID do procedimento')
        parser.add_argument('--todos-botox', action='store_true', help='Ativa em todos com "botox" no nome')

    def handle(self, *args, **options):
        loja = _resolver_loja(options['slug'])
        if not loja:
            self.stderr.write(self.style.ERROR(f'Loja não encontrada: {options["slug"]}'))
            return

        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            self.stderr.write(self.style.ERROR('Banco da loja indisponível.'))
            return

        set_current_tenant_db(loja.database_name)
        set_current_loja_id(loja.id)

        qs = Procedure.objects.filter(is_active=True)
        if options.get('id'):
            qs = qs.filter(id=options['id'])
        elif options.get('todos_botox'):
            qs = qs.filter(nome__icontains='botox')
        elif options.get('nome'):
            qs = qs.filter(nome__icontains=options['nome'].strip())
        else:
            self.stderr.write(self.style.ERROR('Informe --nome, --id ou --todos-botox'))
            return

        procedimentos = list(qs)
        if not procedimentos:
            self.stderr.write(self.style.ERROR('Nenhum procedimento encontrado.'))
            return

        def _texto_termo(nome: str) -> str:
            n = nome.lower()
            if 'botox' in n or 'botul' in n:
                return TERMO_BOTOX
            if 'criolip' in n or 'cryolip' in n:
                return TERMO_CRIOLIPOLISE
            if 'preench' in n:
                return TERMO_PREENCHIMENTO
            if 'carbox' in n:
                return TERMO_CARBOXITERAPIA
            return TERMO_GENERICO.replace('{procedimento}', nome.upper())

        for proc in procedimentos:
            texto = _texto_termo(proc.nome)

            proc.termo_consentimento = texto
            proc.termo_consentimento_ativo = True
            proc.save(update_fields=['termo_consentimento', 'termo_consentimento_ativo', 'updated_at'])
            self.stdout.write(self.style.SUCCESS(
                f'✓ Procedimento #{proc.id} "{proc.nome}" — termo ativado ({len(texto)} caracteres)'
            ))
