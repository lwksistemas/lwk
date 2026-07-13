"""Service layer para documentos clínicos: renderização de templates,
criação de documentos durante consulta e agregação do prontuário.
"""
from django.utils.timezone import now

from .models import (
    Consulta,
    ConsultaEvolucao,
    DocumentoClinico,
    PatientAnamnese,
    PrescricaoMemed,
)

# ---------------------------------------------------------------------------
# Placeholders suportados nos templates de documentos clínicos
# ---------------------------------------------------------------------------

PLACEHOLDERS = {
    "{{paciente_nome}}": lambda ctx: ctx["patient"].nome,
    "{{paciente_cpf}}": lambda ctx: ctx["patient"].cpf or "",
    "{{paciente_data_nascimento}}": lambda ctx: str(ctx["patient"].data_nascimento or ""),
    "{{profissional_nome}}": lambda ctx: ctx["professional"].nome,
    "{{profissional_registro}}": lambda ctx: ctx["professional"].registro_profissional or "",
    "{{profissional_conselho}}": lambda ctx: (
        ctx["professional"].formatar_conselho()
        if hasattr(ctx["professional"], "formatar_conselho")
        else (ctx["professional"].conselho or "")
    ),
    "{{data_atual}}": lambda ctx: ctx["now"].strftime("%d/%m/%Y"),
    "{{consulta_procedimento}}": lambda ctx: ctx["consulta"].procedure.nome if ctx["consulta"].procedure else "",
}


def render_template(template_content: str, context: dict) -> str:
    """Substitui placeholders no conteúdo do template pelos valores reais do contexto.

    O `context` deve conter as chaves:
        - patient: instância de Patient
        - professional: instância de Professional
        - consulta: instância de Consulta
        - now: datetime (opcional, usa now() se ausente)
    """
    if "now" not in context:
        context["now"] = now()

    result = template_content
    for placeholder, resolver in PLACEHOLDERS.items():
        if placeholder in result:
            try:
                value = resolver(context)
            except (AttributeError, KeyError, TypeError):
                value = ""
            result = result.replace(placeholder, str(value))
    return result


def criar_documento(
    *,
    consulta: Consulta,
    professional,
    tipo: str,
    conteudo: str,
    template=None,
    titulo: str = "",
) -> DocumentoClinico:
    """Cria um DocumentoClinico vinculado à consulta.

    Regras:
        - A consulta deve estar com status IN_PROGRESS.
        - Lança ValueError se a consulta não estiver em atendimento.
    """
    if consulta.status != "IN_PROGRESS":
        raise ValueError(
            "Documentos clínicos só podem ser criados durante uma consulta em atendimento (IN_PROGRESS).",
        )

    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    documento = DocumentoClinico(
        consulta=consulta,
        patient=consulta.patient,
        professional=professional,
        template=template,
        tipo=tipo,
        titulo=titulo,
        conteudo=conteudo,
        loja_id=consulta.loja_id,
    )
    if tenant_db and tenant_db != "default":
        documento.save(using=tenant_db)
    else:
        documento.save()
    return documento


def listar_prontuario_paciente(patient_id: int, secao: str = None) -> dict:
    """Agrega o prontuário do paciente por seções.

    Retorna dict com keys:
        - receituario: DocumentoClinico (tipo=receituario) + PrescricaoMemed
        - pedido_exame: DocumentoClinico (tipo=pedido_exame)
        - atestado: DocumentoClinico (tipo=atestado)
        - documento_personalizado: DocumentoClinico (tipo=documento_personalizado)
        - evolucao: ConsultaEvolucao
        - anamnese: PatientAnamnese

    Apenas documentos de consultas com status COMPLETED ou IN_PROGRESS são incluídos
    (Requisito 3.2). Documentos são ordenados cronologicamente do mais recente
    para o mais antigo (Requisito 3.3).

    Se `secao` for informada, retorna apenas a seção solicitada (Requisito 3.4).
    """
    from django.db.models import Q

    # Status de consulta válidos para exibição no prontuário
    STATUS_PRONTUARIO = ["COMPLETED", "IN_PROGRESS"]

    prontuario = {}

    # --- Receituário (Requisito 3.5: agrega DocumentoClinico + PrescricaoMemed) ---
    if secao is None or secao == "receituario":
        docs_receituario = list(
            DocumentoClinico.objects.filter(
                patient_id=patient_id,
                tipo="receituario",
                consulta__status__in=STATUS_PRONTUARIO,
            ).select_related("professional", "consulta").order_by("-created_at"),
        )
        # PrescricaoMemed: consulta pode ser nula (prescrições avulsas da Memed).
        # Incluímos prescrições vinculadas a consultas válidas OU sem consulta vinculada.
        prescricoes_memed = list(
            PrescricaoMemed.objects.filter(
                Q(consulta__status__in=STATUS_PRONTUARIO) | Q(consulta__isnull=True),
                patient_id=patient_id,
            ).select_related("professional", "consulta").order_by("-created_at"),
        )
        prontuario["receituario"] = docs_receituario + prescricoes_memed

    # --- Pedido de Exame ---
    if secao is None or secao == "pedido_exame":
        prontuario["pedido_exame"] = list(
            DocumentoClinico.objects.filter(
                patient_id=patient_id,
                tipo="pedido_exame",
                consulta__status__in=STATUS_PRONTUARIO,
            ).select_related("professional", "consulta").order_by("-created_at"),
        )

    # --- Atestado ---
    if secao is None or secao == "atestado":
        prontuario["atestado"] = list(
            DocumentoClinico.objects.filter(
                patient_id=patient_id,
                tipo="atestado",
                consulta__status__in=STATUS_PRONTUARIO,
            ).select_related("professional", "consulta").order_by("-created_at"),
        )

    # --- Documento Personalizado (Atendimento) ---
    if secao is None or secao == "documento_personalizado":
        prontuario["documento_personalizado"] = list(
            DocumentoClinico.objects.filter(
                patient_id=patient_id,
                tipo="documento_personalizado",
                consulta__status__in=STATUS_PRONTUARIO,
            ).select_related("professional", "consulta").order_by("-created_at"),
        )

    # --- Evolução ---
    if secao is None or secao == "evolucao":
        prontuario["evolucao"] = list(
            ConsultaEvolucao.objects.filter(
                patient_id=patient_id,
                consulta__status__in=STATUS_PRONTUARIO,
            ).select_related("professional", "consulta").order_by("-created_at"),
        )

    # --- Anamnese (não depende de consulta, é registro por paciente) ---
    if secao is None or secao == "anamnese":
        anamnese = PatientAnamnese.objects.filter(patient_id=patient_id).first()
        prontuario["anamnese"] = anamnese

    return prontuario
