import { useCallback, useEffect, useState } from "react";
import { whatsappConfigApi } from "@/lib/whatsapp-config-api";
import { extractMensagemWhatsAppError } from "./mensagens-whatsapp-agenda-utils";

export function useMensagensWhatsAppAgenda(open: boolean, onClose: () => void) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [mensagem, setMensagem] = useState("");
  const [error, setError] = useState("");

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await whatsappConfigApi.get();
      setMensagem((data.mensagem_confirmacao_agenda ?? "").toString());
    } catch {
      setError("Erro ao carregar mensagem.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) void loadConfig();
  }, [open, loadConfig]);

  const usarPadraoSistema = () => setMensagem("");

  const salvar = async () => {
    setSaving(true);
    setError("");
    try {
      await whatsappConfigApi.save({ mensagem_confirmacao_agenda: mensagem.trim() });
      onClose();
    } catch (err) {
      setError(extractMensagemWhatsAppError(err, "Erro ao salvar mensagem."));
    } finally {
      setSaving(false);
    }
  };

  return {
    loading,
    saving,
    mensagem,
    error,
    setMensagem,
    usarPadraoSistema,
    salvar,
  };
}
