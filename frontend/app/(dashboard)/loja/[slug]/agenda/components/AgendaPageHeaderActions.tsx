import { CalendarDays, List, Lock, Plus } from "lucide-react";
import { OfflineIndicator } from "@/components/clinica-beleza/OfflineIndicator";
import { entityName } from "@/lib/clinica-beleza-entities";

export function AgendaPageHeaderActions({
  modoAgenda,
  onToggleModo,
  selectedProfessional,
  onSelectProfessional,
  professionals,
  onBloquear,
  onNovo,
}: {
  modoAgenda: "grade" | "lista";
  onToggleModo: () => void;
  selectedProfessional: string;
  onSelectProfessional: (id: string) => void;
  professionals: { id: number; nome?: string; name?: string }[];
  onBloquear: () => void;
  onNovo: () => void;
}) {
  return (
    <>
      <OfflineIndicator />
      <button
        type="button"
        onClick={onToggleModo}
        className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 text-xs sm:text-sm hover:bg-gray-50 dark:hover:bg-gray-600 shrink-0 transition-colors"
        title={modoAgenda === "grade" ? "Ver agenda em lista" : "Ver agenda em calendário"}
      >
        {modoAgenda === "grade" ? (
          <List size={16} className="sm:w-4 sm:h-4" />
        ) : (
          <CalendarDays size={16} className="sm:w-4 sm:h-4" />
        )}
        <span className="hidden sm:inline">{modoAgenda === "grade" ? "Lista" : "Calendário"}</span>
      </button>
      <select
        value={selectedProfessional}
        onChange={(e) => onSelectProfessional(e.target.value)}
        className="px-2.5 sm:px-3 py-1.5 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#8B3D52]/30 max-w-[120px] sm:max-w-none"
      >
        <option value="">Todos</option>
        {professionals.map((prof) => (
          <option key={prof.id} value={prof.id}>
            {entityName(prof)}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={onBloquear}
        className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors shrink-0 text-xs sm:text-sm"
        title="Bloquear horário"
      >
        <Lock size={16} className="sm:w-4 sm:h-4" />
        <span className="hidden sm:inline">Bloquear</span>
      </button>
      <button
        type="button"
        onClick={onNovo}
        className="hidden sm:flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-white rounded-lg hover:opacity-90 transition-opacity shrink-0 text-xs sm:text-sm font-medium"
        style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        title="Novo agendamento"
      >
        <Plus size={16} className="sm:w-4 sm:h-4" />
        <span>Novo</span>
      </button>
    </>
  );
}
