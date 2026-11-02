import { useCallback, useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { BloqueioProfessional, ModoBloqueioIntervalo } from "./modal-bloqueio-horario-utils";
import {
  TIPOS_BLOQUEIO,
  buildBloqueioRequestBody,
  buildBloqueiosHorarioPorDia,
  buildBloqueiosPorDia,
  enumerarDiasDaSemana,
  extractBloqueioApiError,
  formatDateInput,
  formatTimeInput,
  modoSugeridoParaTipo,
  resolveMotivoBloqueio,
  removerDiasDoMes,
  rotuloDiaSemana,
  rotuloDiasSelecionados,
  selecionarSomenteMes,
  toggleDiaIso,
  validateBloqueioForm,
  weekdaySegundaZero,
} from "./modal-bloqueio-horario-utils";

interface UseModalBloqueioHorarioParams {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  dataInicioSugerida?: Date | null;
  defaultProfessionalId?: string;
}

export function useModalBloqueioHorario({
  isOpen,
  onClose,
  onSuccess,
  dataInicioSugerida,
  defaultProfessionalId,
}: UseModalBloqueioHorarioParams) {
  const [modo, setModo] = useState<ModoBloqueioIntervalo>("horario");
  const [dataInicioDia, setDataInicioDia] = useState("");
  const [dataFimDia, setDataFimDia] = useState("");
  const [diasSelecionados, setDiasSelecionados] = useState<string[]>([]);
  const [mesCursor, setMesCursor] = useState("");
  const [dataHorario, setDataHorario] = useState("");
  const [horaInicio, setHoraInicio] = useState("");
  const [horaFim, setHoraFim] = useState("");
  const [tipoSelecionado, setTipoSelecionado] = useState<string>(TIPOS_BLOQUEIO[0].value);
  const [motivoOutro, setMotivoOutro] = useState("");
  const [professionalId, setProfessionalId] = useState<string>("");
  const [observacoes, setObservacoes] = useState("");
  const [repetir, setRepetir] = useState(false);
  const [weekdayRepeticao, setWeekdayRepeticao] = useState(1);
  const [dataFimRepeticao, setDataFimRepeticao] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  const motivoFinal = resolveMotivoBloqueio(tipoSelecionado, motivoOutro);
  const dataInicioRepeticao =
    modo === "dias" ? (diasSelecionados[0] || dataInicioDia) : dataHorario;

  useEffect(() => {
    if (!isOpen) return;
    setErro("");
    const now = new Date();
    const base = dataInicioSugerida || now;
    setTipoSelecionado(TIPOS_BLOQUEIO[0].value);
    // Default do modal: horário no dia; Férias só muda o modo quando o usuário troca o tipo.
    setModo("horario");
    setMotivoOutro("");
    setProfessionalId(defaultProfessionalId || "");
    setObservacoes("");
    setRepetir(false);

    const dia = formatDateInput(base);
    setDataInicioDia(dia);
    setDataFimDia(dia);
    setDiasSelecionados([dia]);
    setMesCursor(dia);
    setDataHorario(dia);
    setWeekdayRepeticao(weekdaySegundaZero(dia));
    const fimRep = new Date(base);
    fimRep.setMonth(fimRep.getMonth() + 2);
    setDataFimRepeticao(formatDateInput(fimRep));

    const inicio = new Date(base);
    inicio.setMinutes(0, 0, 0);
    const fim = new Date(inicio);
    fim.setHours(fim.getHours() + 1);
    setHoraInicio(formatTimeInput(inicio));
    setHoraFim(formatTimeInput(fim));
  }, [isOpen, dataInicioSugerida, defaultProfessionalId]);

  const onTipoChange = useCallback((tipo: string) => {
    setTipoSelecionado(tipo);
    setModo(modoSugeridoParaTipo(tipo));
  }, []);

  const toggleDia = useCallback((dia: string) => {
    setDiasSelecionados((atual) => toggleDiaIso(atual, dia));
    setMesCursor(dia);
  }, []);

  const selecionarMesInteiro = useCallback(() => {
    const base = mesCursor || dataInicioDia;
    if (!base) return;
    setDiasSelecionados(selecionarSomenteMes(base));
  }, [dataInicioDia, mesCursor]);

  const limparMes = useCallback(() => {
    const base = mesCursor || dataInicioDia;
    if (!base) return;
    setDiasSelecionados((atual) => removerDiasDoMes(atual, base));
  }, [dataInicioDia, mesCursor]);

  const aplicarRepeticaoNoCalendario = useCallback(() => {
    const inicio = dataInicioRepeticao;
    if (!inicio || !dataFimRepeticao) {
      setErro("Informe a data de início e até quando repetir.");
      return;
    }
    const dias = enumerarDiasDaSemana(inicio, dataFimRepeticao, weekdayRepeticao);
    if (!dias.length) {
      setErro(`Nenhuma ${rotuloDiaSemana(weekdayRepeticao).toLowerCase()} nesse intervalo.`);
      return;
    }
    setErro("");
    setDiasSelecionados(dias);
    setMesCursor(dias[0]);
  }, [dataFimRepeticao, dataInicioRepeticao, weekdayRepeticao]);

  const salvar = useCallback(async () => {
    const validationError = validateBloqueioForm({
      modo,
      motivoFinal,
      dataInicioDia: dataInicioRepeticao || dataInicioDia,
      dataFimDia,
      diasSelecionados: modo === "dias" && !repetir ? diasSelecionados : undefined,
      dataHorario,
      horaInicio,
      horaFim,
      repetir,
      dataFimRepeticao,
      weekdayRepeticao,
    });
    if (validationError) {
      setErro(validationError);
      return;
    }
    setLoading(true);
    setErro("");
    try {
      const diasRepetidos = repetir
        ? enumerarDiasDaSemana(dataInicioRepeticao, dataFimRepeticao, weekdayRepeticao)
        : [];
      const diasOrdenados = repetir ? diasRepetidos : [...diasSelecionados].sort();
      const bodies =
        modo === "dias"
          ? buildBloqueiosPorDia({
              dias: diasOrdenados,
              motivo: motivoFinal,
              observacoes,
              professionalId,
            })
          : repetir
            ? buildBloqueiosHorarioPorDia({
                dias: diasOrdenados,
                motivo: motivoFinal,
                observacoes,
                professionalId,
                horaInicio,
                horaFim,
              })
            : [
                buildBloqueioRequestBody({
                  modo,
                  motivo: motivoFinal,
                  observacoes,
                  professionalId,
                  dataInicioDia,
                  dataFimDia,
                  dataHorario,
                  horaInicio,
                  horaFim,
                }),
              ];
      const gravados: string[] = [];
      for (let i = 0; i < bodies.length; i++) {
        const body = bodies[i];
        const res = await clinicaBelezaFetch("/bloqueios/", {
          method: "POST",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          if (gravados.length) onSuccess();
          setDiasSelecionados((atual) => atual.filter((dia) => !gravados.includes(dia)));
          throw new Error(
            gravados.length
              ? `Bloqueou ${gravados.length} dia(s). ${extractBloqueioApiError(data, res.status)}`
              : extractBloqueioApiError(data, res.status),
          );
        }
        if ((modo === "dias" || repetir) && diasOrdenados[i]) gravados.push(diasOrdenados[i]);
      }
      onSuccess();
      onClose();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar bloqueio.");
    } finally {
      setLoading(false);
    }
  }, [
    dataFimDia,
    dataFimRepeticao,
    dataHorario,
    dataInicioDia,
    dataInicioRepeticao,
    diasSelecionados,
    horaFim,
    horaInicio,
    modo,
    motivoFinal,
    observacoes,
    onClose,
    onSuccess,
    professionalId,
    repetir,
    weekdayRepeticao,
  ]);

  return {
    modo,
    setModo,
    dataInicioDia,
    diasSelecionados,
    mesCursor,
    setMesCursor,
    toggleDia,
    selecionarMesInteiro,
    limparMes,
    dataHorario,
    setDataHorario,
    horaInicio,
    setHoraInicio,
    horaFim,
    setHoraFim,
    tipoSelecionado,
    onTipoChange,
    motivoOutro,
    setMotivoOutro,
    professionalId,
    setProfessionalId,
    observacoes,
    setObservacoes,
    repetir,
    setRepetir,
    weekdayRepeticao,
    setWeekdayRepeticao,
    dataFimRepeticao,
    setDataFimRepeticao,
    dataInicioRepeticao,
    aplicarRepeticaoNoCalendario,
    loading,
    erro,
    salvar,
    rotuloSelecao: rotuloDiasSelecionados(diasSelecionados),
    rotuloRepeticao: repetir
      ? `${rotuloDiaSemana(weekdayRepeticao)} até ${dataFimRepeticao.split("-").reverse().join("/")}`
      : "",
  };
}

export type { BloqueioProfessional };
