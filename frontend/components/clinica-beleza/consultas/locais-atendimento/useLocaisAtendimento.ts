import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import {
  extractLocaisAtendimentoError,
  parseValorInput,
  valorToInput,
} from "./locais-atendimento-utils";

export function useLocaisAtendimento(open: boolean) {
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formNome, setFormNome] = useState("");
  const [formValor, setFormValor] = useState("");
  const [error, setError] = useState("");

  const loadLocais = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.locaisAtendimento.list();
      setLocais(Array.isArray(data) ? data : []);
    } catch {
      setError("Erro ao carregar locais de atendimento.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      void loadLocais();
      setIsCreating(false);
      setEditingId(null);
      setFormNome("");
      setFormValor("");
      setError("");
    }
  }, [open, loadLocais]);

  const resetForm = () => {
    setFormNome("");
    setFormValor("");
    setEditingId(null);
    setIsCreating(false);
    setError("");
  };

  const startEdit = (local: LocalAtendimentoItem) => {
    setIsCreating(false);
    setEditingId(local.id);
    setFormNome(local.nome);
    setFormValor(valorToInput(local.valor_consulta));
    setError("");
  };

  const startNew = () => {
    setEditingId(null);
    setFormNome("");
    setFormValor("");
    setIsCreating(true);
    setError("");
  };

  const handleSave = async () => {
    const nome = formNome.trim();
    const valor = parseValorInput(formValor);

    if (!nome) {
      setError("O nome do local é obrigatório.");
      return;
    }
    if (!Number.isFinite(valor) || valor < 0) {
      setError("O valor deve ser um número maior ou igual a zero.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      const payload = { nome, valor_consulta: valor };
      if (editingId) {
        await ClinicaBelezaAPI.locaisAtendimento.update(editingId, payload);
      } else {
        await ClinicaBelezaAPI.locaisAtendimento.create(payload);
      }
      resetForm();
      await loadLocais();
    } catch (err) {
      setError(extractLocaisAtendimentoError(err, "Erro ao salvar local de atendimento."));
    } finally {
      setSaving(false);
    }
  };

  const handleSetPadrao = async (id: number) => {
    try {
      await ClinicaBelezaAPI.locaisAtendimento.update(id, { is_padrao: true });
      await loadLocais();
    } catch (err) {
      setError(extractLocaisAtendimentoError(err, "Erro ao definir padrão."));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Deseja realmente excluir este local de atendimento?")) return;
    try {
      await ClinicaBelezaAPI.locaisAtendimento.delete(id);
      if (editingId === id) resetForm();
      await loadLocais();
    } catch (err) {
      setError(extractLocaisAtendimentoError(err, "Erro ao excluir local de atendimento."));
    }
  };

  const formBusy = isCreating || editingId !== null;

  return {
    locais,
    loading,
    saving,
    editingId,
    isCreating,
    formNome,
    formValor,
    error,
    formBusy,
    setFormNome,
    setFormValor,
    resetForm,
    startEdit,
    startNew,
    handleSave,
    handleSetPadrao,
    handleDelete,
  };
}
