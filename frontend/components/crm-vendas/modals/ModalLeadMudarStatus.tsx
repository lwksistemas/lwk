'use client';

interface ModalLeadMudarStatusProps {
  lead: { nome: string; status: string };
  novoStatus: string;
  formErro: string | null;
  enviando: boolean;
  statusOpcoes: Array<{ value: string; label: string }>;
  onNovoStatusChange: (value: string) => void;
  onSalvar: () => void;
  onClose: () => void;
}

export default function ModalLeadMudarStatus({
  lead,
  novoStatus,
  formErro,
  enviando,
  statusOpcoes,
  onNovoStatusChange,
  onSalvar,
  onClose,
}: ModalLeadMudarStatusProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={() => { if (!enviando) onClose(); }}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-sm p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Mudar status</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{lead.nome}</p>
        {formErro && (
          <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg mb-3">
            {formErro}
          </p>
        )}
        <select
          value={novoStatus}
          onChange={(e) => onNovoStatusChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
        >
          {statusOpcoes.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onSalvar}
            disabled={enviando || novoStatus === lead.status}
            className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
          >
            {enviando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}
