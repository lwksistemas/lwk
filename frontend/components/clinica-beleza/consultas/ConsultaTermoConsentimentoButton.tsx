"use client";

import { ChevronDown, FileSignature } from "lucide-react";
import { useWhatsappEnvioFlags } from "@/hooks/useWhatsappEnvioFlags";
import { TermoConsentimentoPanel } from "./termo-consentimento/TermoConsentimentoPanel";
import { useTermoConsentimento } from "./termo-consentimento/useTermoConsentimento";
import { useTermoDropdown } from "./termo-consentimento/useTermoDropdown";

export function ConsultaTermoConsentimentoButton({
  consultaId,
  onUpdated,
  compacto = false,
}: {
  consultaId: number;
  onUpdated?: () => void;
  compacto?: boolean;
}) {
  const { aberto, toggle, containerRef } = useTermoDropdown();
  const { termo: termoWhatsappHabilitado } = useWhatsappEnvioFlags();

  const { loading, termos, pendentesEnvio, badgeCount, enviar, reenviar, baixarPdf, enviarPdfWhatsapp, assinarProfissional } =
    useTermoConsentimento({
      consultaId,
      onUpdated,
      aberto,
    });

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={toggle}
        className={`flex items-center gap-1 rounded-lg font-medium transition-colors ${
          compacto ? "px-2 py-1 text-[11px]" : "gap-1.5 px-4 py-2 text-sm"
        } ${
          aberto
            ? "text-white"
            : "bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700"
        }`}
        style={aberto ? { backgroundColor: 'var(--cb-primary, #8B3D52)' } : undefined}
        title="Termos de consentimento por procedimento"
      >
        <FileSignature size={compacto ? 12 : 16} />
        {compacto ? "Termo" : "Termos"}
        {badgeCount > 0 && (
          <span
            className={`min-w-[1.25rem] h-5 px-1 rounded-full text-[10px] font-bold flex items-center justify-center ${
              aberto ? "bg-white/25 text-white" : "text-white"
            }`}
            style={aberto ? undefined : { backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          >
            {badgeCount}
          </span>
        )}
        <ChevronDown size={14} className={`transition-transform ${aberto ? "rotate-180" : ""}`} />
      </button>

      {aberto && (
        <TermoConsentimentoPanel
          termos={termos}
          loading={loading}
          pendentesEnvioCount={pendentesEnvio.length}
          termoWhatsappHabilitado={termoWhatsappHabilitado}
          onEnviar={(id, canal) => void enviar(id, canal)}
          onReenviar={(id, nome, canal) => void reenviar(id, nome, canal)}
          onBaixarPdf={(id, nome) => void baixarPdf(id, nome)}
          onEnviarPdfWhatsapp={(id, nome) => void enviarPdfWhatsapp(id, nome)}
          onAssinarProfissional={(id) => void assinarProfissional(id)}
          onEnviarTodos={(canal) => void enviar(undefined, canal)}
          ancora={compacto ? "direita" : "esquerda"}
        />
      )}
    </div>
  );
}
