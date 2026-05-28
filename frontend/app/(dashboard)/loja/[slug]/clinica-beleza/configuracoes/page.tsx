"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Settings, MessageCircle, Save } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";

interface WhatsAppConfig {
  enviar_confirmacao: boolean;
  enviar_lembrete_24h: boolean;
  enviar_lembrete_2h: boolean;
  enviar_cobranca: boolean;
  whatsapp_numero: string;
  whatsapp_ativo: boolean;
  whatsapp_phone_id: string;
  whatsapp_token_set: boolean;
}

export default function ConfiguracoesClinicaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [config, setConfig] = useState<WhatsAppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const res = await clinicaBelezaFetch("/whatsapp-config/");
      if (res.ok) setConfig(await res.json());
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const saveConfig = async () => {
    if (!config) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await clinicaBelezaFetch("/whatsapp-config/", {
        method: "PATCH",
        body: JSON.stringify(config),
      });
      if (res.ok) {
        setMessage({ type: "ok", text: "Configurações salvas!" });
        setConfig(await res.json());
      } else {
        setMessage({ type: "err", text: "Erro ao salvar." });
      }
    } catch {
      setMessage({ type: "err", text: "Erro de conexão." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-white dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 p-4 md:p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => router.push(`/loja/${slug}/dashboard`)} className="p-2 hover:bg-white/80 dark:hover:bg-neutral-700 rounded-lg">
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Settings size={24} /> Configurações
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">WhatsApp e notificações</p>
          </div>
        </div>

        {message && (
          <div className={`mb-4 p-3 rounded-lg text-sm ${message.type === "ok" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
            {message.text}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : config ? (
          <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-md p-6 space-y-6">
            <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 mb-4">
              <MessageCircle size={20} />
              <h2 className="text-lg font-semibold">WhatsApp</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número WhatsApp</label>
                <input
                  type="text"
                  value={config.whatsapp_numero}
                  onChange={(e) => setConfig({ ...config, whatsapp_numero: e.target.value })}
                  placeholder="5516999999999"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                />
              </div>

              <div className="space-y-3">
                {[
                  { key: "enviar_confirmacao", label: "Enviar confirmação de agendamento" },
                  { key: "enviar_lembrete_24h", label: "Lembrete 24h antes" },
                  { key: "enviar_lembrete_2h", label: "Lembrete 2h antes" },
                  { key: "enviar_cobranca", label: "Enviar cobrança" },
                ].map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(config as any)[key]}
                      onChange={(e) => setConfig({ ...config, [key]: e.target.checked })}
                      className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={saveConfig}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium"
            >
              <Save size={18} />
              {saving ? "Salvando..." : "Salvar configurações"}
            </button>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Não foi possível carregar as configurações.</p>
        )}
      </div>
    </div>
  );
}
