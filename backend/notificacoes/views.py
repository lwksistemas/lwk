from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now

from .models import Notification
from .serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    """Lista notificações do usuário autenticado, ordenadas por data (mais recente primeiro)."""
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification(request):
    """Cria uma notificação. Em produção, prefira usar notificacoes.services.notify()."""
    data = request.data.copy()
    # Só permite criar notificação para outro user se for staff
    if 'user' not in data or not request.user.is_staff:
        data['user'] = request.user.id
    serializer = NotificationSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_read(request, pk):
    """Marca uma notificação como lida (apenas do próprio usuário)."""
    try:
        notif = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({'detail': 'Não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    notif.status = 'lido'
    notif.read_at = now()
    notif.save()
    return Response({'ok': True})
