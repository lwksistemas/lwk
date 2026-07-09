"use client";

import { Copy, ExternalLink, QrCode, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useToast } from "@/components/ui/Toast";

export function ConsultaFotosQrModal({
  qrData,
  onClose,
}: {
  qrData: { url: string; qr_base64: string };
  onClose: () => void;
}) {
  const toast = useToast();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl max-w-sm w-full p-6 relative">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-3 right-3 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
        >
          <X size={20} />
        </button>
        <h3 className="text-lg font-semibold text-center mb-1 flex items-center justify-center gap-2">
          <QrCode size={20} />
          Foto no celular do profissional
        </h3>
        <p className="text-xs text-gray-500 text-center mb-4">
          1. Deixe este QR visível no computador
          <br />
          2. Abra a câmera do <strong>seu celular</strong> e escaneie
          <br />
          3. Fotografe o paciente — a imagem entra aqui automaticamente
        </p>
        {qrData.qr_base64 ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`data:image/png;base64,${qrData.qr_base64}`}
            alt="QR Code para fotografar paciente"
            className="mx-auto w-52 h-52"
          />
        ) : (
          <p className="text-center text-sm text-amber-700">QR indisponível — use o link abaixo.</p>
        )}
        <div className="mt-4 flex flex-col gap-2">
          <a
            href={qrData.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg text-sm font-medium border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800"
          >
            <ExternalLink size={16} />
            Abrir link no celular
          </a>
          <button
            type="button"
            onClick={() => {
              void navigator.clipboard.writeText(qrData.url);
              toast.success("Link copiado! Cole no navegador do seu celular.");
            }}
            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg text-sm font-medium text-white"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <Copy size={16} />
            Copiar link
          </button>
        </div>
        <p className="mt-3 text-[10px] text-gray-400 text-center">Válido por 24h · só durante esta consulta</p>
      </div>
    </div>
  );
}
