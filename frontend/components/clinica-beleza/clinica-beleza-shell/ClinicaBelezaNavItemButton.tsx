import type { ElementType } from "react";
import { ChevronDown } from "lucide-react";
import { useClinicaBelezaTheme } from "../ClinicaBelezaThemeContext";

interface ClinicaBelezaNavItemButtonProps {
  label: string;
  icon: ElementType;
  isActive: boolean;
  collapsed: boolean;
  hasChildren?: boolean;
  expanded?: boolean;
  onClick: () => void;
}

export function ClinicaBelezaNavItemButton({
  label,
  icon: Icon,
  isActive,
  collapsed,
  hasChildren,
  expanded,
  onClick,
}: ClinicaBelezaNavItemButtonProps) {
  const { primary } = useClinicaBelezaTheme();
  return (
    <button
      type="button"
      onClick={onClick}
      title={collapsed ? label : undefined}
      className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
        collapsed ? "justify-center px-2" : ""
      } ${
        isActive
          ? "text-white shadow-sm"
          : "text-gray-600 hover:bg-white/80 dark:text-gray-300 dark:hover:bg-gray-700/50"
      }`}
      style={isActive ? { backgroundColor: primary } : undefined}
    >
      <Icon className="w-5 h-5 shrink-0" />
      {!collapsed && (
        <>
          <span className="flex-1 text-left">{label}</span>
          {hasChildren && (
            <ChevronDown
              className={`w-4 h-4 shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
          )}
        </>
      )}
    </button>
  );
}
