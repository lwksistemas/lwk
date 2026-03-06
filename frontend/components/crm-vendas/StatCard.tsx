'use client';

interface StatCardProps {
  title: string;
  value: string;
  className?: string;
}

export default function StatCard({ title, value, className = '' }: StatCardProps) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 p-6 rounded-xl shadow border border-gray-100 dark:border-gray-700 ${className}`}
    >
      <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">
        {title}
      </p>
      <h2 className="text-2xl sm:text-3xl font-bold mt-2 text-gray-900 dark:text-white">
        {value}
      </h2>
    </div>
  );
}
