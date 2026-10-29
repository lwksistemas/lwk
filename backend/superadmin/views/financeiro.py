import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)
from core.logging_utils import mask_email

from ..models import FinanceiroLoja, PagamentoLoja
from ..serializers import FinanceiroLojaSerializer, PagamentoLojaSerializer
from .permissions import IsSuperAdmin


class FinanceiroLojaViewSet(viewsets.ModelViewSet):
    serializer_class = FinanceiroLojaSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return FinanceiroLoja.objects.select_related("loja", "loja__plano").all()

    @action(detail=False, methods=["get"])
    def pendentes(self, request):
        """Lojas com pagamento pendente"""
        pendentes = self.get_queryset().filter(status_pagamento__in=["pendente", "atrasado"])
        serializer = self.get_serializer(pendentes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def renovar(self, request, pk=None):
        """Cria nova cobrança para renovação de assinatura"""
        from superadmin.cobranca_service import CobrancaService

        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            from superadmin.financeiro_views.assinatura_cancelamento import assinatura_esta_cancelada

            if assinatura_esta_cancelada(loja, financeiro):
                return Response({
                    "success": False,
                    "error": "Assinatura cancelada. Use Reativar no histórico para gerar o boleto.",
                }, status=status.HTTP_400_BAD_REQUEST)

            dia_vencimento = request.data.get("dia_vencimento")
            antecipado = bool(request.data.get("antecipado", False))

            if dia_vencimento and not antecipado:
                try:
                    dia_vencimento = int(dia_vencimento)
                    if dia_vencimento < 1 or dia_vencimento > 28:
                        return Response({
                            "success": False,
                            "error": "dia_vencimento deve estar entre 1 e 28",
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        "success": False,
                        "error": "dia_vencimento deve ser um número inteiro",
                    }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Renovando assinatura para loja {loja.slug} (dia_vencimento={dia_vencimento})")

            service = CobrancaService()
            result = service.renovar_cobranca(loja, financeiro, dia_vencimento, antecipado=antecipado)

            if result.get("success"):
                logger.info(f"✅ Cobrança renovada para loja {loja.slug}: {result.get('payment_id')}")
                return Response(result, status=status.HTTP_200_OK)
            logger.error(f"❌ Erro ao renovar cobrança para loja {loja.slug}: {result.get('error')}")
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Erro ao renovar assinatura: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def reenviar_senha(self, request, pk=None):
        """Reenvia senha provisória manualmente (apenas se pagamento já confirmado)"""
        from superadmin.email_service import EmailService

        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner

            if financeiro.status_pagamento != "ativo":
                return Response({
                    "success": False,
                    "error": f"Pagamento ainda não confirmado. Status atual: {financeiro.get_status_pagamento_display()}",
                }, status=status.HTTP_400_BAD_REQUEST)

            owner_email_log = mask_email(getattr(owner, "email", ""))
            logger.info("Reenviando senha provisória: loja=%s, owner_email=%s", loja.slug, owner_email_log)

            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)

            if success:
                logger.info("Senha provisória reenviada: loja=%s, owner_email=%s", loja.slug, owner_email_log)
                return Response({
                    "success": True,
                    "message": f"Senha reenviada para {owner.email}",
                }, status=status.HTTP_200_OK)
            logger.warning("Falha ao reenviar senha provisória: loja=%s, owner_email=%s", loja.slug, owner_email_log)
            return Response({
                "success": False,
                "error": "Falha ao enviar email. Email registrado para retry automático.",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"Erro ao reenviar senha: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"])
    def baixar_nota_fiscal(self, request, pk=None):
        """Baixa a nota fiscal mais recente da loja"""
        from asaas_integration.client import AsaasClient
        from asaas_integration.models import AsaasConfig

        try:
            logger.info(f"🧾 [baixar_nota_fiscal] Iniciando - financeiro_id={pk}")

            financeiro = self.get_object()
            loja = financeiro.loja

            logger.info(f"🧾 [baixar_nota_fiscal] Loja: {loja.nome} (slug: {loja.slug})")
            logger.info(f"🧾 [baixar_nota_fiscal] Payment ID: {financeiro.asaas_payment_id}")

            if not financeiro.asaas_payment_id:
                logger.warning("🧾 [baixar_nota_fiscal] Nenhum payment_id encontrado")
                return Response({
                    "success": False,
                    "error": "Nenhum pagamento Asaas encontrado para esta loja",
                }, status=status.HTTP_404_NOT_FOUND)

            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                logger.error("🧾 [baixar_nota_fiscal] Asaas não configurado")
                return Response({
                    "success": False,
                    "error": "Asaas não configurado",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

            try:
                response = client._make_request("GET", "invoices", {"payment": financeiro.asaas_payment_id})
                invoices = response.get("data", [])

                if not invoices:
                    return Response({
                        "success": False,
                        "error": "Nenhuma nota fiscal encontrada para este pagamento. A nota fiscal é emitida automaticamente após a confirmação do pagamento.",
                    }, status=status.HTTP_404_NOT_FOUND)

                invoice = None
                for inv in invoices:
                    if inv.get("status") == "AUTHORIZED":
                        invoice = inv
                        break

                if not invoice:
                    invoice = invoices[0]

                invoice_id = invoice.get("id")
                status_nf = invoice.get("status")

                if status_nf != "AUTHORIZED":
                    return Response({
                        "success": False,
                        "error": f"Nota fiscal ainda não foi autorizada. Status atual: {status_nf}",
                    }, status=status.HTTP_400_BAD_REQUEST)

                pdf_url = invoice.get("pdfUrl")
                if not pdf_url:
                    pdf_url = invoice.get("invoicePdfUrl") or invoice.get("invoiceUrl")

                if not pdf_url:
                    return Response({
                        "success": False,
                        "error": "URL do PDF da nota fiscal não disponível. Aguarde alguns minutos após a emissão.",
                    }, status=status.HTTP_404_NOT_FOUND)

                return Response({
                    "success": True,
                    "pdf_url": pdf_url,
                    "invoice_id": invoice_id,
                    "status": status_nf,
                })

            except Exception as e:
                logger.error(f"❌ [baixar_nota_fiscal] Erro ao buscar nota fiscal: {e}")
                logger.exception(e)
                return Response({
                    "success": False,
                    "error": f"Erro ao buscar nota fiscal: {e!s}",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"❌ [baixar_nota_fiscal] Erro geral: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def reenviar_nota_fiscal(self, request, pk=None):
        """Reenvia nota fiscal por email para o proprietário da loja"""
        from asaas_integration.client import AsaasClient
        from asaas_integration.models import AsaasConfig

        try:
            financeiro = self.get_object()
            loja = financeiro.loja
            owner = loja.owner

            if not financeiro.asaas_payment_id:
                return Response({
                    "success": False,
                    "error": "Nenhum pagamento Asaas encontrado para esta loja",
                }, status=status.HTTP_404_NOT_FOUND)

            owner_email_log = mask_email(getattr(owner, "email", ""))
            logger.info("Reenviando nota fiscal: loja=%s, owner_email=%s", loja.slug, owner_email_log)

            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response({
                    "success": False,
                    "error": "Asaas não configurado",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

            try:
                response = client._make_request("GET", "invoices", {"payment": financeiro.asaas_payment_id})
                invoices = response.get("data", [])

                if not invoices:
                    return Response({
                        "success": False,
                        "error": "Nenhuma nota fiscal encontrada para este pagamento.",
                    }, status=status.HTTP_404_NOT_FOUND)

                invoice = None
                for inv in invoices:
                    if inv.get("status") == "AUTHORIZED":
                        invoice = inv
                        break

                if not invoice:
                    invoice = invoices[0]

                invoice_id = invoice.get("id")
                status_nf = invoice.get("status")

                if status_nf != "AUTHORIZED":
                    return Response({
                        "success": False,
                        "error": f"Nota fiscal ainda não foi autorizada. Status atual: {status_nf}",
                    }, status=status.HTTP_400_BAD_REQUEST)

                pdf_url = invoice.get("pdfUrl")
                if not pdf_url:
                    pdf_url = invoice.get("invoicePdfUrl") or invoice.get("invoiceUrl")

                if not pdf_url:
                    return Response({
                        "success": False,
                        "error": "URL do PDF da nota fiscal não disponível.",
                    }, status=status.HTTP_404_NOT_FOUND)

                valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == "anual" else loja.plano.preco_mensal
                tipo_assinatura = loja.get_tipo_assinatura_display()

                assunto = f"Nota Fiscal – Assinatura LWK Sistemas - {loja.nome}"

                corpo = f"""
Olá,

Segue a nota fiscal referente à assinatura da loja {loja.nome}.

Dados da assinatura:
- Loja: {loja.nome}
- Plano: {loja.plano.nome} ({tipo_assinatura})
- Valor: R$ {valor_plano:.2f}
- Nota Fiscal: {invoice_id}

Acesse a nota fiscal: {pdf_url}

Em caso de dúvidas, entre em contato com o suporte.

Atenciosamente,
Equipe LWK Sistemas
"""

                from core.email_delivery import create_email_message, send_prepared
                msg = create_email_message(subject=assunto, body=corpo, to=[owner.email])
                send_prepared(msg, fail_silently=False)

                logger.info("Nota fiscal reenviada: loja=%s, owner_email=%s", loja.slug, owner_email_log)

                return Response({
                    "success": True,
                    "message": f"Nota fiscal reenviada para {owner.email}",
                    "invoice_id": invoice_id,
                })

            except Exception as e:
                logger.error(f"Erro ao reenviar nota fiscal: {e}")
                return Response({
                    "success": False,
                    "error": f"Erro ao reenviar nota fiscal: {e!s}",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"Erro ao reenviar nota fiscal: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def alterar_plano(self, request, pk=None):
        """Troca o plano da loja. A próxima cobrança usa o novo valor."""
        from superadmin.models import PlanoAssinatura

        financeiro = self.get_object()
        loja = financeiro.loja
        plano_id = request.data.get("plano_id")
        try:
            plano_id = int(plano_id)
        except (TypeError, ValueError):
            return Response(
                {"success": False, "error": "Informe o plano."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plano = PlanoAssinatura.objects.filter(pk=plano_id, is_active=True).first()
        if not plano:
            return Response(
                {"success": False, "error": "Plano não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not plano.tipos_loja.filter(pk=loja.tipo_loja_id).exists():
            return Response(
                {"success": False, "error": "Este plano não vale para o tipo desta loja."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        loja.plano = plano
        loja.save()
        valor = plano.preco_anual if loja.tipo_assinatura == "anual" and plano.preco_anual else plano.preco_mensal
        # update() não dispara o signal de senha provisória
        FinanceiroLoja.objects.filter(pk=financeiro.pk).update(
            valor_mensalidade=valor,
            updated_at=timezone.now(),
        )
        financeiro.valor_mensalidade = valor

        from asaas_integration.models import LojaAssinatura
        LojaAssinatura.objects.filter(loja_slug=loja.slug).update(
            plano_nome=f"{plano.nome} ({loja.get_tipo_assinatura_display()})",
            plano_valor=valor,
        )
        logger.info("Plano da loja %s alterado para %s", loja.slug, plano.nome)
        return Response({
            "success": True,
            "plano_id": plano.id,
            "plano_nome": plano.nome,
            "plano_valor": str(valor),
        })

    @action(detail=True, methods=["post"])
    def alterar_dia_vencimento(self, request, pk=None):
        """Grava o dia do mês da próxima cobrança, sem emitir boleto novo."""
        from superadmin.services.financeiro_service import FinanceiroService

        financeiro = self.get_object()
        try:
            dia = int(request.data.get("dia_vencimento"))
        except (TypeError, ValueError):
            return Response(
                {"success": False, "error": "dia_vencimento deve ser um número inteiro"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if dia < 1 or dia > 28:
            return Response(
                {"success": False, "error": "dia_vencimento deve estar entre 1 e 28"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proxima = FinanceiroService.calcular_proxima_cobranca(dia, financeiro.loja.tipo_assinatura)
        FinanceiroLoja.objects.filter(pk=financeiro.pk).update(
            dia_vencimento=dia,
            data_proxima_cobranca=proxima,
            updated_at=timezone.now(),
        )
        financeiro.dia_vencimento = dia
        financeiro.data_proxima_cobranca = proxima
        logger.info("Dia de vencimento da loja %s alterado para %s", financeiro.loja.slug, dia)
        return Response({
            "success": True,
            "dia_vencimento": dia,
            "data_proxima_cobranca": financeiro.data_proxima_cobranca.isoformat(),
        })

    @action(detail=True, methods=["post"])
    def confirmar_pagamento_conta(self, request, pk=None):
        """Cliente pagou PIX ou transferência na conta da empresa."""
        from superadmin.financeiro_views.helpers import _erro_comprovante_pdf
        from superadmin.sync_service.asaas import AsaasSyncService

        financeiro = self.get_object()
        comprovante = request.FILES.get("comprovante")
        erro_arquivo = _erro_comprovante_pdf(comprovante)
        if erro_arquivo:
            return Response({"success": False, "error": erro_arquivo}, status=status.HTTP_400_BAD_REQUEST)
        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(
            financeiro.loja,
            request.data.get("forma"),
            comprovante=comprovante,
        )
        if not resultado.get("success"):
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado)

    @action(detail=True, methods=["get"])
    def historico_loja(self, request, pk=None):
        """Pagamentos e notas fiscais da loja, com o mês pago ou vencido."""
        from superadmin.financeiro_views.helpers import historico_pagamentos_e_notas

        from superadmin.financeiro_views.assinatura_cancelamento import assinatura_esta_cancelada
        from superadmin.financeiro_views.troca_banco import nome_banco

        financeiro = self.get_object()
        provedor = (financeiro.loja.provedor_boleto_preferido or "asaas").strip().lower()
        from superadmin.degustacao_service import em_degustacao, tem_boleto_em_aberto

        return Response({
            "itens": historico_pagamentos_e_notas(financeiro.loja),
            "provedor_boleto": provedor,
            "provedor_display": nome_banco(provedor) or "Asaas",
            "assinatura_cancelada": assinatura_esta_cancelada(financeiro.loja, financeiro),
            "em_degustacao": em_degustacao(financeiro),
            "degustacao_ate": financeiro.degustacao_ate.isoformat() if financeiro.degustacao_ate else None,
            "dias_apos_pagamento": financeiro.degustacao_dias_apos_pagamento,
            "boleto_em_aberto": tem_boleto_em_aberto(financeiro.loja, financeiro),
        })

    @action(detail=True, methods=["post"])
    def trocar_banco(self, request, pk=None):
        """Troca o banco da assinatura. Emite agora só se o boleto do mês ainda não existe."""
        from superadmin.financeiro_views.assinatura_cancelamento import assinatura_esta_cancelada
        from superadmin.financeiro_views.troca_banco import trocar_banco_assinatura

        financeiro = self.get_object()
        resultado = trocar_banco_assinatura(
            financeiro.loja,
            request.data.get("provedor"),
            permitir_emissao=not assinatura_esta_cancelada(financeiro.loja, financeiro),
        )
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)

    @action(detail=True, methods=["post"])
    def cancelar_assinatura(self, request, pk=None):
        """Para boletos novos e bloqueia o acesso, sem apagar dados da loja."""
        from superadmin.financeiro_views.assinatura_cancelamento import cancelar_assinatura

        financeiro = self.get_object()
        resultado = cancelar_assinatura(financeiro.loja, financeiro)
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)

    @action(detail=True, methods=["post"])
    def iniciar_degustacao(self, request, pk=None):
        """Abre demonstração numa loja já criada, sem boleto novo."""
        from superadmin.degustacao_service import definir_degustacao_loja_existente

        financeiro = self.get_object()
        resultado = definir_degustacao_loja_existente(
            financeiro.loja,
            financeiro,
            request.data.get("dias"),
        )
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)

    @action(detail=True, methods=["post"])
    def reativar_assinatura(self, request, pk=None):
        """Gera o boleto da volta. O acesso retorna quando o pagamento for confirmado."""
        from superadmin.financeiro_views.assinatura_cancelamento import reativar_assinatura

        financeiro = self.get_object()
        resultado = reativar_assinatura(financeiro.loja, financeiro)
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)

    @action(detail=True, methods=["post"])
    def emitir_boleto(self, request, pk=None):
        """Emite o boleto do vencimento quando não há outro em aberto."""
        from superadmin.financeiro_views.assinatura_cancelamento import assinatura_esta_cancelada
        from superadmin.sync_service.asaas import AsaasSyncService

        financeiro = self.get_object()
        if assinatura_esta_cancelada(financeiro.loja, financeiro):
            return Response({
                "success": False,
                "error": "Assinatura cancelada. Use Reativar no histórico para gerar o boleto.",
            }, status=status.HTTP_400_BAD_REQUEST)
        resultado = AsaasSyncService().emitir_boleto(financeiro.loja)
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)

    @action(detail=True, methods=["post"])
    def reenviar_boleto(self, request, pk=None):
        """Reenvia o boleto em aberto para o e-mail do responsável."""
        from superadmin.sync_service.asaas import AsaasSyncService

        financeiro = self.get_object()
        resultado = AsaasSyncService().reenviar_boleto(financeiro.loja)
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)

    @action(detail=True, methods=["get"])
    def baixar_boleto(self, request, pk=None):
        """Entrega o PDF do boleto em aberto com CPF ou CNPJ e o mês do vencimento."""
        from django.http import HttpResponse

        from superadmin.financeiro_views.boleto_pdf import pdf_boleto_em_aberto

        financeiro = self.get_object()
        pdf, nome, erro = pdf_boleto_em_aberto(financeiro)
        if erro:
            return Response({"error": erro}, status=status.HTTP_400_BAD_REQUEST)
        resposta = HttpResponse(pdf, content_type="application/pdf")
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        return resposta

    @action(detail=True, methods=["post"])
    def cancelar_nota_fiscal(self, request, pk=None):
        """Cancela a nota fiscal mais recente da loja no Asaas."""
        from asaas_integration.client import AsaasClient
        from asaas_integration.models import AsaasConfig

        try:
            financeiro = self.get_object()
            loja = financeiro.loja

            if not financeiro.asaas_payment_id:
                return Response({
                    "success": False,
                    "error": "Nenhum pagamento Asaas encontrado para esta loja",
                }, status=status.HTTP_404_NOT_FOUND)

            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response({
                    "success": False,
                    "error": "Asaas não configurado",
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)

            response = client._make_request("GET", "invoices", {"payment": financeiro.asaas_payment_id})
            invoices = response.get("data", [])

            if not invoices:
                return Response({
                    "success": False,
                    "error": "Nenhuma nota fiscal encontrada para este pagamento",
                }, status=status.HTTP_404_NOT_FOUND)

            invoice = None
            for inv in invoices:
                if inv.get("status") in ("AUTHORIZED", "SCHEDULED"):
                    invoice = inv
                    break

            if not invoice:
                invoice = invoices[0]

            invoice_id = invoice.get("id")
            status_nf = invoice.get("status")

            if status_nf == "CANCELED":
                return Response({
                    "success": False,
                    "error": "Nota fiscal já está cancelada",
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Cancelando nota fiscal {invoice_id} (status: {status_nf}) para loja {loja.nome}")

            client.cancel_invoice(invoice_id)

            logger.info(f"✅ Nota fiscal {invoice_id} cancelada para loja {loja.nome}")

            return Response({
                "success": True,
                "message": f"Nota fiscal {invoice_id} cancelada com sucesso",
                "invoice_id": invoice_id,
            })

        except Exception as e:
            logger.exception(f"Erro ao cancelar nota fiscal: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PagamentoLojaViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoLojaSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return PagamentoLoja.objects.select_related("loja", "financeiro").all()

    @action(detail=True, methods=["post"])
    def confirmar_pagamento(self, request, pk=None):
        """Confirmar pagamento de uma loja"""
        pagamento = self.get_object()

        pagamento.status = "pago"
        pagamento.data_pagamento = timezone.now()
        pagamento.save()

        financeiro = pagamento.financeiro
        financeiro.status_pagamento = "ativo"
        financeiro.ultimo_pagamento = timezone.now()
        financeiro.total_pago += pagamento.valor
        financeiro.save()

        from superadmin.sync_service import tentar_emitir_nfse_assinatura
        payment_id = (pagamento.asaas_payment_id or financeiro.asaas_payment_id or "").strip()
        tentar_emitir_nfse_assinatura(pagamento, payment_id)

        return Response({"message": "Pagamento confirmado com sucesso"})
