'use client';

import { ModalBase } from './ModalBase';

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
      endpoint="/servicos/clientes/"
      formFields={[
        { name: 'nome', label: 'Nome', type: 'text', required: true, fullWidth: true },
        { name: 'email', label: 'Email', type: 'email', transform: (v: string) => v || null },
        { name: 'telefone', label: 'Telefone', type: 'tel', transform: (v: string) => v || null },
        { name: 'tipo_cliente', label: 'Tipo', type: 'select', required: true, options: [{ value: 'pf', label: 'Pessoa Física' }, { value: 'pj', label: 'Pessoa Jurídica' }], defaultValue: 'pf' },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.email || 'Sem email'} • {item.telefone || 'Sem telefone'}</p>
            <span className="inline-block mt-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 text-xs font-semibold rounded-full">{item.tipo_cliente === 'pf' ? 'Pessoa Física' : 'Pessoa Jurídica'}</span>
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
