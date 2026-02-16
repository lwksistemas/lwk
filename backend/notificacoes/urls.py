from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_notifications),
    path('create/', views.create_notification),
    path('<int:pk>/read/', views.mark_as_read),
]
