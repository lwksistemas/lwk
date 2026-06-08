'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Landmark, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import apiClient from '@/lib/api-client';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import { logger } from '@/lib/logger';
import { AsaasConfigSection } from '../components/AsaasConfigSection';

export default function ConfiguracaoAsaasPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;
  const { config, recarregar } = useCRMConfig();

  const asaasWebhookUrl =
    config?.asaas_webhook_url ||
    (slug ? `${getPrimaryApiBaseUrl()}/crm-vendas/webhooks/asaas/${encodeURIComponent(slug)}/` : '');

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [asaasApiKey, setAsaasApiKey] = useState('');
  const [asaasWebhookToken, setAsaasWebhookToken] = useState('');
  const [asaasSandbox, setAsaasSandbox] = useState(false);
  const [asaasTestLoading, setAsaasTestLoading] = useState(false);
  const [asaasTestMessage, setAsaasTestMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (config) {
      setAsaasApiKey('');
      setAsaasWebhookToken('');
      setAsaasSandbox(config.asaas_sandbox ?? false);
    }
  }, [config]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const data = new FormData();
      if (asaasApiKey.trim()) {
        data.append('asaas_api_key', asaasApiKey.trim());
      }
      if (asaasWebhookToken.trim()) {
        data.append('asaas_webhook_token', asaasWebhookToken.trim());
      }
      data.append('asaas_sandbox', asaasSandbox ? 'true' : 'false');

      await apiClient.patch('/crm-vendas/config/', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setMessage({ type: 'success', text: 'Configurações Asaas salvas com sucesso!' });
      setAsaasApiKey('');
      setAsaasWebhookToken('');
      await recarregar();
    } catch (error: unknown) {
      const ax = error as {
        response?: { data?: { detail?: string; asaas_api_key?: string[]; asaas_webhook_token?: string[] } };
      };
      const detail =
        ax.response?.data?.detail ||
        ax.response?.data?.asaas_api_key?.[0] ||
        ax.response?.data?.asaas_webhook_token?.[0] ||
        'Erro ao salvar configurações Asaas';
      logger.warn('Erro ao salvar config Asaas:', error);
      setMessage({ type: 'error', text: String(detail) });
    } finally {
      setLoading(false);
    }
  };

  const testarComunicacaoAsaas = async () => {
    setAsaasTestLoading(true);
    setAsaasTestMessage(null);
    try {
      const payload: { api_key?: string; asaas_sandbox: boolean } = { asaas_sandbox: asaasSandbox };
      const key = asaasApiKey.trim();
      if (key) payload.api_key = key;

      const res = await apiClient.post<{
        success?: boolean;
        message?: string;
        detail?: string;
      }>('/crm-vendas/config/test-asaas/', payload);

      if (res.data?.success) {
        setAsaasTestMessage({ type: 'ok', text: res.data.message || 'Conexão com o Asaas OK.' });
      } else {
        setAsaasTestMessage({
          type: 'error',
          text: res.data?.detail || 'Não foi possível validar a chave.',
        });
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string; message?: string } } };
      const detail =
        ax.response?.data?.detail ||
        ax.response?.data?.message ||
        (err instanceof Error ? err.message : 'Erro ao testar comunicação.');
      setAsaasTestMessage({ type: 'error', text: String(detail) });
    } finally {
      setAsaasTestLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3]"
      >
        <ArrowLeft size={16} />
        Voltar para Configurações
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Landmark size={28} />
          Configuração Asaas (banco)
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          API Key e webhook da conta Asaas da loja — usados para boletos de comissão no CRM
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg flex items-start gap-3 ${
            message.type === 'success'
              ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
              : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
          ) : (
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
          )}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
          <AsaasConfigSection
            apiKey={asaasApiKey}
            sandbox={asaasSandbox}
            apiKeyConfigured={config?.asaas_api_key_configured}
            webhookUrl={asaasWebhookUrl}
            webhookToken={asaasWebhookToken}
            webhookTokenConfigured={config?.asaas_webhook_token_configured}
            webhookTokenMasked={config?.asaas_webhook_token_masked}
            webhookTokenLength={config?.asaas_webhook_token_length}
            testLoading={asaasTestLoading}
            testMessage={asaasTestMessage}
            onApiKeyChange={setAsaasApiKey}
            onSandboxChange={setAsaasSandbox}
            onWebhookTokenChange={setAsaasWebhookToken}
            onTest={() => void testarComunicacaoAsaas()}
          />
        </div>

        <div className="flex items-center justify-end gap-3">
          <Link
            href={base}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg transition-colors"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </div>
  );
}
