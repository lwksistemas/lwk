"use client";

import type { ReactNode } from "react";

export interface EntityListColumn<T> {
  key: string;
  header: string;
  className?: string;
  render: (row: T) => ReactNode;
}

interface Props<T> {
  columns: EntityListColumn<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
  rowKey: (row: T) => string | number;
  emptyMessage?: ReactNode;
  trailingCell?: (row: T) => ReactNode;
}

export function EntityListTable<T>({
  columns,
  rows,
  onRowClick,
  rowKey,
  emptyMessage,
  trailingCell,
}: Props<T>) {
  if (rows.length === 0 && emptyMessage) {
    return <>{emptyMessage}</>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={`text-left px-4 md:px-6 py-3.5 font-semibold ${col.className || ""}`}>
                {col.header}
              </th>
            ))}
            {trailingCell && <th className="w-12" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-t border-gray-100 dark:border-neutral-700/80 transition-colors ${
                onRowClick
                  ? "hover:bg-[#F5E6EA]/40 dark:hover:bg-neutral-700/30 cursor-pointer"
                  : ""
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className={`px-4 md:px-6 py-4 ${col.className || ""}`}>
                  {col.render(row)}
                </td>
              ))}
              {trailingCell && <td className="px-4 py-4 text-gray-400">{trailingCell(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
