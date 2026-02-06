'use client';

import { ModalBase } from '@/components/servicos/modals/ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

export function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Profissionais"
      icon="👥"
      endpoint="/cabeleireiro/profissionais/"
      formFields={[
        { name: 'nome', label: 'Nome Completo', type: 'text', required: true, fullWidth: true },
        { name: 'telefone', label: 'Telefone', type: 'tel', required: true },
        { name: 'email', label: 'Email', type: 'email', transform: (v: string) => v || null },
        { name: 'especialidade', label: 'Especialidade', type: 'text', fullWidth: true, transform: (v: string) => v || null },
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
            <p className="text-sm text-gray-600 dark:text-gray-400">
              📱 {item.telefone || 'Sem telefone'} {item.email && `• ✉️ ${item.email}`}
            </p>
            {item.especialidade && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                ✂️ {item.especialidade}
              </p>
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
