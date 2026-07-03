import { useEffect, useState } from "react";
import {
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
} from "@/hooks/clinica-beleza";
import { useToast } from "@/components/ui/Toast";
import {
  buildCampanhaSaveBody,
  campanhaToForm,
  extractCampanhaSaveError,
  validateCampanhaForm,
} from "./campanhas-page-utils";
import {
  EMPTY_CAMPANHA_FORM,
  type Campanha,
  type CampanhaFormState,
} from "./campanhas-page-types";

interface UseCampanhasFormParams {
  isNovo: boolean;
  editIdParam: string | null;
  editId: number | null;
  list: Campanha[];
  voltarLista: () => void;
  load: () => void;
}

export function useCampanhasForm({
  isNovo,
  editIdParam,
  editId,
  list,
  voltarLista,
  load,
}: UseCampanhasFormParams) {
  const toast = useToast();
  const [editing, setEditing] = useState<Campanha | null>(null);
  const [form, setForm] = useState<CampanhaFormState>(EMPTY_CAMPANHA_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isNovo) {
      setEditing(null);
      setForm(EMPTY_CAMPANHA_FORM);
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const c = list.find((x) => String(x.id) === editIdParam);
      if (c) {
        setEditing(c);
        setForm(campanhaToForm(c));
        setError("");
      }
    }
  }, [isNovo, editIdParam, list]);

  const save = async () => {
    const validationError = validateCampanhaForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError("");
    try {
      const body = buildCampanhaSaveBody(form);
      if (editing) {
        await saveClinicaBelezaEntity(`/campanhas/${editing.id}/`, "PUT", body);
        toast.success("Campanha atualizada.");
      } else {
        await saveClinicaBelezaEntity("/campanhas/", "POST", body);
        toast.success("Campanha criada.");
      }
      voltarLista();
      load();
    } catch (e: unknown) {
      const msg = extractCampanhaSaveError(e, "Erro ao salvar");
      if (msg === "SESSION_ENDED") return;
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return {
    editing,
    form,
    setForm,
    saving,
    error,
    save,
    editId,
  };
}

interface UseCampanhasExclusaoParams {
  editId: number | null;
  voltarLista: () => void;
  load: () => void;
}

export function useCampanhasExclusao({ editId, voltarLista, load }: UseCampanhasExclusaoParams) {
  const toast = useToast();
  const [excluirCampanha, setExcluirCampanha] = useState<Campanha | null>(null);
  const [excluindo, setExcluindo] = useState(false);

  const confirmarExclusao = async () => {
    const c = excluirCampanha;
    if (!c) return;
    setExcluindo(true);
    try {
      await deleteClinicaBelezaEntity(`/campanhas/${c.id}/`, "Erro ao excluir.");
      toast.success("Campanha excluída.");
      if (editId === c.id) voltarLista();
      setExcluirCampanha(null);
      load();
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      toast.error("Erro ao excluir campanha.");
    } finally {
      setExcluindo(false);
    }
  };

  return {
    excluirCampanha,
    setExcluirCampanha,
    excluindo,
    confirmarExclusao,
  };
}
