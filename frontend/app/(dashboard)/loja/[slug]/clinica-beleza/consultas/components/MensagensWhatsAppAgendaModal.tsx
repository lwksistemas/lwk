"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, MessageCircle, RotateCcw, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { whatsappConfigApi } from "@/lib/whatsapp-config-api";

interface MensagensWhatsAppAgendaModalProps {
  open: boolean;
  onClose: () => void;
}

const PLACEHOLDERS = ["{nome}", "{data}", "{hora}", "{procedimento}", "{profissional}", "{link}"];

const MENSAGEM_PADRAO = `Olá {nome} 😊

Você tem um agendamento:
📅 {data}
⏰ {hora}
💆 {procedimento}
👤 Profissional: {profissional}

Por favor, confirme ou cancele sua consulta:
🔗 {link}

Qualquer dúvida, fale conosco.`;

function extractApiError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const val of Object.values(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return val[0];
    if (typeof val === "string") return val;
  }
  return fallback;
}

export function MensagensWhatsAppAgendaModal({ open, onClose }: MensagensWhatsAppAgendaModalProps) {
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
    if (open) {
      loadConfig();
    }
  }, [open, loadConfig]);

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      await whatsappConfigApi.save({ mensagem_confirmacao_agenda: mensagem.trim() });
      onClose();
    } catch (err) {
      setError(extractApiError(err, "Erro ao salvar mensagem."));
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div className="flex items-center gap-2">
            <MessageCircle size={18} style={{ color: CLINICA_BELEZA_PRIMARY }} />
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
              Mensagem WhatsApp — confirmação
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Texto enviado ao paciente com o link para confirmar ou cancelar o agendamento. Deixe em branco
            para usar a mensagem padrão do sistema.
          </p>

          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Variáveis disponíveis</p>
            <div className="flex flex-wrap gap-1.5">
              {PLACEHOLDERS.map((ph) => (
                <code
                  key={ph}
                  className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300"
                >
                  {ph}
                </code>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 size={20} className="animate-spin mr-2" />
              Carregando...
            </div>
          ) : (
            <textarea
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              rows={12}
              placeholder={MENSAGEM_PADRAO}
              className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-mono leading-relaxed resize-y min-h-[200px]"
            />
          )}

          {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        </div>

        <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-gray-200 dark:border-neutral-700 shrink-0">
          <button
            type="button"
            onClick={() => setMensagem("")}
            disabled={saving || loading}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <RotateCcw size={14} />
            Usar padrão do sistema
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || loading}
              className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50 inline-flex items-center gap-2"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {saving && <Loader2 size={14} className="animate-spin" />}
              Salvar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
