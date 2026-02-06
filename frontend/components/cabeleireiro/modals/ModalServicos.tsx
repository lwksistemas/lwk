'use client';

import { ModalBase } from '@/components/servicos/modals/ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

export function ModalServicos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Serviços"
      icon="✂️"
      endpoint="/cabeleireiro/servicos/"
      formFields={[
        { name: 'nome', label: 'Nome do Serviço', type: 'text', required: true, fullWidth: true },
        { name: 'descricao', label: 'Descrição', type: 'textarea', fullWidth: true, transform: (v: string) => v || null },
        { name: 'duracao', label: 'Duração (minutos)', type: 'number', required: true },
        { name: 'preco', label: 'Preço (R$)', type: 'number', required: true, step: '0.01' },
        { name: 'ativo', label: 'Ativo', type: 'checkbox', defaultValue: true }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
              {item.ativo ? (
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-semibold rounded-full">Ativo</span>
              ) : (
                <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-semibold rounded-full">Inativo</span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              ⏱️ {item.duracao} min • 💰 R$ {parseFloat(item.preco).toFixed(2)}
            </p>
            {item.descricao && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{item.descricao}</p>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, item.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
    />
  );
}
