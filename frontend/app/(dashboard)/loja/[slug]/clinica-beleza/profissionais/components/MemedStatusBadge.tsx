'use client';

export interface MemedStatusInfo {
  state: string;
  label: string;
  status?: string;
  terms_accepted?: boolean;
  tem_token?: boolean;
  environment?: string;
}

function badgeClass(info: MemedStatusInfo): string {
  const base = 'inline-block px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap';
  if (info.state === 'ok') {
    const s = (info.status || '').toLowerCase();
    if (s === 'ativo') {
      return `${base} bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300`;
    }
    if (s.includes('análise') || s.includes('analise')) {
      return `${base} bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300`;
    }
    return `${base} bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300`;
  }
  if (info.state === 'nao_cadastrado') {
    return `${base} bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-400`;
  }
  if (info.state === 'sem_cpf') {
    return `${base} bg-gray-50 dark:bg-neutral-800 text-gray-400 dark:text-gray-500`;
  }
  if (info.state === 'erro' || info.state === 'sem_credenciais') {
    return `${base} bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300`;
  }
  return `${base} bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-400`;
}

function tooltip(info: MemedStatusInfo): string {
  const parts = [info.label];
  if (info.state === 'ok') {
    if (info.terms_accepted === false) {
      parts.push('Termos da Memed ainda não aceitos pelo prescritor.');
    }
    if (info.environment) {
      parts.push(`Ambiente: ${info.environment}.`);
    }
  }
  return parts.join(' ');
}

interface Props {
  info?: MemedStatusInfo | null;
  loading?: boolean;
}

export function MemedStatusBadge({ info, loading }: Props) {
  if (loading) {
    return <span className="text-xs text-gray-400 dark:text-gray-500">…</span>;
  }
  if (!info) {
    return <span className="text-xs text-gray-400 dark:text-gray-500">—</span>;
  }
  return (
    <span className={badgeClass(info)} title={tooltip(info)}>
      {info.label}
    </span>
  );
}
