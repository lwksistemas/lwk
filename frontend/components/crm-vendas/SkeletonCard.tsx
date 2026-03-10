export default function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-[#16325c] p-5 rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm animate-pulse">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 space-y-3">
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
        </div>
        <div className="w-14 h-14 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
      </div>
    </div>
  );
}
