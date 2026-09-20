import { useCallback, useEffect, useRef, useState } from "react";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";

export interface ReciboAssinaturaData {
  tipo_documento?: string;
  titulo?: string;
  valor?: string;
  nome_assinante?: string;
  paciente_nome?: string;
  profissional_nome?: string;
  clinica_nome?: string;
}

function decodeToken(tokenRaw: string): string {
  try {
    return decodeURIComponent(tokenRaw);
  } catch {
    return tokenRaw;
  }
}

export function useAssinarRecibo(tokenRaw: string) {
  const token = decodeToken(tokenRaw);
  const tokenApiSegment = encodeURIComponent(token);
  const base = `/clinica-beleza/assinar-recibo/${tokenApiSegment}`;
  const urls = { recibo: `${base}/`, pdf: `${base}/pdf/` };

  const [loading, setLoading] = useState(true);
  const [recibo, setRecibo] = useState<ReciboAssinaturaData | null>(null);
  const [erro, setErro] = useState("");
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [baixandoPdf, setBaixandoPdf] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfInlineLoading, setPdfInlineLoading] = useState(false);
  const [pdfInlineError, setPdfInlineError] = useState(false);
  const [pdfInteracaoFeita, setPdfInteracaoFeita] = useState(false);
  const [declarouLeituraCompleta, setDeclarouLeituraCompleta] = useState(false);
  const [pdfReloadKey, setPdfReloadKey] = useState(0);
  const pdfBlobUrlRef = useRef<string | null>(null);

  const pdfPronto = Boolean(pdfBlobUrl) && !pdfInlineLoading && !pdfInlineError;
  const podeAssinar = pdfPronto && pdfInteracaoFeita && declarouLeituraCompleta;

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
        const res = await fetch(`${url}${urls.recibo}`);
        const data = await res.json();
        if (!res.ok) {
          setErro(data.error || "Erro ao carregar recibo");
          return;
        }
        setRecibo(data);
      } catch {
        setErro("Erro ao carregar. Verifique sua conexão.");
      } finally {
        setLoading(false);
      }
    })();
  }, [urls.recibo]);

  useEffect(() => {
    if (!recibo) return;
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
  }, [recibo, urls.pdf, pdfReloadKey]);

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
      const res = await fetch(`${url}${urls.recibo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.error || "Erro ao assinar");
        return;
      }
      setSucesso(true);
    } catch {
      setErro("Erro ao assinar. Tente novamente.");
    } finally {
      setAssinando(false);
    }
  }, [podeAssinar, urls.recibo]);

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
      const alvo = pdfBlobUrl || window.URL.createObjectURL((await fetchPdfBlob()) as Blob);
      if (!alvo) {
        setErro("Erro ao baixar PDF.");
        return;
      }
      const a = document.createElement("a");
      a.href = alvo;
      a.download = "recibo.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      if (!pdfBlobUrl) window.URL.revokeObjectURL(alvo);
      setPdfInteracaoFeita(true);
    } catch {
      setErro("Erro ao baixar PDF.");
    } finally {
      setBaixandoPdf(false);
    }
  }, [fetchPdfBlob, pdfBlobUrl]);

  return {
    loading,
    recibo,
    erro,
    assinando,
    sucesso,
    baixandoPdf,
    pdfBlobUrl,
    pdfInlineLoading,
    pdfInlineError,
    pdfInteracaoFeita,
    declarouLeituraCompleta,
    setDeclarouLeituraCompleta,
    setPdfReloadKey,
    pdfPronto,
    podeAssinar,
    assinar,
    visualizarPdf,
    baixarPdf,
  };
}
