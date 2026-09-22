import logging

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Chamado, ErroFrontend, RespostaChamado
from .serializers import ChamadoSerializer, RespostaChamadoSerializer
from .services import get_chamados_queryset_for_user

logger = logging.getLogger(__name__)


# Palavras que indicam cada severidade nas mensagens/erros (heurística — não há
# campo estruturado de severidade ainda; classifica pelo texto e pelo status HTTP).
_KW_TIMEOUT = ("timeout", "timed out", "tempo esgotado", "etimedout", "deadline", "504", "gateway time")
_KW_FALHA = ("warn", "aviso", "falha", "failed", "cancel", "abort", "404", "409", "422", "400")


def classificar_severidade(texto: str = "", status_http: int | None = None) -> str:
    """Classifica um log em 'timeout', 'falha' ou 'erro' por heurística.

    - timeout: menções a tempo esgotado / 504.
    - falha: avisos, cancelamentos, erros de validação/cliente (4xx exceto graves).
    - erro: o restante (padrão), inclui 5xx e exceções não classificadas.
    """
    t = (texto or "").lower()
    if any(k in t for k in _KW_TIMEOUT):
        return "timeout"
    if status_http is not None:
        if status_http in (408, 504):
            return "timeout"
        if 400 <= status_http < 500:
            return "falha"
        if status_http >= 500:
            return "erro"
    if any(k in t for k in _KW_FALHA):
        return "falha"
    return "erro"


def _status_http_do_texto(texto: str) -> int | None:
    """Extrai um código HTTP (3 dígitos 100-599) do texto, se houver."""
    import re

    m = re.search(r"\b([1-5]\d{2})\b", texto or "")
    if m:
        return int(m.group(1))
    return None


class ChamadoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar chamados de suporte - Banco 'suporte'"""

    serializer_class = ChamadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_chamados_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"])
    def responder(self, request, pk=None):
        """Adicionar resposta a um chamado"""
        chamado = self.get_object()

        resposta = RespostaChamado.objects.create(
            chamado=chamado,
            usuario_nome=request.user.username,
            mensagem=request.data.get("mensagem"),
            is_suporte=request.user.groups.filter(name="suporte").exists(),
        )

        serializer = RespostaChamadoSerializer(resposta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        """Marcar chamado como resolvido"""
        chamado = self.get_object()
        chamado.status = "resolvido"
        chamado.resolvido_em = timezone.now()
        chamado.save()

        serializer = self.get_serializer(chamado)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="detalhes-contexto")
    def detalhes_contexto(self, request, pk=None):
        """Retorna erros recentes da loja (backend + frontend) para o suporte.
        Usa dados da sessão/contexto da loja — não consulta Heroku/Vercel.
        """
        chamado = self.get_object()
        # Apenas suporte ou superadmin
        if not request.user.is_superuser and not request.user.groups.filter(name="suporte").exists():
            return Response({"detail": "Sem permissão"}, status=status.HTTP_403_FORBIDDEN)

        loja_slug = chamado.loja_slug
        erros_backend = []
        erros_navegador = []
        erros_frontend = []

        # Erros backend: falhas da loja no HistoricoAcessoGlobal (banco default)
        try:
            from superadmin.models import HistoricoAcessoGlobal
            qs = HistoricoAcessoGlobal.objects.using("default").filter(
                loja_slug=loja_slug,
                sucesso=False,
            ).order_by("-created_at")[:50]
            for h in qs:
                erro_txt = (h.erro or "")[:1000]
                sev = classificar_severidade(erro_txt, _status_http_do_texto(erro_txt))
                erros_backend.append({
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                    "url": h.url or "",
                    "metodo_http": h.metodo_http or "",
                    "erro": erro_txt,
                    "usuario_email": h.usuario_email or "",
                    "severidade": sev,
                })
        except Exception as e:
            logger.warning("detalhes_contexto HistoricoAcessoGlobal: %s", e)

        # Erros do cliente (ErroFrontend): separa navegador vs frontend (React) por heurística,
        # já que a tabela ainda não persiste o tipo de origem.
        try:
            qs = ErroFrontend.objects.filter(loja_slug=loja_slug).order_by("-created_at")[:100]
            for e in qs:
                msg = e.mensagem or ""
                stack = (e.stack or "")[:2000]
                base = f"{msg} {stack}".lower()
                item = {
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "mensagem": msg,
                    "stack": stack,
                    "url": e.url or "",
                    "user_agent": (e.user_agent or "")[:300],
                    "severidade": classificar_severidade(base, _status_http_do_texto(base)),
                }
                # Erros de React/framework → frontend; window.onerror/promise → navegador.
                is_frontend = any(k in base for k in (
                    "react", "hydration", "hydrat", "component", "minified react",
                    "render", "hook", "jsx", "next", "chunkloaderror", "loading chunk",
                ))
                if is_frontend:
                    erros_frontend.append(item)
                else:
                    erros_navegador.append(item)
        except Exception as e:
            logger.warning("detalhes_contexto ErroFrontend: %s", e)

        return Response({
            "loja_slug": loja_slug,
            "erros_navegador": erros_navegador[:50],
            "erros_frontend": erros_frontend[:50],
            "erros_backend": erros_backend,
            "periodo_exibido": "Erros recentes da loja, do mais recente ao mais antigo.",
            "limite_por_tipo": 50,
        })



@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def criar_chamado_rapido(request):
    """Endpoint para criar chamado rapidamente de qualquer dashboard
    Aceita usuários autenticados (lojas, superadmin, suporte)
    """
    try:
        # Extrair dados do request
        titulo = request.data.get("titulo")
        descricao = request.data.get("descricao")
        tipo = request.data.get("tipo", "duvida")
        prioridade = request.data.get("prioridade", "media")
        detalhes_tecnicos = request.data.get("detalhes_tecnicos", "") or ""

        # Validações
        if not titulo or not descricao:
            return Response(
                {"error": "Título e descrição são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Identificar origem do chamado
        user = request.user
        loja_slug = request.data.get("loja_slug", "sistema")
        loja_nome = request.data.get("loja_nome", "Sistema")

        # Se for usuário de loja, pegar dados da loja
        if hasattr(user, "lojas_owned") and user.lojas_owned.exists():
            loja = user.lojas_owned.first()
            loja_slug = loja.slug
            loja_nome = loja.nome

        chamado = Chamado.objects.create(
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            prioridade=prioridade,
            status="aberto",
            loja_slug=loja_slug,
            loja_nome=loja_nome,
            usuario_nome=user.get_full_name() or user.username,
            usuario_email=user.email,
            detalhes_tecnicos=detalhes_tecnicos[:10000] if detalhes_tecnicos else "",  # limite 10k chars
        )

        serializer = ChamadoSerializer(chamado)

        return Response({
            "message": "Chamado criado com sucesso!",
            "chamado": serializer.data,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": f"Erro ao criar chamado: {e!s}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def meus_chamados(request):
    """Listar chamados do usuário logado (filtrado por permissões e loja).
    """
    chamados = get_chamados_queryset_for_user(request.user)

    # Filtros opcionais
    status_filter = request.query_params.get("status")
    if status_filter:
        chamados = chamados.filter(status=status_filter)

    # Ordenar por mais recente
    chamados = chamados.order_by("-created_at")[:20]  # Últimos 20

    serializer = ChamadoSerializer(chamados, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def registrar_erro_frontend(request):
    """Registra erro de frontend/navegador reportado pela loja (sessão única).
    Usado para o painel 'Detalhes' do suporte — não sobrecarrega servidor;
    só grava quando ocorre um erro no navegador do usuário da loja.
    """
    try:
        mensagem = (request.data.get("mensagem") or "")[:500]
        stack = (request.data.get("stack") or "")[:5000]
        url_pagina = (request.data.get("url") or "")[:500]
        loja_slug = request.data.get("loja_slug") or ""

        if not mensagem:
            return Response(
                {"error": "mensagem é obrigatória"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not loja_slug and hasattr(user, "lojas_owned") and user.lojas_owned.exists():
            loja_slug = user.lojas_owned.first().slug
        if not loja_slug:
            loja_slug = "sistema"

        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        ErroFrontend.objects.create(
            loja_slug=loja_slug,
            mensagem=mensagem,
            stack=stack,
            url=url_pagina,
            user_agent=user_agent,
        )
        return Response({"ok": True}, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.warning("registrar_erro_frontend: %s", e)
        return Response(
            {"error": str(e)[:200]},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
