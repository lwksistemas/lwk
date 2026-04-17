'use client';

type VarianteVisual = 'proposta' | 'contrato';

interface CrmDocumentoStatusBadgeProps {
  statusAssinatura?: string;
  status: string;
  labelsComercial: Record<string, string>;
  labelsAssinatura: Record<string, string>;
  variante: VarianteVisual;
}

/**
 * Badge de status na listagem: prioriza workflow de assinatura quando ativo.
 */
export default function CrmDocumentoStatusBadge({
  statusAssinatura,
  status,
  labelsComercial,
  labelsAssinatura,
  variante,
}: CrmDocumentoStatusBadgeProps) {
  if (statusAssinatura && statusAssinatura !== 'rascunho') {
    const sa = statusAssinatura;
    let cls =
      'inline-block px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-600';
    if (sa === 'concluido') {
      cls = 'inline-block px-2 py-0.5 rounded text-xs bg-green-100 dark:bg-green-900/30 text-green-700';
    } else if (variante === 'proposta') {
      if (sa === 'aguardando_vendedor') {
        cls = 'inline-block px-2 py-0.5 rounded text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-700';
      } else if (sa === 'aguardando_cliente') {
        cls = 'inline-block px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700';
      }
    } else {
      if (sa === 'aguardando_vendedor' || sa === 'aguardando_cliente') {
        cls = 'inline-block px-2 py-0.5 rounded text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700';
      }
    }
    return <span className={cls}>{labelsAssinatura[sa] || sa}</span>;
  }

  let cls =
    'inline-block px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-600';
  if (variante === 'proposta') {
    if (status === 'aceita') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-green-100 dark:bg-green-900/30 text-green-700';
    else if (status === 'rejeitada') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-red-100 dark:bg-red-900/30 text-red-700';
    else if (status === 'cancelada') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-red-100 dark:bg-red-900/30 text-red-700';
    else if (status === 'enviada') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700';
  } else {
    if (status === 'assinado') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-green-100 dark:bg-green-900/30 text-green-700';
    else if (status === 'cancelado') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-red-100 dark:bg-red-900/30 text-red-700';
    else if (status === 'enviado') cls = 'inline-block px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700';
  }

  return <span className={cls}>{labelsComercial[status] || status}</span>;
}
