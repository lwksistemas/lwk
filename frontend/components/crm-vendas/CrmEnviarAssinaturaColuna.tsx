'use client';

import { crmAssinaturaColunaLabels } from '@/lib/crm-enviar-cliente';
import CrmEnviarClienteIcones from '@/components/crm-vendas/CrmEnviarClienteIcones';

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
        <span className="block text-[10px] font-medium text-gray-600 dark:text-gray-400">{titulo}</span>
        {subtitulo && (
          <span className="block text-[9px] text-gray-400 dark:text-gray-500">{subtitulo}</span>
        )}
      </div>
      <CrmEnviarClienteIcones
        whatsappHabilitado={whatsappHabilitado}
        enviando={enviando}
        onEnviar={onEnviar}
        statusAssinatura={statusAssinatura}
      />
    </div>
  );
}
