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
import type { UseConsultaDetailLoaderArgs } from "./consulta-detail-loader-types";
import {
  extractObservacoesConsulta,
  mergeConsultaFresh,
  normalizeConsultaList,
  resolveInitialConsultaTab,
} from "./consulta-detail-loader-utils";
import { useConsultaDetailTabLoader } from "./useConsultaDetailTabLoader";

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

  const { loadTabData, loadHistoricoExtras } = useConsultaDetailTabLoader({
    loadedTabsRef,
    historico,
    setTabLoading,
    setProtocolos,
    setAnamnese,
    setAnamneseDraft,
    setEvolucoes,
    setHistorico,
    setPrescricoes,
  });

  const loadDetalhes = useCallback(
    async (c: Consulta, opts?: { detailPreloaded?: boolean }) => {
      if (loadingDetalheRef.current && lastLoadedIdRef.current === c.id) return;
      loadingDetalheRef.current = true;
      lastLoadedIdRef.current = c.id;
      loadedTabsRef.current = new Set();

      setLoadingDetalhe(true);
      setSelected(c);
      onLoadStart?.();
      const obs = extractObservacoesConsulta(c);
      setObservacoes(obs);
      setObservacoesDraft(obs);

      if (c.id !== consulta.id) {
        onSelectConsulta(c);
      }

      try {
        let consultaAtual = c;
        if (!opts?.detailPreloaded) {
          const fresh = await ClinicaBelezaAPI.consultas.get(c.id).catch(() => null);
          consultaAtual = mergeConsultaFresh(c, fresh);
          setSelected(consultaAtual);
        }

        const hist = await fetchHistoricoPaciente(consultaAtual.patient).catch(() => []);
        const histList = normalizeConsultaList(hist);
        setHistorico(histList);
        const initialTab = resolveInitialConsultaTab(consultaAtual.status, histList.length);
        setTab(initialTab);

        if (initialTab === "historico") {
          loadedTabsRef.current.add("historico");
          await loadHistoricoExtras(consultaAtual.patient);
        } else {
          await loadTabData(initialTab, consultaAtual, true);
        }
      } catch (e) {
        logger.warn("Erro ao carregar detalhes da consulta:", e);
      } finally {
        loadingDetalheRef.current = false;
        setLoadingDetalhe(false);
      }
    },
    [consulta.id, loadHistoricoExtras, loadTabData, onLoadStart, onSelectConsulta],
  );

  const refreshConsulta = useCallback(
    async (patch?: Record<string, unknown>) => {
      try {
        const fresh = patch ?? (await ClinicaBelezaAPI.consultas.get(selected.id));
        setSelected((prev) => ({ ...prev, ...fresh }));
        if (patch) await onListRefresh?.();
      } catch (e) {
        logger.warn("Erro ao atualizar consulta:", e);
      }
    },
    [selected.id, onListRefresh],
  );

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
