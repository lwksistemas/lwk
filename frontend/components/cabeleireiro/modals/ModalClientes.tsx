'use client';

import { ModalBase } from '@/components/servicos/modals/ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

export function ModalClientes({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Clientes"
      icon="👤"
      endpoint="/cabeleireiro/clientes/"
      formFields={[
        { name: 'nome', label: 'Nome Completo', type: 'text', required: true, fullWidth: true },
        { name: 'telefone', label: 'Telefone', type: 'tel', required: true },
        { name: 'email', label: 'Email', type: 'email', transform: (v: string) => v || null },
        { name: 'data_nascimento', label: 'Data de Nascimento', type: 'date', transform: (v: string) => v || null },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              📱 {item.telefone || 'Sem telefone'} {item.email && `• ✉️ ${item.email}`}
            </p>
            {item.data_nascimento && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                🎂 {new Date(item.data_nascimento).toLocaleDateString('pt-BR')}
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
