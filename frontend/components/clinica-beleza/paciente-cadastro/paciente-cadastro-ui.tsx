import type { InputHTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export const FORM_SELECT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

export const SECTION_TITLE_CLASS =
  "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2";

export function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
      {children}
    </label>
  );
}

export function IconInput({
  icon: Icon,
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { icon: LucideIcon }) {
  return (
    <div className="relative">
      <Icon
        size={16}
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
        aria-hidden
      />
      <input
        {...props}
        className={`w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-0 ${className}`}
      />
    </div>
  );
}
