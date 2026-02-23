'use client';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  cor: string;
  trend?: string;
}

/** Card de estatística do dashboard. */
export function StatCard({ title, value, icon, cor, trend }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 md:p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 card-hover group">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm font-medium truncate">{title}</h3>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold mt-1 sm:mt-2 text-gray-900 dark:text-white truncate" style={{ color: cor }}>
            {value}
          </p>
          {trend != null && (
            <span className="text-[10px] sm:text-xs text-green-500 dark:text-green-400 font-medium mt-1 inline-block">
              {trend} vs mês anterior
            </span>
          )}
        </div>
        <div
          className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0
                     transform group-hover:scale-110 transition-transform duration-200"
          style={{ backgroundColor: `${cor}20` }}
        >
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}
