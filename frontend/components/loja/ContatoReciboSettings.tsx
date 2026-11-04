"use client";

import { useCallback, useEffect, useState } from "react";
import { Phone, Mail, Save } from "lucide-react";
import apiClient from "@/lib/api-client";
import { formatTelefone, telefoneInternacionalBr } from "@/lib/format-br";
import { useToast } from "@/components/ui/Toast";
import { ImageUploadMedia } from "@/components/ImageUploadMedia";

type ContatoReciboInfo = {
  telefone_contato?: string;
  email_contato?: string;
  telefone?: string;
  email?: string;
  owner_telefone?: string;
  owner_email?: string;
  recibo_logo?: string;
  recibo_cor?: string;
  cor_primaria?: string;
};

type ContatoReciboSettingsProps = {
  /** Prefixo da API da clínica. */
  apiPrefix: "/clinica-beleza";
  accentColor?: string;
  entidadeLabel?: string;
};

export function ContatoReciboSettings({
  apiPrefix,
  accentColor = "#8B3D52",
  entidadeLabel = "clínica",
}: ContatoReciboSettingsProps) {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [telefone, setTelefone] = useState("");
  const [email, setEmail] = useState("");
  const [fallbackTel, setFallbackTel] = useState("");
  const [fallbackEmail, setFallbackEmail] = useState("");
  const [logo, setLogo] = useState("");
  const [cor, setCor] = useState(accentColor);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<ContatoReciboInfo>(`${apiPrefix}/loja-info/`);
      setTelefone(formatTelefone(data.telefone_contato || ""));
      setEmail((data.email_contato || "").trim());
      setFallbackTel(formatTelefone(data.owner_telefone || ""));
      setFallbackEmail((data.owner_email || "").trim());
      setLogo((data.recibo_logo || "").trim());
      setCor((data.recibo_cor || data.cor_primaria || accentColor).trim() || accentColor);
    } catch {
      toast.error("Não foi possível carregar o contato da loja.");
    } finally {
      setLoading(false);
    }
    // toast é estável o suficiente; evita re-fetch em loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiPrefix]);

  useEffect(() => {
    void load();
  }, [load]);

  const salvar = async () => {
    setSaving(true);
    try {
      await apiClient.patch(`${apiPrefix}/loja-info/`, {
        telefone_contato: telefone.trim() ? telefoneInternacionalBr(telefone) : "",
        email_contato: email.trim(),
        recibo_logo: logo.trim(),
        recibo_cor: cor.trim(),
      });
      toast.success("Recibo atualizado.");
      await load();
    } catch {
      toast.error("Erro ao salvar contato do recibo.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 p-8 text-center text-gray-500">
        Carregando...
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 p-5 sm:p-6 space-y-5 max-w-xl">
      <div>
        <h2 className="text-base font-semibold text-gray-900 dark:text-white">
          Contato no recibo
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Telefone, e-mail, cor e logomarca do recibo impresso ou enviado ao paciente.
          A logo da tela de login não entra mais no recibo. Se o telefone ou o e-mail
          ficarem em branco, o sistema usa os dados do administrador da {entidadeLabel}.
        </p>
      </div>

      <div className="space-y-2">
        <ImageUploadMedia
          label="Logomarca do recibo"
          description="Aparece no topo do recibo. Trocar a logo da tela de login não altera este arquivo."
          value={logo}
          onChange={setLogo}
          maxSize={2}
          folder="fotos"
        />
        {logo ? (
          <button
            type="button"
            onClick={() => setLogo("")}
            className="text-sm text-gray-600 underline dark:text-gray-300"
          >
            Remover logomarca do recibo
          </button>
        ) : null}
      </div>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Cor do recibo
        </span>
        <span className="flex items-center gap-3">
          <input
            type="color"
            value={/^#[0-9A-Fa-f]{6}$/.test(cor) ? cor : accentColor}
            onChange={(e) => setCor(e.target.value.toUpperCase())}
            aria-label="Cor do recibo"
            className="h-10 w-14 cursor-pointer rounded border border-gray-300 bg-white"
          />
          <input
            value={cor}
            onChange={(e) => setCor(e.target.value)}
            className="w-32 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2.5 text-sm"
          />
          <span className="h-8 flex-1 rounded-lg" style={{ backgroundColor: /^#[0-9A-Fa-f]{6}$/.test(cor) ? cor : accentColor }} />
        </span>
      </label>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Phone size={16} />
          Telefone da {entidadeLabel}
        </span>
        <input
          type="tel"
          inputMode="tel"
          value={telefone}
          onChange={(e) => setTelefone(formatTelefone(e.target.value))}
          placeholder={fallbackTel || "(00) 00000-0000"}
          className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2.5 text-sm text-gray-900 dark:text-gray-100"
        />
      </label>

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Mail size={16} />
          E-mail da {entidadeLabel}
        </span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={fallbackEmail || `contato@sua${entidadeLabel}.com.br`}
          className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-3 py-2.5 text-sm text-gray-900 dark:text-gray-100"
        />
      </label>

      {(fallbackTel || fallbackEmail) && !telefone && !email ? (
        <p className="text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
          Hoje o recibo ainda usa o contato do administrador
          {fallbackTel ? ` (${fallbackTel})` : ""}
          {fallbackEmail ? ` · ${fallbackEmail}` : ""}. Preencha os campos acima para trocar.
        </p>
      ) : null}

      <button
        type="button"
        onClick={() => void salvar()}
        disabled={saving}
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-white disabled:opacity-50"
        style={{ backgroundColor: accentColor }}
      >
        <Save size={16} />
        {saving ? "Salvando..." : "Salvar"}
      </button>
    </div>
  );
}
