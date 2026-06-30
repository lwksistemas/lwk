"""Middleware: bloqueia API da loja quando is_blocked por inadimplência."""
from superadmin.services.assinatura_bloqueio_service import check_inadimplencia_block


class LojaInadimplenciaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        violation = check_inadimplencia_block(request)
        if violation:
            return violation
        return self.get_response(request)
