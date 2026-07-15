'use client';

import { useCallback, useEffect, useState } from 'react';
import { X } from 'lucide-react';
import {
  DIAS_SEMANA,
  buildHorariosSavePayload,
  createDefaultHorarioRows,
  mergeHorariosFromApi,
  type HorarioTrabalhoItem,
} from '@/components/clinica-beleza/horarios-trabalho-modal/horarios-trabalho-modal-utils';
import { CabeleireiroAPI } from '@/lib/cabeleireiro-api';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

type Props = {
  profissionalId: number;
  profissionalNome: string;
  onClose: () => void;
  onSaved?: () => void;
};

export function ModalHorariosSalao({ profissionalId, profissionalNome, onClose, onSaved }: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState(createDefaultHorarioRows);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await CabeleireiroAPI.profissionais.horarios.get(profissionalId);
        setRows(mergeHorariosFromApi(data as HorarioTrabalhoItem[]));
      } catch {
        setError('Não foi possível carregar os horários.');
      } finally {
        setLoading(false);
      }
    })();
  }, [profissionalId]);

  const updateRow = useCallback((dia: number, field: keyof HorarioTrabalhoItem, value: unknown) => {
    setRows((prev) => ({
      ...prev,
      [dia]: { ...prev[dia], [field]: value },
    }));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await CabeleireiroAPI.profissionais.horarios.save(
        profissionalId,
        buildHorariosSavePayload(rows) as Record<string, unknown>[],
      );
      onSaved?.();
      onClose();
    } catch {
      setError('Erro ao salvar horários.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col border border-[#E8D5DC]">
        <div className="flex justify-between items-center p-4 border-b border-[#E8D5DC] shrink-0">
          <h2 className="text-lg font-bold text-gray-900">Horários de trabalho — {profissionalNome}</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 rounded" aria-label="Fechar">
            <X size={20} />
          </button>
        </div>
        <div className="p-4 overflow-y-auto flex-1 min-h-0">
          {error && <div className="mb-4 p-2 rounded bg-red-50 text-red-700 text-sm">{error}</div>}
          {loading ? (
            <div className="flex items-center justify-center py-12 text-sm text-gray-500">Carregando...</div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Marque os dias em que o profissional trabalha e defina entrada, saída e intervalo (ex.: almoço).
              </p>
              <div className="space-y-3">
                {DIAS_SEMANA.map((d) => (
                  <div key={d.value} className="flex flex-wrap items-center gap-2 p-3 rounded-lg bg-[#FBF5F7]">
                    <label className="flex items-center gap-2 w-full sm:w-40 shrink-0">
                      <input
                        type="checkbox"
                        checked={rows[d.value].ativo}
                        onChange={(e) => updateRow(d.value, 'ativo', e.target.checked)}
                        className="rounded border-gray-300"
                        style={{ accentColor: SALAO_PRIMARY }}
                      />
                      <span className="text-sm font-medium text-gray-800">{d.label}</span>
                    </label>
                    <div className="flex flex-wrap items-center gap-2 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500">Entrada</span>
                        <input
                          type="time"
                          value={rows[d.value].hora_entrada}
                          onChange={(e) => updateRow(d.value, 'hora_entrada', e.target.value)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border rounded bg-white text-sm disabled:opacity-50"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500">Saída</span>
                        <input
                          type="time"
                          value={rows[d.value].hora_saida}
                          onChange={(e) => updateRow(d.value, 'hora_saida', e.target.value)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border rounded bg-white text-sm disabled:opacity-50"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500">Intervalo</span>
                        <input
                          type="time"
                          value={rows[d.value].intervalo_inicio || ''}
                          onChange={(e) => updateRow(d.value, 'intervalo_inicio', e.target.value || null)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border rounded bg-white text-sm disabled:opacity-50"
                        />
                        <span className="text-xs text-gray-400">–</span>
                        <input
                          type="time"
                          value={rows[d.value].intervalo_fim || ''}
                          onChange={(e) => updateRow(d.value, 'intervalo_fim', e.target.value || null)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border rounded bg-white text-sm disabled:opacity-50"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
        <div className="p-4 border-t border-[#E8D5DC] flex justify-end gap-2 shrink-0">
          <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg text-sm">
            Cancelar
          </button>
          <button
            type="button"
            disabled={saving || loading}
            onClick={() => void handleSave()}
            className="px-4 py-2 rounded-lg text-sm text-white disabled:opacity-60"
            style={{ backgroundColor: SALAO_PRIMARY }}
          >
            {saving ? 'Salvando...' : 'Salvar horários'}
          </button>
        </div>
      </div>
    </div>
  );
}
