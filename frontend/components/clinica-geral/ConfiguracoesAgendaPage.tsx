'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, CalendarClock, CheckCircle, Save } from 'lucide-react';
import { getConfiguracao, saveConfiguracao } from '@/lib/clinica-geral-api';
import type { ConfiguracaoConsultorio } from '@/lib/clinica-geral-types';

const NAVY = '#2F2E5B';
const TEAL = '#0D9B9B';
const DURACOES = [5, 10, 15, 20, 30, 45, 60];

function hhmm(value: string): string {
  return (value || '08:00').slice(0, 5);
}

const VAZIA: ConfiguracaoConsultorio = {
  hora_inicio: '08:00',
  hora_fim: '18:00',
  duracao_minutos: 15,
  endereco: '',
  telefone: '',
  especialidade: 'Clínica médica',
  crm: '',
  medico_nome: '',
  teto_tele_minutos: 600,
};

export function ConfiguracoesAgendaPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [config, setConfig] = useState<ConfiguracaoConsultorio>(VAZIA);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    getConfiguracao()
      .then((c) =>
        setConfig({
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
      const r = await saveConfiguracao(config);
      setConfig({
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
    <div className="min-h-full bg-[#F7F8FB]">
      <div className="text-white shadow-sm" style={{ backgroundColor: NAVY }}>
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-5 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-white/15 p-2">
              <CalendarClock className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Agenda</h1>
              <p className="text-sm text-white/80">Expediente e dados do consultório</p>
            </div>
          </div>
          <Link
            href={`/loja/${slug}/clinica-geral/configuracoes`}
            className="flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25"
          >
            <ArrowLeft className="h-4 w-4" /> Voltar
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
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
              <h2 className="mb-4 text-base font-semibold text-slate-900">Consultório</h2>
              <div className="space-y-4">
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">Endereço</span>
                  <input
                    value={config.endereco}
                    onChange={(e) => setConfig((c) => ({ ...c, endereco: e.target.value }))}
                    placeholder="Rua, número, bairro, cidade"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  <span className="mb-1 block font-medium text-slate-700">Telefone</span>
                  <input
                    value={config.telefone}
                    onChange={(e) => setConfig((c) => ({ ...c, telefone: e.target.value }))}
                    placeholder="(16) 0000-0000"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                  />
                </label>
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
    </div>
  );
}
