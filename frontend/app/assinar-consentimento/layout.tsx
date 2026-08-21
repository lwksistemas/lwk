import type { ReactNode } from "react";
import type { Viewport } from "next";
import { AssinarConsentimentoThemeSync } from "@/components/assinar-consentimento/AssinarConsentimentoTheme";

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#ffffff",
};

const FORCE_LIGHT = `(function(){var h=document.documentElement;h.classList.remove('dark');h.classList.add('light');h.style.colorScheme='only light';var e=document.getElementById('assinar-consentimento-root');if(!e)return;e.classList.remove('dark');e.style.colorScheme='only light';})();`;

export default function AssinarConsentimentoLayout({ children }: { children: ReactNode }) {
  return (
    <div id="assinar-consentimento-root" className="light" style={{ colorScheme: "only light" }}>
      <script dangerouslySetInnerHTML={{ __html: FORCE_LIGHT }} />
      <AssinarConsentimentoThemeSync />
      {children}
    </div>
  );
}
