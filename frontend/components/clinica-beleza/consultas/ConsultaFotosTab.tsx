"use client";

import { useEffect, type ReactNode } from "react";
import { Columns2, Check, Trash2 } from "lucide-react";
import { ImageUploadMedia as ImageUpload } from "@/components/ImageUploadMedia";
import { PacienteFotoZoomModal } from "./PacienteFotoZoomModal";
import { MAX_FOTOS_POR_CONSULTA } from "./fotos/fotos-constants";
import { useConsultaFotosTab } from "./fotos-tab/useConsultaFotosTab";
import { ConsultaFotosToolbar } from "./fotos-tab/ConsultaFotosToolbar";
import { ConsultaFotosQrModal } from "./fotos-tab/ConsultaFotosQrModal";
import { ConsultaFotosComparacaoModal } from "./fotos-tab/ConsultaFotosComparacaoModal";

export function ConsultaFotosTab({
  consultaId,
  permiteEnviar,
  ativa,
  onToolbarChange,
  ocultarAvisoFinalizada = false,
}: {
  consultaId: number;
  permiteEnviar?: boolean;
  ativa?: boolean;
  onToolbarChange?: (toolbar: ReactNode | null) => void;
  /** No prontuário: fotos são só leitura mesmo com consulta em andamento. */
  ocultarAvisoFinalizada?: boolean;
}) {
  const {
    fotos,
    fotosConsultaCount,
    permiteUploadPlano,
    loading,
    qrAberto,
    setQrAberto,
    qrData,
    qrLoading,
    selecionadas,
    comparar,
    setComparar,
    salvando,
    zoomFoto,
    setZoomFoto,
    carregar,
    podeEnviarMais,
    abrirQr,
    salvarArquivo,
    excluir,
    toggleSelecao,
    fotosComparar,
    podeComparar,
  } = useConsultaFotosTab(consultaId, permiteEnviar, ativa);

  useEffect(() => {
    if (!onToolbarChange) return;
    onToolbarChange(
      <ConsultaFotosToolbar
        fotosConsultaCount={fotosConsultaCount}
        podeEnviarMais={podeEnviarMais}
        qrLoading={qrLoading}
        onCarregar={carregar}
        onAbrirQr={abrirQr}
      />,
    );
    return () => onToolbarChange(null);
  }, [onToolbarChange, podeEnviarMais, qrLoading, carregar, abrirQr, fotosConsultaCount]);

  return (
    <div className="space-y-3">
      {!permiteUploadPlano && (
        <p className="text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
          Seu plano não inclui fotos de acompanhamento. Faça upgrade para Intermediário ou Completo para enviar fotos pelo painel ou QR.
        </p>
      )}
      {!permiteEnviar && permiteUploadPlano && !ocultarAvisoFinalizada && (
        <p className="text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
          Consulta finalizada — apenas visualizar e comparar fotos.
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        {permiteEnviar && permiteUploadPlano ? (
          <div className="flex flex-wrap items-center gap-2">
            {podeEnviarMais ? (
              <ImageUpload
                compact
                buttonLabel={salvando ? "Salvando…" : "Adicionar foto"}
                onFileSelect={(file) => void salvarArquivo(file)}
                folder="fotos"
                disabled={salvando}
                maxSize={2}
              />
            ) : (
              <span className="text-xs text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg px-2.5 py-1.5">
                Limite de {MAX_FOTOS_POR_CONSULTA} fotos nesta consulta
              </span>
            )}
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {fotosConsultaCount}/{MAX_FOTOS_POR_CONSULTA}
              {podeEnviarMais ? " · ou QR no topo" : ""}
            </span>
          </div>
        ) : (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Histórico do paciente em todas as consultas
          </span>
        )}

        {fotos.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 ml-auto">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {selecionadas.length === 0
                ? "Marque ✓ em 2 ou 3 fotos para comparar"
                : `${selecionadas.length} selecionada${selecionadas.length !== 1 ? "s" : ""}`}
            </span>
            {podeComparar && (
              <button
                type="button"
                onClick={() => setComparar(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-white"
                style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
              >
                <Columns2 size={15} />
                Comparar lado a lado
              </button>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-gray-500 py-8 text-center">Carregando fotos…</p>
      ) : !fotos.length ? (
        <p className="text-sm text-gray-500 py-8 text-center rounded-xl border border-dashed border-gray-300 dark:border-neutral-600">
          {permiteEnviar && permiteUploadPlano
            ? "Nenhuma foto ainda. Durante a consulta, escaneie o QR com seu celular ou envie pelo painel."
            : "Nenhuma foto registrada neste acompanhamento."}
        </p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {fotos.map((f) => {
            const sel = selecionadas.includes(f.id);
            return (
              <div
                key={f.id}
                className={`relative group rounded-xl overflow-hidden border-2 transition-colors ${
                  sel ? "border-purple-600 ring-2 ring-purple-300" : "border-gray-200 dark:border-neutral-700"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setZoomFoto(f)}
                  className="block w-full aspect-square cursor-zoom-in"
                  title="Ampliar foto"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={f.url}
                    alt={`Foto ${f.consulta_data}`}
                    className="w-full h-full object-cover"
                  />
                </button>
                <button
                  type="button"
                  onClick={() => toggleSelecao(f.id)}
                  className={`absolute top-2 left-2 rounded-full p-1.5 shadow transition-colors ${
                    sel
                      ? "bg-purple-600 text-white"
                      : "bg-black/50 text-white hover:bg-black/70"
                  }`}
                  title={sel ? "Desmarcar comparação" : "Selecionar para comparar"}
                >
                  <Check size={14} />
                </button>
                <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[10px] px-2 py-1">
                  {f.consulta_data || "—"} · {f.origem_display}
                </div>
                {permiteEnviar && (
                  <button
                    type="button"
                    onClick={() => void excluir(f.id)}
                    className="absolute top-2 right-2 p-1.5 rounded-full bg-red-600/90 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Remover"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {qrAberto && qrData && (
        <ConsultaFotosQrModal qrData={qrData} onClose={() => setQrAberto(false)} />
      )}

      {zoomFoto && (
        <PacienteFotoZoomModal
          foto={zoomFoto}
          fotos={fotos}
          onClose={() => setZoomFoto(null)}
          onChangeFoto={setZoomFoto}
        />
      )}

      {comparar && fotosComparar.length >= 2 && (
        <ConsultaFotosComparacaoModal
          fotos={fotosComparar}
          onClose={() => setComparar(false)}
        />
      )}
    </div>
  );
}
