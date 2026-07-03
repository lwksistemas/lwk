import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { CategoriaDespesa, DespesaFormState, DespesaItem } from "./despesa-form-modal-types";
import {
  buildDespesaPayload,
  despesaItemToForm,
  emptyDespesaForm,
  extractDespesaSaveError,
  validateDespesaForm,
} from "./despesa-form-modal-types";

interface UseDespesaFormModalParams {
  open: boolean;
  editing: DespesaItem | null;
  onClose: () => void;
  onSaved: () => void;
}

export function useDespesaFormModal({ open, editing, onClose, onSaved }: UseDespesaFormModalParams) {
  const [form, setForm] = useState<DespesaFormState>(emptyDespesaForm());
  const [categorias, setCategorias] = useState<CategoriaDespesa[]>([]);
  const [erro, setErro] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    ClinicaBelezaAPI.financeiro.despesas
      .categorias()
      .then((data) => setCategorias(Array.isArray(data) ? data : []))
      .catch(() => setCategorias([]));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setForm(editing ? despesaItemToForm(editing) : emptyDespesaForm());
    setErro("");
  }, [open, editing]);

  const salvar = useCallback(async () => {
    const validationError = validateDespesaForm(form);
    if (validationError) {
      setErro(validationError);
      return;
    }
    setErro("");
    setSaving(true);
    try {
      const payload = buildDespesaPayload(form);
      if (editing) {
        await ClinicaBelezaAPI.financeiro.despesas.update(editing.id, payload);
      } else {
        await ClinicaBelezaAPI.financeiro.despesas.create(payload);
      }
      onSaved();
      onClose();
    } catch (e: unknown) {
      setErro(extractDespesaSaveError(e));
    } finally {
      setSaving(false);
    }
  }, [editing, form, onClose, onSaved]);

  return { form, setForm, categorias, erro, saving, salvar };
}
