import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import {
  ClinicaBelezaAPI,
  type ConvenioItem,
  type ProcedureConvenioPrecoItem,
} from "@/lib/clinica-beleza-api";
import {
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
} from "@/hooks/clinica-beleza";
import { isBrowserOffline } from "@/lib/clinica-beleza-offline";
import { salvarProcedimentosOffline } from "@/lib/offline-db";
import { entityName } from "@/lib/clinica-beleza-entities";
import { useOfflineSave } from "@/hooks/clinica-beleza/useOfflineSave";
import { logger } from "@/lib/logger";
import {
  buildPrecosConvenioPayload,
  buildProcedimentoSaveBody,
  mapPrecosConvenioFromApi,
  validateProcedimentoForm,
} from "./procedimentos-page-utils";
import {
  EMPTY_PROCEDIMENTO_FORM,
  procedureToForm,
  type Procedure,
  type ProcedimentoFormState,
} from "./procedimentos-page-types";

interface UseProcedimentosFormParams {
  isFormView: boolean;
  isNovo: boolean;
  editIdParam: string | null;
  list: Procedure[];
  presetCategoria: string;
  defaultCategoria: string;
  convenios: ConvenioItem[];
  setList: Dispatch<SetStateAction<Procedure[]>>;
  voltarLista: () => void;
  load: () => void;
  carregarMatrix: () => Promise<void>;
}

export function useProcedimentosForm({
  isFormView,
  isNovo,
  editIdParam,
  list,
  presetCategoria,
  defaultCategoria,
  convenios,
  setList,
  voltarLista,
  load,
  carregarMatrix,
}: UseProcedimentosFormParams) {
  const [editing, setEditing] = useState<Procedure | null>(null);
  const [form, setForm] = useState<ProcedimentoFormState>(EMPTY_PROCEDIMENTO_FORM);
  const [precosConvenio, setPrecosConvenio] = useState<Record<number, string>>({});
  const [error, setError] = useState("");

  const { save: offlineSave, saving } = useOfflineSave<Procedure>({
    entityType: "procedimento",
    saveOnline: async (body, ed) => {
      let procedureId: number;
      if (ed) {
        await saveClinicaBelezaEntity(`/procedures/${ed.id}/`, "PUT", body);
        procedureId = ed.id;
      } else {
        const created = await saveClinicaBelezaEntity("/procedures/", "POST", body) as { id?: number };
        procedureId = created?.id ?? 0;
      }
      if (procedureId > 0 && convenios.length > 0) {
        await ClinicaBelezaAPI.procedures.savePrecosConvenio(
          procedureId,
          buildPrecosConvenioPayload(convenios, precosConvenio),
        );
      }
    },
    list,
    setList,
    saveOffline: salvarProcedimentosOffline,
    buildNewEntity: (body, tempId) => ({
      id: tempId,
      name: body.name as string,
      description: body.description as string | null,
      price: "0",
      duration: body.duration as number,
      categoria: body.category as string,
      active: true,
    }),
    duplicatePredicate: (p) =>
      entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
    offlineMessage: "Salvo offline. O procedimento será sincronizado quando você estiver online.",
  });

  useEffect(() => {
    if (defaultCategoria && isNovo) {
      setForm((f) => ({ ...f, categoria: defaultCategoria }));
    }
  }, [defaultCategoria, isNovo]);

  useEffect(() => {
    if (!isFormView) return;
    if (isNovo) {
      setEditing(null);
      setForm({ ...EMPTY_PROCEDIMENTO_FORM, categoria: presetCategoria });
      setPrecosConvenio({});
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const p = list.find((x) => String(x.id) === editIdParam);
      if (p) {
        setEditing(p);
        setForm(procedureToForm(p));
        setError("");
        if (!isBrowserOffline() && p.id > 0) {
          ClinicaBelezaAPI.procedures.precosConvenio(p.id)
            .then((rows: ProcedureConvenioPrecoItem[]) => {
              setPrecosConvenio(mapPrecosConvenioFromApi(rows));
            })
            .catch((e) => logger.warn("Erro ao carregar preços do procedimento:", e));
        }
      }
    }
  }, [isFormView, isNovo, editIdParam, list, presetCategoria]);

  const save = async () => {
    const validationError = validateProcedimentoForm(form, convenios, precosConvenio, presetCategoria);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    const body = buildProcedimentoSaveBody(form, presetCategoria);
    const result = await offlineSave(body, editing);
    if (!result.ok) {
      if (result.error) setError(result.error);
      return;
    }
    if (result.offline) {
      voltarLista();
      alert(result.message);
      return;
    }
    voltarLista();
    load();
    void carregarMatrix();
  };

  const exclude = async (p: Procedure) => {
    if (!confirm(`Desativar o procedimento "${entityName(p)}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/procedures/${p.id}/`);
      load();
      void carregarMatrix();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  return {
    editing,
    form,
    setForm,
    precosConvenio,
    setPrecosConvenio,
    error,
    saving,
    save,
    exclude,
  };
}
