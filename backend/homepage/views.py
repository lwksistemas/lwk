"""API pública da Homepage - sem autenticação.
Retorna os dados configurados para exibir na página inicial.
"""
import logging

from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmpresaConfig, Funcionalidade, HeroSection, ItemMenu, ModuloSistema, WhyUsBenefit
from .serializers import (
    EmpresaConfigSerializer,
    FuncionalidadeSerializer,
    HeroSerializer,
    ItemMenuSerializer,
    ModuloSerializer,
    WhyUsBenefitSerializer,
)


class HomePageAPIView(APIView):
    """API pública - retorna dados da homepage para exibição."""

    permission_classes = [AllowAny]

    def get(self, request):
        from .models import HeroImagem

        hero = HeroSection.objects.filter(ativo=True).first()
        funcionalidades = Funcionalidade.objects.filter(ativo=True)
        modulos = ModuloSistema.objects.filter(ativo=True)
        whyus = WhyUsBenefit.objects.filter(ativo=True)
        hero_imagens = HeroImagem.objects.filter(ativo=True)

        # Dados da empresa (singleton)
        empresa = EmpresaConfig.objects.first()

        # Serializer inline para HeroImagem
        hero_imagens_data = [
            {
                "id": img.id,
                "imagem": img.imagem,
                "titulo": img.titulo,
                "link": img.link,
                "ordem": img.ordem,
            }
            for img in hero_imagens
        ]

        return Response({
            "hero": HeroSerializer(hero).data if hero else None,
            "hero_imagens": hero_imagens_data,
            "funcionalidades": FuncionalidadeSerializer(funcionalidades, many=True).data,
            "modulos": ModuloSerializer(modulos, many=True).data,
            "whyus": WhyUsBenefitSerializer(whyus, many=True).data,
            "empresa": EmpresaConfigSerializer(empresa).data if empresa else None,
            "menu": {
                "solucoes": ItemMenuSerializer(
                    ItemMenu.objects.filter(ativo=True, grupo=ItemMenu.GRUPO_SOLUCOES),
                    many=True,
                ).data,
                "segmentos": ItemMenuSerializer(
                    ItemMenu.objects.filter(ativo=True, grupo=ItemMenu.GRUPO_SEGMENTOS),
                    many=True,
                ).data,
            },
        })


class PaginaSiteAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        from .models import PaginaSite
        from .serializers import PaginaSiteSerializer

        pagina = PaginaSite.objects.filter(slug=slug, ativo=True).first()
        if pagina is None:
            return Response({"detail": "Página não encontrada."}, status=404)
        return Response(PaginaSiteSerializer(pagina).data)


class ContatoSiteAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        from .models import EmpresaConfig, PaginaSite
        from .serializers import SolicitacaoContatoSerializer

        ip = request.META.get("REMOTE_ADDR", "") or "sem-ip"
        chave = f"site-contato:{ip}"
        tentativas = cache.get(chave, 0)
        if tentativas >= 8:
            return Response({"detail": "Muitas mensagens deste acesso. Tente mais tarde."}, status=429)

        serializer = SolicitacaoContatoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solicitacao = serializer.save()
        cache.set(chave, tentativas + 1, 3600)

        empresa = EmpresaConfig.objects.first()
        destino = (empresa.email_contato or "").strip() if empresa else ""
        if destino:
            produto = PaginaSite.objects.filter(slug=solicitacao.produto).first()
            nome_produto = produto.titulo if produto else solicitacao.produto
            try:
                send_mail(
                    subject=f"Site LWK — {nome_produto}",
                    message=(
                        f"Nome: {solicitacao.nome}\n"
                        f"Empresa: {solicitacao.empresa}\n"
                        f"WhatsApp: {solicitacao.whatsapp}\n"
                        f"Produto: {nome_produto}\n"
                        f"Origem: {solicitacao.origem}\n\n"
                        f"{solicitacao.mensagem}"
                    ),
                    from_email=None,
                    recipient_list=[destino],
                    fail_silently=True,
                )
            except Exception:
                logging.getLogger(__name__).exception("Falha ao enviar e-mail do formulário do site")

        return Response({"ok": True}, status=201)
