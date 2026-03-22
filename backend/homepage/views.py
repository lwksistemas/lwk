"""
API pública da Homepage - sem autenticação.
Retorna os dados configurados para exibir na página inicial.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import HeroSection, Funcionalidade, ModuloSistema, WhyUsBenefit
from .serializers import HeroSerializer, FuncionalidadeSerializer, ModuloSerializer, WhyUsBenefitSerializer


class HomePageAPIView(APIView):
    """API pública - retorna dados da homepage para exibição."""
    permission_classes = [AllowAny]

    def get(self, request):
        hero = HeroSection.objects.filter(ativo=True).first()
        funcionalidades = Funcionalidade.objects.filter(ativo=True)
        modulos = ModuloSistema.objects.filter(ativo=True)
        whyus = WhyUsBenefit.objects.filter(ativo=True)

        return Response({
            'hero': HeroSerializer(hero).data if hero else None,
            'funcionalidades': FuncionalidadeSerializer(funcionalidades, many=True).data,
            'modulos': ModuloSerializer(modulos, many=True).data,
            'whyus': WhyUsBenefitSerializer(whyus, many=True).data,
        })
