"""Admin e API pública do Agendamento Online."""
from __future__ import annotations

import logging
from datetime import datetime

from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import get_current_timezone, is_naive, make_aware
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.permissions import CLINICA_ADMIN
from tenants.middleware import _configure_tenant_db_for_loja, get_current_loja_id

from .agendamento_online_service import (
    AgendamentoOnlineError,
    categorias_com_procedimentos,
    config_publica_ativa,
    criar_agendamento_online,
    dias_com_vaga,
    gerar_slots_dia,
    get_or_create_config,
    procedimentos_liberados,
    profissionais_para_procedimento,
    serializar_procedimento_publico,
    serializar_profissional_publico,
)
from .models import (
    AgendamentoOnlineHorario,
    AgendamentoOnlineProcedimento,
    AgendamentoOnlineProfissional,
    Appointment,
    Procedure,
    Professional,
)

logger = logging.getLogger(__name__)


def _loja_from_slug(slug: str):
    from superadmin.models import Loja

    return (
        Loja.objects.using("default")
        .select_related("plano")
        .filter(slug=slug, is_active=True)
        .first()
    )


def _ativar_tenant(loja) -> bool:
    return bool(_configure_tenant_db_for_loja(loja))


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

class AgendamentoOnlineConfigView(APIView):
    """GET/PATCH /clinica-beleza/agendamento-online/config/"""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        loja_id = get_current_loja_id()
        cfg = get_or_create_config(loja_id)
        return Response(_serialize_config(cfg, request))

    def patch(self, request):
        loja_id = get_current_loja_id()
        cfg = get_or_create_config(loja_id)
        data = request.data or {}
        campos = [
            "ativo", "antecedencia_minima_horas", "dias_futuros", "permitir_mesmo_dia",
            "intervalo_slots_minutos", "modo_confirmacao", "permitir_cancelamento_cliente",
            "permitir_reagendamento_cliente", "prazo_cancelamento_horas", "reserva_pendente_minutos",
            "enviar_confirmacao", "enviar_lembrete", "enviar_cancelamento", "enviar_reagendamento",
            "notificar_secretaria", "botao_whatsapp_ativo", "whatsapp_secretaria",
            "nome_publico", "texto_apresentacao", "logo_url", "banner_url",
            "cor_primaria", "cor_secundaria", "endereco_publico", "telefone_publico",
            "politica_privacidade",
        ]
        for campo in campos:
            if campo in data:
                setattr(cfg, campo, data[campo])
        cfg.save()
        return Response(_serialize_config(cfg, request))


def _serialize_config(cfg, request=None) -> dict:
    slug = ""
    if request is not None:
        slug = getattr(getattr(request, "loja", None), "slug", "") or ""
        if not slug:
            try:
                from superadmin.models import Loja
                loja = Loja.objects.using("default").filter(pk=cfg.loja_id).first()
                slug = getattr(loja, "slug", "") or ""
            except Exception:
                slug = ""
    link = f"/loja/{slug}/agendamento-online" if slug else ""
    return {
        "id": cfg.id,
        "ativo": cfg.ativo,
        "antecedencia_minima_horas": cfg.antecedencia_minima_horas,
        "dias_futuros": cfg.dias_futuros,
        "permitir_mesmo_dia": cfg.permitir_mesmo_dia,
        "intervalo_slots_minutos": cfg.intervalo_slots_minutos,
        "modo_confirmacao": cfg.modo_confirmacao,
        "permitir_cancelamento_cliente": cfg.permitir_cancelamento_cliente,
        "permitir_reagendamento_cliente": cfg.permitir_reagendamento_cliente,
        "prazo_cancelamento_horas": cfg.prazo_cancelamento_horas,
        "reserva_pendente_minutos": cfg.reserva_pendente_minutos,
        "enviar_confirmacao": cfg.enviar_confirmacao,
        "enviar_lembrete": cfg.enviar_lembrete,
        "enviar_cancelamento": cfg.enviar_cancelamento,
        "enviar_reagendamento": cfg.enviar_reagendamento,
        "notificar_secretaria": cfg.notificar_secretaria,
        "botao_whatsapp_ativo": cfg.botao_whatsapp_ativo,
        "whatsapp_secretaria": cfg.whatsapp_secretaria,
        "nome_publico": cfg.nome_publico,
        "texto_apresentacao": cfg.texto_apresentacao,
        "logo_url": cfg.logo_url,
        "banner_url": cfg.banner_url,
        "cor_primaria": cfg.cor_primaria,
        "cor_secundaria": cfg.cor_secundaria,
        "endereco_publico": cfg.endereco_publico,
        "telefone_publico": cfg.telefone_publico,
        "politica_privacidade": cfg.politica_privacidade,
        "link_publico": link,
    }


