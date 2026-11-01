from django.urls import path

from .views import ContatoSiteAPIView, PaginaSiteAPIView

urlpatterns = [
    path("paginas/<slug:slug>/", PaginaSiteAPIView.as_view()),
    path("contato/", ContatoSiteAPIView.as_view()),
]
