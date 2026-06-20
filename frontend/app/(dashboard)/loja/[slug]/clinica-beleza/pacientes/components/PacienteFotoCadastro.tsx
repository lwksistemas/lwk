"use client";

import { useRef, useState } from "react";
import { Camera, Loader2, Upload, User, X } from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";
import {
  cloudinaryLojaClinicaPacientePerfil,
  useLojaCloudinaryDocument,
} from "@/lib/cloudinary-folders";
import { uploadImagemCloudinary } from "@/lib/cloudinary-direct-upload";

interface PacienteFotoCadastroProps {
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
  const { documento: lojaDoc, ready: lojaDocReady, loading: lojaDocLoading } =
    useLojaCloudinaryDocument(slug);
  const folder = lojaDoc ? cloudinaryLojaClinicaPacientePerfil(lojaDoc) : "";
  const uploadDisabled = disabled || lojaDocLoading || !lojaDocReady || !folder;

  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [erro, setErro] = useState("");

  const enviarArquivo = async (file: File | undefined) => {
    if (!file || !folder) return;
    if (!file.type.startsWith("image/") && !/\.(jpe?g|png|gif|webp|heic|heif|bmp)$/i.test(file.name)) {
      setErro("Selecione um arquivo de imagem.");
      return;
    }
    setUploading(true);
    setErro("");
    try {
      const url = await uploadImagemCloudinary(file, folder);
      onChange(url);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao enviar foto.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="pb-2">
      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
        Foto do cliente
      </label>
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
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Importe da galeria ou tire foto com a câmera do dispositivo.
          </p>
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
              onClick={() => cameraInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
              style={accentColor ? { borderColor: `${accentColor}55` } : undefined}
            >
              {uploading ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
              Tirar foto
            </button>
          </div>
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="user"
            className="hidden"
            onChange={(e) => {
              void enviarArquivo(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
          {!lojaDocLoading && !lojaDocReady && (
            <p className="text-xs text-amber-700 dark:text-amber-300">
              Aguardando dados da loja para habilitar upload…
            </p>
          )}
          {erro && <p className="text-xs text-red-600 dark:text-red-400">{erro}</p>}
        </div>
      </div>
    </div>
  );
}