class AgendamentoOnlineProfissionaisView(APIView):
    """GET/PUT /clinica-beleza/agendamento-online/profissionais/"""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        get_current_loja_id()
        pros = Professional.objects.filter(is_active=True, is_profissional=True).order_by("nome")
        vinculos = {
            v.professional_id: v
            for v in AgendamentoOnlineProfissional.objects.filter(professional_id__in=[p.id for p in pros]).prefetch_related("horarios")
        }
        saida = []
        for p in pros:
            v = vinculos.get(p.id)
            saida.append({
                "professional_id": p.id,
                "nome": p.nome,
                "especialidade": p.especialidade or "",
                "foto_url": getattr(p, "foto_url", None) or "",
                "liberado": bool(v.liberado) if v else False,
                "bloqueado_temporariamente": bool(v.bloqueado_temporariamente) if v else False,
                "usar_horarios_exclusivos": bool(v.usar_horarios_exclusivos) if v else False,
                "horarios": [
                    {
                        "id": h.id,
                        "dia_semana": h.dia_semana,
                        "hora_inicio": h.hora_inicio.strftime("%H:%M"),
                        "hora_fim": h.hora_fim.strftime("%H:%M"),
                        "ativo": h.ativo,
                    }
                    for h in (v.horarios.all() if v else [])
                ],
            })
        return Response(saida)

    def put(self, request):
        loja_id = get_current_loja_id()
        itens = request.data if isinstance(request.data, list) else request.data.get("profissionais") or []
        for item in itens:
            pid = item.get("professional_id") or item.get("professional")
            if not pid:
                continue
            prof = Professional.objects.filter(pk=pid, is_active=True).first()
            if not prof:
                continue
            v, _ = AgendamentoOnlineProfissional.objects.get_or_create(
                professional=prof, defaults={"loja_id": loja_id},
            )
            for campo in ("liberado", "bloqueado_temporariamente", "usar_horarios_exclusivos"):
                if campo in item:
                    setattr(v, campo, bool(item[campo]))
            if not v.loja_id:
                v.loja_id = loja_id
            v.save()
            if "horarios" in item:
                v.horarios.all().delete()
                for h in item.get("horarios") or []:
                    AgendamentoOnlineHorario.objects.create(
                        vinculo=v,
                        loja_id=loja_id,
                        dia_semana=int(h["dia_semana"]),
                        hora_inicio=h["hora_inicio"],
                        hora_fim=h["hora_fim"],
                        ativo=bool(h.get("ativo", True)),
                    )
        return self.get(request)


class AgendamentoOnlineProcedimentosView(APIView):
    """GET/POST /clinica-beleza/agendamento-online/procedimentos/"""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        get_current_loja_id()
        vinculos = (
            AgendamentoOnlineProcedimento.objects.select_related("procedure")
            .prefetch_related("profissionais")
            .order_by("ordem", "id")
        )
        return Response([_serialize_proc_admin(v) for v in vinculos])

    def post(self, request):
        loja_id = get_current_loja_id()
        pid = request.data.get("procedure_id") or request.data.get("procedure")
        procedure = Procedure.objects.filter(pk=pid, is_active=True).first()
        if not procedure:
            return Response({"error": "Procedimento não encontrado."}, status=400)
        v, created = AgendamentoOnlineProcedimento.objects.get_or_create(
            procedure=procedure,
            defaults={
                "loja_id": loja_id,
                "liberado": True,
                "exibir_valor": bool(request.data.get("exibir_valor", True)),
            },
        )
        if not created:
            return Response({"error": "Procedimento já vinculado."}, status=400)
        ids = request.data.get("profissionais") or []
        if ids:
            v.profissionais.set(Professional.objects.filter(pk__in=ids))
        return Response(_serialize_proc_admin(v), status=201)


class AgendamentoOnlineProcedimentoDetailView(APIView):
    """PATCH/DELETE /clinica-beleza/agendamento-online/procedimentos/<pk>/"""

    permission_classes = CLINICA_ADMIN

    def patch(self, request, pk):
        get_current_loja_id()
        v = AgendamentoOnlineProcedimento.objects.filter(pk=pk).select_related("procedure").first()
        if not v:
            return Response({"error": "Não encontrado."}, status=404)
        for campo in ("liberado", "exibir_valor", "ordem"):
            if campo in request.data:
                setattr(v, campo, request.data[campo])
        v.save()
        if "profissionais" in request.data:
            ids = request.data.get("profissionais") or []
            v.profissionais.set(Professional.objects.filter(pk__in=ids))
        return Response(_serialize_proc_admin(v))

    def delete(self, request, pk):
        get_current_loja_id()
        deleted, _ = AgendamentoOnlineProcedimento.objects.filter(pk=pk).delete()
        if not deleted:
            return Response({"error": "Não encontrado."}, status=404)
        return Response(status=204)


