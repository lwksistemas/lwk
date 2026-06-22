"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useParams } from "next/navigation";
import {
  QrCode,
  X,
  Trash2,
  Columns2,
  RefreshCw,
  Check,
  Copy,
  ExternalLink,
  Smartphone,
} from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";
import { cloudinaryLojaClinicaFotos, useLojaCloudinaryDocument } from "@/lib/cloudinary-folders";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type PacienteFotoItem } from "@/lib/clinica-beleza-api";
import { PacienteFotoZoomModal } from "./PacienteFotoZoomModal";

const MIN_COMPARAR = 2;
const MAX_COMPARAR = 3;

export function ConsultaFotosTab({
  consultaId,
  permiteEnviar,
  ativa,
  onToolbarChange,
}: {
  consultaId: number;
  /** Só true com consulta em andamento — envio pelo painel ou QR */
  permiteEnviar?: boolean;
  ativa?: boolean;
  onToolbarChange?: (toolbar: ReactNode | null) => void;
}) {
  const params = useParams();
  const slug = (params.slug as string) || "loja";
  const { documento: lojaDoc, ready: lojaDocReady, loading: lojaDocLoading } = useLojaCloudinaryDocument(slug);

  const [fotos, setFotos] = useState<PacienteFotoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [qrAberto, setQrAberto] = useState(false);
  const [qrData, setQrData] = useState<{ url: string; qr_base64: string } | null>(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [selecionadas, setSelecionadas] = useState<number[]>([]);
  const [comparar, setComparar] = useState(false);
  const [uploadUrl, setUploadUrl] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [zoomFoto, setZoomFoto] = useState<PacienteFotoItem | null>(null);

  const carregar = useCallback(async () => {
    try {
      const res = await ClinicaBelezaAPI.consultas.fotos.list(consultaId);
      setFotos(res.fotos || []);
    } catch {
      setFotos([]);
    } finally {
      setLoading(false);
    }
  }, [consultaId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  useEffect(() => {
    if (!ativa) return;
    const id = window.setInterval(() => {
      if (document.visibilityState !== "hidden") void carregar();
    }, 5000);
    return () => clearInterval(id);
  }, [ativa, carregar]);

  const abrirQr = useCallback(async () => {
    setQrLoading(true);
    try {
      const res = await ClinicaBelezaAPI.consultas.fotos.gerarQr(consultaId);
      setQrData({ url: res.url, qr_base64: res.qr_base64 });
      setQrAberto(true);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao gerar QR.");
    } finally {
      setQrLoading(false);
    }
  }, [consultaId]);

  const salvarUploadPainel = async (url: string) => {
    if (!url) return;
    setSalvando(true);
    try {
      await ClinicaBelezaAPI.consultas.fotos.salvar(consultaId, url);
      setUploadUrl("");
      await carregar();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao salvar foto.");
    } finally {
      setSalvando(false);
    }
  };

  const excluir = async (fotoId: number) => {
    if (!confirm("Remover esta foto do acompanhamento?")) return;
    try {
      await ClinicaBelezaAPI.consultas.fotos.excluir(consultaId, fotoId);
      setSelecionadas((s) => s.filter((id) => id !== fotoId));
      await carregar();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao remover.");
    }
  };

  const toggleSelecao = (id: number) => {
    setSelecionadas((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_COMPARAR) return [...prev.slice(1), id];
      return [...prev, id];
    });
  };

  const fotosComparar = fotos.filter((f) => selecionadas.includes(f.id));

  useEffect(() => {
    if (!onToolbarChange) return;
    onToolbarChange(
      <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
        <span className="hidden xl:inline text-xs text-gray-500 dark:text-gray-400 max-w-[220px] truncate">
          Fotos em todas as consultas · zoom · compare 3
        </span>
        <button
          type="button"
          onClick={() => void carregar()}
          className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg text-xs sm:text-sm border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800"
        >
          <RefreshCw size={14} />
          <span className="hidden sm:inline">Atualizar</span>
        </button>
        {permiteEnviar && (
          <button
            type="button"
            onClick={() => void abrirQr()}
            disabled={qrLoading}
            className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg text-white text-xs sm:text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <Smartphone size={14} />
            <span className="hidden md:inline">{qrLoading ? "Gerando…" : "QR — foto no celular"}</span>
            <span className="md:hidden">{qrLoading ? "…" : "QR"}</span>
          </button>
        )}
        {selecionadas.length >= MIN_COMPARAR && (
          <button
            type="button"
            onClick={() => setComparar(true)}
            className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium bg-gray-900 text-white dark:bg-white dark:text-gray-900"
          >
            <Columns2 size={14} />
            <span className="hidden sm:inline">Comparar lado a lado</span>
            <span className="sm:hidden">Comparar</span>
          </button>
        )}
      </div>,
    );
    return () => onToolbarChange(null);
  }, [onToolbarChange, permiteEnviar, qrLoading, selecionadas.length, carregar, abrirQr]);

  const podeComparar = selecionadas.length >= MIN_COMPARAR;
  const colsComparacao =
    fotosComparar.length >= MAX_COMPARAR
      ? "md:grid-cols-3"
      : fotosComparar.length === MIN_COMPARAR
        ? "md:grid-cols-2"
        : "md:grid-cols-1";

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
                    src={f.cloudinary_url}
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl max-w-sm w-full p-6 relative">
            <button
              type="button"
              onClick={() => setQrAberto(false)}
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
                  alert("Link copiado! Cole no navegador do seu celular.");
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
      )}

      {zoomFoto && (
        <PacienteFotoZoomModal
          foto={zoomFoto}
          fotos={fotos}
          onClose={() => setZoomFoto(null)}
          onChangeFoto={setZoomFoto}
        />
      )}

      {comparar && fotosComparar.length >= MIN_COMPARAR && (
        <div
          className="fixed inset-0 z-[60] bg-black flex flex-col"
          role="dialog"
          aria-modal
        >
          <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white shrink-0">
            <span className="text-sm font-medium">
              Comparação de {fotosComparar.length} foto{fotosComparar.length !== 1 ? "s" : ""} — tela cheia
            </span>
            <button
              type="button"
              onClick={() => setComparar(false)}
              className="p-2 rounded-lg hover:bg-white/10"
            >
              <X size={22} />
            </button>
          </div>
          <div className={`flex-1 grid grid-cols-1 ${colsComparacao} gap-0 min-h-0`}>
            {fotosComparar.map((f, i) => (
              <div key={f.id} className="relative flex flex-col min-h-0">
                <p className="text-xs text-white/70 px-3 py-1 shrink-0 bg-black/60 text-center">
                  Foto {i + 1} — {f.consulta_data} ({f.origem_display})
                </p>
                <div className="flex-1 min-h-0 overflow-hidden bg-neutral-900">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={f.cloudinary_url}
                    alt={`Comparação ${i + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
