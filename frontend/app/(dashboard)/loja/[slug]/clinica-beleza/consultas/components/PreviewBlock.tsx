export function PreviewBlock({
  label,
  value,
  empty = "—",
  mono,
}: {
  label: string;
  value?: string | null;
  empty?: string;
  mono?: boolean;
}) {
  const text = (value ?? "").trim();
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <div
        className={`rounded-lg bg-gray-50 dark:bg-neutral-900/60 border border-gray-100 dark:border-neutral-700 px-3 py-2.5 text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap min-h-[2.5rem] ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {text || empty}
      </div>
    </div>
  );
}
