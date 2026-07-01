'use client';

import { Mail, MessageCircle } from 'lucide-react';
import { crmAssinaturaBotaoTitle } from '@/lib/crm-enviar-cliente';

interface Props {
  whatsappHabilitado: boolean;
  enviando: boolean;
  onEnviar: (canal: 'email' | 'whatsapp') => void;
  /** Contexto para tooltip (ex.: aguardando_cliente). */
  statusAssinatura?: string;
  /** Estilo dos botões na lista do pipeline (modal editar). */
  variant?: 'table' | 'modal';
}

export default function CrmEnviarClienteIcones({
  whatsappHabilitado,
  enviando,
  onEnviar,
  statusAssinatura,
  variant = 'table',
}: Props) {
  const isModal = variant === 'modal';
  const emailCls = isModal
    ? 'p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50'
    : 'p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400 disabled:opacity-50';
  const waCls = isModal
    ? 'p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50'
    : 'p-1.5 rounded hover:bg-green-50 dark:hover:bg-green-900/30 text-green-600 dark:text-green-400 disabled:opacity-50';

  return (
    <div className="flex gap-1 shrink-0">
      <button
        type="button"
        onClick={() => onEnviar('email')}
        disabled={enviando}
        className={emailCls}
        title={statusAssinatura ? crmAssinaturaBotaoTitle('email', statusAssinatura) : 'Enviar por e-mail'}
      >
        <Mail size={16} />
      </button>
      {whatsappHabilitado && (
        <button
          type="button"
          onClick={() => onEnviar('whatsapp')}
          disabled={enviando}
          className={waCls}
          title={
            statusAssinatura
              ? crmAssinaturaBotaoTitle('whatsapp', statusAssinatura)
              : 'Enviar link ao cliente por WhatsApp'
          }
        >
          <MessageCircle size={16} />
        </button>
      )}
    </div>
  );
}
