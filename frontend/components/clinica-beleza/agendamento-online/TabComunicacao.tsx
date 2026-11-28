"use client";

import type { AgendamentoOnlineConfig } from "@/lib/clinica-beleza-api/agendamento-online";
import { SaveBar, SectionCard, TextInput, ToggleRow, useConfigDraft } from "./ui";

const CAMPOS = [
  "enviar_confirmacao",
  "enviar_lembrete",
  "enviar_cancelamento",
  "enviar_reagendamento",
  "notificar_secretaria",
  "botao_whatsapp_ativo",
  "whatsapp_secretaria",
] as const;

export function TabComunicacao({
  cfg,
  primary,
  onSaved,
}: {
  cfg: AgendamentoOnlineConfig;
  primary: string;
  onSaved: (c: AgendamentoOnlineConfig) => void;
}) {
  const { draft, set, save, saving, dirty } = useConfigDraft(cfg, CAMPOS, onSaved);

  return (
    <div className="space-y-4">
      <SectionCard
        title="Mensagens ao cliente"
        description="Enviadas por WhatsApp quando a integração da clínica está configurada."
      >
        <ToggleRow
          label="Enviar confirmação de agendamento"
          checked={draft.enviar_confirmacao}
          onChange={(v) => set("enviar_confirmacao", v)}
          primary={primary}
        />
        <ToggleRow
          label="Enviar lembrete"
          checked={draft.enviar_lembrete}
          onChange={(v) => set("enviar_lembrete", v)}
          primary={primary}
        />
        <ToggleRow
          label="Enviar aviso de cancelamento"
          checked={draft.enviar_cancelamento}
          onChange={(v) => set("enviar_cancelamento", v)}
          primary={primary}
        />
        <ToggleRow
          label="Enviar aviso de reagendamento"
          checked={draft.enviar_reagendamento}
          onChange={(v) => set("enviar_reagendamento", v)}
          primary={primary}
        />
      </SectionCard>

      <SectionCard title="Equipe e atendimento">
        <ToggleRow
          label="Notificar a secretaria a cada novo agendamento"
          checked={draft.notificar_secretaria}
          onChange={(v) => set("notificar_secretaria", v)}
          primary={primary}
        />
        <ToggleRow
          label="Mostrar botão flutuante de WhatsApp na página pública"
          checked={draft.botao_whatsapp_ativo}
          onChange={(v) => set("botao_whatsapp_ativo", v)}
          primary={primary}
        />
        <div className="max-w-sm">
          <TextInput
            label="WhatsApp da secretaria"
            hint="Opcional. Vazio = telefone da clínica. Use DDD, ex.: 11999998888."
            value={draft.whatsapp_secretaria}
            onChange={(v) => set("whatsapp_secretaria", v)}
            placeholder="11999998888"
          />
        </div>
      </SectionCard>

      <SaveBar dirty={dirty} saving={saving} onSave={save} primary={primary} />
    </div>
  );
}
