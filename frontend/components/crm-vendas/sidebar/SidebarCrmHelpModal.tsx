'use client';

import { HelpCircle, X } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function SidebarCrmHelpModal({ open, onClose }: Props) {
  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <HelpCircle size={20} />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Central de Ajuda</h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6 space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Bem-vindo ao CRM de Vendas</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Sistema completo de gestão de vendas estilo Salesforce Lightning.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
              <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-2">O que está sincronizado</h4>
              <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Calendário — Atividades do CRM com Google Calendar</li>
                <li>• Notificações — Agendamentos, lembretes, financeiro</li>
              </ul>
            </div>

            <div className="space-y-4">
              {[
                { color: 'border-[#0176d3]', title: 'Home', text: 'Dashboard com métricas, gráficos e visão geral das vendas.' },
                { color: 'border-[#06a59a]', title: 'Leads', text: 'Gerencie seus leads, qualifique e converta em oportunidades.' },
                { color: 'border-[#ffb75d]', title: 'Oportunidades', text: 'Pipeline visual com etapas de vendas e acompanhamento de negociações.' },
                { color: 'border-[#e287b2]', title: 'Contas', text: 'Cadastro completo de clientes com informações de contato e segmentação.' },
                { color: 'border-[#0176d3]', title: 'Calendário', text: 'Visualize e gerencie reuniões, ligações e tarefas sincronizadas com o CRM.' },
              ].map((section) => (
                <div key={section.title} className={`border-l-4 ${section.color} pl-4`}>
                  <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">{section.title}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{section.text}</p>
                </div>
              ))}
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold text-blue-900 dark:text-blue-200 text-sm mb-2">Dica</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Use os atalhos de teclado para navegar mais rápido. Pressione{' '}
                <kbd className="px-2 py-1 bg-white dark:bg-gray-700 rounded border border-blue-300 dark:border-blue-700 text-xs">
                  Ctrl + K
                </kbd>{' '}
                para busca rápida.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors text-sm font-medium"
            >
              Entendi
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
