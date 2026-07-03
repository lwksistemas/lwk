import {
  CLINICA_BELEZA_NAV_ITEMS,
  isClinicaBelezaNavGroupActive,
} from "../clinica-beleza-nav";
import { SIDEBAR_COLLAPSED_STORAGE_KEY } from "./clinica-beleza-shell-types";

export function normalizeNavPath(path: string): string {
  return path.split("?")[0].replace(/\/$/, "");
}

export function shouldSkipNavigation(pathname: string, href: string): boolean {
  const normalizedPath = normalizeNavPath(pathname);
  const normalizedHref = normalizeNavPath(href);
  return normalizedPath === normalizedHref && !href.includes("?");
}

export function buildInitialOpenGroups(pathname: string, slug: string): Record<string, boolean> {
  const initial: Record<string, boolean> = {};
  CLINICA_BELEZA_NAV_ITEMS.forEach((item) => {
    if (item.children && isClinicaBelezaNavGroupActive(pathname, slug, item)) {
      initial[item.label] = true;
    }
  });
  return initial;
}

export function readSidebarCollapsedFromSession(): boolean | null {
  if (typeof window === "undefined") return null;
  const stored = sessionStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY);
  if (stored === null) return null;
  return stored === "true";
}

export function getDefaultSidebarCollapsed(): boolean {
  const stored = readSidebarCollapsedFromSession();
  if (stored !== null) return stored;
  return typeof window !== "undefined" && window.innerWidth >= 1024;
}

export function getDesktopSidebarClassName(collapsed: boolean): string {
  return `flex flex-col shrink-0 sticky top-0 h-screen z-20 overflow-hidden bg-[#f0eaec] dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 ${
    collapsed ? "w-16" : "w-64"
  }`;
}

export function getMobileDrawerClassName(open: boolean): string {
  return `lg:hidden fixed inset-y-0 left-0 z-[100] w-[min(18rem,85vw)] max-w-xs flex flex-col bg-[#f0eaec] dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 shadow-xl transform transition-transform duration-200 ease-out ${
    open ? "translate-x-0" : "-translate-x-full pointer-events-none"
  }`;
}
