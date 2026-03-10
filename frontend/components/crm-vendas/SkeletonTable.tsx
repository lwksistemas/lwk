interface SkeletonTableProps {
  rows?: number;
  columns?: number;
}

export default function SkeletonTable({ rows = 5, columns = 4 }: SkeletonTableProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden animate-pulse">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
              {Array.from({ length: columns }).map((_, i) => (
                <th key={i} className="text-left py-3 px-4">
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b border-gray-100 dark:border-gray-700"
              >
                {Array.from({ length: columns }).map((_, colIndex) => (
                  <td key={colIndex} className="py-3 px-4">
                    <div className={`h-4 bg-gray-200 dark:bg-gray-700 rounded ${
                      colIndex === 0 ? 'w-32' : colIndex === columns - 1 ? 'w-16' : 'w-24'
                    }`}></div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
