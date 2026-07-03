'use client';

interface Props {
  label: string;
  valor: string;
  labelClass?: string;
  hint?: string;
}

export default function CrmOportunidadeVinculadaReadonly({
  label,
  valor,
  labelClass = 'block text-xs text-gray-500 dark:text-gray-400 mb-0.5',
  hint = 'A oportunidade não pode ser alterada na edição.',
}: Props) {
  return (
    <div>
      <span className={labelClass}>{label}</span>
      <p className="text-sm font-medium text-gray-900 dark:text-white py-2.5 px-3 rounded-lg bg-gray-50 dark:bg-[#0d1f3c]/40 border border-gray-200 dark:border-[#0d1f3c]">
        {valor || '—'}
      </p>
      {hint ? <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{hint}</p> : null}
    </div>
  );
}
