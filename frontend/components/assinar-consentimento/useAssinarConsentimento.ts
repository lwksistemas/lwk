import { useCallback, useEffect, useRef, useState } from "react";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";
import type { TermoConsentimentoData } from "./assinar-consentimento-types";
import {
  buildAssinaturaConsentimentoUrls,
  decodeAssinaturaToken,
  podeAssinarTermo,
} from "./assinar-consentimento-utils";

export function useAssinarConsentimento(tokenRaw: string) {
  const token = decodeAssinaturaToken(tokenRaw);
  const tokenApiSegment = encodeURIComponent(token);
  const urls = buildAssinaturaConsentimentoUrls(tokenApiSegment);

  const [loading, setLoading] = useState(true);
  const [termo, setTermo] = useState<TermoConsentimentoData | null>(null);
  const [erro, setErro] = useState("");
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [proximoStatus, setProximoStatus] = useState("");
  const [baixandoPdf, setBaixandoPdf] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfInlineLoading, setPdfInlineLoading] = useState(false);
  const [pdfInlineError, setPdfInlineError] = useState(false);
  const [pdfInteracaoFeita, setPdfInteracaoFeita] = useState(false);
  const [declarouLeituraCompleta, setDeclarouLeituraCompleta] = useState(false);
  const [pdfReloadKey, setPdfReloadKey] = useState(0);
  const pdfBlobUrlRef = useRef<string | null>(null);

  const pdfPronto = Boolean(pdfBlobUrl) && !pdfInlineLoading && !pdfInlineError;
  const podeAssinar = podeAssinarTermo(pdfPronto, pdfInteracaoFeita, declarouLeituraCompleta);

  useEffect(() => {
    pdfBlobUrlRef.current = pdfBlobUrl;
  }, [pdfBlobUrl]);

  useEffect(() => {
    return () => {
      if (pdfBlobUrlRef.current) {
        URL.revokeObjectURL(pdfBlobUrlRef.current);
        pdfBlobUrlRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}${urls.termo}`);
        const data = await res.json();
        if (!res.ok) {
          setErro(data.error || "Erro ao carregar termo");
          return;
        }
        setTermo(data);
      } catch {
        setErro("Erro ao carregar. Verifique sua conexão.");
      } finally {
        setLoading(false);
      }
    })();
  }, [urls.termo]);

  useEffect(() => {
    if (!termo) return;
    let cancelled = false;
    (async () => {
      setPdfBlobUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setPdfInlineLoading(true);
      setPdfInlineError(false);
      setPdfInteracaoFeita(false);
      setDeclarouLeituraCompleta(false);
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}${urls.pdf}`);
        if (!res.ok) {
          if (!cancelled) setPdfInlineError(true);
          return;
        }
        const blob = await res.blob();
        if (cancelled) return;
        const blobUrl = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(blobUrl);
          return;
        }
        setPdfBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return blobUrl;
        });
      } catch {
        if (!cancelled) setPdfInlineError(true);
      } finally {
        if (!cancelled) setPdfInlineLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [termo, urls.pdf, pdfReloadKey]);

  useEffect(() => {
    if (sucesso) {
      const t = setTimeout(() => window.close(), 3000);
      return () => clearTimeout(t);
    }
  }, [sucesso]);

  const assinar = useCallback(async () => {
    if (!podeAssinar) return;
    setAssinando(true);
    setErro("");
    try {
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}${urls.termo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.error || "Erro ao assinar");
        return;
      }
      setSucesso(true);
      setProximoStatus(data.proximo_status_display || data.proximo_status);
    } catch {
      setErro("Erro ao assinar. Tente novamente.");
    } finally {
      setAssinando(false);
    }
  }, [podeAssinar, urls.termo]);

  const fetchPdfBlob = useCallback(async (): Promise<Blob | null> => {
    const url = getPrimaryApiBaseUrl();
    const res = await fetch(`${url}${urls.pdf}`);
    if (!res.ok) return null;
    return res.blob();
  }, [urls.pdf]);

  const visualizarPdf = useCallback(async () => {
    if (pdfBlobUrl) {
      window.open(pdfBlobUrl, "_blank", "noopener,noreferrer");
      setPdfInteracaoFeita(true);
      return;
    }
    setBaixandoPdf(true);
    try {
      const blob = await fetchPdfBlob();
      if (!blob) {
        setErro("Erro ao carregar PDF.");
        return;
      }
      const blobUrl = window.URL.createObjectURL(blob);
      window.open(blobUrl, "_blank", "noopener,noreferrer");
      setPdfInteracaoFeita(true);
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60_000);
    } catch {
      setErro("Erro ao carregar PDF.");
    } finally {
      setBaixandoPdf(false);
    }
  }, [fetchPdfBlob, pdfBlobUrl]);

  const baixarPdf = useCallback(async () => {
    setBaixandoPdf(true);
    setErro("");
    try {
      if (pdfBlobUrl) {
        const a = document.createElement("a");
        a.href = pdfBlobUrl;
        a.download = "termo_consentimento.pdf";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setPdfInteracaoFeita(true);
        return;
      }
      const blob = await fetchPdfBlob();
      if (!blob) {
        setErro("Erro ao baixar PDF.");
        return;
      }
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = "termo_consentimento.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
      setPdfInteracaoFeita(true);
    } catch {
      setErro("Erro ao baixar PDF.");
    } finally {
      setBaixandoPdf(false);
    }
  }, [fetchPdfBlob, pdfBlobUrl]);

  return {
    loading,
    termo,
    erro,
    assinando,
    sucesso,
    proximoStatus,
    baixandoPdf,
    pdfBlobUrl,
    pdfInlineLoading,
    pdfInlineError,
    pdfInteracaoFeita,
    declarouLeituraCompleta,
    setDeclarouLeituraCompleta,
    pdfReloadKey,
    setPdfReloadKey,
    pdfPronto,
    podeAssinar,
    assinar,
    visualizarPdf,
    baixarPdf,
  };
}
