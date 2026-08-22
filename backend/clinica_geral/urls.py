from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConsultaViewSet, PacienteViewSet

router = DefaultRouter()
router.register(r"pacientes", PacienteViewSet, basename="clinica-geral-pacientes")
router.register(r"consultas", ConsultaViewSet, basename="clinica-geral-consultas")

urlpatterns = [
    path("", include(router.urls)),
]
