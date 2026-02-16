from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import PushSubscription


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_push(request):
    """
    Registra a inscrição push do cliente (Service Worker).
    Body: { "endpoint": "...", "keys": { "p256dh": "...", "auth": "..." } }
    """
    endpoint = request.data.get('endpoint')
    keys = request.data.get('keys')
    if not endpoint or not keys:
        return Response(
            {'error': 'endpoint e keys são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Evitar duplicata pelo mesmo endpoint
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    PushSubscription.objects.create(
        user=request.user,
        endpoint=endpoint,
        keys=keys,
    )
    return Response({'ok': True}, status=status.HTTP_201_CREATED)
