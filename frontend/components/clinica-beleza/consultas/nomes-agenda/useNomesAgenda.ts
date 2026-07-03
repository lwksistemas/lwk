import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI, type NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { extractNomesAgendaError } from "./nomes-agenda-utils";

export function useNomesAgenda(open: boolean) {
  const [nomes, setNomes] = useState<NomeAgendaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formNome, setFormNome] = useState("");
  const [error, setError] = useState("");

  const loadNomes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.nomesAgenda.list();
      setNomes(Array.isArray(data) ? data : []);
    } catch {
      setError("Erro ao carregar nomes de agenda.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      void loadNomes();
      setIsCreating(false);
      setEditingId(null);
      setFormNome("");
      setError("");
    }
  }, [open, loadNomes]);

  const resetForm = () => {
    setFormNome("");
    setEditingId(null);
    setIsCreating(false);
    setError("");
  };

  const startNew = () => {
    setEditingId(null);
    setFormNome("");
    setIsCreating(true);
    setError("");
  };

  const startEdit = (item: NomeAgendaItem) => {
    setIsCreating(false);
    setEditingId(item.id);
    setFormNome(item.nome);
    setError("");
  };

  const handleSave = async () => {
    const nome = formNome.trim();
    if (!nome) {
      setError("O nome da agenda é obrigatório.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (editingId) {
        await ClinicaBelezaAPI.nomesAgenda.update(editingId, { nome });
      } else {
        await ClinicaBelezaAPI.nomesAgenda.create({ nome });
      }
      resetForm();
      await loadNomes();
    } catch (err) {
      setError(extractNomesAgendaError(err, "Erro ao salvar nome de agenda."));
    } finally {
      setSaving(false);
    }
  };

  const handleSetPadrao = async (id: number) => {
    try {
      await ClinicaBelezaAPI.nomesAgenda.update(id, { is_padrao: true });
      await loadNomes();
    } catch (err) {
      setError(extractNomesAgendaError(err, "Erro ao definir padrão."));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Deseja excluir este nome de agenda?")) return;
    try {
      await ClinicaBelezaAPI.nomesAgenda.delete(id);
      if (editingId === id) resetForm();
      await loadNomes();
    } catch (err) {
      setError(extractNomesAgendaError(err, "Erro ao excluir."));
    }
  };

  const formBusy = isCreating || editingId !== null;
  const showForm = isCreating || editingId !== null;

  return {
    nomes,
    loading,
    saving,
    editingId,
    isCreating,
    formNome,
    error,
    formBusy,
    showForm,
    setFormNome,
    resetForm,
    startNew,
    startEdit,
    handleSave,
    handleSetPadrao,
    handleDelete,
  };
}
