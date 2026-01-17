from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChamadoViewSet, criar_chamado_rapido, meus_chamados

router = DefaultRouter()
router.register(r'chamados', ChamadoViewSet, basename='chamado')

urlpatterns = [
    path('', include(router.urls)),
    path('criar-chamado/', criar_chamado_rapido, name='criar-chamado-rapido'),
    path('meus-chamados/', meus_chamados, name='meus-chamados'),
]
