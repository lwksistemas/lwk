import { Info } from "lucide-react";
import { NFSE_CARD_CLASS, NFSE_INPUT_CLASS } from "@/components/clinica-beleza/nfse/nfse-form-types";
import type { NFSeConfigSnapshot } from "@/components/clinica-beleza/nfse/nfse-form-types";

interface Props {
  config: NFSeConfigSnapshot | null;
  asaasApiKey: string;
  asaasWebhookToken: string;
  asaasSandbox: boolean;
  onApiKeyChange: (value: string) => void;
  onWebhookTokenChange: (value: string) => void;
  onSandboxChange: (value: boolean) => void;
}

export function NFSeAsaasSection({
  config,
  asaasApiKey,
  asaasWebhookToken,
  asaasSandbox,
  onApiKeyChange,
  onWebhookTokenChange,
  onSandboxChange,
}: Props) {
  return (
    <div className={NFSE_CARD_CLASS}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Conta Asaas da Loja</h2>
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
        <div className="flex items-start gap-3">
          <Info size={18} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <p className="text-xs text-blue-800 dark:text-blue-200">
            Configure a API Key da conta Asaas da sua clínica para emissão de NFS-e. A chave fica no painel Asaas em
            Integrações → Chave de API.
          </p>
        </div>
      </div>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">API Key Asaas</label>
          <input
            type="password"
            value={asaasApiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder={
              config?.asaas_api_key_configured
                ? "••• chave já salva — cole nova para alterar"
                : "$aact_prod_... ou $aact_hmlg_..."
            }
            className={`${NFSE_INPUT_CLASS} font-mono text-sm`}
          />
          {config?.asaas_api_key_configured && (
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">✓ Chave configurada</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Token do Webhook (min. 32 caracteres)
          </label>
          <input
            type="password"
            value={asaasWebhookToken}
            onChange={(e) => onWebhookTokenChange(e.target.value)}
            placeholder={config?.asaas_webhook_token_configured ? "••• token já salvo" : "Token de autenticação"}
            className={`${NFSE_INPUT_CLASS} font-mono text-sm`}
          />
          {config?.asaas_webhook_token_configured && (
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">✓ Token configurado</p>
          )}
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={asaasSandbox}
            onChange={(e) => onSandboxChange(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">Sandbox (homologação)</span>
        </label>
        {config?.asaas_webhook_url && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 mt-2">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL do Webhook (configurar no painel Asaas):
            </p>
            <code className="text-xs text-gray-600 dark:text-gray-400 break-all">{config.asaas_webhook_url}</code>
          </div>
        )}
      </div>
    </div>
  );
}
