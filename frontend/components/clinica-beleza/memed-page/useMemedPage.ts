import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ClinicaBelezaAPI, getClinicaBelezaBaseUrl, getClinicaBelezaHeadersWithLoja } from "@/lib/clinica-beleza-api";
import type { MemedDiagStatus, TimbradoStatus } from "./memed-page-types";
import { buildMemedConfigBasePath, buildTimbradoApplyFeedback } from "./memed-page-utils";

export function useMemedPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = buildMemedConfigBasePath(slug);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<TimbradoStatus>({ tem_timbrado: false });
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");
  const [memedDiag, setMemedDiag] = useState<MemedDiagStatus | null>(null);

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const [timbradoData, statusData] = await Promise.all([
        ClinicaBelezaAPI.memed.timbrado.get(),
        ClinicaBelezaAPI.memed.status().catch(() => null),
      ]);
      setStatus(timbradoData as TimbradoStatus);
      if (statusData) setMemedDiag(statusData);
    } catch {
      setErro("Não foi possível carregar o timbrado.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const enviarPdf = useCallback(
    async (apenasAplicar = false) => {
      setSaving(true);
      setErro("");
      setMsg("");
      try {
        const url = `${getClinicaBelezaBaseUrl()}/memed/timbrado/`;
        const headers = getClinicaBelezaHeadersWithLoja();
        delete (headers as Record<string, string>)["Content-Type"];

        let res: Response;
        if (apenasAplicar) {
          res = await fetch(url, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ aplicar: true }),
          });
        } else {
          if (!arquivo) {
            setErro("Selecione o PDF timbrado A4.");
            setSaving(false);
            return;
          }
          const form = new FormData();
          form.append("pdf", arquivo);
          res = await fetch(url, { method: "POST", headers, body: form });
        }

        const data = await res.json();
        if (!res.ok) {
          setErro(typeof data?.error === "string" ? data.error : "Falha ao enviar timbrado.");
          return;
        }
        const timbrado = data as TimbradoStatus;
        setStatus(timbrado);
        setArquivo(null);
        const feedback = buildTimbradoApplyFeedback(timbrado);
        setMsg(feedback.msg);
        setErro(feedback.erro);
      } catch {
        setErro("Erro de conexão ao enviar timbrado.");
      } finally {
        setSaving(false);
      }
    },
    [arquivo],
  );

  return {
    base,
    loading,
    saving,
    status,
    arquivo,
    setArquivo,
    msg,
    erro,
    memedDiag,
    enviarPdf,
  };
}
