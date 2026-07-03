import type { HistoricoSection, HistoricoSectionConfig } from "./historico-types";

export function HistoricoSectionNav({
  sections,
  active,
  onChange,
}: {
  sections: HistoricoSectionConfig[];
  active: HistoricoSection;
  onChange: (section: HistoricoSection) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {sections.map(({ id, label, icon: Icon, count }) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            active === id
              ? "bg-[#8B3D52] text-white"
              : "bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-neutral-700"
          }`}
        >
          <Icon size={14} />
          {label}
          {count > 0 && (
            <span
              className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] ${
                active === id
                  ? "bg-white/20 text-white"
                  : "bg-gray-200 dark:bg-neutral-700 text-gray-600 dark:text-gray-400"
              }`}
            >
              {count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
