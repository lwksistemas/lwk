import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { TemplateFormState } from "./template-form-page-types";
import {
  buildTemplatesListPath,
  extractTemplateLoadError,
  extractTemplateSaveError,
  parseTemplateEditId,
  validateTemplateForm,
} from "./template-form-page-utils";

const emptyForm: TemplateFormState = { nome: "", tipo: "receituario", conteudo: "" };

export function useTemplateFormPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const editIdParam = searchParams.get("id");
  const editId = parseTemplateEditId(editIdParam);
  const isEditing = editId !== null;

  const [form, setForm] = useState<TemplateFormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (editId === null) return;
    setLoading(true);
    setError("");
    ClinicaBelezaAPI.templates
      .get(editId)
      .then((template) => {
        setForm({
          nome: template.nome || "",
          tipo: template.tipo || "receituario",
          conteudo: template.conteudo || "",
        });
      })
      .catch((e: { detail?: string; message?: string }) => setError(extractTemplateLoadError(e)))
      .finally(() => setLoading(false));
  }, [editId]);

  const set = useCallback((field: keyof TemplateFormState, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
  }, []);

  const voltarLista = useCallback(() => {
    router.push(buildTemplatesListPath(slug));
  }, [router, slug]);

  const inserirPlaceholder = useCallback((tag: string) => {
    setForm((f) => ({ ...f, conteudo: f.conteudo + tag }));
  }, []);

  const salvar = useCallback(async () => {
    const validationError = validateTemplateForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError("");
    try {
      const payload = {
        nome: form.nome.trim(),
        tipo: form.tipo,
        conteudo: form.conteudo,
      };
      if (isEditing && editId !== null) {
        await ClinicaBelezaAPI.templates.update(editId, payload);
      } else {
        await ClinicaBelezaAPI.templates.create(payload);
      }
      voltarLista();
    } catch (e) {
      setError(extractTemplateSaveError(e as Record<string, unknown>));
    } finally {
      setSaving(false);
    }
  }, [editId, form, isEditing, voltarLista]);

  return {
    isEditing,
    form,
    set,
    saving,
    loading,
    error,
    voltarLista,
    salvar,
    inserirPlaceholder,
  };
}
