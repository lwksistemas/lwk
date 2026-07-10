'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, MessageCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { LojaWhatsAppConfigPanel } from '@/components/whatsapp/LojaWhatsAppConfigPanel';
import {
  configuracoesPathForTipo,
  isTipoCRMVendas,
  resolveIsClinicaBeleza,
} from '@/lib/loja-tipo';
import { whatsappFeaturesForTipoLoja } from '@/lib/whatsapp-config-api';
import {
  ClinicaBelezaPageContent,
  ClinicaBelezaPanel,
} from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import {
  ClinicaBelezaStandardPageHeader,
  useClinicaBelezaShellActions,
} from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

const CRM_PRIMARY = '#0176d3';

export default function LojaConfiguracoesWhatsappPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const shellActions = useClinicaBelezaShellActions();
  const [tipoLojaNome, setTipoLojaNome] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const { data } = await apiClient.get<{ tipo_loja_nome?: string }>(
          `/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`,
        );
        if (!cancel) setTipoLojaNome(data?.tipo_loja_nome || '');
      } catch {
        if (!cancel) setTipoLojaNome('');
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [slug]);

  const features = whatsappFeaturesForTipoLoja(tipoLojaNome);
  const backHref = configuracoesPathForTipo(slug, tipoLojaNome);
  const inClinicaShell = Boolean(shellActions);
  const clinicaBeleza = resolveIsClinicaBeleza(tipoLojaNome);
  const crmVendas = isTipoCRMVendas(tipoLojaNome);
  const accentColor = clinicaBeleza ? CLINICA_BELEZA_PRIMARY : crmVendas ? CRM_PRIMARY : undefined;

  const panel = (
    <LojaWhatsAppConfigPanel
      features={features}
      accentColor={accentColor}
      embedded={clinicaBeleza || crmVendas}
    />
  );

  const backLink = (
    <Link
      href={backHref}
      className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
    >
      <ArrowLeft size={16} />
      Voltar às configurações
    </Link>
  );

  if (clinicaBeleza && inClinicaShell) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title="Configurar WhatsApp"
          subtitle="Meta Cloud API ou WhatsApp Web (Evolution)"
          icon={MessageCircle}
          backHref={backHref}
        />
        <ClinicaBelezaPageContent>
          <ClinicaBelezaPanel className="p-4 sm:p-6 w-full">
            {loading ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
            ) : (
              panel
            )}
          </ClinicaBelezaPanel>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  if (clinicaBeleza) {
    return (
      <ClinicaBelezaPageContent className="space-y-6">
        {backLink}
        <ClinicaBelezaPanel className="p-4 sm:p-6 w-full">
          <div className="flex items-center gap-3 mb-4">
            <div
              className="p-2.5 rounded-lg text-white"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              <MessageCircle size={24} />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Configurar WhatsApp</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Meta Cloud API ou WhatsApp Web (Evolution)
              </p>
            </div>
          </div>
          {loading ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
          ) : (
            panel
          )}
        </ClinicaBelezaPanel>
      </ClinicaBelezaPageContent>
    );
  }

  if (crmVendas) {
    return (
      <div className="space-y-6 w-full">
        {backLink}

        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6 w-full">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
              <MessageCircle size={24} />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Configurar WhatsApp</h1>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Meta Cloud API ou WhatsApp Web (Evolution) — lembretes de tarefas e envio de documentos pelo CRM.
          </p>
          {loading ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
          ) : (
            panel
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gray-50 dark:bg-gray-900">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
        {backLink}

        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
            <MessageCircle size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configurar WhatsApp</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Meta Cloud API ou WhatsApp Web (Evolution) — disponível para todos os apps
            </p>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          panel
        )}
      </div>
    </div>
  );
}
