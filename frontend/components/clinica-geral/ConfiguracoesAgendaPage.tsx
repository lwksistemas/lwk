'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, Save } from 'lucide-react';
import { getConfiguracao, saveConfiguracao } from '@/lib/clinica-geral-api';
import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { ConfiguracaoConsultorio } from '@/lib/clinica-geral-types';

const DURACOES = [5, 10, 15, 20, 30, 45, 60];

function hhmm(value: string): string {
  return (value || '08:00').slice(0, 5);
}

const VAZIA: ConfiguracaoConsultorio = {
  hora_inicio: '08:00',
  hora_fim: '18:00',
  duracao_minutos: 15,
  endereco: '',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  telefone: '',
  especialidade: 'Clínica médica',
  crm: '',
  medico_nome: '',
  teto_tele_minutos: 600,
  prontuario_prefixo: '',
  prontuario_abas_ocultas: [],
};

export function ConfiguracoesAgendaPage() {
  const [config, setConfig] = useState<ConfiguracaoConsultorio>(VAZIA);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    getConfiguracao()
      .then((c) =>
        setConfig({
          ...VAZIA,
          ...c,
          hora_inicio: hhmm(c.hora_inicio),
          hora_fim: hhmm(c.hora_fim),
          duracao_minutos: c.duracao_minutos || 15,
        }),
      )
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const salvar = async () => {
    setSalvando(true);
    setErro('');
    try {
      const r = await saveConfiguracao({
        hora_inicio: config.hora_inicio,
        hora_fim: config.hora_fim,
        duracao_minutos: config.duracao_minutos,
        especialidade: config.especialidade,
        crm: config.crm,
        medico_nome: config.medico_nome,
      });
      setConfig({
        ...VAZIA,
        ...r,
        hora_inicio: hhmm(r.hora_inicio),
        hora_fim: hhmm(r.hora_fim),
      });
      setSalvo(true);
      setTimeout(() => setSalvo(false), 3000);
    } catch {
      setErro('Não foi possível salvar. Confira os horários e tente de novo.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <ConfiguracoesLayout>
      <div className="max-w-3xl space-y-6">
        {loading ? (
          <p className="py-12 text-center text-sm text-slate-500">Carregando configurações...</p>
        ) : (
          <>
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <h2 className="mb-4 text-base font-semibold text-slate-900">Horário de atendimento</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">Início</span>
                  <input
                    type="time"
                    value={config.hora_inicio}
                    onChange={(e) => setConfig((c) => ({ ...c, hora_inicio: e.target.value }))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">Fim</span>
                  <input
                    type="time"
                    value={config.hora_fim}
                    onChange={(e) => setConfig((c) => ({ ...c, hora_fim: e.target.value }))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">Duração do slot</span>
                  <select
                    value={config.duracao_minutos}
                    onChange={(e) => setConfig((c) => ({ ...c, duracao_minutos: Number(e.target.value) }))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  >
                    {DURACOES.map((n) => (
                      <option key={n} value={n}>
                        {n} min
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <h2 className="mb-4 text-base font-semibold text-slate-900">Médico</h2>
              <div className="space-y-4">
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">Especialidade</span>
                  <input
                    value={config.especialidade}
                    onChange={(e) => setConfig((c) => ({ ...c, especialidade: e.target.value }))}
                    placeholder="Clínica médica"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </label>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-slate-700">Médico</span>
                    <input
                      value={config.medico_nome}
                      onChange={(e) => setConfig((c) => ({ ...c, medico_nome: e.target.value }))}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium text-slate-700">CRM</span>
                    <input
                      value={config.crm}
                      onChange={(e) => setConfig((c) => ({ ...c, crm: e.target.value }))}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />
                  </label>
                </div>
              </div>
            </div>

            {erro && (
              <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">{erro}</p>
            )}

            <button
              type="button"
              onClick={() => void salvar()}
              disabled={salvando}
              className="flex w-full items-center justify-center gap-2 rounded-xl py-3 font-semibold text-white disabled:opacity-50"
              style={{ backgroundColor: TEAL }}
            >
              {salvo ? <CheckCircle size={18} /> : <Save size={18} />}
              {salvando ? 'Salvando...' : salvo ? 'Salvo!' : 'Salvar configurações'}
            </button>
          </>
        )}
      </div>
    </ConfiguracoesLayout>
  );
}
