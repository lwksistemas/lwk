import { useCallback, type Dispatch, type MutableRefObject, type SetStateAction } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { fetchHistoricoPaciente } from "@/lib/clinica-beleza-cadastros-api";
import { logger } from "@/lib/logger";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import {
  type Anamnese,
  type Consulta,
  type Evolucao,
  type Protocolo,
  type TabId,
  EMPTY_ANAMNESE,
} from "@/components/clinica-beleza/consultas/consultas-types";
import {
  isTabWithoutRemoteLoad,
  mergeAnamnese,
  normalizeConsultaList,
} from "./consulta-detail-loader-utils";

interface UseConsultaDetailTabLoaderParams {
  loadedTabsRef: MutableRefObject<Set<TabId>>;
  historico: Consulta[];
  setTabLoading: (loading: boolean) => void;
  setProtocolos: Dispatch<SetStateAction<Protocolo[]>>;
  setAnamnese: Dispatch<SetStateAction<Anamnese>>;
  setAnamneseDraft: Dispatch<SetStateAction<Anamnese>>;
  setEvolucoes: Dispatch<SetStateAction<Evolucao[]>>;
  setHistorico: Dispatch<SetStateAction<Consulta[]>>;
  setPrescricoes: Dispatch<SetStateAction<PrescricaoMemedItem[]>>;
}

export function useConsultaDetailTabLoader({
  loadedTabsRef,
  historico,
  setTabLoading,
  setProtocolos,
  setAnamnese,
  setAnamneseDraft,
  setEvolucoes,
  setHistorico,
  setPrescricoes,
}: UseConsultaDetailTabLoaderParams) {
  const loadTabData = useCallback(
    async (tabId: TabId, c: Consulta, force = false) => {
      if (!force && loadedTabsRef.current.has(tabId)) return;

      if (isTabWithoutRemoteLoad(tabId)) {
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
            const anamMerged = mergeAnamnese(anam as Partial<Anamnese> | null | undefined);
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
            setHistorico(normalizeConsultaList(hist));
            const anamMerged = mergeAnamnese(anam as Partial<Anamnese> | null | undefined);
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
    },
    [
      historico,
      loadedTabsRef,
      setAnamnese,
      setAnamneseDraft,
      setEvolucoes,
      setHistorico,
      setPrescricoes,
      setProtocolos,
      setTabLoading,
    ],
  );

  const loadHistoricoExtras = useCallback(
    async (patientId: number) => {
      const [anam, presc] = await Promise.all([
        ClinicaBelezaAPI.anamnese.get(patientId).catch(() => EMPTY_ANAMNESE),
        ClinicaBelezaAPI.memed.listarPrescricoesPaciente(patientId).catch(() => []),
      ]);
      const anamMerged = mergeAnamnese(anam as Partial<Anamnese> | null | undefined);
      setAnamnese(anamMerged);
      setAnamneseDraft(anamMerged);
      setPrescricoes(Array.isArray(presc) ? presc : []);
    },
    [setAnamnese, setAnamneseDraft, setPrescricoes],
  );

  return { loadTabData, loadHistoricoExtras };
}
