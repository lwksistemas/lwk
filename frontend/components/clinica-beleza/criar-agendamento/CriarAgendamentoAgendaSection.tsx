import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import {
  CRIAR_AGENDAMENTO_INPUT_CLASS,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { entityName } from "@/lib/clinica-beleza-entities";
import { FieldLabel, SectionTitle } from "./CriarAgendamentoFormFields";

type Props = Pick<
  UseCriarAgendamentoReturn,
  | "dateInput"
  | "setDateInput"
  | "time"
  | "setTime"
  | "professionalId"
  | "setProfessionalId"
  | "professionals"
  | "nomeAgendaId"
  | "setNomeAgendaId"
  | "nomeAgendaUnico"
  | "nomesAgenda"
  | "convenioId"
  | "setConvenioId"
  | "convenios"
  | "localAtendimentoId"
  | "setLocalAtendimentoId"
  | "localUnico"
  | "locaisAtendimento"
  | "patientId"
  | "retornoInfo"
  | "taxaConsultaBase"
  | "totalEstimado"
  | "resumo"
>;

export function CriarAgendamentoAgendaSection({
  dateInput,
  setDateInput,
  time,
  setTime,
  professionalId,
  setProfessionalId,
  professionals,
  nomeAgendaId,
  setNomeAgendaId,
  nomeAgendaUnico,
  nomesAgenda,
  convenioId,
  setConvenioId,
  convenios,
  localAtendimentoId,
  setLocalAtendimentoId,
  localUnico,
  locaisAtendimento,
  patientId,
  retornoInfo,
  taxaConsultaBase,
  totalEstimado,
  resumo,
}: Props) {
  const inputClass = CRIAR_AGENDAMENTO_INPUT_CLASS;

  const campoNomeAgenda = nomeAgendaUnico ? (
    <div>
      <FieldLabel>Nome da agenda *</FieldLabel>
      <div className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-gray-50/80 dark:bg-neutral-900/50 text-gray-900 dark:text-gray-100">
        {nomeAgendaUnico.nome}
      </div>
    </div>
  ) : (
    <div>
      <FieldLabel>Nome da agenda *</FieldLabel>
      <select
        value={nomeAgendaId}
        onChange={(e) => setNomeAgendaId(e.target.value ? Number(e.target.value) : "")}
        className={inputClass}
        required
      >
        <option value="">Selecione a agenda</option>
        {nomesAgenda.map((a) => (
          <option key={a.id} value={a.id}>
            {a.nome}
          </option>
        ))}
      </select>
      {nomesAgenda.length === 0 && (
        <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          Cadastre nomes de agenda em Consultas → ícone de calendário.
        </p>
      )}
    </div>
  );

  const campoLocalAtendimento = localUnico ? (
    <div>
      <FieldLabel>Local de atendimento</FieldLabel>
      <div className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-gray-50/80 dark:bg-neutral-900/50 text-gray-900 dark:text-gray-100">
        {localUnico.nome}
      </div>
    </div>
  ) : (
    <div>
      <FieldLabel>Local de atendimento</FieldLabel>
      <select
        value={localAtendimentoId}
        onChange={(e) => setLocalAtendimentoId(e.target.value ? Number(e.target.value) : "")}
        className={inputClass}
      >
        <option value="">Selecione o local (opcional)</option>
        {locaisAtendimento.map((l) => (
          <option key={l.id} value={l.id}>
            {l.nome}
          </option>
        ))}
      </select>
      {locaisAtendimento.length === 0 && (
        <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          Cadastre locais em Consultas → ícone de engrenagem.
        </p>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      <SectionTitle>Agendamento</SectionTitle>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <FieldLabel>Data *</FieldLabel>
          <input
            type="date"
            value={dateInput}
            onChange={(e) => setDateInput(e.target.value)}
            className={inputClass}
            required
          />
        </div>
        <div>
          <FieldLabel>Horário *</FieldLabel>
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className={inputClass}
            required
          />
        </div>
        <div className="sm:col-span-2">
          <FieldLabel>Profissional</FieldLabel>
          <select
            value={professionalId}
            onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
            className={inputClass}
          >
            <option value="">Selecione o profissional (opcional)</option>
            {professionals.map((p) => (
              <option key={p.id} value={p.id}>
                {entityName(p)}
              </option>
            ))}
          </select>
        </div>
        <div>{campoNomeAgenda}</div>
        <div>
          <ConvenioSelect
            convenios={convenios}
            value={convenioId}
            onChange={setConvenioId}
            hint=""
            className={inputClass}
          />
        </div>
        <div>{campoLocalAtendimento}</div>
      </div>

      {retornoInfo?.elegivel && patientId && (
        <div className="p-2.5 rounded-lg text-sm bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <span className="font-medium">Retorno gratuito</span>
          <span className="block text-xs mt-0.5">{retornoInfo.mensagem}</span>
        </div>
      )}

      {localAtendimentoId && (
        <div className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-900/50 text-sm space-y-1 border border-gray-100 dark:border-neutral-700">
          <div className="flex justify-between text-gray-600 dark:text-gray-400">
            <span>Taxa de consulta</span>
            <span>
              {retornoInfo?.elegivel ? (
                <>
                  <span className="line-through opacity-60 mr-1">
                    {taxaConsultaBase.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                  </span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">R$ 0,00</span>
                </>
              ) : (
                taxaConsultaBase.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
              )}
            </span>
          </div>
          {resumo.valor > 0 && (
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Procedimentos</span>
              <span>{resumo.valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span>
            </div>
          )}
          <div className="flex justify-between font-medium text-gray-900 dark:text-gray-100 pt-1 border-t border-gray-200 dark:border-neutral-700">
            <span>Total estimado</span>
            <span>{totalEstimado.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span>
          </div>
        </div>
      )}
    </div>
  );
}
