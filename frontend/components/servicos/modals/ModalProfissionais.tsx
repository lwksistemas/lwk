'use client';

import { ModalBase } from './ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

export function ModalProfissionais({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      title="Profissionais"
      icon="👨‍🔧"
      endpoint="/servicos/profissionais/"
      formFields={[
        { name: 'nome', label: 'Nome', type: 'text', required: true, fullWidth: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'telefone', label: 'Telefone', type: 'tel', required: true },
        { name: 'especialidade', label: 'Especialidade', type: 'text', required: true },
        { name: 'registro_profissional', label: 'Registro Profissional', type: 'text', placeholder: 'Ex: CREA, CRM, etc.', transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.especialidade}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.email} • {item.telefone}</p>
            {item.registro_profissional && <span className="inline-block mt-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-semibold rounded-full">{item.registro_profissional}</span>}
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
