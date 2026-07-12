import { useEffect, useState } from "react";
import {
  ClinicaBelezaAPI,
  type ConvenioItem,
  type LocalAtendimentoItem,
} from "@/lib/clinica-beleza-api";
import { useOfflineSave } from "@/hooks/clinica-beleza/useOfflineSave";
import { logger } from "@/lib/logger";
import { useToast } from "@/components/ui/Toast";
import {
  buildComissoesSavePayload,
  buildProfissionalSaveBody,
  mapComissoesConsultaFromApi,
  mapComissoesProcedimentoFromApi,
  mapProfissionalFormFromApi,
  validateProfissionalForm,
  type ProfissionalApiRow,
} from "./profissional-form-utils";
import {
  DEFAULT_PROFISSIONAL_FORM,
  type ProfissionalEditing,
  type ProfissionalFormState,
  type ProfissionalProcedure,
} from "./profissional-form-types";
import { useProfissionalComissoes } from "./useProfissionalComissoes";

export function useProfissionalForm(editId: string | null, onDone: () => void) {
  const toast = useToast();
  const [form, setForm] = useState<ProfissionalFormState>(DEFAULT_PROFISSIONAL_FORM);
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [procedures, setProcedures] = useState<ProfissionalProcedure[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!!editId);

  const comissoesState = useProfissionalComissoes(locais);

  const salvarComissoesOnline = async (profId: number) => {
    const payload = buildComissoesSavePayload(
      comissoesState.comissoes,
      comissoesState.comissoesConsultaLocal,
    );
    await ClinicaBelezaAPI.professionals.comissoes.save(profId, payload);
  };

  const { save: offlineSave, saving } = useOfflineSave<ProfissionalEditing>({
    entityType: "profissional",
    saveOnline: async (body, editing) => {
      let profId: number;
      if (editing) {
        await ClinicaBelezaAPI.professionals.update(editing.id, body);
        profId = editing.id;
      } else {
        profId = (await ClinicaBelezaAPI.professionals.create(body) as { id: number }).id;
      }
      await salvarComissoesOnline(profId);
    },
  });

  const setField = (field: keyof ProfissionalFormState, value: string | boolean) => {
    setForm((f) => ({ ...f, [field]: value }));
  };

  useEffect(() => {
    ClinicaBelezaAPI.procedures.list().then((data) => {
      setProcedures(Array.isArray(data) ? (data as ProfissionalProcedure[]) : []);
    }).catch(() => {});
    ClinicaBelezaAPI.locaisAtendimento.list().then((data) => {
      setLocais(Array.isArray(data) ? (data as LocalAtendimentoItem[]) : []);
    }).catch(() => {});
    ClinicaBelezaAPI.convenios.list().then((data) => {
      setConvenios(Array.isArray(data) ? (data as ConvenioItem[]) : []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!editId) return;
    setLoading(true);
    (async () => {
      try {
        const [prof, comissoesData, locaisData] = await Promise.all([
          ClinicaBelezaAPI.professionals.get(Number(editId)),
          ClinicaBelezaAPI.professionals.comissoes.list(Number(editId)).catch(() => []),
          ClinicaBelezaAPI.locaisAtendimento.list().catch(() => []),
        ]);
        const locaisAtivos = Array.isArray(locaisData) ? locaisData : [];
        setLocais(locaisAtivos);
        setForm(mapProfissionalFormFromApi(prof as unknown as ProfissionalApiRow));
        comissoesState.setComissoes(mapComissoesProcedimentoFromApi(comissoesData));
        comissoesState.setComissoesConsultaLocal(
          mapComissoesConsultaFromApi(comissoesData, locaisAtivos),
        );
      } catch (e) {
        logger.warn("Erro ao carregar profissional:", e);
        setError("Erro ao carregar dados do profissional.");
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carrega só ao mudar editId
  }, [editId]);

  const salvar = async () => {
    const validationError = validateProfissionalForm(
      form,
      comissoesState.comissoes,
      comissoesState.comissoesConsultaLocal,
      !!editId,
    );
    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");
    const body = buildProfissionalSaveBody(form, editId);
    const result = await offlineSave(body, editId ? { id: Number(editId) } : null);
    if (!result.ok) {
      if (result.error) setError(result.error);
      return;
    }
    if (result.offline) {
      toast.warning(result.message);
    }
    onDone();
  };

  return {
    form,
    setField,
    locais,
    convenios,
    procedures,
    error,
    loading,
    saving,
    salvar,
    comissoes: comissoesState.comissoes,
    comissoesConsultaLocal: comissoesState.comissoesConsultaLocal,
    addComissao: comissoesState.addComissao,
    addComissaoConsultaLocal: comissoesState.addComissaoConsultaLocal,
    removeComissaoConsultaLocal: comissoesState.removeComissaoConsultaLocal,
    updateComissaoConsultaLocal: comissoesState.updateComissaoConsultaLocal,
    removeComissao: comissoesState.removeComissao,
    updateComissao: comissoesState.updateComissao,
    locaisDisponiveisConsulta: comissoesState.locaisDisponiveisConsulta,
  };
}
