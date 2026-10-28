import { ConvenioSelect } from "@/components/clinica-beleza/ConvenioSelect";
import {
  CRIAR_AGENDAMENTO_INPUT_CLASS,
  CRIAR_AGENDAMENTO_TIME_SLOTS,
} from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { entityName } from "@/lib/clinica-beleza-entities";
import { normalizarTipoAgendaNome, sortTiposAgenda } from "@/lib/clinica-beleza-tipo-agenda";
import {
  dividirValorProtocolo,
  formatarValorProtocolo,
  rotuloIntervaloProtocolo,
} from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import { formatCurrency } from "@/lib/financeiro-helpers";
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
  | "protocoloSelecionado"
  | "protocoloCliente"
  | "protocolos"
  | "protocolosClienteCarregando"
  | "protocolosDaCliente"
  | "protocoloClienteId"
  | "setProtocoloClienteId"
  | "protocoloModeloId"
  | "setProtocoloModeloId"
  | "setSelectedProcedures"
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
  protocoloSelecionado,
  protocoloCliente,
  protocolos,
  protocolosClienteCarregando,
  protocolosDaCliente,
  protocoloClienteId,
  setProtocoloClienteId,
  protocoloModeloId,
  setProtocoloModeloId,
  setSelectedProcedures,
}: Props) {
  const inputClass = CRIAR_AGENDAMENTO_INPUT_CLASS;
  const protocoloEscolhido = Boolean(protocoloSelecionado || protocoloCliente);
  const tipoSelecionado = nomesAgenda.find((item) => item.id === nomeAgendaId);
  const agendaEhProtocolo = normalizarTipoAgendaNome(tipoSelecionado?.nome || "") === "PROTOCOLO";

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
          Cadastre tipos de agenda em Atendimentos → ícone de calendário.
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
          Cadastre locais em Atendimentos → ícone de engrenagem.
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
        <div className="sm:col-span-2">{campoLocalAtendimento}</div>
        {agendaEhProtocolo && patientId && protocoloEscolhido && (protocolosClienteCarregando || protocolosDaCliente.length > 0 || protocolos.length > 1) ? (
          <div className="sm:col-span-2">
            <CriarAgendamentoProtocoloEscolha
              inputClass={inputClass}
              protocolosClienteCarregando={protocolosClienteCarregando}
              protocolosDaCliente={protocolosDaCliente}
              protocolos={protocolos}
              protocoloClienteId={protocoloClienteId}
              setProtocoloClienteId={setProtocoloClienteId}
              protocoloModeloId={protocoloModeloId}
              setProtocoloModeloId={setProtocoloModeloId}
              setSelectedProcedures={setSelectedProcedures}
              protocoloSelecionado={protocoloSelecionado}
            />
          </div>
        ) : null}
      </div>

      {retornoInfo?.elegivel && patientId && !protocoloSelecionado && !protocoloCliente && (
        <div className="p-2.5 rounded-lg text-sm bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <span className="font-medium">Retorno gratuito</span>
          <span className="block text-xs mt-0.5">{retornoInfo.mensagem}</span>
        </div>
      )}

      {localAtendimentoId && !protocoloSelecionado && !protocoloCliente && (
        <div className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-900/50 text-sm space-y-1 border border-gray-100 dark:border-neutral-700">
          <div className="flex justify-between text-gray-600 dark:text-gray-400">
            <span>Taxa de avaliação</span>
            <span>
              {retornoInfo?.elegivel ? (
                <>
                  <span className="line-through opacity-60 mr-1">
                    {formatCurrency(taxaConsultaBase)}
                  </span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">R$ 0,00</span>
                </>
              ) : (
                formatCurrency(taxaConsultaBase)
              )}
            </span>
          </div>
          {resumo.valor > 0 && (
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Procedimentos</span>
              <span>{formatCurrency(resumo.valor)}</span>
            </div>
          )}
          <div className="flex justify-between font-medium text-gray-900 dark:text-gray-100 pt-1 border-t border-gray-200 dark:border-neutral-700">
            <span>Total estimado</span>
            <span>{formatCurrency(totalEstimado)}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function ProtocoloCobrancaBox({
  nome,
  sessoes,
  intervaloQuantidade,
  intervaloUnidade,
  valorPacote,
  forma,
  onForma,
  isConsulta,
  totalDestaVisita,
  ocultarResumo = false,
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
  ocultarResumo?: boolean;
}) {
  const partes = dividirValorProtocolo(valorPacote, sessoes, "POR_CONSULTA");
  const parcela = formatarValorProtocolo(partes[0] || 0);
  const pacote = formatarValorProtocolo(valorPacote);

  return (
    <div className={ocultarResumo ? "text-sm space-y-3" : "p-3 rounded-lg bg-gray-50 dark:bg-neutral-900/50 text-sm space-y-3 border border-gray-100 dark:border-neutral-700"}>
      {ocultarResumo ? null : (
      <div>
        <p className="font-medium text-gray-900 dark:text-gray-100">{nome}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {sessoes} sessões · {rotuloIntervaloProtocolo(intervaloQuantidade, intervaloUnidade)}
        </p>
      </div>
      )}
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
          <span>Por atendimento — {sessoes}x de {parcela}</span>
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
        No Receber pagamento, depois da consulta, esta escolha ainda pode mudar.
      </p>
    </div>
  );
}

export function CriarAgendamentoProtocoloEscolha({
  inputClass,
  protocolosClienteCarregando,
  protocolosDaCliente,
  protocolos,
  protocoloClienteId,
  setProtocoloClienteId,
  protocoloModeloId,
  setProtocoloModeloId,
  setSelectedProcedures,
  protocoloSelecionado,
}: Pick<
  UseCriarAgendamentoReturn,
  | "protocolosClienteCarregando"
  | "protocolosDaCliente"
  | "protocolos"
  | "protocoloClienteId"
  | "setProtocoloClienteId"
  | "protocoloModeloId"
  | "setProtocoloModeloId"
  | "setSelectedProcedures"
  | "protocoloSelecionado"
> & { inputClass: string }) {
  return (
    <div className="space-y-2">
      <FieldLabel>Protocolo *</FieldLabel>
      {protocolosClienteCarregando ? (
        <p className="text-sm text-gray-500">Carregando protocolos...</p>
      ) : protocolosDaCliente.length > 0 ? (
        <select
          value={protocoloClienteId}
          onChange={(e) => {
            const id = e.target.value ? Number(e.target.value) : "";
            setProtocoloClienteId(id);
            setProtocoloModeloId("");
            if (id) setSelectedProcedures([]);
          }}
          className={inputClass}
          required
        >
          <option value="">Selecione o protocolo</option>
          {protocolosDaCliente.map((item) => (
            <option key={`cliente-${item.id}`} value={item.id}>
              {item.nome}
            </option>
          ))}
        </select>
      ) : protocolos.length > 1 ? (
        <div className="space-y-2">
          {protocolos.map((item) => {
            const escolhido = protocoloModeloId === item.id;
            const procedimentos = (item.procedimentos || [])
              .map((linha) => linha.nome)
              .filter(Boolean)
              .join(" + ");
            return (
              <button
                key={`modelo-${item.id}`}
                type="button"
                onClick={() => {
                  setProtocoloModeloId(item.id);
                  setProtocoloClienteId("");
                  setSelectedProcedures([]);
                }}
                className={`w-full text-left rounded-lg border px-3 py-2 ${
                  escolhido
                    ? "border-[var(--cb-primary,#8B3D52)] bg-[var(--cb-primary,#8B3D52)]/10"
                    : "border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900"
                }`}
              >
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.nome}</p>
                {procedimentos ? (
                  <p className="text-xs text-gray-500 mt-0.5">{procedimentos}</p>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : protocolos.length === 0 ? (
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Não há protocolo para agendar. Cadastre no prontuário ou em Protocolos.
        </p>
      ) : null}
      {!protocolosClienteCarregando && protocolosDaCliente.length === 0 && protocolos.length > 1 && !protocoloSelecionado ? (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Esta cliente ainda não tem protocolo no prontuário. O modelo escolhido vira o protocolo dela ao salvar.
        </p>
      ) : null}
    </div>
  );
}
