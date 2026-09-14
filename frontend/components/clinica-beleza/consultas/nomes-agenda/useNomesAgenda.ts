import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI, type NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { isTipoAgendaSistema } from "@/lib/clinica-beleza-tipo-agenda";
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
      setError("Erro ao carregar tipos de agenda.");
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
      setError("O tipo de agenda é obrigatório.");
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
      setError(extractNomesAgendaError(err, "Erro ao salvar tipo de agenda."));
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
    const item = nomes.find((n) => n.id === id);
    if (item && isTipoAgendaSistema(item.nome)) {
      setError("Consulta e Retorno são tipos padrão do sistema e não podem ser removidos.");
      return;
    }
    if (!confirm("Deseja excluir este tipo de agenda?")) return;
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
