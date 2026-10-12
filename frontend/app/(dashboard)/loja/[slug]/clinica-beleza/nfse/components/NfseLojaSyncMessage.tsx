'use client';

export function NfseLojaSyncMessage({ type, text }: { type: 'ok' | 'err' | 'info'; text: string }) {
  const cls =
    type === 'ok'
      ? 'bg-green-50 border-green-200 text-green-900 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200'
      : type === 'info'
        ? 'bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200'
        : 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-200';
  return <div className={`rounded-lg border px-4 py-3 text-sm ${cls}`}>{text}</div>;
}
