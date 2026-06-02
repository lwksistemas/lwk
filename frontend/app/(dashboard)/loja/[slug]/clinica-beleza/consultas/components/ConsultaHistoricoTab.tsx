import { useState } from "react";
import { ChevronRight, Pill, FlaskConical, ClipboardList, Activity } from "lucide-react";
import type { Consulta } from "./consultas-types";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";

type HistoricoSection = "atendimentos" | "receituarios" | "exames" | "evolucoes";

export function ConsultaHistoricoTab({
  historico,
  selectedId,
  prescricoes = [],
  formatData,
  onSelect,
}: {
  historico: Consulta[];
  selectedId: number;
  prescricoes?: PrescricaoMemedItem[];
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
}) {
  const [section, setSection] = useState<HistoricoSection>("atendimentos");

  // Separar prescrições em receituários e exames
  const receituarios = prescricoes.filter(
    (p) => !p.itens?.every((it) => it.tipo === "exame"),
  );
  const exames = prescricoes.filter(
    (p) => p.itens?.some((it) => it.tipo === "exame"),
  );

  const sections: { id: HistoricoSection; label: string; icon: typeof Pill; count: number }[] = [
    { id: "atendimentos", label: "Atendimentos", icon: ClipboardList, count: historico.length },
    { id: "receituarios", label: "Receituários", icon: Pill, count: receituarios.length },
    { id: "exames", label: "Exames", icon: FlaskConical, count: exames.length },
    { id: "evolucoes", label: "Evoluções", icon: Activity, count: historico.reduce((sum, h) => sum + (h.total_evolucoes || 0), 0) },
  ];

  return (
    <div className="space-y-4">
      {/* Sub-tabs */}
      <div className="flex flex-wrap gap-2">
        {sections.map(({ id, label, icon: Icon, count }) => (
          <button
            key={id}
            type="button"
            onClick={() => setSection(id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              section === id
                ? "bg-[#8B3D52] text-white"
                : "bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-neutral-700"
            }`}
          >
            <Icon size={14} />
            {label}
            {count > 0 && (
              <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] ${
                section === id ? "bg-white/20 text-white" : "bg-gray-200 dark:bg-neutral-700 text-gray-600 dark:text-gray-400"
              }`}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Conteúdo da seção */}
      <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-5">
        {section === "atendimentos" && (
          <HistoricoAtendimentos historico={historico} selectedId={selectedId} formatData={formatData} onSelect={onSelect} />
        )}
        {section === "receituarios" && (
          <HistoricoPrescricoes items={receituarios} formatData={formatData} emptyMsg="Nenhum receituário emitido." />
        )}
        {section === "exames" && (
          <HistoricoPrescricoes items={exames} formatData={formatData} emptyMsg="Nenhum exame solicitado." />
        )}
        {section === "evolucoes" && (
          <HistoricoEvolucoes historico={historico} formatData={formatData} />
        )}
      </div>
    </div>
  );
}

function HistoricoAtendimentos({
  historico, selectedId, formatData, onSelect,
}: {
  historico: Consulta[]; selectedId: number;
  formatData: (d?: string | null) => string;
  onSelect: (c: Consulta) => void;
}) {
  if (historico.length === 0) return <p className="text-gray-500 text-sm">Nenhuma consulta anterior.</p>;
  return (
    <div className="space-y-2">
      {historico.map((h) => (
        <button
          key={h.id}
          type="button"
          onClick={() => h.id !== selectedId && onSelect(h)}
          disabled={h.id === selectedId}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            h.id === selectedId
              ? "border-[#8B3D52] bg-[#F5E6EA]/40 dark:bg-neutral-700 cursor-default"
              : "border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700/50"
          }`}
        >
          <div className="flex justify-between items-center gap-2">
            <div>
              <p className="font-medium text-sm text-gray-900 dark:text-gray-100">{h.procedure_name}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {formatData(h.data_inicio)}
                {h.professional_name ? ` · ${h.professional_name}` : ""}
              </p>
            </div>
            {h.id !== selectedId && <ChevronRight size={16} className="text-gray-400 shrink-0" />}
          </div>
        </button>
      ))}
    </div>
  );
}

function HistoricoPrescricoes({
  items, formatData, emptyMsg,
}: {
  items: PrescricaoMemedItem[];
  formatData: (d?: string | null) => string;
  emptyMsg: string;
}) {
  if (items.length === 0) return <p className="text-gray-500 text-sm">{emptyMsg}</p>;
  return (
    <div className="space-y-3">
      {items.map((p) => (
        <div key={p.id} className="p-3 rounded-lg border border-gray-200 dark:border-neutral-600">
          <p className="text-xs text-gray-500">
            {formatData(p.created_at)}
            {p.professional_name ? ` · ${p.professional_name}` : ""}
          </p>
          {p.itens && p.itens.length > 0 ? (
            <ul className="mt-1.5 space-y-1">
              {p.itens.map((it, idx) => (
                <li key={idx} className="text-sm text-gray-800 dark:text-gray-200">
                  <span className="font-medium">{it.nome}</span>
                  {it.posologia ? <span className="text-gray-500"> — {it.posologia}</span> : null}
                </li>
              ))}
            </ul>
          ) : (
            p.resumo && <p className="mt-1.5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{p.resumo}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function HistoricoEvolucoes({
  historico, formatData,
}: {
  historico: Consulta[];
  formatData: (d?: string | null) => string;
}) {
  const totalEvolucoes = historico.reduce((sum, h) => sum + (h.total_evolucoes || 0), 0);
  if (totalEvolucoes === 0) return <p className="text-gray-500 text-sm">Nenhuma evolução registrada.</p>;
  return (
    <div className="space-y-3">
      {historico
        .filter((h) => (h.total_evolucoes || 0) > 0)
        .map((h) => (
          <div key={h.id} className="p-3 rounded-lg border border-gray-200 dark:border-neutral-600">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{h.procedure_name}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {formatData(h.data_inicio)}
              {h.professional_name ? ` · ${h.professional_name}` : ""}
              {` · ${h.total_evolucoes} evolução(ões)`}
            </p>
          </div>
        ))}
    </div>
  );
}
