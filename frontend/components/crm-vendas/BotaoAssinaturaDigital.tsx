'use client';

import { useState } from 'react';
import { FileSignature, Mail, CheckCircle, AlertCircle } from 'lucide-react';

interface BotaoAssinaturaDigitalProps {
  documentoId: number;
  tipoDocumento: 'proposta' | 'contrato';
  statusAssinatura?: string;
  leadEmail?: string;
  onSucesso?: () => void;
}

export default function BotaoAssinaturaDigital({
  documentoId,
  tipoDocumento,
  statusAssinatura = 'rascunho',
  leadEmail,
  onSucesso,
}: BotaoAssinaturaDigitalProps) {
  const [enviando, setEnviando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: 'sucesso' | 'erro'; texto: string } | null>(null);
  
  // Não mostrar botão se já está em processo de assinatura ou concluído
  if (statusAssinatura !== 'rascunho') {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <span className="text-sm text-blue-700 dark:text-blue-300">
          Status: {getStatusDisplay(statusAssinatura)}
        </span>
      </div>
    );
  }
  
  const enviarParaAssinatura = async () => {
    if (!leadEmail) {
      setMensagem({
        tipo: 'erro',
        texto: 'Lead não possui email cadastrado. Adicione um email antes de enviar para assinatura.',
      });
      return;
    }
    
    setEnviando(true);
    setMensagem(null);
    
    try {
      const endpoint = tipoDocumento === 'proposta' 
        ? `/crm-vendas/propostas/${documentoId}/enviar_para_assinatura/`
        : `/crm-vendas/contratos/${documentoId}/enviar_para_assinatura/`;
      
      // Usar apiClient ao invés de fetch para incluir autenticação
      const { default: apiClient } = await import('@/lib/api-client');
      const res = await apiClient.post(endpoint);
      
      setMensagem({
        tipo: 'sucesso',
        texto: res.data.message || `Email enviado para ${leadEmail}`,
      });
      
      // Chamar callback de sucesso após 2 segundos
      setTimeout(() => {
        if (onSucesso) {
          onSucesso();
        }
      }, 2000);
    } catch (err: any) {
      setMensagem({
        tipo: 'erro',
        texto: err.response?.data?.detail || 'Erro ao enviar para assinatura. Tente novamente.',
      });
    } finally {
      setEnviando(false);
    }
  };
  
  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={enviarParaAssinatura}
        disabled={enviando || !leadEmail}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-colors"
        title={!leadEmail ? 'Lead precisa ter email cadastrado' : 'Enviar para assinatura digital'}
      >
        {enviando ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Enviando...</span>
          </>
        ) : (
          <>
            <FileSignature className="w-4 h-4" />
            <span>Enviar para Assinatura Digital</span>
          </>
        )}
      </button>
      
      {mensagem && (
        <div
          className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
            mensagem.tipo === 'sucesso'
              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
          }`}
        >
          {mensagem.tipo === 'sucesso' ? (
            <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          )}
          <span>{mensagem.texto}</span>
        </div>
      )}
      
      {!leadEmail && (
        <p className="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          Lead precisa ter email cadastrado para enviar assinatura digital
        </p>
      )}
    </div>
  );
}

function getStatusDisplay(status: string): string {
  const statusMap: Record<string, string> = {
    rascunho: 'Rascunho',
    aguardando_cliente: 'Aguardando Cliente',
    aguardando_vendedor: 'Aguardando Vendedor',
    concluido: 'Concluído',
    cancelado: 'Cancelado',
  };
  return statusMap[status] || status;
}
