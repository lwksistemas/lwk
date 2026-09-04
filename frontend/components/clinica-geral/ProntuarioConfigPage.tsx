'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, Save } from 'lucide-react';
import { getConfiguracao, saveConfiguracao } from '@/lib/clinica-geral-api';
import { ABAS_ATENDIMENTO } from '@/lib/clinica-geral-atendimento';
import { TEAL } from '@/lib/clinica-geral-theme';

const inputClass = 'mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal';
const labelClass = 'block text-[13px] font-bold text-slate-700 dark:text-slate-200';

export function ProntuarioConfigPage() {
  const [prefixo, setPrefixo] = useState('');
  const [especialidade, setEspecialidade] = useState('Clínica médica');
  const [ocultas, setOcultas] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    getConfiguracao()
      .then((c) => {
        setPrefixo(c.prontuario_prefixo || '');
        setEspecialidade(c.especialidade || 'Clínica médica');
        setOcultas(Array.isArray(c.prontuario_abas_ocultas) ? c.prontuario_abas_ocultas : []);
      })
      .catch(() => setErro('Não foi possível carregar as configurações do prontuário.'))
      .finally(() => setLoading(false));
  }, []);

  const toggleAba = (id: string) => {
    setOcultas((atual) => (atual.includes(id) ? atual.filter((x) => x !== id) : [...atual, id]));
  };

  const salvar = async () => {
    setSalvando(true);
    setErro('');
    try {
      const r = await saveConfiguracao({
        prontuario_prefixo: prefixo.trim(),
        especialidade: especialidade.trim() || 'Clínica médica',
        prontuario_abas_ocultas: ocultas,
      });
      setPrefixo(r.prontuario_prefixo || '');
      setEspecialidade(r.especialidade || 'Clínica médica');
      setOcultas(Array.isArray(r.prontuario_abas_ocultas) ? r.prontuario_abas_ocultas : []);
      setSalvo(true);
      setTimeout(() => setSalvo(false), 3000);
    } catch {
      setErro('Não foi possível salvar.');
    } finally {
      setSalvando(false);
    }
  };

  if (loading) return <p className="py-12 text-sm text-slate-500">Carregando prontuário...</p>;

  return (
    <div className="max-w-2xl">
      <h2 className="mb-1 text-lg font-medium text-slate-800 dark:text-slate-100">Prontuário</h2>
      <p className="mb-6 text-sm text-slate-500">
        Prefixo do número de prontuário e abas visíveis no atendimento.
      </p>
      {erro ? <p className="mb-4 text-sm text-red-600">{erro}</p> : null}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label className={labelClass}>
          Prefixo do prontuário
          <input
            className={inputClass}
            maxLength={20}
            placeholder="Ex.: CG-"
            value={prefixo}
            onChange={(e) => setPrefixo(e.target.value)}
          />
        </label>
        <label className={labelClass}>
          Especialidade padrão
          <input
            className={inputClass}
            value={especialidade}
            onChange={(e) => setEspecialidade(e.target.value)}
          />
        </label>
      </div>

      <p className={`${labelClass} mt-6 mb-2`}>Abas do atendimento</p>
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {ABAS_ATENDIMENTO.map((aba) => (
          <li key={aba.id}>
            <label className="flex items-start gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={!ocultas.includes(aba.id)}
                onChange={() => toggleAba(aba.id)}
              />
              <span>
                <span className="font-medium">{aba.label}</span>
                <span className="block text-xs font-normal text-slate-500">{aba.titulo}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => void salvar()}
        disabled={salvando}
        className="mt-6 flex items-center gap-2 rounded px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        style={{ backgroundColor: TEAL }}
      >
        {salvo ? <CheckCircle size={16} /> : <Save size={16} />}
        {salvando ? 'Salvando...' : salvo ? 'Salvo!' : 'Salvar'}
      </button>
    </div>
  );
}
