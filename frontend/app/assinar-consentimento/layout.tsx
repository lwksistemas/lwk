import type { ReactNode } from "react";
import { AssinarConsentimentoThemeSync } from "@/components/assinar-consentimento/AssinarConsentimentoTheme";

const APPLY_SYSTEM_DARK = `(function(){var e=document.getElementById('assinar-consentimento-root');if(!e)return;var d=window.matchMedia('(prefers-color-scheme: dark)').matches;e.classList.toggle('dark',d);e.style.colorScheme=d?'dark':'light';})();`;

export default function AssinarConsentimentoLayout({ children }: { children: ReactNode }) {
  return (
    <div id="assinar-consentimento-root">
      <script dangerouslySetInnerHTML={{ __html: APPLY_SYSTEM_DARK }} />
      <AssinarConsentimentoThemeSync />
      {children}
    </div>
  );
}
