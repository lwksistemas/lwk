'use client';

import { useState } from 'react';
import { Info, Loader2, AlertCircle, CheckCircle2, Eye, EyeOff } from 'lucide-react';

function gerarTokenWebhook(): string {
  const part1 = crypto.randomUUID().replace(/-/g, '');
  const part2 = crypto.randomUUID().replace(/-/g, '').slice(0, 11);
  return `${part1}${part2}`;
}

interface Props {
  apiKey: string;
  sandbox: boolean;
  apiKeyConfigured?: boolean;
  webhookUrl: string;
  webhookToken: string;
  webhookTokenConfigured?: boolean;
  webhookTokenMasked?: string;
  webhookTokenLength?: number;
  testLoading: boolean;
  testMessage: { type: 'ok' | 'error'; text: string } | null;
  onApiKeyChange: (v: string) => void;
  onSandboxChange: (v: boolean) => void;
  onWebhookTokenChange: (v: string) => void;
  onTest: () => void;
}

export function AsaasConfigSection({
  apiKey,
  sandbox,
  apiKeyConfigured,
  webhookUrl,
  webhookToken,
  webhookTokenConfigured,
  webhookTokenMasked,
  webhookTokenLength,
  testLoading,
  testMessage,
  onApiKeyChange,
  onSandboxChange,
  onWebhookTokenChange,
  onTest,
}: Props) {
  const [showWebhookToken, setShowWebhookToken] = useState(false);

  const copiarToken = async () => {
    const value = webhookToken.trim();
    if (!value) return;
    await navigator.clipboard.writeText(value);
  };

  return (
    <div className="space-y-4 max-w-xl">
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 flex items-start gap-3">
        <Info size={20} className="text-amber-700 dark:text-amber-300 shrink-0 mt-0.5" />
        <div className="text-sm text-amber-950 dark:text-amber-100">
          <p className="font-medium mb-2">Conta Asaas da sua loja (separada da LWK)</p>
          <p className="text-xs mb-2">
            Usada para <strong>boletos de comissão</strong> nos relatórios do CRM. Se o provedor de NFS-e for Asaas,
            a mesma chave é usada na emissão de notas.
          </p>
          <p className="text-xs">
            Chave de <strong>produção</strong>: começa com <code className="text-[10px]">$aact_prod_</code> — desmarque sandbox abaixo.
          </p>
          <a
            href="https://www.asaas.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#0176d3] underline text-xs font-medium mt-2 inline-block"
          >
            Site Asaas
          </a>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">API Key (token v3)</label>
        <input
          type="password"
          autoComplete="off"
          value={apiKey}
          onChange={(e) => onApiKeyChange(e.target.value)}
          placeholder={
            apiKeyConfigured ? '•••••••• (já configurada — digite para substituir)' : 'Cole a chave da conta Asaas da loja'
          }
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white font-mono text-sm"
        />
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={sandbox} onChange={(e) => onSandboxChange(e.target.checked)} className="w-4 h-4" />
          <span className="text-sm text-gray-700 dark:text-gray-300">Usar ambiente sandbox (homologação)</span>
        </label>
        <p className="text-[11px] pl-7">
          <span
            className={
              sandbox
                ? 'text-amber-700 dark:text-amber-300 font-medium'
                : 'text-green-800 dark:text-green-300 font-medium'
            }
          >
            {sandbox ? 'Modo atual: sandbox (homologação)' : 'Modo atual: produção'}
          </span>
        </p>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <button
          type="button"
          onClick={onTest}
          disabled={testLoading || (!apiKey.trim() && !apiKeyConfigured)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] dark:text-[#5eb0ff] dark:border-[#5eb0ff] hover:bg-[#0176d3]/10 text-sm font-medium disabled:opacity-50"
        >
          {testLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Testando…
            </>
          ) : (
            'Testar comunicação com o Asaas'
          )}
        </button>
      </div>

      {testMessage && (
        <div
          className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
            testMessage.type === 'ok'
              ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
          }`}
        >
          {testMessage.type === 'ok' ? (
            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          )}
          <span>{testMessage.text}</span>
        </div>
      )}

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Webhook no Asaas</h3>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
            No painel Asaas da <strong>conta da loja</strong> (Integrações → Webhooks, método POST), cadastre a URL abaixo.
            Marque <code className="text-[10px]">PAYMENT_RECEIVED</code> e <code className="text-[10px]">PAYMENT_CONFIRMED</code>{' '}
            para confirmar pagamento dos boletos de comissão.
          </p>
          {webhookUrl ? (
            <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
              <code className="flex-1 text-[11px] sm:text-xs break-all p-3 rounded-lg bg-gray-100 dark:bg-[#0d1f3c] text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-[#0d1f3c]">
                {webhookUrl}
              </code>
              <button
                type="button"
                onClick={() => void navigator.clipboard.writeText(webhookUrl)}
                className="shrink-0 px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
              >
                Copiar URL
              </button>
            </div>
          ) : (
            <p className="text-xs text-amber-700 dark:text-amber-300">Slug da loja indisponível.</p>
          )}
        </div>

        <div>
          <label htmlFor="asaas_webhook_token" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Token de autenticação
          </label>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
            O Asaas envia o header <code className="text-[10px]">asaas-access-token</code> em cada requisição do webhook.
            Gere ou cole o token aqui, salve, e use o <strong>mesmo valor</strong> no campo &quot;Token de autenticação&quot; do painel Asaas
            (mínimo 32 caracteres).
          </p>
          <div className="relative">
            <input
              id="asaas_webhook_token"
              type={showWebhookToken ? 'text' : 'password'}
              autoComplete="off"
              value={webhookToken}
              onChange={(e) => onWebhookTokenChange(e.target.value)}
              placeholder={
                webhookTokenConfigured
                  ? 'Deixe vazio para manter o token atual — ou cole um novo (mín. 32 caracteres)'
                  : 'Gere um token ou cole o valor que usará no Asaas'
              }
              className="w-full pr-10 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white font-mono text-sm"
            />
            <button
              type="button"
              onClick={() => setShowWebhookToken((v) => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              aria-label={showWebhookToken ? 'Ocultar token' : 'Mostrar token'}
            >
              {showWebhookToken ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {webhookTokenConfigured && webhookTokenMasked && !webhookToken.trim() && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Token salvo: {webhookTokenMasked}
              {webhookTokenLength ? ` (${webhookTokenLength} caracteres)` : ''}
            </p>
          )}
          <div className="flex flex-wrap gap-2 mt-3">
            <button
              type="button"
              onClick={() => onWebhookTokenChange(gerarTokenWebhook())}
              className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]"
            >
              Gerar token
            </button>
            <button
              type="button"
              onClick={() => void copiarToken()}
              disabled={!webhookToken.trim()}
              className="px-3 py-2 text-sm rounded-lg border border-[#0176d3] text-[#0176d3] dark:text-[#5eb0ff] disabled:opacity-50"
            >
              Copiar token para o Asaas
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
