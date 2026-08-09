"use client";

import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI, type PacienteFotoItem } from "@/lib/clinica-beleza-api";
import { useToast } from "@/components/ui/Toast";
import { MAX_FOTOS_POR_CONSULTA } from "../fotos/fotos-constants";

const MIN_COMPARAR = 2;
const MAX_COMPARAR = 3;

export function useConsultaFotosTab(
  consultaId: number,
  permiteEnviar: boolean | undefined,
  ativa: boolean | undefined,
) {
  const toast = useToast();

  const [fotos, setFotos] = useState<PacienteFotoItem[]>([]);
  const [fotosConsultaCount, setFotosConsultaCount] = useState(0);
  const [permiteUploadPlano, setPermiteUploadPlano] = useState(true);
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
      const lista = res.fotos || [];
      setFotos(lista);
      if (typeof res.permite_upload_fotos === "boolean") {
        setPermiteUploadPlano(res.permite_upload_fotos);
      }
      const countApi = res.fotos_consulta_count;
      if (typeof countApi === "number") {
        setFotosConsultaCount(countApi);
      } else {
        setFotosConsultaCount(lista.filter((f) => f.consulta_id === consultaId).length);
      }
    } catch (e: unknown) {
      setFotos([]);
      setFotosConsultaCount(0);
      toast.error(e instanceof Error ? e.message : "Erro ao carregar fotos.");
    } finally {
      setLoading(false);
    }
  }, [consultaId, toast]);

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

  const limiteAtingido = fotosConsultaCount >= MAX_FOTOS_POR_CONSULTA;
  const podeEnviarMais = Boolean(permiteEnviar) && permiteUploadPlano && !limiteAtingido;

  const abrirQr = useCallback(async () => {
    if (limiteAtingido) {
      toast.error(`Máximo de ${MAX_FOTOS_POR_CONSULTA} fotos por consulta.`);
      return;
    }
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
  }, [consultaId, limiteAtingido, toast]);

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

  const salvarArquivo = async (file: File) => {
    setSalvando(true);
    try {
      await ClinicaBelezaAPI.consultas.fotos.salvarArquivo(consultaId, file);
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
      if (prev.length >= MAX_COMPARAR) return [...prev.slice(1), id];
      return [...prev, id];
    });
  };

  const fotosComparar = fotos.filter((f) => selecionadas.includes(f.id));
  const podeComparar = selecionadas.length >= MIN_COMPARAR;

  return {
    fotos,
    setFotos,
    fotosConsultaCount,
    permiteUploadPlano,
    loading,
    qrAberto,
    setQrAberto,
    qrData,
    qrLoading,
    selecionadas,
    setSelecionadas,
    comparar,
    setComparar,
    uploadUrl,
    setUploadUrl,
    salvando,
    setSalvando,
    zoomFoto,
    setZoomFoto,
    carregar,
    limiteAtingido,
    podeEnviarMais,
    abrirQr,
    salvarUploadPainel,
    salvarArquivo,
    excluir,
    toggleSelecao,
    fotosComparar,
    podeComparar,
  };
}
