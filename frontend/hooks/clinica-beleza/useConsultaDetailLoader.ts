"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import { logger } from "@/lib/logger";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import {
  type Consulta,
  type Protocolo,
  type Anamnese,
  type Evolucao,
  type TabId,
  EMPTY_ANAMNESE,
} from "@/components/clinica-beleza/consultas/consultas-types";

type UseConsultaDetailLoaderArgs = {
  consulta: Consulta;
  detailPreloaded?: boolean;
  onSelectConsulta: (c: Consulta) => void;
  onLoadStart?: () => void;
  onListRefresh?: () => void | Promise<void>;
};

export function useConsultaDetailLoader({
  consulta,
  detailPreloaded = false,
  onSelectConsulta,
  onLoadStart,
  onListRefresh,
}: UseConsultaDetailLoaderArgs) {
  const [selected, setSelected] = useState(consulta);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);
  const [tab, setTab] = useState<TabId>("atendimento");
  const [protocolos, setProtocolos] = useState<Protocolo[]>([]);
  const [anamnese, setAnamnese] = useState<Anamnese>(EMPTY_ANAMNESE);
  const [anamneseDraft, setAnamneseDraft] = useState<Anamnese>(EMPTY_ANAMNESE);
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [historico, setHistorico] = useState<Consulta[]>([]);
  const [prescricoes, setPrescricoes] = useState<PrescricaoMemedItem[]>([]);
  const [observacoes, setObservacoes] = useState("");
  const [observacoesDraft, setObservacoesDraft] = useState("");
  const [tabLoading, setTabLoading] = useState(false);

  const lastLoadedIdRef = useRef<number | null>(null);
  const loadingDetalheRef = useRef(false);
  const loadedTabsRef = useRef<Set<TabId>>(new Set());

  const loadTabData = useCallback(async (tabId: TabId, c: Consulta, force = false) => {
    if (!force && loadedTabsRef.current.has(tabId)) return;

    if (tabId === "produtos" || tabId === "documentos" || tabId === "fotos") {
      loadedTabsRef.current.add(tabId);
      return;
    }

    setTabLoading(true);
    const patientId = c.patient;
    try {
      switch (tabId) {
        case "atendimento": {
          const prots = await ClinicaBelezaAPI.getList<Protocolo>("/protocolos/", {
            procedure: c.procedure,
          }).catch(() => []);
          setProtocolos(Array.isArray(prots) ? prots : []);
          break;
        }
        case "anamnese": {
          const anam = await ClinicaBelezaAPI.anamnese.get(patientId).catch(() => EMPTY_ANAMNESE);
          const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
          setAnamnese(anamMerged);
          setAnamneseDraft(anamMerged);
          break;
        }
        case "evolucao": {
          const evol = await ClinicaBelezaAPI.consultas.evolucoes.list(c.id).catch(() => []);
          setEvolucoes(Array.isArray(evol) ? evol : []);
          break;
        }
        case "historico": {
          const histPromise =
            historico.length > 0 && !force
              ? Promise.resolve(historico)
              : fetchHistoricoPaciente(patientId);
          const [hist, anam, presc] = await Promise.all([
            histPromise,
            ClinicaBelezaAPI.anamnese.get(patientId).catch(() => EMPTY_ANAMNESE),
            ClinicaBelezaAPI.memed.listarPrescricoesPaciente(patientId).catch(() => []),
          ]);
          setHistorico(Array.isArray(hist) ? (hist as Consulta[]) : []);
          const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
          setAnamnese(anamMerged);
          setAnamneseDraft(anamMerged);
          setPrescricoes(Array.isArray(presc) ? presc : []);
          break;
        }
      }
      loadedTabsRef.current.add(tabId);
    } catch (e) {
      logger.warn(`Erro ao carregar aba ${tabId}:`, e);
    } finally {
      setTabLoading(false);
    }
  }, [historico]);

  const loadDetalhes = useCallback(async (c: Consulta, opts?: { detailPreloaded?: boolean }) => {
    if (loadingDetalheRef.current && lastLoadedIdRef.current === c.id) return;
    loadingDetalheRef.current = true;
    lastLoadedIdRef.current = c.id;
    loadedTabsRef.current = new Set();

    setLoadingDetalhe(true);
    setSelected(c);
    onLoadStart?.();
    const obs = c.observacoes_gerais || c.protocolo_notas || "";
    setObservacoes(obs);
    setObservacoesDraft(obs);

    if (c.id !== consulta.id) {
      onSelectConsulta(c);
    }

    try {
      let consultaAtual = c;
      if (!opts?.detailPreloaded) {
        const fresh = await ClinicaBelezaAPI.consultas.get(c.id).catch(() => null);
        consultaAtual = fresh ? { ...c, ...fresh } : c;
        setSelected(consultaAtual);
      }

      const hist = await fetchHistoricoPaciente(consultaAtual.patient).catch(() => []);
      const histList = Array.isArray(hist) ? (hist as Consulta[]) : [];
      setHistorico(histList);
      const temHistoricoAnterior = histList.length > 1;
      const initialTab: TabId =
        consultaAtual.status === "SCHEDULED" && temHistoricoAnterior ? "historico" : "atendimento";
      setTab(initialTab);

      if (initialTab === "historico") {
        loadedTabsRef.current.add("historico");
        const [anam, presc] = await Promise.all([
          ClinicaBelezaAPI.anamnese.get(consultaAtual.patient).catch(() => EMPTY_ANAMNESE),
          ClinicaBelezaAPI.memed.listarPrescricoesPaciente(consultaAtual.patient).catch(() => []),
        ]);
        const anamMerged = { ...EMPTY_ANAMNESE, ...anam };
        setAnamnese(anamMerged);
        setAnamneseDraft(anamMerged);
        setPrescricoes(Array.isArray(presc) ? presc : []);
      } else {
        await loadTabData(initialTab, consultaAtual, true);
      }
    } catch (e) {
      logger.warn("Erro ao carregar detalhes da consulta:", e);
    } finally {
      loadingDetalheRef.current = false;
      setLoadingDetalhe(false);
    }
  }, [onSelectConsulta, consulta.id, loadTabData, onLoadStart]);

  const refreshConsulta = useCallback(async (patch?: Record<string, unknown>) => {
    try {
      const fresh = patch ?? (await ClinicaBelezaAPI.consultas.get(selected.id));
      setSelected((prev) => ({ ...prev, ...fresh }));
      if (patch) await onListRefresh?.();
    } catch (e) {
      logger.warn("Erro ao atualizar consulta:", e);
    }
  }, [selected.id, onListRefresh]);

  const recarregarPrescricoes = useCallback(async () => {
    try {
      const presc = await ClinicaBelezaAPI.memed.listarPrescricoesPaciente(selected.patient);
      setPrescricoes(Array.isArray(presc) ? presc : []);
    } catch (e) {
      logger.warn("Erro ao recarregar prescrições:", e);
    }
  }, [selected.patient]);

  useEffect(() => {
    if (lastLoadedIdRef.current === consulta.id) return;
    void loadDetalhes(consulta, { detailPreloaded });
  }, [consulta.id, detailPreloaded, loadDetalhes, consulta]);

  useEffect(() => {
    if (loadingDetalhe) return;
    void loadTabData(tab, selected);
  }, [tab, selected.id, loadingDetalhe, loadTabData, selected]);

  return {
    selected,
    setSelected,
    loadingDetalhe,
    tab,
    setTab,
    tabLoading,
    protocolos,
    setProtocolos,
    anamnese,
    setAnamnese,
    anamneseDraft,
    setAnamneseDraft,
    evolucoes,
    setEvolucoes,
    historico,
    setHistorico,
    prescricoes,
    setPrescricoes,
    observacoes,
    setObservacoes,
    observacoesDraft,
    setObservacoesDraft,
    loadDetalhes,
    loadTabData,
    refreshConsulta,
    recarregarPrescricoes,
  };
}
