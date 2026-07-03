import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { HorarioTrabalhoItem } from "./horarios-trabalho-modal-utils";
import {
  buildHorariosSavePayload,
  createDefaultHorarioRows,
  mergeHorariosFromApi,
} from "./horarios-trabalho-modal-utils";

export function useHorariosTrabalhoModal(professionalId: number, onClose: () => void, onSaved?: () => void) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [rows, setRows] = useState(createDefaultHorarioRows);

  useEffect(() => {
    const fetchHorarios = async () => {
      setLoading(true);
      setError("");
      try {
        const data = (await ClinicaBelezaAPI.professionals.horarios.get(professionalId)) as HorarioTrabalhoItem[];
        setRows(mergeHorariosFromApi(data));
      } catch {
        setError("Não foi possível carregar os horários.");
      } finally {
        setLoading(false);
      }
    };
    void fetchHorarios();
  }, [professionalId]);

  const updateRow = useCallback((dia: number, field: keyof HorarioTrabalhoItem, value: unknown) => {
    setRows((prev) => ({
      ...prev,
      [dia]: { ...prev[dia], [field]: value },
    }));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setError("");
    try {
      await ClinicaBelezaAPI.professionals.horarios.save(professionalId, buildHorariosSavePayload(rows));
      onSaved?.();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar horários.");
    } finally {
      setSaving(false);
    }
  }, [onClose, onSaved, professionalId, rows]);

  return { loading, saving, error, rows, updateRow, handleSave };
}
