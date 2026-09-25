import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import {
  CRIAR_AGENDAMENTO_INPUT_CLASS,
  CRIAR_AGENDAMENTO_TIME_SLOTS,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { entityName } from "@/lib/clinica-beleza-entities";
import { sortTiposAgenda } from "@/lib/clinica-beleza-tipo-agenda";
import {
  dividirValorProtocolo,
  formatarValorProtocolo,
  rotuloIntervaloProtocolo,
} from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
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
  | "isConsulta"
  | "protocoloSelecionado"
  | "protocoloErro"
  | "formaCobranca"
  | "setFormaCobranca"
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
  isConsulta,
  protocoloSelecionado,
  protocoloErro,
  formaCobranca,
  setFormaCobranca,
}: Props) {
  const inputClass = CRIAR_AGENDAMENTO_INPUT_CLASS;

  const campoNomeAgenda = nomeAgendaUnico ? (
    <div>
      <FieldLabel>Tipo de agenda *</FieldLabel>
      <div className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-gray-50/80 dark:bg-neutral-900/50 text-gray-900 dark:text-gray-100">
        {nomeAgendaUnico.nome}
      </div>
    </div>
  ) : (
    <div>
      <FieldLabel>Tipo de agenda *</FieldLabel>
      <select
        value={nomeAgendaId}
        onChange={(e) => setNomeAgendaId(e.target.value ? Number(e.target.value) : "")}
        className={inputClass}
        required
      >
        <option value="">Selecione o tipo</option>
        {sortTiposAgenda(nomesAgenda).map((a) => (
          <option key={a.id} value={a.id}>
            {a.nome}
          </option>
        ))}
      </select>
      {nomesAgenda.length === 0 && (
        <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          Cadastre tipos de agenda em Consultas → ícone de calendário.
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
          <select
            value={
              CRIAR_AGENDAMENTO_TIME_SLOTS.includes(time)
                ? time
                : time || CRIAR_AGENDAMENTO_TIME_SLOTS[0]
            }
            onChange={(e) => setTime(e.target.value)}
            className={`${inputClass} touch-manipulation`}
            required
          >
            {!CRIAR_AGENDAMENTO_TIME_SLOTS.includes(time) && time ? (
              <option value={time}>{time}</option>
            ) : null}
            {CRIAR_AGENDAMENTO_TIME_SLOTS.map((slot) => (
              <option key={slot} value={slot}>
                {slot}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <FieldLabel>Profissional *</FieldLabel>
          <select
            value={professionalId}
            onChange={(e) => setProfessionalId(e.target.value ? Number(e.target.value) : "")}
            className={inputClass}
            required
          >
            <option value="">Selecione o profissional</option>
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
            hint="Particular é o padrão. Outro convênio no cadastro vale só para esse cliente."
            className={inputClass}
          />
        </div>
        <div>{campoLocalAtendimento}</div>
      </div>

      {protocoloErro && (
        <div className="p-2.5 rounded-lg text-sm bg-amber-50 dark:bg-amber-900/20 text-amber-900 dark:text-amber-200 border border-amber-200 dark:border-amber-800">
          {protocoloErro}
        </div>
      )}

      {protocoloSelecionado && (
        <ProtocoloCobrancaBox
          nome={protocoloSelecionado.nome}
          sessoes={protocoloSelecionado.sessoes || 1}
          intervaloQuantidade={protocoloSelecionado.intervalo_quantidade || 1}
          intervaloUnidade={protocoloSelecionado.intervalo_unidade || "dias"}
          valorPacote={resumo.valor}
          forma={formaCobranca}
          onForma={setFormaCobranca}
          isConsulta={isConsulta}
          totalDestaVisita={totalEstimado}
        />
      )}

      {retornoInfo?.elegivel && patientId && !protocoloSelecionado && (
        <div className="p-2.5 rounded-lg text-sm bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <span className="font-medium">Retorno gratuito</span>
          <span className="block text-xs mt-0.5">{retornoInfo.mensagem}</span>
        </div>
      )}

      {localAtendimentoId && !protocoloSelecionado && (
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

function ProtocoloCobrancaBox({
  nome,
  sessoes,
  intervaloQuantidade,
  intervaloUnidade,
  valorPacote,
  forma,
  onForma,
  isConsulta,
  totalDestaVisita,
}: {
  nome: string;
  sessoes: number;
  intervaloQuantidade: number;
  intervaloUnidade: "dias" | "semanas" | "meses";
  valorPacote: number;
  forma: "POR_CONSULTA" | "TOTAL";
  onForma: (forma: "POR_CONSULTA" | "TOTAL") => void;
  isConsulta: boolean;
  totalDestaVisita: number;
}) {
  const partes = dividirValorProtocolo(valorPacote, sessoes, "POR_CONSULTA");
  const parcela = formatarValorProtocolo(partes[0] || 0);
  const pacote = formatarValorProtocolo(valorPacote);

  return (
    <div className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-900/50 text-sm space-y-3 border border-gray-100 dark:border-neutral-700">
      <div>
        <p className="font-medium text-gray-900 dark:text-gray-100">{nome}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {sessoes} sessões · {rotuloIntervaloProtocolo(intervaloQuantidade, intervaloUnidade)}
        </p>
      </div>
      <fieldset className="space-y-2">
        <legend className="text-xs font-medium text-gray-600 dark:text-gray-400">Como cobrar</legend>
        <label className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
          <input
            type="radio"
            name="forma-cobranca-protocolo"
            className="mt-1"
            checked={forma === "POR_CONSULTA"}
            onChange={() => onForma("POR_CONSULTA")}
          />
          <span>Por consulta — {sessoes}x de {parcela}</span>
        </label>
        <label className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
          <input
            type="radio"
            name="forma-cobranca-protocolo"
            className="mt-1"
            checked={forma === "TOTAL"}
            onChange={() => onForma("TOTAL")}
          />
          <span>Valor total — {pacote} na primeira sessão. As demais não geram nova cobrança.</span>
        </label>
      </fieldset>
      {valorPacote <= 0 && (
        <p className="text-xs text-amber-800 dark:text-amber-200">
          O preço deste procedimento está zerado. Ajuste em Procedimentos, nos valores por convênio.
        </p>
      )}
      <div className="flex justify-between font-medium text-gray-900 dark:text-gray-100 pt-1 border-t border-gray-200 dark:border-neutral-700">
        <span>{forma === "TOTAL" ? "Total na primeira sessão" : "Total desta sessão"}</span>
        <span>{formatarValorProtocolo(totalDestaVisita)}</span>
      </div>
      <p className="text-xs text-gray-500">
        {isConsulta
          ? "A primeira sessão abre agora para recebimento. As demais ficam na agenda."
          : "Todas as sessões entram na agenda."}{" "}
        A taxa do consultório não entra no protocolo. O valor acima é o do protocolo.
      </p>
    </div>
  );
}
