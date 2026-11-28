"use client";

import { useMemo, useState } from "react";
import { Copy, ExternalLink, MessageCircle, QrCode } from "lucide-react";
import { useToast } from "@/components/ui/Toast";
import type { AgendamentoOnlineConfig } from "@/lib/clinica-beleza-api/agendamento-online";
import {
  Field,
  SaveBar,
  SectionCard,
  SecondaryButton,
  TextArea,
  TextInput,
  useConfigDraft,
} from "./ui";

const CAMPOS = [
  "nome_publico",
  "texto_apresentacao",
  "logo_url",
  "banner_url",
  "cor_primaria",
  "cor_secundaria",
  "endereco_publico",
  "telefone_publico",
  "politica_privacidade",
] as const;

function ColorInput({
  label,
  value,
  onChange,
  fallback,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  fallback: string;
}) {
  const valido = /^#[0-9a-fA-F]{6}$/.test(value);
  return (
    <Field label={label}>
      <div className="flex items-center gap-2">
        <input
          type="color"
          aria-label={label}
          value={valido ? value : fallback}
          onChange={(e) => onChange(e.target.value)}
          className="h-10 w-12 cursor-pointer rounded-lg border border-[#e8d9dc] bg-white p-1"
        />
        <input
          value={value}
          placeholder={fallback}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-xl border border-[#e8d9dc] bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
        />
      </div>
    </Field>
  );
}

export function TabPagina({
  cfg,
  slug,
  primary,
  onSaved,
}: {
  cfg: AgendamentoOnlineConfig;
  slug: string;
  primary: string;
  onSaved: (c: AgendamentoOnlineConfig) => void;
}) {
  const toast = useToast();
  const { draft, set, save, saving, dirty } = useConfigDraft(cfg, CAMPOS, onSaved);
  const [mostrarQr, setMostrarQr] = useState(false);

  const linkCompleto = useMemo(() => {
    const path = cfg.link_publico || `/loja/${slug}/agendamento-online`;
    if (typeof window === "undefined") return path;
    return `${window.location.origin}${path}`;
  }, [cfg.link_publico, slug]);

  const nomeClinica = draft.nome_publico || "nossa clínica";
  const mensagemWa = `Agende seu horário online em ${nomeClinica}: ${linkCompleto}`;

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(linkCompleto);
      toast.success("Link copiado.");
    } catch {
      toast.error("Não foi possível copiar. Selecione o link manualmente.");
    }
  };

  return (
    <div className="space-y-4">
      <SectionCard title="Link da página pública" description="Compartilhe com seus clientes em redes sociais, bio e WhatsApp.">
        <div className="rounded-2xl border border-pink-200 bg-pink-50 px-3 py-2.5 text-sm break-all text-gray-900 dark:bg-pink-950/20 dark:text-gray-100">
          {linkCompleto}
        </div>
        {!cfg.ativo ? (
          <p className="text-xs text-amber-700">
            O agendamento online está desativado. Ative na aba Geral para a página aceitar pedidos.
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          <SecondaryButton href={linkCompleto} target="_blank">
            <ExternalLink className="h-4 w-4" /> Visualizar
          </SecondaryButton>
          <SecondaryButton onClick={copiar}>
            <Copy className="h-4 w-4" /> Copiar link
          </SecondaryButton>
          <SecondaryButton href={`https://wa.me/?text=${encodeURIComponent(mensagemWa)}`} target="_blank">
            <MessageCircle className="h-4 w-4" /> Compartilhar no WhatsApp
          </SecondaryButton>
          <SecondaryButton onClick={() => setMostrarQr((v) => !v)}>
            <QrCode className="h-4 w-4" /> {mostrarQr ? "Ocultar QR Code" : "QR Code"}
          </SecondaryButton>
        </div>
        {mostrarQr ? (
          <div className="flex flex-col items-start gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(linkCompleto)}`}
              alt="QR Code do link de agendamento online"
              width={200}
              height={200}
              className="rounded-2xl border border-[#f0e4e6] bg-white p-2"
            />
            <a
              href={`https://api.qrserver.com/v1/create-qr-code/?size=600x600&format=png&data=${encodeURIComponent(linkCompleto)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs underline"
              style={{ color: primary }}
            >
              Abrir em tamanho grande
            </a>
          </div>
        ) : null}
      </SectionCard>

      <SectionCard title="Identidade da página" description="Deixe em branco para usar os dados da clínica.">
        <div className="grid gap-4 sm:grid-cols-2">
          <TextInput label="Nome exibido" value={draft.nome_publico} onChange={(v) => set("nome_publico", v)} />
          <TextInput
            label="Telefone / WhatsApp público"
            value={draft.telefone_publico}
            onChange={(v) => set("telefone_publico", v)}
          />
          <TextInput label="URL do logo" value={draft.logo_url} onChange={(v) => set("logo_url", v)} placeholder="https://" />
          <TextInput label="URL do banner" value={draft.banner_url} onChange={(v) => set("banner_url", v)} placeholder="https://" />
          <ColorInput label="Cor primária" value={draft.cor_primaria} onChange={(v) => set("cor_primaria", v)} fallback="#ec4899" />
          <ColorInput label="Cor secundária" value={draft.cor_secundaria} onChange={(v) => set("cor_secundaria", v)} fallback="#db2777" />
        </div>
        <TextInput label="Endereço" value={draft.endereco_publico} onChange={(v) => set("endereco_publico", v)} />
        <TextArea
          label="Texto de apresentação"
          value={draft.texto_apresentacao}
          onChange={(v) => set("texto_apresentacao", v)}
        />
        <TextArea
          label="Política de privacidade"
          hint="Exibida no formulário de dados pessoais."
          rows={4}
          value={draft.politica_privacidade}
          onChange={(v) => set("politica_privacidade", v)}
        />
      </SectionCard>

      <SaveBar dirty={dirty} saving={saving} onSave={save} primary={primary} />
    </div>
  );
}
