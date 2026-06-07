"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useParams } from "next/navigation";
import {
  Camera,
  QrCode,
  X,
  Trash2,
  Columns2,
  RefreshCw,
  Check,
  Copy,
  ExternalLink,
  Smartphone,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type PacienteFotoItem } from "@/lib/clinica-beleza-api";

const ZOOM_MIN = 1;
const ZOOM_MAX = 4;
const ZOOM_STEP = 0.5;
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
  const [zoomScale, setZoomScale] = useState(1);
  const [zoomPan, setZoomPan] = useState({ x: 0, y: 0 });
  const arrastandoRef = useRef(false);
  const ultimoPontoRef = useRef({ x: 0, y: 0 });

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

  const abrirZoom = (foto: PacienteFotoItem) => {
    setZoomFoto(foto);
    setZoomScale(1);
    setZoomPan({ x: 0, y: 0 });
  };

  const fecharZoom = () => {
    setZoomFoto(null);
    setZoomScale(1);
    setZoomPan({ x: 0, y: 0 });
  };

  const ajustarZoom = (delta: number) => {
    setZoomScale((s) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, +(s + delta).toFixed(2))));
    if (zoomScale + delta <= 1) setZoomPan({ x: 0, y: 0 });
  };

  const navegarZoom = (dir: -1 | 1) => {
    if (!zoomFoto) return;
    const idx = fotos.findIndex((f) => f.id === zoomFoto.id);
    if (idx < 0) return;
    const next = fotos[idx + dir];
    if (next) abrirZoom(next);
  };

  useEffect(() => {
    if (!zoomFoto) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        fecharZoom();
        return;
      }
      const idx = fotos.findIndex((f) => f.id === zoomFoto.id);
      if (e.key === "ArrowLeft" && idx > 0) abrirZoom(fotos[idx - 1]);
      if (e.key === "ArrowRight" && idx >= 0 && idx < fotos.length - 1) abrirZoom(fotos[idx + 1]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [zoomFoto, fotos]);

  const onZoomWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    ajustarZoom(e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP);
  };

  const iniciarArraste = (clientX: number, clientY: number) => {
    if (zoomScale <= 1) return;
    arrastandoRef.current = true;
    ultimoPontoRef.current = { x: clientX, y: clientY };
  };

  const moverArraste = (clientX: number, clientY: number) => {
    if (!arrastandoRef.current || zoomScale <= 1) return;
    const dx = clientX - ultimoPontoRef.current.x;
    const dy = clientY - ultimoPontoRef.current.y;
    ultimoPontoRef.current = { x: clientX, y: clientY };
    setZoomPan((p) => ({ x: p.x + dx, y: p.y + dy }));
  };

  const pararArraste = () => {
    arrastandoRef.current = false;
  };

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
        {selecionadas.length === MAX_COMPARAR && (
          <button
            type="button"
            onClick={() => setComparar(true)}
            className="inline-flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium bg-gray-900 text-white dark:bg-white dark:text-gray-900"
          >
            <Columns2 size={14} />
            <span className="hidden sm:inline">Comparar 3 fotos</span>
            <span className="sm:hidden">Comparar</span>
          </button>
        )}
      </div>,
    );
    return () => onToolbarChange(null);
  }, [onToolbarChange, permiteEnviar, qrLoading, selecionadas.length, carregar, abrirQr]);

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {permiteEnviar
          ? "Histórico em todas as consultas. Use o QR no celular ou envie pelo painel. Clique na foto para ampliar; marque até 3 para comparar."
          : "Histórico em todas as consultas. Consulta finalizada — apenas visualização e comparação."}
      </p>

      {!permiteEnviar && (
        <p className="text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
          Esta consulta já foi finalizada. Não é possível enviar ou remover fotos — apenas visualizar e comparar.
        </p>
      )}

      {permiteEnviar && (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-2">
            <Camera size={16} />
            Enviar foto pelo painel
          </p>
          <ImageUpload
            value={uploadUrl}
            onChange={(url) => {
              setUploadUrl(url);
              if (url) void salvarUploadPainel(url);
            }}
            label="Adicionar foto"
            description="A foto ficará no histórico do paciente."
            folder={`lwksistemas/${slug}/clinica-beleza/fotos-paciente`}
            disabled={salvando}
          />
        </div>
      )}

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
                  onClick={() => abrirZoom(f)}
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
        <div
          className="fixed inset-0 z-[55] bg-black/95 flex flex-col"
          role="dialog"
          aria-modal
          aria-label="Visualização ampliada da foto"
        >
          <div className="flex items-center justify-between px-3 py-2 bg-black/80 text-white shrink-0 gap-2">
            <div className="min-w-0 text-xs sm:text-sm truncate">
              {zoomFoto.consulta_data || "—"} · {zoomFoto.origem_display}
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={() => navegarZoom(-1)}
                disabled={fotos.findIndex((f) => f.id === zoomFoto.id) <= 0}
                className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
                title="Foto anterior"
              >
                <ChevronLeft size={20} />
              </button>
              <button
                type="button"
                onClick={() => ajustarZoom(-ZOOM_STEP)}
                disabled={zoomScale <= ZOOM_MIN}
                className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
                title="Diminuir zoom"
              >
                <ZoomOut size={20} />
              </button>
              <span className="text-xs w-12 text-center tabular-nums">{Math.round(zoomScale * 100)}%</span>
              <button
                type="button"
                onClick={() => ajustarZoom(ZOOM_STEP)}
                disabled={zoomScale >= ZOOM_MAX}
                className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
                title="Aumentar zoom"
              >
                <ZoomIn size={20} />
              </button>
              <button
                type="button"
                onClick={() => navegarZoom(1)}
                disabled={fotos.findIndex((f) => f.id === zoomFoto.id) >= fotos.length - 1}
                className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-30"
                title="Próxima foto"
              >
                <ChevronRight size={20} />
              </button>
              <button
                type="button"
                onClick={fecharZoom}
                className="p-2 rounded-lg hover:bg-white/10 ml-1"
                title="Fechar"
              >
                <X size={22} />
              </button>
            </div>
          </div>
          <div
            className="flex-1 overflow-hidden flex items-center justify-center touch-none select-none"
            onWheel={onZoomWheel}
            onMouseDown={(e) => iniciarArraste(e.clientX, e.clientY)}
            onMouseMove={(e) => moverArraste(e.clientX, e.clientY)}
            onMouseUp={pararArraste}
            onMouseLeave={pararArraste}
            onTouchStart={(e) => {
              const t = e.touches[0];
              if (t) iniciarArraste(t.clientX, t.clientY);
            }}
            onTouchMove={(e) => {
              const t = e.touches[0];
              if (t) moverArraste(t.clientX, t.clientY);
            }}
            onTouchEnd={pararArraste}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={zoomFoto.cloudinary_url}
              alt={`Foto ampliada ${zoomFoto.consulta_data}`}
              className="max-w-none transition-transform duration-100"
              style={{
                transform: `translate(${zoomPan.x}px, ${zoomPan.y}px) scale(${zoomScale})`,
                maxHeight: zoomScale === 1 ? "90vh" : "none",
                maxWidth: zoomScale === 1 ? "100%" : "none",
                cursor: zoomScale > 1 ? "grab" : "zoom-in",
              }}
              draggable={false}
              onDoubleClick={() => {
                if (zoomScale < ZOOM_MAX) ajustarZoom(ZOOM_STEP);
              }}
            />
          </div>
          <p className="text-[10px] text-white/50 text-center py-2 shrink-0">
            Scroll ou botões para zoom · arraste para mover · duplo clique para ampliar · Esc para fechar
          </p>
        </div>
      )}

      {comparar && fotosComparar.length === MAX_COMPARAR && (
        <div
          className="fixed inset-0 z-[60] bg-black flex flex-col"
          role="dialog"
          aria-modal
        >
          <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white shrink-0">
            <span className="text-sm font-medium">Comparação de 3 fotos — tela cheia</span>
            <button
              type="button"
              onClick={() => setComparar(false)}
              className="p-2 rounded-lg hover:bg-white/10"
            >
              <X size={22} />
            </button>
          </div>
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-0 min-h-0">
            {fotosComparar.map((f, i) => (
              <div key={f.id} className="relative flex flex-col min-h-0 border-t md:border-t-0 md:border-l border-white/10">
                <p className="text-xs text-white/70 px-3 py-2 shrink-0 bg-black/40">
                  Foto {i + 1} — {f.consulta_data} ({f.origem_display})
                </p>
                <div className="flex-1 flex items-center justify-center p-2 min-h-0">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={f.cloudinary_url}
                    alt={`Comparação ${i + 1}`}
                    className="max-w-full max-h-full object-contain"
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
