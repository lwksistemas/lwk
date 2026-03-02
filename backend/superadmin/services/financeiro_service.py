"""
Serviço para gerenciamento financeiro de lojas
Centraliza lógica de criação de financeiro e cobranças
"""
import logging
from datetime import date, timedelta
from calendar import monthrange

logger = logging.getLogger(__name__)


class FinanceiroService:
    """
    Serviço responsável pelo gerenciamento financeiro das lojas
    """
    
    @staticmethod
    def calcular_valor_mensalidade(loja) -> float:
        """
        Calcula valor da mensalidade baseado no tipo de assinatura
        
        Args:
            loja: Objeto Loja
            
        Returns:
            Valor da mensalidade
        """
        if loja.tipo_assinatura == 'anual':
            if loja.plano.preco_anual:
                return loja.plano.preco_anual / 12
            return loja.plano.preco_mensal
        return loja.plano.preco_mensal
    
    @staticmethod
    def calcular_primeiro_vencimento(dias_para_vencer: int = 3) -> date:
        """
        Calcula data do primeiro vencimento
        
        Args:
            dias_para_vencer: Dias até o vencimento
            
        Returns:
            Data do primeiro vencimento
        """
        hoje = date.today()
        return hoje + timedelta(days=dias_para_vencer)
    
    @staticmethod
    def calcular_proxima_cobranca(dia_vencimento: int) -> date:
        """
        Calcula data da próxima cobrança no próximo mês
        
        Args:
            dia_vencimento: Dia do mês para vencimento
            
        Returns:
            Data da próxima cobrança
        """
        hoje = date.today()
        
        # Calcular próximo mês
        if hoje.month == 12:
            proximo_mes = 1
            proximo_ano = hoje.year + 1
        else:
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year
        
        # Ajustar dia se o mês não tiver esse dia (ex: dia 31 em fevereiro)
        ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
        dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
        
        return date(proximo_ano, proximo_mes, dia_cobranca)
    
    @staticmethod
    def criar_financeiro_loja(loja, dia_vencimento: int = 10):
        """
        Cria registro financeiro para a loja
        
        Args:
            loja: Objeto Loja
            dia_vencimento: Dia do mês para vencimento
            
        Returns:
            Objeto FinanceiroLoja criado
        """
        from superadmin.models import FinanceiroLoja
        
        try:
            # Calcular valores
            valor_mensalidade = FinanceiroService.calcular_valor_mensalidade(loja)
            
            # Calcular datas
            # Primeiro boleto vence em 3 dias
            primeiro_vencimento = FinanceiroService.calcular_primeiro_vencimento(dias_para_vencer=3)
            
            # Usar primeiro vencimento como próxima cobrança
            proxima_cobranca = primeiro_vencimento
            
            # Status inicial sempre pendente (aguardando primeiro pagamento)
            status_pagamento = 'pendente'
            
            # Criar financeiro
            financeiro = FinanceiroLoja.objects.create(
                loja=loja,
                data_proxima_cobranca=proxima_cobranca,
                valor_mensalidade=valor_mensalidade,
                dia_vencimento=dia_vencimento,
                status_pagamento=status_pagamento
            )
            
            logger.info(
                f"Financeiro criado para loja {loja.slug}: "
                f"valor={valor_mensalidade}, vencimento={proxima_cobranca}, status={status_pagamento}"
            )
            
            return financeiro
            
        except Exception as e:
            logger.error(f"Erro ao criar financeiro para loja {loja.slug}: {e}")
            raise
    
    @staticmethod
    def atualizar_proxima_cobranca(financeiro, dia_vencimento: int = None):
        """
        Atualiza data da próxima cobrança
        
        Args:
            financeiro: Objeto FinanceiroLoja
            dia_vencimento: Dia do mês (opcional, usa o atual se não fornecido)
        """
        if dia_vencimento is None:
            dia_vencimento = financeiro.dia_vencimento
        
        proxima_cobranca = FinanceiroService.calcular_proxima_cobranca(dia_vencimento)
        
        financeiro.data_proxima_cobranca = proxima_cobranca
        financeiro.save()
        
        logger.info(f"Próxima cobrança atualizada para {proxima_cobranca}")
