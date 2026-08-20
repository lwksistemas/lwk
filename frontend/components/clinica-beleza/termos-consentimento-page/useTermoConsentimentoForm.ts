import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaAPI, type TermoConsentimentoSecao, type TermoConsentimentoTipo } from "@/lib/clinica-beleza-api";
import { buildTermoListaPath, novaSecao } from "./termos-consentimento-utils";

export interface TermoFormState {
  nome: string;
  tipo: TermoConsentimentoTipo;
  introducao: string;
  conteudo: string;
  secoes: TermoConsentimentoSecao[];
}

const emptyForm: TermoFormState = {
  nome: "",
  tipo: "interativo",
  introducao: "",
  conteudo: "",
  secoes: [novaSecao()],
};

export function useTermoConsentimentoForm() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const editId = Number(searchParams.get("id") || 0) || null;
  const isEditing = editId !== null;

  const [form, setForm] = useState<TermoFormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!editId) return;
    setLoading(true);
    ClinicaBelezaAPI.termosConsentimento
      .get(editId)
      .then((t) => {
        setForm({
          nome: t.nome || "",
          tipo: t.tipo === "simples" ? "simples" : "interativo",
          introducao: t.introducao || "",
          conteudo: t.conteudo || "",
          secoes: t.secoes?.length ? t.secoes : [novaSecao()],
        });
      })
      .catch(() => setError("Não foi possível carregar o termo."))
      .finally(() => setLoading(false));
  }, [editId]);

  const set = useCallback(<K extends keyof TermoFormState>(field: K, value: TermoFormState[K]) => {
    setForm((f) => ({ ...f, [field]: value }));
  }, []);

  const patchSecao = useCallback((idx: number, patch: Partial<TermoConsentimentoSecao>) => {
    setForm((f) => ({
      ...f,
      secoes: f.secoes.map((s, i) => (i === idx ? { ...s, ...patch } : s)),
    }));
  }, []);

  const addSecao = useCallback(() => {
    setForm((f) => ({ ...f, secoes: [...f.secoes, novaSecao()] }));
  }, []);

  const removeSecao = useCallback((idx: number) => {
    setForm((f) => ({ ...f, secoes: f.secoes.filter((_, i) => i !== idx) }));
  }, []);

  const voltarLista = useCallback(() => {
    router.push(buildTermoListaPath(slug));
  }, [router, slug]);

  const salvar = useCallback(async () => {
    if (!form.nome.trim()) {
      setError("Informe o nome do termo.");
      return;
    }
    setSaving(true);
    setError("");
    const payload = {
      nome: form.nome.trim(),
      tipo: form.tipo,
      introducao: form.introducao,
      conteudo: form.conteudo,
      secoes: form.tipo === "interativo" ? form.secoes : [],
      is_active: true,
    };
    try {
      if (isEditing && editId) {
        await ClinicaBelezaAPI.termosConsentimento.update(editId, payload);
      } else {
        await ClinicaBelezaAPI.termosConsentimento.create(payload);
      }
      voltarLista();
    } catch {
      setError("Não foi possível salvar. Verifique os campos e tente de novo.");
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
    patchSecao,
    addSecao,
    removeSecao,
  };
}
