import { useEffect, useState } from "react";
import {
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
} from "@/hooks/clinica-beleza";
import { useToast } from "@/components/ui/Toast";
import {
  buildProtocoloSaveBody,
  extractProtocoloSaveError,
  protocolToForm,
  validateProtocoloForm,
} from "./protocolos-page-utils";
import {
  EMPTY_PROTOCOLO_FORM,
  type Protocol,
  type ProtocoloFormState,
} from "./protocolos-page-types";

interface UseProtocolosFormParams {
  isFormView: boolean;
  isNovo: boolean;
  editIdParam: string | null;
  list: Protocol[];
  voltarLista: () => void;
  load: () => void;
}

export function useProtocolosForm({
  isFormView,
  isNovo,
  editIdParam,
  list,
  voltarLista,
  load,
}: UseProtocolosFormParams) {
  const toast = useToast();
  const [editing, setEditing] = useState<Protocol | null>(null);
  const [form, setForm] = useState<ProtocoloFormState>(EMPTY_PROTOCOLO_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isFormView) return;
    if (isNovo) {
      setEditing(null);
      setForm(EMPTY_PROTOCOLO_FORM);
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const p = list.find((x) => String(x.id) === editIdParam);
      if (p) {
        setEditing(p);
        setForm(protocolToForm(p));
        setError("");
      }
    }
  }, [isFormView, isNovo, editIdParam, list]);

  const save = async () => {
    const validationError = validateProtocoloForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError("");
    const body = buildProtocoloSaveBody(form);
    try {
      if (editing) {
        await saveClinicaBelezaEntity(`/protocolos/${editing.id}/`, "PUT", body);
      } else {
        await saveClinicaBelezaEntity("/protocolos/", "POST", body);
      }
      voltarLista();
      load();
    } catch (e: unknown) {
      const msg = extractProtocoloSaveError(e);
      if (msg === "SESSION_ENDED") return;
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const exclude = async (p: Protocol) => {
    if (!confirm(`Desativar o protocolo "${p.nome}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/protocolos/${p.id}/`);
      load();
    } catch {
      toast.error("Erro ao desativar.");
    }
  };

  return {
    editing,
    form,
    setForm,
    saving,
    error,
    save,
    exclude,
  };
}
