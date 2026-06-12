'use client';

import { Mail, MessageCircle } from 'lucide-react';
import {
  crmAssinaturaBotaoTitle,
  crmAssinaturaColunaLabels,
} from '@/lib/crm-enviar-cliente';

interface CrmEnviarAssinaturaColunaProps {
  statusAssinatura?: string;
  whatsappHabilitado: boolean;
  enviando: boolean;
  onEnviar: (canal: 'email' | 'whatsapp') => void;
}

export default function CrmEnviarAssinaturaColuna({
  statusAssinatura,
  whatsappHabilitado,
  enviando,
  onEnviar,
}: CrmEnviarAssinaturaColunaProps) {
  const { titulo, subtitulo } = crmAssinaturaColunaLabels(statusAssinatura);

  if (statusAssinatura === 'concluido' || !titulo) {
    return <span className="text-gray-300 dark:text-gray-600 text-center block">—</span>;
  }

  return (
    <div className="flex flex-col items-center gap-1 min-w-[88px]">
      <div className="text-center leading-tight">
        <span className="block text-[10px] font-medium text-gray-600 dark:text-gray-400">
          {titulo}
        </span>
        {subtitulo && (
          <span className="block text-[9px] text-gray-400 dark:text-gray-500">{subtitulo}</span>
        )}
      </div>
      <div className="flex justify-center items-center gap-1">
        <button
          type="button"
          onClick={() => onEnviar('email')}
          disabled={enviando}
          className="p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400 disabled:opacity-50"
          title={crmAssinaturaBotaoTitle('email', statusAssinatura)}
        >
          <Mail size={16} />
        </button>
        {whatsappHabilitado && (
          <button
            type="button"
            onClick={() => onEnviar('whatsapp')}
            disabled={enviando}
            className="p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/30 text-green-600 dark:text-green-400 disabled:opacity-50"
            title={crmAssinaturaBotaoTitle('whatsapp', statusAssinatura)}
          >
            <MessageCircle size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
