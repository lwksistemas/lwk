"use client";

import { Camera, Loader2, User, X } from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";
import { usePacienteFotoCadastro } from "./usePacienteFotoCadastro";

export interface PacienteFotoCadastroProps {
  slug: string;
  value: string;
  onChange: (url: string) => void;
  disabled?: boolean;
  accentColor?: string;
}

export function PacienteFotoCadastro({
  slug,
  value,
  onChange,
  disabled = false,
  accentColor,
}: PacienteFotoCadastroProps) {
  const {
    folder,
    uploadDisabled,
    lojaDocLoading,
    lojaDocReady,
    uploading,
    erro,
    cameraOpen,
    videoRef,
    pararCamera,
    abrirCamera,
    capturarFoto,
    enviarArquivo,
  } = usePacienteFotoCadastro({ slug, value, onChange, disabled });

  return (
    <>
      <div className="pb-2">
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">Foto do cliente</label>
        <div className="flex flex-wrap items-start gap-4">
          <div className="relative shrink-0">
            <div className="w-24 h-24 rounded-full border-2 border-gray-200 dark:border-neutral-600 overflow-hidden bg-gray-50 dark:bg-neutral-800 flex items-center justify-center">
              {value ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={value} alt="Foto do cliente" className="w-full h-full object-cover" />
              ) : (
                <User size={32} className="text-gray-300 dark:text-neutral-600" />
              )}
            </div>
            {value && !disabled && (
              <button
                type="button"
                onClick={() => onChange("")}
                className="absolute -top-1 -right-1 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow"
                title="Remover foto"
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div className="flex-1 min-w-[200px] space-y-2">
            <p className="text-xs text-gray-500 dark:text-gray-400">Importe da galeria ou use a webcam do notebook/celular.</p>
            <div className="flex flex-wrap gap-2">
              <ImageUpload
                compact
                value={value}
                onChange={onChange}
                folder={folder || "lwksistemas/misc"}
                aspectRatio="1:1"
                maxSize={5}
                disabled={uploadDisabled || uploading}
                buttonLabel={uploading ? "Enviando…" : "Importar foto"}
              />
              <button
                type="button"
                disabled={uploadDisabled || uploading}
                onClick={() => void abrirCamera()}
                className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
                style={accentColor ? { borderColor: `${accentColor}55` } : undefined}
              >
                {uploading ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
                Tirar foto
              </button>
            </div>
            {!lojaDocLoading && !lojaDocReady && (
              <p className="text-xs text-amber-700 dark:text-amber-300">Aguardando dados da loja para habilitar upload…</p>
            )}
            {erro && <p className="text-xs text-red-600 dark:text-red-400">{erro}</p>}
          </div>
        </div>
      </div>

      {cameraOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4">
          <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-neutral-700">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Tirar foto</h3>
              <button
                type="button"
                onClick={pararCamera}
                className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
                aria-label="Fechar câmera"
              >
                <X size={18} />
              </button>
            </div>
            <div className="p-4 bg-black flex items-center justify-center">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full max-h-[60vh] rounded-lg object-contain mirror"
                style={{ transform: "scaleX(-1)" }}
              />
            </div>
            <div className="flex gap-3 px-4 py-4 border-t border-gray-200 dark:border-neutral-700">
              <button type="button" onClick={pararCamera} className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium">
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void capturarFoto()}
                disabled={uploading}
                className="flex-1 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-60 inline-flex items-center justify-center gap-2"
                style={{ backgroundColor: accentColor || "#7c3aed" }}
              >
                {uploading ? <Loader2 size={16} className="animate-spin" /> : <Camera size={16} />}
                Capturar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
