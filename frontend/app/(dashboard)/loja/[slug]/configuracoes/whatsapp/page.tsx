'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, MessageCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { LojaWhatsAppConfigPanel } from '@/components/whatsapp/LojaWhatsAppConfigPanel';
import { configuracoesPathForTipo } from '@/lib/loja-tipo';
import { whatsappFeaturesForTipoLoja } from '@/lib/whatsapp-config-api';

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
          <LojaWhatsAppConfigPanel features={features} />
        )}
      </div>
    </div>
  );
}
