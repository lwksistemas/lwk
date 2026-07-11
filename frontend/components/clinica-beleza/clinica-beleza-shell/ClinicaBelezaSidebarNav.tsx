"use client";

import { useEffect, useState } from "react";
import {
  CLINICA_BELEZA_NAV_ITEMS,
  getClinicaBelezaNavHref,
  isClinicaBelezaNavActive,
  isClinicaBelezaNavGroupActive,
  type ClinicaBelezaNavItem,
} from "../clinica-beleza-nav";
import { CB_PRIMARY_CSS } from "@/lib/clinica-beleza-theme-utils";
import { buildInitialOpenGroups } from "./clinica-beleza-shell-utils";
import { ClinicaBelezaNavItemButton } from "./ClinicaBelezaNavItemButton";

interface ClinicaBelezaSidebarNavProps {
  slug: string;
  pathname: string;
  collapsed: boolean;
  onNavigate: (href: string) => void;
}

export function ClinicaBelezaSidebarNav({
  slug,
  pathname,
  collapsed,
  onNavigate,
}: ClinicaBelezaSidebarNavProps) {
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const initial = buildInitialOpenGroups(pathname, slug);
    setOpenGroups((prev) => ({ ...initial, ...prev }));
  }, [pathname, slug]);

  const toggleGroup = (label: string) => {
    setOpenGroups((prev) => ({ ...prev, [label]: !prev[label] }));
  };

  const renderItem = (item: ClinicaBelezaNavItem) => {
    if (item.children && item.children.length > 0) {
      const groupActive = isClinicaBelezaNavGroupActive(pathname, slug, item);
      const expanded = openGroups[item.label] ?? groupActive;

      return (
        <div key={item.label} className="space-y-0.5">
          <ClinicaBelezaNavItemButton
            label={item.label}
            icon={item.icon}
            isActive={groupActive && !expanded}
            collapsed={collapsed}
            hasChildren={!collapsed}
            expanded={expanded}
            onClick={() => {
              if (collapsed && item.children?.[0]) {
                onNavigate(getClinicaBelezaNavHref(slug, item.children[0].path));
              } else {
                toggleGroup(item.label);
              }
            }}
          />
          {!collapsed && expanded && (
            <div className="ml-4 pl-3 border-l border-gray-200 dark:border-gray-600 space-y-0.5">
              {item.children.map((child) => {
                const href = getClinicaBelezaNavHref(slug, child.path);
                const childActive = isClinicaBelezaNavActive(pathname, slug, child.path);
                return (
                  <button
                    key={child.path}
                    type="button"
                    onClick={() => onNavigate(href)}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      childActive
                        ? "font-medium text-white"
                        : "text-gray-500 hover:text-gray-800 hover:bg-white/60 dark:text-gray-400 dark:hover:bg-gray-700/40"
                    }`}
                    style={childActive ? { backgroundColor: CB_PRIMARY_CSS } : undefined}
                  >
                    {child.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      );
    }

    const path = item.path!;
    const href = getClinicaBelezaNavHref(slug, path);
    const isActive = isClinicaBelezaNavActive(pathname, slug, path);

    return (
      <ClinicaBelezaNavItemButton
        key={path}
        label={item.label}
        icon={item.icon}
        isActive={isActive}
        collapsed={collapsed}
        onClick={() => onNavigate(href)}
      />
    );
  };

  return (
    <nav
      className={`space-y-0.5 shrink-0 ${collapsed ? "p-2" : "px-3 py-2"} max-lg:flex-1 max-lg:min-h-0 max-lg:overflow-y-auto lg:overflow-visible`}
    >
      {CLINICA_BELEZA_NAV_ITEMS.map(renderItem)}
    </nav>
  );
}
