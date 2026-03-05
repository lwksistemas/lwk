'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export interface ConfigBackup {
  id: number;
  backup_automatico_ativo: boolean;
  horario_envio: string;
  frequencia: 'diario' | 'semanal' | 'mensal';
  dia_semana: number | null;
  dia_mes: number | null;
  incluir_imagens: boolean;
  manter_ultimos_n_backups: number;
  ultimo_backup: string | null;
  total_backups_realizados: number;
}

const DIAS_SEMANA = [
  { value: 0, label: 'Segunda' },
  { value: 1, label: 'Terça' },
  { value: 2, label: 'Quarta' },
  { value: 3, label: 'Quinta' },
  { value: 4, label: 'Sexta' },
  { value: 5, label: 'Sábado' },
  { value: 6, label: 'Domingo' },
];

interface BackupConfigModalProps {
  open: boolean;
  onClose: () => void;
  lojaId: number;
  addToast: (t: { tipo: string; titulo: string; mensagem: string }) => void;
}

export default function BackupConfigModal({ open, onClose, lojaId, addToast }: BackupConfigModalProps) {
  const [config, setConfig] = useState<ConfigBackup | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !lojaId) return;
    let cancelled = false;
    setLoading(true);
    apiClient
      .get(`/superadmin/lojas/${lojaId}/configuracao_backup/`)
      .then((res) => {
        if (!cancelled && res.data?.success && res.data?.config) setConfig(res.data.config);
      })
      .catch(() => {
        if (!cancelled) addToast({ tipo: 'erro', titulo: 'Erro', mensagem: 'Não foi possível carregar a configuração.' });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [open, lojaId, addToast]);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const horario = config.horario_envio?.slice(0, 5) || '03:00';
      const payload = {
        backup_automatico_ativo: config.backup_automatico_ativo,
        horario_envio: horario.length === 5 ? `${horario}:00` : '03:00:00',
        frequencia: config.frequencia,
        dia_semana: config.frequencia === 'semanal' ? (config.dia_semana ?? 0) : null,
        dia_mes: config.frequencia === 'mensal' ? (config.dia_mes ?? 1) : null,
        incluir_imagens: config.incluir_imagens,
        manter_ultimos_n_backups: Math.min(30, Math.max(1, config.manter_ultimos_n_backups)),
      };
      const res = await apiClient.patch(`/superadmin/lojas/${lojaId}/atualizar_configuracao_backup/`, payload);
      if (res.data?.success) {
        setConfig(res.data.config);
        addToast({ tipo: 'sucesso', titulo: 'Backup', mensagem: 'Configuração salva com sucesso!' });
      } else {
        addToast({
          tipo: 'erro',
          titulo: 'Erro',
          mensagem: res.data?.errors ? Object.values(res.data.errors).flat().join(' ') : 'Erro ao salvar.',
        });
      }
    } catch (e: any) {
      const msg = e.response?.data?.errors
        ? Object.values(e.response.data.errors).flat().join(' ')
        : 'Erro ao salvar configuração.';
      addToast({ tipo: 'erro', titulo: 'Erro', mensagem: msg });
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Configurar backup automático</h3>
            <button type="button" onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              ✕
            </button>
          </div>
          <div className="p-4 space-y-4">
            {loading ? (
              <p className="text-sm text-gray-500">Carregando...</p>
            ) : config ? (
              <>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.backup_automatico_ativo}
                    onChange={(e) => setConfig((c) => (c ? { ...c, backup_automatico_ativo: e.target.checked } : c))}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Ativar backup automático</span>
                </label>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Horário</label>
                  <input
                    type="time"
                    value={config.horario_envio?.slice(0, 5) || '03:00'}
                    onChange={(e) => setConfig((c) => (c ? { ...c, horario_envio: e.target.value + ':00' } : c))}
                    className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-2 py-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Frequência</label>
                  <select
                    value={config.frequencia}
                    onChange={(e) => setConfig((c) => (c ? { ...c, frequencia: e.target.value as ConfigBackup['frequencia'] } : c))}
                    className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-2 py-1"
                  >
                    <option value="diario">Diário</option>
                    <option value="semanal">Semanal</option>
                    <option value="mensal">Mensal</option>
                  </select>
                </div>
                {config.frequencia === 'semanal' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dia da semana</label>
                    <select
                      value={config.dia_semana ?? 0}
                      onChange={(e) => setConfig((c) => (c ? { ...c, dia_semana: parseInt(e.target.value, 10) } : c))}
                      className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-2 py-1"
                    >
                      {DIAS_SEMANA.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                )}
                {config.frequencia === 'mensal' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dia do mês (1-28)</label>
                    <input
                      type="number"
                      min={1}
                      max={28}
                      value={config.dia_mes ?? 1}
                      onChange={(e) => setConfig((c) => (c ? { ...c, dia_mes: parseInt(e.target.value, 10) || 1 } : c))}
                      className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-2 py-1"
                    />
                  </div>
                )}
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.incluir_imagens}
                    onChange={(e) => setConfig((c) => (c ? { ...c, incluir_imagens: e.target.checked } : c))}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Incluir imagens (aumenta o tamanho)</span>
                </label>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manter últimos N backups</label>
                  <input
                    type="number"
                    min={1}
                    max={30}
                    value={config.manter_ultimos_n_backups}
                    onChange={(e) => setConfig((c) => (c ? { ...c, manter_ultimos_n_backups: parseInt(e.target.value, 10) || 1 } : c))}
                    className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-2 py-1"
                  />
                </div>
                <p className="text-xs text-gray-500">
                  Total de backups realizados: {config.total_backups_realizados}
                  {config.ultimo_backup && ` • Último: ${new Date(config.ultimo_backup).toLocaleString('pt-BR')}`}
                </p>
              </>
            ) : (
              <p className="text-sm text-gray-500">Não foi possível carregar a configuração.</p>
            )}
          </div>
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
            >
              Fechar
            </button>
            {config && (
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="px-3 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
