"use client";

import { useEffect, useState } from "react";
import { CalendarClock } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { PrazoPagamentoPolitica } from "@/lib/clinica-beleza-api/client-entities";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";

type Modo = "" | "DIAS_APOS" | "DIA_FIXO";

interface PrazoPagamentoCardProps {
  patientId: number;
  /** Controla a visibilidade do painel (abre/fecha pelo botão da tab bar). */
  open: boolean;
  /** Fecha o painel após salvar com sucesso. */
  onClose: () => void;
}

const fieldClass =
  "w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm";

/**
 * Painel de política de prazo de pagamento do paciente.
 * Visível só quando aberto (pelo botão "Prazo de pagamento" na tab bar).
 * A regra de negócio (só admin) é aplicada no botão que controla este painel.
 */
export function PrazoPagamentoCard({ patientId, open, onClose }: PrazoPagamentoCardProps) {
  const toast = useToast();
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [modo, setModo] = useState<Modo>("");
  const [dias, setDias] = useState("");
  const [diaMes, setDiaMes] = useState("");

  useEffect(() => {
    if (!open) return;
    let ativo = true;
    setCarregando(true);
    ClinicaBelezaAPI.patients.prazoPagamento
      .get(patientId)
      .then((p) => {
        if (!ativo) return;
        setModo((p.prazo_pagamento_modo || "") as Modo);
        setDias(p.prazo_pagamento_dias != null ? String(p.prazo_pagamento_dias) : "");
        setDiaMes(p.prazo_pagamento_dia_mes != null ? String(p.prazo_pagamento_dia_mes) : "");
      })
      .catch(() => {
        /* mantém vazio */
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [open, patientId]);

  if (!open) return null;

  const handleSalvar = async () => {
    const payload: Partial<PrazoPagamentoPolitica> = { prazo_pagamento_modo: modo };
    if (modo === "DIAS_APOS") payload.prazo_pagamento_dias = dias ? Number(dias) : null;
    if (modo === "DIA_FIXO") payload.prazo_pagamento_dia_mes = diaMes ? Number(diaMes) : null;

    setSalvando(true);
    try {
      await ClinicaBelezaAPI.patients.prazoPagamento.save(patientId, payload);
      toast.success("Prazo de pagamento salvo.");
      onClose();
    } catch (e) {
      toast.error(formatApiErrorBody(e) || "Erro ao salvar o prazo de pagamento.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <ClinicaBelezaPanel className="p-4 sm:p-5">
      <div className="flex items-center gap-2 mb-1">
        <CalendarClock size={18} style={{ color: "var(--cb-primary, #8B3D52)" }} />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Prazo de pagamento
        </h3>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
        Define o vencimento quando este paciente paga a consulta a prazo. Sem prazo configurado,
        a recepção não consegue receber a prazo.
      </p>

      {carregando ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">Carregando…</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium mb-1">Modo do prazo</label>
            <select
              value={modo}
              onChange={(e) => setModo(e.target.value as Modo)}
              className={fieldClass}
            >
              <option value="">Sem prazo (não recebe a prazo)</option>
              <option value="DIAS_APOS">Dias para pagar (a partir do lançamento)</option>
              <option value="DIA_FIXO">Dia fixo do mês</option>
            </select>
          </div>

          {modo === "DIAS_APOS" && (
            <div>
              <label className="block text-xs font-medium mb-1">Dias para pagar</label>
              <input
                type="number"
                min={1}
                max={365}
                value={dias}
                onChange={(e) => setDias(e.target.value)}
                placeholder="ex.: 10"
                className={fieldClass}
              />
              <p className="text-xs text-gray-500 mt-1">Conta a partir do dia em que a recepção lança o pagamento a prazo.</p>
            </div>
          )}

          {modo === "DIA_FIXO" && (
            <div>
              <label className="block text-xs font-medium mb-1">Dia fixo do mês (1 a 28)</label>
              <input
                type="number"
                min={1}
                max={28}
                value={diaMes}
                onChange={(e) => setDiaMes(e.target.value)}
                placeholder="ex.: 10"
                className={fieldClass}
              />
              <p className="text-xs text-gray-500 mt-1">Vence no próximo dia escolhido: neste mês se ainda não passou, senão no mês seguinte.</p>
            </div>
          )}

          <div className="sm:col-span-2 flex items-center gap-2">
            <button
              type="button"
              onClick={handleSalvar}
              disabled={salvando}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              {salvando ? "Salvando…" : "Salvar prazo"}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={salvando}
              className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 disabled:opacity-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </ClinicaBelezaPanel>
  );
}
