'use client';

import { BookOpen, ExternalLink } from 'lucide-react';

const META_DEV = 'https://developers.facebook.com/apps/';
const META_API_SETUP = 'https://developers.facebook.com/docs/whatsapp/cloud-api/get-started';

interface WhatsAppConfigHelpProps {
  variant?: 'clinica' | 'crm';
}

export function WhatsAppConfigHelp({ variant = 'clinica' }: WhatsAppConfigHelpProps) {
  const isCrm = variant === 'crm';
  const boxClass = isCrm
    ? 'rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50/60 dark:bg-blue-900/20 px-4 py-4 space-y-3'
    : 'rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50/60 dark:bg-rose-950/20 px-4 py-4 space-y-3';
  const titleClass = isCrm
    ? 'text-sm font-medium text-blue-900 dark:text-blue-100 flex items-center gap-2'
    : 'text-sm font-medium text-rose-900 dark:text-rose-100 flex items-center gap-2';
  const linkClass = isCrm
    ? 'inline-flex items-center gap-1.5 text-xs font-medium text-blue-700 dark:text-blue-300 hover:underline'
    : 'inline-flex items-center gap-1.5 text-xs font-medium text-rose-700 dark:text-rose-300 hover:underline';
  const introClass = isCrm
    ? 'text-xs text-blue-800 dark:text-blue-200 font-medium'
    : 'text-xs text-rose-800 dark:text-rose-200 font-medium';
  const anchorClass = isCrm
    ? 'text-blue-700 dark:text-blue-300 hover:underline'
    : 'text-rose-700 dark:text-rose-300 hover:underline';

  return (
    <div className={boxClass}>
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <p className={titleClass}>
          <BookOpen size={16} />
          Como configurar na Meta
        </p>
        <a
          href={META_API_SETUP}
          target="_blank"
          rel="noopener noreferrer"
          className={linkClass}
        >
          Documentação oficial Meta
          <ExternalLink size={12} />
        </a>
      </div>

      <p className={introClass}>
        Modelo LWK: cada loja conecta <strong>seu próprio</strong> WhatsApp Business na Meta (número e token da{' '}
        {isCrm ? 'loja' : 'clínica'}).
      </p>

      <ol className="text-xs text-gray-700 dark:text-gray-300 space-y-1.5 list-decimal list-inside">
        <li>
          Crie um app em{' '}
          <a href={META_DEV} target="_blank" rel="noopener noreferrer" className={anchorClass}>
            developers.facebook.com
          </a>{' '}
          e adicione o produto <strong>WhatsApp</strong>.
        </li>
        <li>
          Em <strong>WhatsApp → API Setup</strong>, copie o <strong>Phone number ID</strong> e gere um{' '}
          <strong>token permanente</strong> (permissões de mensagens).
        </li>
        <li>
          Em modo teste, cadastre o celular do paciente em <strong>API Setup → To</strong> antes de enviar.
        </li>
        <li>Cole Phone ID e token abaixo, marque <strong>WhatsApp ativo</strong> e salve.</li>
      </ol>

      {variant === 'clinica' ? (
        <p className="text-xs text-gray-600 dark:text-gray-400">
          Confirmações saem ao confirmar agendamento. Lembretes 24h e 2h e <strong>cobranças de débitos pendentes</strong>{' '}
          rodam automaticamente no servidor LWK. Campanhas em massa podem exigir <strong>template aprovado</strong> na Meta.
        </p>
      ) : (
        <p className="text-xs text-gray-600 dark:text-gray-400">
          O CRM usa a mesma integração da loja. Lembretes de tarefas são enviados uma vez por dia (entre 7h e 9h) para o
          número configurado abaixo.
        </p>
      )}

    </div>
  );
}

interface WhatsAppConfigStatusProps {
  whatsappAtivo: boolean;
  whatsappPhoneId: string;
  whatsappTokenSet: boolean;
  whatsappNumero?: string;
  whatsappProvider?: 'meta' | 'evolution';
  whatsappConnectionStatus?: 'disconnected' | 'qr_pending' | 'connected' | 'error';
  whatsappConnectedPhone?: string;
  variant?: 'clinica' | 'crm';
}

export function WhatsAppConfigStatus({
  whatsappAtivo,
  whatsappPhoneId,
  whatsappTokenSet,
  whatsappNumero = '',
  whatsappProvider = 'meta',
  whatsappConnectionStatus = 'disconnected',
  whatsappConnectedPhone = '',
  variant = 'clinica',
}: WhatsAppConfigStatusProps) {
  const ready =
    whatsappProvider === 'evolution'
      ? whatsappAtivo && whatsappConnectionStatus === 'connected'
      : whatsappAtivo && whatsappPhoneId.trim() && whatsappTokenSet;
  const partial =
    whatsappProvider === 'evolution'
      ? whatsappAtivo || whatsappConnectionStatus === 'qr_pending'
      : whatsappAtivo && (whatsappPhoneId.trim() || whatsappTokenSet);

  let message: React.ReactNode;
  if (ready) {
    message =
      variant === 'crm' ? (
        <>Integração ativa — lembretes de tarefas podem ser enviados.</>
      ) : (
        <>Integração ativa — confirmações, lembretes e campanhas podem ser enviados.</>
      );
  } else if (partial) {
    message =
      whatsappProvider === 'evolution' ? (
        <>Conecte via QR Code e marque &quot;WhatsApp ativo&quot; para enviar.</>
      ) : (
        <>Preencha Phone ID e Token e mantenha &quot;WhatsApp ativo&quot; marcado.</>
      );
  } else if (whatsappProvider === 'evolution' && whatsappConnectionStatus === 'connected') {
    message = (
      <>
        WhatsApp Web conectado{whatsappConnectedPhone ? ` (${whatsappConnectedPhone})` : ''}. Ative acima para enviar.
      </>
    );
  } else if (whatsappNumero.trim()) {
    message = <>Número definido. Ative a integração acima para enviar mensagens.</>;
  } else {
    message = <>Configure Phone ID, token e número para começar a enviar.</>;
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/40 px-4 py-3">
      <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-0.5">Status</p>
      <p className="text-sm text-gray-800 dark:text-gray-200">
        {ready ? '✅ ' : partial ? '⚠️ ' : 'ℹ️ '}
        {message}
      </p>
    </div>
  );
}
