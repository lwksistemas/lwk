'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, Save } from 'lucide-react';
import { getConfiguracao, saveConfiguracao } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { ConfiguracaoConsultorio } from '@/lib/clinica-geral-types';
import { consultaCep, formatarCep } from '@/lib/consulta-cep';
import { formatTelefone } from '@/lib/format-br';

const inputClass = 'mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal';
const labelClass = 'block text-[13px] font-bold text-slate-700 dark:text-slate-200';

const VAZIO: Pick<
  ConfiguracaoConsultorio,
  'cep' | 'logradouro' | 'numero' | 'complemento' | 'bairro' | 'cidade' | 'uf' | 'telefone' | 'endereco'
> = {
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  telefone: '',
  endereco: '',
};

export function EnderecoConsultorioPage() {
  const [form, setForm] = useState(VAZIO);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [consultando, setConsultando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    getConfiguracao()
      .then((c) => {
        const logradouro = c.logradouro || (!c.cep && c.endereco ? c.endereco : '');
        setForm({
          cep: c.cep || '',
          logradouro,
          numero: c.numero || '',
          complemento: c.complemento || '',
          bairro: c.bairro || '',
          cidade: c.cidade || '',
          uf: c.uf || '',
          telefone: c.telefone || '',
          endereco: c.endereco || '',
        });
      })
      .catch(() => setErro('Não foi possível carregar o endereço.'))
      .finally(() => setLoading(false));
  }, []);

  const buscarCep = async (cep: string) => {
    const digits = cep.replace(/\D/g, '');
    if (digits.length !== 8) return;
    setConsultando(true);
    try {
      const endereco = await consultaCep(cep);
      if (!endereco) return;
      setForm((f) => ({
        ...f,
        logradouro: endereco.logradouro || f.logradouro,
        bairro: endereco.bairro || f.bairro,
        cidade: endereco.cidade || f.cidade,
        uf: endereco.uf || f.uf,
      }));
    } finally {
      setConsultando(false);
    }
  };

  const salvar = async () => {
    setSalvando(true);
    setErro('');
    try {
      const r = await saveConfiguracao({
        cep: form.cep,
        logradouro: form.logradouro,
        numero: form.numero,
        complemento: form.complemento,
        bairro: form.bairro,
        cidade: form.cidade,
        uf: form.uf,
        telefone: form.telefone,
      });
      setForm({
        cep: r.cep || '',
        logradouro: r.logradouro || '',
        numero: r.numero || '',
        complemento: r.complemento || '',
        bairro: r.bairro || '',
        cidade: r.cidade || '',
        uf: r.uf || '',
        telefone: r.telefone || '',
        endereco: r.endereco || '',
      });
      setSalvo(true);
      setTimeout(() => setSalvo(false), 3000);
    } catch {
      setErro('Não foi possível salvar o endereço.');
    } finally {
      setSalvando(false);
    }
  };

  if (loading) return <p className="py-12 text-sm text-slate-500">Carregando endereço...</p>;

  return (
    <div className="max-w-2xl">
      <h2 className="mb-1 text-lg font-medium text-slate-800 dark:text-slate-100">Endereço</h2>
      <p className="mb-6 text-sm text-slate-500">Endereço de atendimento do consultório, usado em receituários e documentos.</p>
      {erro ? <p className="mb-4 text-sm text-red-600">{erro}</p> : null}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-6">
        <label className={`${labelClass} sm:col-span-2`}>
          CEP
          <input
            className={inputClass}
            value={formatarCep(form.cep)}
            onChange={(e) => {
              const cep = formatarCep(e.target.value);
              setForm((f) => ({ ...f, cep }));
              if (cep.replace(/\D/g, '').length === 8) void buscarCep(cep);
            }}
          />
          {consultando ? <span className="text-xs font-normal text-slate-400">Consultando CEP...</span> : null}
        </label>
        <label className={`${labelClass} sm:col-span-4`}>
          Logradouro
          <input className={inputClass} value={form.logradouro} onChange={(e) => setForm((f) => ({ ...f, logradouro: e.target.value }))} />
        </label>
        <label className={`${labelClass} sm:col-span-2`}>
          Número
          <input className={inputClass} value={form.numero} onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))} />
        </label>
        <label className={`${labelClass} sm:col-span-4`}>
          Complemento
          <input className={inputClass} value={form.complemento} onChange={(e) => setForm((f) => ({ ...f, complemento: e.target.value }))} />
        </label>
        <label className={`${labelClass} sm:col-span-3`}>
          Bairro
          <input className={inputClass} value={form.bairro} onChange={(e) => setForm((f) => ({ ...f, bairro: e.target.value }))} />
        </label>
        <label className={`${labelClass} sm:col-span-2`}>
          Cidade
          <input className={inputClass} value={form.cidade} onChange={(e) => setForm((f) => ({ ...f, cidade: e.target.value }))} />
        </label>
        <label className={labelClass}>
          UF
          <input
            className={inputClass}
            maxLength={2}
            value={form.uf}
            onChange={(e) => setForm((f) => ({ ...f, uf: e.target.value.toUpperCase().slice(0, 2) }))}
          />
        </label>
        <label className={`${labelClass} sm:col-span-3`}>
          Telefone
          <input
            className={inputClass}
            value={formatTelefone(form.telefone)}
            onChange={(e) => setForm((f) => ({ ...f, telefone: formatTelefone(e.target.value) }))}
          />
        </label>
      </div>

      <button
        type="button"
        onClick={() => void salvar()}
        disabled={salvando}
        className="mt-6 flex items-center gap-2 rounded px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        style={{ backgroundColor: TEAL }}
      >
        {salvo ? <CheckCircle size={16} /> : <Save size={16} />}
        {salvando ? 'Salvando...' : salvo ? 'Salvo!' : 'Salvar endereço'}
      </button>
    </div>
  );
}
