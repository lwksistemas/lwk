import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI, type PacienteFotoItem } from "@/lib/clinica-beleza-api";
import { useToast } from "@/components/ui/Toast";
import { MAX_FOTOS_COMPARAR } from "./fotos-constants";

export function useConsultaFotos(consultaId: number, ativa?: boolean) {
  const toast = useToast();
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
      toast.error(e instanceof Error ? e.message : "Erro ao gerar QR.");
    } finally {
      setQrLoading(false);
    }
  }, [consultaId, toast]);

  const salvarUploadPainel = async (url: string) => {
    if (!url) return;
    setSalvando(true);
    try {
      await ClinicaBelezaAPI.consultas.fotos.salvar(consultaId, url);
      setUploadUrl("");
      await carregar();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao salvar foto.");
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
      toast.error(e instanceof Error ? e.message : "Erro ao remover.");
    }
  };

  const toggleSelecao = (id: number) => {
    setSelecionadas((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_FOTOS_COMPARAR) return [...prev.slice(1), id];
      return [...prev, id];
    });
  };

  const fotosComparar = fotos.filter((f) => selecionadas.includes(f.id));

  return {
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
  };
}
