'use client';

interface KPICardProps {
  title: string;
  value: string | number;
  className?: string;
}

export default function KPICard({ title, value, className = '' }: KPICardProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 p-6 rounded-lg shadow ${className}`}>
      <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">{title}</h3>
      <p className="text-2xl sm:text-3xl font-bold mt-1 text-gray-900 dark:text-white">
        {value}
      </p>
    </div>
  );
}
