"use client";

import { RefreshCw, Smartphone } from "lucide-react";
import { MAX_FOTOS_POR_CONSULTA } from "../fotos/fotos-constants";

interface ConsultaFotosToolbarProps {
  fotosConsultaCount: number;
  podeEnviarMais: boolean;
  qrLoading: boolean;
  onCarregar: () => void;
  onAbrirQr: () => void;
}

export function ConsultaFotosToolbar({
  fotosConsultaCount,
  podeEnviarMais,
  qrLoading,
  onCarregar,
  onAbrirQr,
}: ConsultaFotosToolbarProps) {
  return (
    <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
      <span className="hidden xl:inline text-xs text-gray-500 dark:text-gray-400 max-w-[220px] truncate">
        Esta consulta {fotosConsultaCount}/{MAX_FOTOS_POR_CONSULTA} · histórico · compare 3
      </span>
      <button
        type="button"
        onClick={() => void onCarregar()}
        className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg text-xs sm:text-sm border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800"
      >
        <RefreshCw size={14} />
        <span className="hidden sm:inline">Atualizar</span>
      </button>
      {podeEnviarMais && (
        <button
          type="button"
          onClick={() => void onAbrirQr()}
          disabled={qrLoading}
          className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg text-white text-xs sm:text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
        >
          <Smartphone size={14} />
          <span className="hidden md:inline">{qrLoading ? "Gerando…" : "QR — foto no celular"}</span>
          <span className="md:hidden">{qrLoading ? "…" : "QR"}</span>
        </button>
      )}
    </div>
  );
}
