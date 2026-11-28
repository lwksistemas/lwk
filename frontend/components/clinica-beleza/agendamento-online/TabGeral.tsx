"use client";

import type { AgendamentoOnlineConfig } from "@/lib/clinica-beleza-api/agendamento-online";
import {
  NumberInput,
  SaveBar,
  SectionCard,
  SelectInput,
  ToggleRow,
  useConfigDraft,
} from "./ui";

const CAMPOS = [
  "ativo",
  "antecedencia_minima_horas",
  "dias_futuros",
  "permitir_mesmo_dia",
  "intervalo_slots_minutos",
  "modo_confirmacao",
  "permitir_cancelamento_cliente",
  "permitir_reagendamento_cliente",
  "prazo_cancelamento_horas",
  "reserva_pendente_minutos",
] as const;

export function TabGeral({
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
        title="Agendamento online"
        description="Quando ativo, os clientes podem agendar pela página pública da clínica."
      >
        <ToggleRow
          label="Ativar agendamento online"
          hint={draft.ativo ? "A página pública está disponível." : "A página pública exibe aviso de indisponibilidade."}
          checked={draft.ativo}
          onChange={(v) => set("ativo", v)}
          primary={primary}
        />
      </SectionCard>

      <SectionCard title="Regras de horário" description="Controle até quando e com que antecedência o cliente pode agendar.">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <NumberInput
            label="Antecedência mínima (horas)"
            hint="Tempo mínimo entre agora e o início do horário."
            value={draft.antecedencia_minima_horas}
            onChange={(v) => set("antecedencia_minima_horas", v)}
          />
          <NumberInput
            label="Dias futuros no calendário"
            hint="Quantos dias à frente o cliente enxerga."
            value={draft.dias_futuros}
            onChange={(v) => set("dias_futuros", v)}
            min={1}
          />
          <NumberInput
            label="Intervalo entre horários (min)"
            hint="Ex.: 30 = horários de meia em meia hora."
            value={draft.intervalo_slots_minutos}
            onChange={(v) => set("intervalo_slots_minutos", v)}
            min={5}
          />
          <NumberInput
            label="Reserva de pedido pendente (min)"
            hint="Quanto tempo um pedido aguardando aprovação segura o horário."
            value={draft.reserva_pendente_minutos}
            onChange={(v) => set("reserva_pendente_minutos", v)}
          />
        </div>
        <ToggleRow
          label="Permitir agendar no mesmo dia"
          checked={draft.permitir_mesmo_dia}
          onChange={(v) => set("permitir_mesmo_dia", v)}
          primary={primary}
        />
      </SectionCard>

      <SectionCard title="Confirmação" description="Defina como os pedidos entram na agenda.">
        <SelectInput
          label="Modo de confirmação"
          value={draft.modo_confirmacao}
          onChange={(v) => set("modo_confirmacao", v as AgendamentoOnlineConfig["modo_confirmacao"])}
          options={[
            { value: "automatico", label: "Confirmação automática" },
            { value: "secretaria", label: "Aprovação pela secretaria" },
          ]}
        />
      </SectionCard>

      <SectionCard title="Cancelamento e reagendamento">
        <ToggleRow
          label="Permitir cancelamento pelo cliente"
          checked={draft.permitir_cancelamento_cliente}
          onChange={(v) => set("permitir_cancelamento_cliente", v)}
          primary={primary}
        />
        <ToggleRow
          label="Permitir reagendamento pelo cliente"
          checked={draft.permitir_reagendamento_cliente}
          onChange={(v) => set("permitir_reagendamento_cliente", v)}
          primary={primary}
        />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <NumberInput
            label="Prazo para cancelar/reagendar (horas)"
            hint="Horas mínimas antes do horário marcado."
            value={draft.prazo_cancelamento_horas}
            onChange={(v) => set("prazo_cancelamento_horas", v)}
          />
        </div>
      </SectionCard>

      <SaveBar dirty={dirty} saving={saving} onSave={save} primary={primary} />
    </div>
  );
}
