'use client';

interface Props {
  enviando: boolean;
  showCancel?: boolean;
  onCancel?: () => void;
  className?: string;
  saveLabel?: string;
  savingLabel?: string;
}

export default function CrmDocumentoFormActions({
  enviando,
  showCancel = true,
  onCancel,
  className = '',
  saveLabel = 'Salvar',
  savingLabel = 'Salvando...',
}: Props) {
  return (
    <div className={`flex gap-2 pt-2 ${className}`}>
      {showCancel && onCancel && (
        <button
          type="button"
          onClick={() => !enviando && onCancel()}
          className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          Cancelar
        </button>
      )}
      <button
        type="submit"
        disabled={enviando}
        className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
      >
        {enviando ? savingLabel : saveLabel}
      </button>
    </div>
  );
}