def _serialize_proc_admin(v: AgendamentoOnlineProcedimento) -> dict:
    p = v.procedure
    return {
        "id": v.id,
        "procedure_id": p.id,
        "nome": p.nome,
        "categoria": p.categoria or "",
        "duracao_minutos": int(p.duracao_minutos or 0),
        "preco": str(p.preco) if p.preco is not None else None,
        "liberado": v.liberado,
        "exibir_valor": v.exibir_valor,
        "ordem": v.ordem,
        "profissionais": list(v.profissionais.values_list("id", flat=True)),
        "profissionais_nomes": list(v.profissionais.values_list("nome", flat=True)),
    }


# ---------------------------------------------------------------------------
# Público (AllowAny + slug)
# ---------------------------------------------------------------------------

class AgendamentoOnlinePublicoInfoView(APIView):
    """GET /clinica-beleza/agendamento-online/publico/<slug>/"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        loja = _loja_from_slug(slug)
        if not loja:
            return Response({"disponivel": False, "error": "Clínica não encontrada."}, status=404)
        from superadmin.plano_features import loja_plano_permite_agendamento_online

        ok, msg = loja_plano_permite_agendamento_online(loja)
        if not ok:
            return Response({"disponivel": False, "error": msg or "Agendamento online indisponível."})
        if not _ativar_tenant(loja):
            return Response({"disponivel": False, "error": "Clínica indisponível."}, status=503)
        cfg = config_publica_ativa(loja.id)
        if not cfg:
            return Response({
                "disponivel": False,
                "error": "O agendamento online está temporariamente indisponível.",
                "telefone": getattr(loja, "telefone", "") or "",
                "nome": loja.nome,
            })
        whatsapp = cfg.whatsapp_secretaria or cfg.telefone_publico or getattr(loja, "telefone", "") or ""
        return Response({
            "disponivel": True,
            "slug": slug,
            "nome": cfg.nome_publico or loja.nome,
            "texto_apresentacao": cfg.texto_apresentacao
                or "Agende seu atendimento de forma prática, rápida e segura.",
            "logo_url": cfg.logo_url or getattr(loja, "logo", None) or getattr(loja, "login_logo", None) or "",
            "banner_url": cfg.banner_url or getattr(loja, "login_background", None) or "",
            "cor_primaria": cfg.cor_primaria or getattr(loja, "cor_primaria", None) or "#EC4899",
            "cor_secundaria": cfg.cor_secundaria or getattr(loja, "cor_secundaria", None) or "#DB2777",
            "endereco": cfg.endereco_publico or "",
            "telefone": cfg.telefone_publico or getattr(loja, "telefone", "") or "",
            "politica_privacidade": cfg.politica_privacidade or "",
            "botao_whatsapp_ativo": cfg.botao_whatsapp_ativo,
            "whatsapp": whatsapp,
            "modo_confirmacao": cfg.modo_confirmacao,
        })


class AgendamentoOnlinePublicoCategoriasView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        loja = _loja_from_slug(slug)
        if not loja or not _ativar_tenant(loja):
            return Response({"error": "Indisponível."}, status=404)
        if not config_publica_ativa(loja.id):
            return Response({"error": "Agendamento online desativado."}, status=403)
        return Response(categorias_com_procedimentos(loja.id))


class AgendamentoOnlinePublicoProcedimentosView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        loja = _loja_from_slug(slug)
        if not loja or not _ativar_tenant(loja):
            return Response({"error": "Indisponível."}, status=404)
        if not config_publica_ativa(loja.id):
            return Response({"error": "Agendamento online desativado."}, status=403)
        categoria = (request.query_params.get("categoria") or "").strip()
        itens = []
        for v in procedimentos_liberados(loja.id):
            if categoria and (v.procedure.categoria or "") != categoria:
                continue
            itens.append(serializar_procedimento_publico(v))
        return Response(itens)


class AgendamentoOnlinePublicoProfissionaisView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        loja = _loja_from_slug(slug)
        if not loja or not _ativar_tenant(loja):
            return Response({"error": "Indisponível."}, status=404)
        if not config_publica_ativa(loja.id):
            return Response({"error": "Agendamento online desativado."}, status=403)
        procedure_id = request.query_params.get("procedure")
        vinculo = (
            AgendamentoOnlineProcedimento.objects.filter(
                procedure_id=procedure_id, liberado=True,
            ).first()
        )
        if not vinculo:
            return Response([])
        return Response([
            serializar_profissional_publico(v)
            for v in profissionais_para_procedimento(vinculo)
        ])


class AgendamentoOnlinePublicoDisponibilidadeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        loja = _loja_from_slug(slug)
        if not loja or not _ativar_tenant(loja):
            return Response({"error": "Indisponível."}, status=404)
        cfg = config_publica_ativa(loja.id)
        if not cfg:
            return Response({"error": "Agendamento online desativado."}, status=403)
        try:
            professional_id = int(request.query_params.get("professional"))
            procedure_id = int(request.query_params.get("procedure"))
        except (TypeError, ValueError):
            return Response({"error": "Informe professional e procedure."}, status=400)
        professional = Professional.objects.filter(pk=professional_id, is_active=True).first()
        procedure = Procedure.objects.filter(pk=procedure_id, is_active=True).first()
        if not professional or not procedure:
            return Response({"error": "Dados inválidos."}, status=400)
        dia_raw = request.query_params.get("date")
        if dia_raw:
            dia = parse_date(dia_raw)
            if not dia:
                return Response({"error": "Data inválida."}, status=400)
            return Response({
                "date": dia.isoformat(),
                "slots": gerar_slots_dia(
                    professional=professional, procedure=procedure, dia=dia, config=cfg,
                ),
            })
        return Response({
            "dias": dias_com_vaga(professional=professional, procedure=procedure, config=cfg),
        })


class AgendamentoOnlinePublicoCriarView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, slug):
        loja = _loja_from_slug(slug)
        if not loja or not _ativar_tenant(loja):
            return Response({"error": "Indisponível."}, status=404)
        cfg = config_publica_ativa(loja.id)
        if not cfg:
            return Response({"error": "Agendamento online desativado."}, status=403)

        data = request.data or {}
        nome = (data.get("nome") or "").strip()
        telefone = (data.get("telefone") or data.get("celular") or "").strip()
        if not nome or not telefone:
            return Response({"error": "Nome e celular são obrigatórios."}, status=400)
        try:
            professional_id = int(data.get("professional"))
            procedure_id = int(data.get("procedure"))
        except (TypeError, ValueError):
            return Response({"error": "Procedimento e profissional são obrigatórios."}, status=400)

        date_raw = data.get("date") or data.get("data")
        date_start = parse_datetime(str(date_raw)) if date_raw else None
        if date_start is None and data.get("date_ymd") and data.get("time"):
            date_start = parse_datetime(f"{data['date_ymd']}T{data['time']}:00")
        if date_start is None:
            return Response({"error": "Data/hora inválida."}, status=400)
        if is_naive(date_start):
            date_start = make_aware(date_start, get_current_timezone())

        nascimento = None
        if data.get("data_nascimento"):
            nascimento = parse_date(str(data.get("data_nascimento")))

        try:
            appointment = criar_agendamento_online(
                loja_id=loja.id,
                config=cfg,
                professional_id=professional_id,
                procedure_id=procedure_id,
                date_start=date_start,
                nome=nome,
                telefone=telefone,
                email=(data.get("email") or "").strip(),
                observacoes=(data.get("observacoes") or "").strip(),
                data_nascimento=nascimento,
            )
        except AgendamentoOnlineError as exc:
            return Response({"error": exc.message}, status=400)
        except Exception as exc:
            from .agenda_service import AgendaValidationError
            if isinstance(exc, AgendaValidationError):
                return Response({"error": exc.message}, status=400)
            logger.exception("Erro ao criar agendamento online")
            return Response({"error": "Não foi possível concluir o agendamento."}, status=500)

        pendente = cfg.modo_confirmacao == "secretaria"
        return Response({
            "id": appointment.id,
            "numero": appointment.id,
            "status": appointment.status,
            "pendente_aprovacao": pendente,
            "mensagem": (
                "Solicitação de agendamento enviada com sucesso! Aguarde a confirmação da clínica."
                if pendente
                else "Agendamento realizado com sucesso!"
            ),
            "date": appointment.date.isoformat(),
            "professional_nome": getattr(appointment.professional, "nome", ""),
            "procedure_nome": getattr(appointment.procedure, "nome", ""),
            "origem": appointment.origem,
        }, status=201)
