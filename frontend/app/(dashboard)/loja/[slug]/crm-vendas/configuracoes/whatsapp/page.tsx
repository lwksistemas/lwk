'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, MessageCircle } from 'lucide-react';

export default function ConfiguracoesWhatsappPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;

  return (
    <div className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3] dark:hover:text-[#0d9dda]"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
            <MessageCircle size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Configurar WhatsApp
          </h1>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Envie lembretes de tarefas do calendário por WhatsApp. Configure a integração para
          receber notificações automáticas das suas atividades.
        </p>
        <div className="bg-gray-50 dark:bg-[#0d1f3c] rounded-lg p-4 border border-gray-200 dark:border-[#0d1f3c]">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            A integração WhatsApp para envio de tarefas do calendário está em desenvolvimento.
            Entre em contato com o suporte para mais informações.
          </p>
        </div>
      </div>
    </div>
  );
}
