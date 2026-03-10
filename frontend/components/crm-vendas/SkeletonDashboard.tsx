import SkeletonCard from './SkeletonCard';

export default function SkeletonDashboard() {
  return (
    <div className="space-y-5">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse"></div>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse"></div>
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-28 animate-pulse"></div>
        </div>
      </div>

      {/* Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Pipeline Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6 animate-pulse">
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-40"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-36"></div>
          </div>
        </div>
        <div className="lg:col-span-2 bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-5 animate-pulse">
          <div className="space-y-4">
            <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-40"></div>
            <div className="flex gap-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex-shrink-0 w-32 h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Chart Skeleton */}
      <div className="bg-blue-50/40 dark:bg-blue-900/10 rounded-2xl border-2 border-blue-200 dark:border-blue-800 p-6 animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-5"></div>
        <div className="h-80 bg-white/60 dark:bg-slate-800/60 rounded-xl"></div>
      </div>

      {/* Activities Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-5 animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 py-2.5">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-5 animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 py-2.5">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
                </div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
