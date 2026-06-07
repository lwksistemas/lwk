"use client";

import { useCallback, useEffect, useState } from "react";
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
} from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type PacienteFotoItem } from "@/lib/clinica-beleza-api";

export function ConsultaFotosTab({
  consultaId,
  patientNome,
  permiteEnviar,
  ativa,
}: {
  consultaId: number;
  patientNome: string;
  /** Só true com consulta em andamento — envio pelo painel ou QR */
  permiteEnviar?: boolean;
  ativa?: boolean;
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

  const abrirQr = async () => {
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
  };

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
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  const fotosComparar = fotos.filter((f) => selecionadas.includes(f.id));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Fotos de acompanhamento
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Histórico de <strong>{patientNome}</strong> em todas as consultas.
            {permiteEnviar
              ? " Durante o atendimento, use o QR no seu celular ou envie pelo painel. "
              : " Consulta finalizada — apenas visualização e comparação. "}
            Selecione 2 fotos para comparar em tela cheia.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void carregar()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border border-gray-300 dark:border-neutral-600"
          >
            <RefreshCw size={16} />
            Atualizar
          </button>
          {permiteEnviar && (
            <button
              type="button"
              onClick={() => void abrirQr()}
              disabled={qrLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Smartphone size={16} />
              {qrLoading ? "Gerando…" : "QR — foto no meu celular"}
            </button>
          )}
          {selecionadas.length === 2 && (
            <button
              type="button"
              onClick={() => setComparar(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-900 text-white dark:bg-white dark:text-gray-900"
            >
              <Columns2 size={16} />
              Comparar 2 fotos
            </button>
          )}
        </div>
      </div>

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
                  onClick={() => toggleSelecao(f.id)}
                  className="block w-full aspect-square"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={f.cloudinary_url}
                    alt={`Foto ${f.consulta_data}`}
                    className="w-full h-full object-cover"
                  />
                  {sel && (
                    <span className="absolute top-2 left-2 bg-purple-600 text-white rounded-full p-1">
                      <Check size={14} />
                    </span>
                  )}
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

      {comparar && fotosComparar.length === 2 && (
        <div
          className="fixed inset-0 z-[60] bg-black flex flex-col"
          role="dialog"
          aria-modal
        >
          <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white shrink-0">
            <span className="text-sm font-medium">Comparação — tela cheia</span>
            <button
              type="button"
              onClick={() => setComparar(false)}
              className="p-2 rounded-lg hover:bg-white/10"
            >
              <X size={22} />
            </button>
          </div>
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-0 min-h-0">
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
