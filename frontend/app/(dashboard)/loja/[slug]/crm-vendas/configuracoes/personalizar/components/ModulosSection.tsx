'use client';

interface Props {
  modulos: Record<string, boolean>;
  onSave: (modulos: Record<string, boolean>) => void;
}

const MODULOS = [
  { key: 'leads', label: 'Leads', desc: 'Módulo principal (sempre ativo)', fixed: true },
  { key: 'contas', label: 'Contas (Empresas)', desc: 'Gerenciar empresas/organizações clientes', fixed: false },
  { key: 'contatos', label: 'Contatos', desc: 'Gerenciar pessoas de contato das empresas', fixed: false },
  { key: 'pipeline', label: 'Pipeline de Vendas', desc: 'Módulo principal (sempre ativo)', fixed: true },
  { key: 'atividades', label: 'Calendário / Atividades', desc: 'Módulo principal (sempre ativo)', fixed: true },
];

export function ModulosSection({ modulos, onSave }: Props) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Módulos Ativos</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Habilite ou desabilite módulos do CRM.</p>
      </div>
      <div className="space-y-3">
        {MODULOS.map((m) => (
          <div key={m.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={m.fixed ? true : modulos[m.key] !== false}
                disabled={m.fixed}
                onChange={() => { if (!m.fixed) onSave({ ...modulos, [m.key]: !modulos[m.key] }); }}
                className="w-4 h-4 text-[#0176d3] rounded disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{m.label}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{m.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
