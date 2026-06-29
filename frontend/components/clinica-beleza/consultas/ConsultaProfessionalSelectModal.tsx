"use client";

interface ConsultaProfessionalSelectModalProps {
  open: boolean;
  profissionais: { id: number; nome?: string; name?: string }[];
  onSelect: (id: number) => void;
  onClose: () => void;
}

export function ConsultaProfessionalSelectModal({
  open,
  profissionais,
  onSelect,
  onClose,
}: ConsultaProfessionalSelectModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-sm">
        <div className="px-5 py-4 border-b border-gray-200 dark:border-neutral-700">
          <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            Selecione o Profissional
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Este agendamento não possui profissional. Informe quem realizará o atendimento.
          </p>
        </div>
        <div className="p-4 max-h-60 overflow-y-auto space-y-2">
          {profissionais.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelect(p.id)}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
            >
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {p.nome || p.name}
              </span>
            </button>
          ))}
          {profissionais.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              Nenhum profissional cadastrado.
            </p>
          )}
        </div>
        <div className="px-5 py-3 border-t border-gray-200 dark:border-neutral-700">
          <button
            type="button"
            onClick={onClose}
            className="w-full px-4 py-2 text-sm text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
