'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, LogIn } from 'lucide-react';

export default function ConfiguracoesLoginPage() {
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
            <LogIn size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Configurar tela de login
          </h1>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Personalize a aparência da tela de login da sua loja (logo, cores e identidade visual).
        </p>
        <div className="bg-gray-50 dark:bg-[#0d1f3c] rounded-lg p-4 border border-gray-200 dark:border-[#0d1f3c]">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Em breve você poderá personalizar a tela de login. Entre em contato com o suporte para
            solicitar alterações na identidade visual da sua loja.
          </p>
        </div>
      </div>
    </div>
  );
}
