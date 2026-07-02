'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Edit2, Trash2 } from 'lucide-react';
import { CrmPagePanel } from '@/components/crm-vendas/CrmPagePanel';
import { ContaDetailView } from '@/components/crm-vendas/ContaDetailView';
import CrmConfirmDeleteModal from '@/components/crm-vendas/CrmConfirmDeleteModal';
import { useCrmContaDetailPage } from '@/hooks/crm-vendas/useCrmContaDetailPage';

export default function ContaDetailPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const id = parseInt(String(params?.id ?? ''), 10);

  const {
    conta,
    loading,
    excluindo,
    confirmarExclusao,
    setConfirmarExclusao,
    excluir,
    voltar,
    irParaEditar,
  } = useCrmContaDetailPage(slug, id);

  if (loading || !conta) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-col min-h-[calc(100dvh-3.5rem)]">
      <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <div className="max-w-4xl mx-auto space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={voltar}
              className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white w-fit"
            >
              <ArrowLeft size={16} />
              Voltar para contas
            </button>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={irParaEditar}
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium"
              >
                <Edit2 size={16} />
                Editar
              </button>
              <button
                type="button"
                onClick={() => setConfirmarExclusao(true)}
                className="inline-flex items-center gap-2 px-4 py-2 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <Trash2 size={16} />
                Excluir
              </button>
            </div>
          </div>

          <CrmPagePanel className="p-5 md:p-6 lg:p-8">
            <ContaDetailView conta={conta} />
          </CrmPagePanel>

          <div className="text-sm text-gray-500 dark:text-gray-400">
            <Link
              href={`/loja/${slug}/crm-vendas/contatos?conta_id=${conta.id}`}
              className="text-[#0176d3] hover:underline"
            >
              Ver contatos desta conta
            </Link>
          </div>
        </div>
      </div>

      {confirmarExclusao && (
        <CrmConfirmDeleteModal
          tituloItem={conta.nome}
          enviando={excluindo}
          onClose={() => setConfirmarExclusao(false)}
          onConfirm={excluir}
        />
      )}
    </div>
  );
}
