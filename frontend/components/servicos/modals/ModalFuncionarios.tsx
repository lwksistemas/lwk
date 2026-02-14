'use client';

import { ModalBase } from './ModalBase';

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
      title="Funcionários"
      icon="👥"
      endpoint="/servicos/funcionarios/"
      formFields={[
        { name: 'nome', label: 'Nome', type: 'text', required: true, fullWidth: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'telefone', label: 'Telefone', type: 'tel', required: true },
        { name: 'cargo', label: 'Cargo', type: 'text', placeholder: 'Ex: Atendente, Técnico, etc.' },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => {
        const isAdmin = item.is_admin || item.cargo?.toLowerCase().includes('admin');
        return (
          <div key={item.id} className={`flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3 ${isAdmin ? 'bg-blue-50 dark:bg-blue-900/10' : ''}`}>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.nome}</p>
                {isAdmin && <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">👤 Administrador</span>}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">{item.email} • {item.telefone}</p>
              {item.cargo && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{item.cargo}</p>}
            </div>
            <div className="flex gap-2">
              {isAdmin ? (
                <button disabled className="px-3 py-2 text-sm bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded-lg cursor-not-allowed min-h-[40px]">🔒 Protegido</button>
              ) : (
                <>
                  <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                  <button onClick={() => handleExcluir(item.id, item.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
                </>
              )}
            </div>
          </div>
        );
      }}
      emptyMessage="Nenhum funcionário cadastrado"
    />
  );
}
