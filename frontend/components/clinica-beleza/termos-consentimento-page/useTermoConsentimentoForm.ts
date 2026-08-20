import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaAPI, type TermoConsentimentoSecao, type TermoConsentimentoTipo } from "@/lib/clinica-beleza-api";
import { buildTermoListaPath, novaSecao } from "./termos-consentimento-utils";

export interface ProcedimentoOpcaoTermo {
  id: number;
  nome: string;
  termo_template?: number | null;
}

export interface TermoFormState {
  nome: string;
  tipo: TermoConsentimentoTipo;
  introducao: string;
  conteudo: string;
  secoes: TermoConsentimentoSecao[];
  procedimentoId: number | null;
}

const emptyForm: TermoFormState = {
  nome: "",
  tipo: "interativo",
  introducao: "",
  conteudo: "",
  secoes: [novaSecao()],
  procedimentoId: null,
};

function mensagemErroApi(err: unknown): string {
  if (!err || typeof err !== "object") {
    return "Não foi possível salvar. Verifique os campos e tente de novo.";
  }
  const data = err as Record<string, unknown>;
  const primeiro = data.procedimento_id;
  if (Array.isArray(primeiro) && primeiro[0]) return String(primeiro[0]);
  if (typeof primeiro === "string") return primeiro;
  if (typeof data.error === "string") return data.error;
  return "Não foi possível salvar. Verifique os campos e tente de novo.";
}

export function useTermoConsentimentoForm() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const editId = Number(searchParams.get("id") || 0) || null;
  const isEditing = editId !== null;

  const [form, setForm] = useState<TermoFormState>(emptyForm);
  const [procedimentos, setProcedimentos] = useState<ProcedimentoOpcaoTermo[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    ClinicaBelezaAPI.procedures
      .list({ active: true, all: 1 })
      .then((res) => {
        const list = (Array.isArray(res) ? res : []) as ProcedimentoOpcaoTermo[];
        setProcedimentos(list.map((p) => ({
          id: p.id,
          nome: p.nome,
          termo_template: p.termo_template ?? null,
        })));
      })
      .catch(() => setProcedimentos([]));
  }, []);

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
          procedimentoId: t.procedimento_id ?? t.procedimentos?.[0]?.id ?? null,
        });
      })
      .catch(() => setError("Não foi possível carregar o termo."))
      .finally(() => setLoading(false));
  }, [editId]);

  const procedimentosDisponiveis = useMemo(
    () => procedimentos.filter((p) => !p.termo_template || p.termo_template === editId || p.id === form.procedimentoId),
    [procedimentos, editId, form.procedimentoId],
  );

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
    if (!form.procedimentoId) {
      setError("Selecione o procedimento deste termo.");
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
      procedimento_id: form.procedimentoId,
    };
    try {
      if (isEditing && editId) {
        await ClinicaBelezaAPI.termosConsentimento.update(editId, payload);
      } else {
        await ClinicaBelezaAPI.termosConsentimento.create(payload);
      }
      voltarLista();
    } catch (err) {
      setError(mensagemErroApi(err));
    } finally {
      setSaving(false);
    }
  }, [editId, form, isEditing, voltarLista]);

  return {
    isEditing,
    form,
    set,
    procedimentosDisponiveis,
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
