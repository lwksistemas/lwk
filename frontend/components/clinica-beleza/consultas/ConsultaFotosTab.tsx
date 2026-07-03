"use client";

import { useEffect, type ReactNode } from "react";
import { useParams } from "next/navigation";
import { Columns2 } from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";
import { cloudinaryLojaClinicaFotos, useLojaCloudinaryDocument } from "@/lib/cloudinary-folders";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { PacienteFotoZoomModal } from "./PacienteFotoZoomModal";
import { ConsultaFotosCompararModal } from "./fotos/ConsultaFotosCompararModal";
import { ConsultaFotosGrid } from "./fotos/ConsultaFotosGrid";
import { ConsultaFotosQrModal } from "./fotos/ConsultaFotosQrModal";
import { ConsultaFotosToolbar } from "./fotos/ConsultaFotosToolbar";
import { MIN_FOTOS_COMPARAR } from "./fotos/fotos-constants";
import { useConsultaFotos } from "./fotos/useConsultaFotos";

export function ConsultaFotosTab({
  consultaId,
  permiteEnviar,
  ativa,
  onToolbarChange,
}: {
  consultaId: number;
  permiteEnviar?: boolean;
  ativa?: boolean;
  onToolbarChange?: (toolbar: ReactNode | null) => void;
}) {
  const params = useParams();
  const slug = (params.slug as string) || "loja";
  const { documento: lojaDoc, ready: lojaDocReady, loading: lojaDocLoading } = useLojaCloudinaryDocument(slug);

  const {
    fotos,
    loading,
    qrAberto,
    setQrAberto,
    qrData,
    qrLoading,
    selecionadas,
    comparar,
    setComparar,
    uploadUrl,
    setUploadUrl,
    salvando,
    zoomFoto,
    setZoomFoto,
    carregar,
    abrirQr,
    salvarUploadPainel,
    excluir,
    toggleSelecao,
    fotosComparar,
  } = useConsultaFotos(consultaId, ativa);

  useEffect(() => {
    if (!onToolbarChange) return;
    onToolbarChange(
      <ConsultaFotosToolbar
        permiteEnviar={permiteEnviar}
        qrLoading={qrLoading}
        onAtualizar={() => void carregar()}
        onAbrirQr={() => void abrirQr()}
      />,
    );
    return () => onToolbarChange(null);
  }, [onToolbarChange, permiteEnviar, qrLoading, carregar, abrirQr]);

  const podeComparar = selecionadas.length >= MIN_FOTOS_COMPARAR;

  return (
    <div className="space-y-3">
      {!permiteEnviar && (
        <p className="text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
          Consulta finalizada — apenas visualizar e comparar fotos.
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        {permiteEnviar ? (
          <div className="flex flex-wrap items-center gap-2">
            <ImageUpload
              compact
              buttonLabel={salvando ? "Salvando…" : "Adicionar foto"}
              value={uploadUrl}
              onChange={(url) => {
                setUploadUrl(url);
                if (url) void salvarUploadPainel(url);
              }}
              folder={cloudinaryLojaClinicaFotos(lojaDoc)}
              disabled={salvando || lojaDocLoading || !lojaDocReady}
            />
            <span className="text-xs text-gray-500 dark:text-gray-400 hidden sm:inline">
              ou QR no topo da página
            </span>
          </div>
        ) : (
          <span className="text-xs text-gray-500 dark:text-gray-400">Histórico do paciente em todas as consultas</span>
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
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
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
          {permiteEnviar
            ? "Nenhuma foto ainda. Durante a consulta, escaneie o QR com seu celular ou envie pelo painel."
            : "Nenhuma foto registrada neste acompanhamento."}
        </p>
      ) : (
        <ConsultaFotosGrid
          fotos={fotos}
          permiteEnviar={permiteEnviar}
          selecionadas={selecionadas}
          onZoom={setZoomFoto}
          onToggleSelecao={toggleSelecao}
          onExcluir={(id) => void excluir(id)}
        />
      )}

      {qrAberto && qrData && <ConsultaFotosQrModal qrData={qrData} onClose={() => setQrAberto(false)} />}

      {zoomFoto && (
        <PacienteFotoZoomModal
          foto={zoomFoto}
          fotos={fotos}
          onClose={() => setZoomFoto(null)}
          onChangeFoto={setZoomFoto}
        />
      )}

      {comparar && fotosComparar.length >= MIN_FOTOS_COMPARAR && (
        <ConsultaFotosCompararModal fotos={fotosComparar} onClose={() => setComparar(false)} />
      )}
    </div>
  );
}
