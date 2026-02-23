'use client';

/**
 * Modal para configurar dias e horários de atendimento do profissional (Clínica de Estética).
 * GET/PUT /api/clinica/profissionais/<id>/horarios-trabalho/
 */

import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { clinicaApiClient } from '@/lib/api-client';

const DIAS_SEMANA = [
  { value: 0, label: 'Segunda-feira' },
  { value: 1, label: 'Terça-feira' },
  { value: 2, label: 'Quarta-feira' },
  { value: 3, label: 'Quinta-feira' },
  { value: 4, label: 'Sexta-feira' },
  { value: 5, label: 'Sábado' },
  { value: 6, label: 'Domingo' },
];

export interface HorarioTrabalhoItem {
  id?: number;
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string | null;
  intervalo_fim: string | null;
  ativo: boolean;
}

interface ModalHorariosTrabalhoProps {
  profissionalId: number;
  profissionalNome: string;
  onClose: () => void;
  onSaved?: () => void;
  corPrimaria?: string;
}

export function ModalHorariosTrabalho({
  profissionalId,
  profissionalNome,
  onClose,
  onSaved,
  corPrimaria = '#8B5CF6',
}: ModalHorariosTrabalhoProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [rows, setRows] = useState<Record<number, HorarioTrabalhoItem>>(() => {
    const initial: Record<number, HorarioTrabalhoItem> = {};
    DIAS_SEMANA.forEach((d) => {
      initial[d.value] = {
        dia_semana: d.value,
        hora_entrada: '08:00',
        hora_saida: '18:00',
        intervalo_inicio: '12:00',
        intervalo_fim: '13:00',
        ativo: d.value < 5,
      };
    });
    return initial;
  });

  useEffect(() => {
    const fetchHorarios = async () => {
      setLoading(true);
      setError('');
      try {
        const { data } = await clinicaApiClient.get(`/clinica/profissionais/${profissionalId}/horarios-trabalho/`);
        const arr = Array.isArray(data) ? data : [];
        const byDay: Record<number, HorarioTrabalhoItem> = {};
        DIAS_SEMANA.forEach((d) => {
          byDay[d.value] = {
            dia_semana: d.value,
            hora_entrada: '08:00',
            hora_saida: '18:00',
            intervalo_inicio: '12:00',
            intervalo_fim: '13:00',
            ativo: false,
          };
        });
        arr.forEach((h: HorarioTrabalhoItem & { hora_entrada?: string; hora_saida?: string }) => {
          const day = Number(h.dia_semana);
          if (day in byDay) {
            byDay[day] = {
              id: h.id,
              dia_semana: day,
              hora_entrada: typeof h.hora_entrada === 'string' ? h.hora_entrada.slice(0, 5) : '08:00',
              hora_saida: typeof h.hora_saida === 'string' ? h.hora_saida.slice(0, 5) : '18:00',
              intervalo_inicio: h.intervalo_inicio ? String(h.intervalo_inicio).slice(0, 5) : null,
              intervalo_fim: h.intervalo_fim ? String(h.intervalo_fim).slice(0, 5) : null,
              ativo: (h as HorarioTrabalhoItem).ativo !== false,
            };
          }
        });
        setRows(byDay);
      } catch {
        setError('Não foi possível carregar os horários.');
      } finally {
        setLoading(false);
      }
    };
    fetchHorarios();
  }, [profissionalId]);

  const updateRow = (dia: number, field: keyof HorarioTrabalhoItem, value: unknown) => {
    setRows((prev) => ({
      ...prev,
      [dia]: { ...prev[dia], [field]: value },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const payload = DIAS_SEMANA.filter((d) => rows[d.value].ativo).map((d) => {
        const r = rows[d.value];
        return {
          dia_semana: r.dia_semana,
          hora_entrada: r.hora_entrada,
          hora_saida: r.hora_saida,
          intervalo_inicio: r.intervalo_inicio || null,
          intervalo_fim: r.intervalo_fim || null,
          ativo: true,
        };
      });
      await clinicaApiClient.put(`/clinica/profissionais/${profissionalId}/horarios-trabalho/`, payload);
      onSaved?.();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao salvar horários.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col border border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Horários de atendimento — {profissionalNome}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1 min-h-0">
          {error && (
            <div className="mb-4 p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: corPrimaria }} />
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Marque os dias em que o profissional atende e defina entrada, saída e intervalo (ex.: almoço). Esses horários aparecem no calendário.
              </p>
              <div className="space-y-3">
                {DIAS_SEMANA.map((d) => (
                  <div
                    key={d.value}
                    className="flex flex-wrap items-center gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                  >
                    <label className="flex items-center gap-2 w-full sm:w-40 shrink-0">
                      <input
                        type="checkbox"
                        checked={rows[d.value].ativo}
                        onChange={(e) => updateRow(d.value, 'ativo', e.target.checked)}
                        className="rounded border-gray-300 dark:border-gray-600"
                        style={{ accentColor: corPrimaria }}
                      />
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{d.label}</span>
                    </label>
                    <div className="flex flex-wrap items-center gap-2 flex-1">
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Entrada</span>
                        <input
                          type="time"
                          value={rows[d.value].hora_entrada}
                          onChange={(e) => updateRow(d.value, 'hora_entrada', e.target.value)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Saída</span>
                        <input
                          type="time"
                          value={rows[d.value].hora_saida}
                          onChange={(e) => updateRow(d.value, 'hora_saida', e.target.value)}
                          disabled={!rows[d.value].ativo}
                          className="px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                        />
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Intervalo</span>
                        <input
                          type="time"
                          value={rows[d.value].intervalo_inicio ?? ''}
                          onChange={(e) => updateRow(d.value, 'intervalo_inicio', e.target.value || null)}
                          disabled={!rows[d.value].ativo}
                          className="w-20 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                          placeholder="Início"
                        />
                        <span className="text-gray-400">–</span>
                        <input
                          type="time"
                          value={rows[d.value].intervalo_fim ?? ''}
                          onChange={(e) => updateRow(d.value, 'intervalo_fim', e.target.value || null)}
                          disabled={!rows[d.value].ativo}
                          className="w-20 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm disabled:opacity-50"
                          placeholder="Fim"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex gap-2 p-4 border-t border-gray-200 dark:border-gray-700 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="flex-1 py-2 rounded-lg text-white hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: corPrimaria }}
          >
            {saving ? 'Salvando...' : 'Salvar horários'}
          </button>
        </div>
      </div>
    </div>
  );
}
