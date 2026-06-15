'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, MessageCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { LojaWhatsAppConfigPanel } from '@/components/whatsapp/LojaWhatsAppConfigPanel';
import { configuracoesPathForTipo, isTipoClinicaBeleza } from '@/lib/loja-tipo';
import { whatsappFeaturesForTipoLoja } from '@/lib/whatsapp-config-api';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

export default function LojaConfiguracoesWhatsappPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
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
  const clinicaBeleza = isTipoClinicaBeleza(tipoLojaNome);

  if (clinicaBeleza) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title="Configurar WhatsApp"
          subtitle="Meta Cloud API ou WhatsApp Web (Evolution)"
          icon={MessageCircle}
          backHref={backHref}
        />
        <ClinicaBelezaPageContent>
          {loading ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
          ) : (
            <LojaWhatsAppConfigPanel features={features} />
          )}
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <Link
          href={backHref}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
        >
          <ArrowLeft size={16} />
          Voltar
        </Link>

        <div className="flex items-center gap-3">
          <div
            className="p-2.5 rounded-lg text-white"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
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
          <LojaWhatsAppConfigPanel features={features} />
        )}
      </div>
    </div>
  );
}
