import type { ReactNode } from "react";
import type { LojaInfo } from "@/types/dashboard";

export interface ClinicaBelezaShellProps {
  loja: LojaInfo;
  onLogout?: () => void;
  children: ReactNode;
  mainClassName?: string;
}

export interface ClinicaBelezaSidebarContentProps {
  loja: LojaInfo;
  slug: string;
  pathname: string;
  sidebarCollapsed: boolean;
  isMobileDrawer?: boolean;
  onCloseMobile?: () => void;
  setSidebarCollapsed: (v: boolean) => void;
  onNavigate: (href: string) => void;
}

export const SIDEBAR_COLLAPSED_STORAGE_KEY = "sidebar-collapsed";
