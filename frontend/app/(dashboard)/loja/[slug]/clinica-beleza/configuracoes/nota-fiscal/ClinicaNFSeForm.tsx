'use client';

import { FileText, Loader2 } from 'lucide-react';
import { NFSeAsaasSection } from '@/components/clinica-beleza/nfse/NFSeAsaasSection';
import { NFSeFormBanner } from '@/components/clinica-beleza/nfse/NFSeFormBanner';
import { NFSeGeralSection } from '@/components/clinica-beleza/nfse/NFSeGeralSection';
import { NFSeIssnetSection } from '@/components/clinica-beleza/nfse/NFSeIssnetSection';
import { NFSeProvedorSection } from '@/components/clinica-beleza/nfse/NFSeProvedorSection';
import { useClinicaNFSeForm } from '@/hooks/clinica-beleza/useClinicaNFSeForm';

type Props = { configBackHref: string };

export default function ClinicaNFSeForm({ configBackHref: _configBackHref }: Props) {
  const form = useClinicaNFSeForm();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} />
          Nota Fiscal — Configuração da Clínica
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Configuração individual de NFS-e desta clínica para emissão aos seus clientes
        </p>
      </div>

      {form.message && <NFSeFormBanner message={form.message} />}

      <form onSubmit={form.handleSubmit} className="space-y-6">
        <NFSeProvedorSection
          provedor={form.formData.provedor_nf}
          onChange={(provedor) => form.updateFormField('provedor_nf', provedor)}
        />

        {form.formData.provedor_nf === 'asaas' && (
          <NFSeAsaasSection
            config={form.config}
            asaasApiKey={form.asaasApiKey}
            asaasWebhookToken={form.asaasWebhookToken}
            asaasSandbox={form.asaasSandbox}
            onApiKeyChange={form.setAsaasApiKey}
            onWebhookTokenChange={form.setAsaasWebhookToken}
            onSandboxChange={form.setAsaasSandbox}
          />
        )}

        {form.formData.provedor_nf === 'issnet' && (
          <NFSeIssnetSection
            formData={form.formData}
            config={form.config}
            certificadoFile={form.certificadoFile}
            issnetTestLoading={form.issnetTestLoading}
            issnetTestMessage={form.issnetTestMessage}
            issnetTestDisabled={form.issnetTestDisabled}
            onFieldChange={form.updateFormField}
            onFileChange={form.handleFileChange}
            onTest={form.testarConexaoIssnet}
          />
        )}

        <NFSeGeralSection formData={form.formData} onFieldChange={form.updateFormField} />

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={form.loading}
            className="px-6 py-3 bg-[#0176d3] text-white rounded-lg font-medium hover:bg-[#0156a3] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {form.loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Salvar Configurações
          </button>
        </div>
      </form>
    </div>
  );
}
