import { useCallback, useEffect, useMemo, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { ConsultaProcedimento } from "../consultas-types";
import type { AppointmentProcedureItem } from "./procedimentos-consulta-types";
import {
  avisoTermoProcedimentoAdicionado,
  extractProcedimentosConsultaError,
  mapProcedimentosFromConsulta,
  normalizarCatalogoProcedimentos,
} from "./procedimentos-consulta-utils";

export function useConsultaProcedimentos({
  consultaId,
  procedimentosIniciais = [],
  onChanged,
}: {
  consultaId: number;
  procedimentosIniciais?: ConsultaProcedimento[];
  onChanged?: (consulta?: Record<string, unknown>) => void;
}) {
  const [itens, setItens] = useState<AppointmentProcedureItem[]>([]);
  const [catalogo, setCatalogo] = useState<{ id: number; nome: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showManageList, setShowManageList] = useState(false);
  const [procedureId, setProcedureId] = useState<number | "">("");
  const [erro, setErro] = useState("");
  const [avisoTermo, setAvisoTermo] = useState("");

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const [lista, procs] = await Promise.all([
        ClinicaBelezaAPI.consultas.procedimentos.list(consultaId),
        ClinicaBelezaAPI.procedures.list({ active: true, page_size: 500 }),
      ]);
      setItens(Array.isArray(lista) ? lista : mapProcedimentosFromConsulta(procedimentosIniciais));
      setCatalogo(normalizarCatalogoProcedimentos(procs));
    } catch {
      setItens(mapProcedimentosFromConsulta(procedimentosIniciais));
      setErro("Erro ao carregar procedimentos.");
    } finally {
      setLoading(false);
    }
  }, [consultaId, procedimentosIniciais]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const idsJaAdicionados = useMemo(() => new Set(itens.map((i) => i.procedure)), [itens]);
  const opcoesDisponiveis = useMemo(
    () => catalogo.filter((p) => !idsJaAdicionados.has(p.id)),
    [catalogo, idsJaAdicionados],
  );

  const podeAdicionar = !loading && opcoesDisponiveis.length > 0;

  const toggleManageList = () => {
    setShowManageList((v) => !v);
    setShowAddForm(false);
  };

  const abrirAddForm = () => {
    setShowAddForm((v) => !v);
    setShowManageList(false);
    setErro("");
    setAvisoTermo("");
  };

  const fecharAddForm = () => {
    setShowAddForm(false);
    setProcedureId("");
    setErro("");
  };

  const adicionar = async () => {
    if (!procedureId) {
      setErro("Selecione um procedimento.");
      return;
    }
    setSaving(true);
    setErro("");
    setAvisoTermo("");
    const procId = Number(procedureId);
    try {
      const res = await ClinicaBelezaAPI.consultas.procedimentos.add(consultaId, procId);
      const lista = await ClinicaBelezaAPI.consultas.procedimentos.list(consultaId);
      setItens(Array.isArray(lista) ? lista : []);
      setProcedureId("");
      setShowAddForm(false);
      setShowManageList(false);
      onChanged?.(res.consulta);
      setAvisoTermo(avisoTermoProcedimentoAdicionado(res.consulta, procId));
    } catch (e: unknown) {
      setErro(extractProcedimentosConsultaError(e, "Erro ao adicionar procedimento."));
    } finally {
      setSaving(false);
    }
  };

  const remover = async (item: AppointmentProcedureItem) => {
    if (!confirm(`Remover "${item.procedure_name}" deste atendimento?`)) return;
    setSaving(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.procedimentos.remove(consultaId, item.id);
      const lista = await ClinicaBelezaAPI.consultas.procedimentos.list(consultaId);
      const fresh = await ClinicaBelezaAPI.consultas.get(consultaId);
      setItens(Array.isArray(lista) ? lista : []);
      onChanged?.(fresh as Record<string, unknown>);
      if ((Array.isArray(lista) ? lista : []).length === 0) setShowManageList(false);
    } catch (e: unknown) {
      setErro(extractProcedimentosConsultaError(e, "Erro ao remover procedimento."));
    } finally {
      setSaving(false);
    }
  };

  return {
    itens,
    loading,
    saving,
    showAddForm,
    showManageList,
    procedureId,
    erro,
    avisoTermo,
    opcoesDisponiveis,
    podeAdicionar,
    setProcedureId,
    toggleManageList,
    abrirAddForm,
    fecharAddForm,
    adicionar,
    remover,
  };
}
