'use client';

interface ActionButtonProps {
  onClick: () => void;
  color: string;
  icon: string;
  label: string;
}

/** Botão de ação rápida do dashboard (grid de ações). */
export function ActionButton({ onClick, color, icon, label }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl text-white font-semibold
                 transition-all duration-200 transform hover:scale-105 active:scale-95
                 shadow-md sm:shadow-lg hover:shadow-xl btn-press
                 relative overflow-hidden min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
    >
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" aria-hidden />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2 transform group-hover:scale-110 transition-transform duration-200">{icon}</div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
      </div>
    </button>
  );
}
