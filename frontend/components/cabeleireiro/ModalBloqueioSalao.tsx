'use client';

import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import {
  TIPOS_BLOQUEIO,
  MODOS_BLOQUEIO_INTERVALO,
  buildBloqueioRequestBody,
  extractBloqueioApiError,
  resolveMotivoBloqueio,
  validateBloqueioForm,
  type ModoBloqueioIntervalo,
} from '@/components/clinica-beleza/modal-bloqueio-horario/modal-bloqueio-horario-utils';
import { CabeleireiroAPI, type SalaoProfissional } from '@/lib/cabeleireiro-api';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  profissionais: SalaoProfissional[];
  dataSugerida?: string;
};

const fieldClass =
  'w-full px-3 py-2.5 border border-[#E8D5DC] rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-[#4A3042]/30';

export function ModalBloqueioSalao({
  isOpen,
  onClose,
  onSuccess,
  profissionais,
  dataSugerida,
}: Props) {
  const hoje = dataSugerida || new Date().toISOString().slice(0, 10);
  const [modo, setModo] = useState<ModoBloqueioIntervalo>('horario');
  const [tipo, setTipo] = useState<string>(TIPOS_BLOQUEIO[0].value);
  const [motivoOutro, setMotivoOutro] = useState('');
  const [obs, setObs] = useState('');
  const [profissionalId, setProfissionalId] = useState('');
  const [dataInicioDia, setDataInicioDia] = useState(hoje);
  const [dataFimDia, setDataFimDia] = useState(hoje);
  const [dataHorario, setDataHorario] = useState(hoje);
  const [horaInicio, setHoraInicio] = useState('09:00');
  const [horaFim, setHoraFim] = useState('12:00');
  const [erro, setErro] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setErro('');
    setDataInicioDia(hoje);
    setDataFimDia(hoje);
    setDataHorario(hoje);
  }, [isOpen, hoje]);

  if (!isOpen) return null;

  const salvar = async () => {
    const motivo = resolveMotivoBloqueio(tipo, motivoOutro);
    const msg = validateBloqueioForm({
      modo,
      motivoFinal: motivo,
      dataInicioDia,
      dataFimDia,
      dataHorario,
      horaInicio,
      horaFim,
    });
    if (msg) {
      setErro(msg);
      return;
    }
    setSaving(true);
    setErro('');
    try {
      const body = buildBloqueioRequestBody({
        modo,
        motivo,
        observacoes: obs,
        professionalId: profissionalId,
        dataInicioDia,
        dataFimDia,
        dataHorario,
        horaInicio,
        horaFim,
      });
      await CabeleireiroAPI.bloqueios.create(body);
      onSuccess();
      onClose();
    } catch (e: unknown) {
      const data =
        e && typeof e === 'object' && 'response' in e
          ? ((e as { response?: { data?: Record<string, unknown>; status?: number } }).response?.data ?? {})
          : {};
      const status =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { status?: number } }).response?.status || 400
          : 400;
      setErro(extractBloqueioApiError(data as Record<string, unknown>, status));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[92vh] overflow-hidden flex flex-col">
        <div className="shrink-0 border-b border-[#E8D5DC] px-5 py-3.5 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Bloquear horário</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Fechar">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {erro && <div className="p-3 rounded-lg bg-red-50 text-red-800 text-sm">{erro}</div>}
          <div>
            <span className="block text-sm font-medium text-gray-700 mb-2">Intervalo</span>
            <div className="inline-flex rounded-lg border border-[#E8D5DC] p-0.5 bg-[#FBF5F7]">
              {MODOS_BLOQUEIO_INTERVALO.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setModo(m.value)}
                  className={`px-4 py-2 text-sm font-medium rounded-md ${
                    modo === m.value ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
          <label className="block text-sm space-y-1">
            <span className="font-medium text-gray-700">Tipo</span>
            <select className={fieldClass} value={tipo} onChange={(e) => setTipo(e.target.value)}>
              {TIPOS_BLOQUEIO.map((t) => (
                <option key={t.label} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          {!tipo && (
            <label className="block text-sm space-y-1">
              <span className="font-medium text-gray-700">Motivo</span>
              <input className={fieldClass} value={motivoOutro} onChange={(e) => setMotivoOutro(e.target.value)} />
            </label>
          )}
          <label className="block text-sm space-y-1">
            <span className="font-medium text-gray-700">Profissional</span>
            <select
              className={fieldClass}
              value={profissionalId}
              onChange={(e) => setProfissionalId(e.target.value)}
            >
              <option value="">Todos</option>
              {profissionais.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome}
                </option>
              ))}
            </select>
          </label>
          {modo === 'dias' ? (
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm space-y-1">
                <span className="font-medium text-gray-700">Início</span>
                <input
                  type="date"
                  className={fieldClass}
                  value={dataInicioDia}
                  onChange={(e) => setDataInicioDia(e.target.value)}
                />
              </label>
              <label className="text-sm space-y-1">
                <span className="font-medium text-gray-700">Fim</span>
                <input
                  type="date"
                  className={fieldClass}
                  value={dataFimDia}
                  onChange={(e) => setDataFimDia(e.target.value)}
                />
              </label>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label className="text-sm space-y-1">
                <span className="font-medium text-gray-700">Data</span>
                <input
                  type="date"
                  className={fieldClass}
                  value={dataHorario}
                  onChange={(e) => setDataHorario(e.target.value)}
                />
              </label>
              <label className="text-sm space-y-1">
                <span className="font-medium text-gray-700">Início</span>
                <input
                  type="time"
                  className={fieldClass}
                  value={horaInicio}
                  onChange={(e) => setHoraInicio(e.target.value)}
                />
              </label>
              <label className="text-sm space-y-1">
                <span className="font-medium text-gray-700">Fim</span>
                <input
                  type="time"
                  className={fieldClass}
                  value={horaFim}
                  onChange={(e) => setHoraFim(e.target.value)}
                />
              </label>
            </div>
          )}
          <label className="block text-sm space-y-1">
            <span className="font-medium text-gray-700">Observações</span>
            <textarea className={`${fieldClass} min-h-[70px]`} value={obs} onChange={(e) => setObs(e.target.value)} />
          </label>
        </div>
        <div className="shrink-0 border-t border-[#E8D5DC] px-5 py-3 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg text-sm">
            Cancelar
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => void salvar()}
            className="px-4 py-2 rounded-lg text-sm text-white disabled:opacity-60"
            style={{ backgroundColor: SALAO_PRIMARY }}
          >
            {saving ? 'Salvando...' : 'Bloquear'}
          </button>
        </div>
      </div>
    </div>
  );
}
