"""API pública da Homepage - sem autenticação.
Retorna os dados configurados para exibir na página inicial.
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmpresaConfig, Funcionalidade, HeroSection, ModuloSistema, WhyUsBenefit
from .serializers import (
    EmpresaConfigSerializer,
    FuncionalidadeSerializer,
    HeroSerializer,
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
        })
