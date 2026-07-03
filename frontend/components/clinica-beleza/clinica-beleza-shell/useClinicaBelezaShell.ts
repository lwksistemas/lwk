"use client";

import { useEffect, useState } from "react";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { syncLojaTenantSlug } from "@/lib/auth";
import type { LojaInfo } from "@/types/dashboard";
import {
  getDefaultSidebarCollapsed,
  shouldSkipNavigation,
} from "./clinica-beleza-shell-utils";
import { SIDEBAR_COLLAPSED_STORAGE_KEY } from "./clinica-beleza-shell-types";

export function useClinicaBelezaShell(loja: LojaInfo) {
  const params = useParams();
  const pathname = usePathname() ?? "";
  const router = useRouter();
  const slug = (params?.slug as string) || loja?.slug || "";

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(getDefaultSidebarCollapsed);
  const [darkMode, setDarkMode] = useClinicaBelezaDark();

  useEffect(() => {
    sessionStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    if (slug) syncLojaTenantSlug(slug);
  }, [slug]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!sidebarOpen) {
      document.body.style.overflow = "";
      return;
    }
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [sidebarOpen]);

  const handleNavigate = (href: string) => {
    setSidebarOpen(false);
    if (shouldSkipNavigation(pathname, href)) return;
    syncLojaTenantSlug(slug);
    router.push(href);
  };

  return {
    slug,
    pathname,
    sidebarOpen,
    setSidebarOpen,
    sidebarCollapsed,
    setSidebarCollapsed,
    darkMode,
    setDarkMode,
    handleNavigate,
  };
}
