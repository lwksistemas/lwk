'use client';

import { FileText } from 'lucide-react';

interface Props {
  onDownloadPdf: () => void;
  onDownloadDocx?: () => void;
  motivoCancelamento?: string;
  somentePdf?: boolean;
}

export default function CrmDocumentoArquivoAcoes({
  onDownloadPdf,
  onDownloadDocx,
  motivoCancelamento,
  somentePdf = false,
}: Props) {
  return (
    <>
      <button
        type="button"
        onClick={onDownloadPdf}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <FileText size={15} className="text-red-500" /> Baixar PDF
      </button>
      {!somentePdf && onDownloadDocx && (
        <button
          type="button"
          onClick={onDownloadDocx}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <FileText size={15} className="text-blue-600" /> Baixar Word
        </button>
      )}
      {motivoCancelamento && (
        <div className="px-3 py-2 border-t border-gray-100 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Motivo do cancelamento:</p>
          <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{motivoCancelamento}</p>
        </div>
      )}
    </>
  );
}
