import Link from "next/link";
import { ConsultaTermoConsentimentoButton } from "@/components/clinica-beleza/consultas/ConsultaTermoConsentimentoButton";
import { consultaPagamentoUi } from "@/hooks/clinica-beleza/consulta-detail-actions/consulta-detail-actions-utils";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { classeStatusPdv, horaCurta, podeMarcarPresente, rotuloStatusPdv, seloCaixaPdv } from "./pdv-utils";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { rosa } from "./pdv-tipos";

type ConsultaDia = Consulta & { appointment?: number | null };

export function PdvListaAgenda({
  slug,
  agendaHoje,
  consultas,
  selecionadoId,
  onSelecionar,
  onMarcarPresente,
}: {
  slug: string;
  agendaHoje: AgendaEventData[];
  consultas: ConsultaDia[];
  selecionadoId: number | null;
  onSelecionar: (id: number) => void;
  onMarcarPresente: (id: number) => void;
}) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Próximos agendamentos</h2>
        <Link href={`/loja/${slug}/agenda`} className="text-sm font-medium" style={{ color: rosa }}>Ver agenda &gt;</Link>
      </div>
      <div className="space-y-2">
        {agendaHoje.length === 0 && <p className="text-sm text-gray-500">Nenhum agendamento hoje.</p>}
        {agendaHoje.map((evento) => {
          const id = Number(evento.extendedProps?.dbId);
          const status = evento.extendedProps?.status;
          const consultaItem = consultas.find((item) => item.appointment === id);
          const selo = seloCaixaPdv(consultaItem);
          const isento = Boolean(consultaItem && consultaPagamentoUi(consultaItem).mostrarIsento);
          const ativo = id === selecionadoId;
          const termoNoPdv = (status === "CONFIRMED" || status === "IN_PROGRESS")
            && Boolean(consultaItem?.id)
            && Boolean(consultaItem?.exige_termo_consentimento);
          return (
            <div key={evento.id} className={`flex w-full items-center gap-2 rounded-xl border px-3 py-2.5 text-left ${ativo ? "border-pink-200 bg-pink-50/60" : "border-transparent hover:bg-gray-50"}`}>
              <button type="button" onClick={() => onSelecionar(id)} className="flex min-w-0 flex-1 items-center gap-3 text-left">
                <span className="w-12 text-sm font-medium text-gray-500">{horaCurta(evento.start)}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold text-gray-900">{evento.extendedProps?.patient_name || evento.title}</span>
                  <span className="block truncate text-xs text-gray-500">{evento.extendedProps?.procedure_name || "Consulta"} • {evento.extendedProps?.professional_name || "Profissional"}</span>
                </span>
              </button>
              {podeMarcarPresente(status) ? (
                <button type="button" onClick={() => onMarcarPresente(id)} className="rounded-full border px-2 py-1 text-[11px] font-medium" style={{ color: rosa, borderColor: rosa }}>Marcar presente</button>
              ) : (
                <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${isento ? "bg-sky-100 text-sky-800" : classeStatusPdv(status, selo)}`}>{isento ? "Isento" : rotuloStatusPdv(status, selo)}</span>
              )}
              {termoNoPdv && consultaItem?.id && (
                <ConsultaTermoConsentimentoButton
                  consultaId={consultaItem.id}
                  compacto
                  permitirAssinaturaProfissional={false}
                />
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
