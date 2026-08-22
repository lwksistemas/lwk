'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  abrirTele,
  createPrescricao,
  createGuiaTiss,
  evolucaoPdfUrl,
  getEvolucaoDaConsulta,
  listPrescricoes,
  openPdf,
  receitaPdfUrl,
  registrarTele,
  saveEvolucao,
  updateConsulta,
  updateConsultaStatus,
} from '@/lib/clinica-geral-api';
import type { Consulta, Evolucao, Prescricao, PrescricaoItem } from '@/lib/clinica-geral-types';
import { alertaAlergia, formatBRL, formatHora } from '@/lib/clinica-geral-utils';

const TEAL = '#0D9B9B';
const EMPTY_ITEM: PrescricaoItem = { medicamento: '', dosagem: '', posologia: '', quantidade: '' };

export function AtendimentoPage() {
  const params = useParams();
  const slug = params.slug as string;
  const id = Number(params.id);
  const router = useRouter();
  const [consulta, setConsulta] = useState<Consulta | null>(null);
  const [evolucao, setEvolucao] = useState<Partial<Evolucao>>({
    subjetivo: '',
    objetivo: '',
    avaliacao: '',
    plano: '',
    especialidade: '',
  });
  const [itens, setItens] = useState<PrescricaoItem[]>([{ ...EMPTY_ITEM }]);
  const [prescricoes, setPrescricoes] = useState<Prescricao[]>([]);
  const [valor, setValor] = useState('');
  const [msg, setMsg] = useState('');
  const [teleInfo, setTeleInfo] = useState('');

  useEffect(() => {
    if (!id) return;
    void (async () => {
      const achada = await fetchConsultaFallback(id);
      if (!achada) return;
      setConsulta(achada);
      setValor(achada.valor || '');
      const ev = await getEvolucaoDaConsulta(id);
      if (ev) setEvolucao(ev);
      setPrescricoes(await listPrescricoes(id));
    })();
  }, [id]);

  if (!consulta) return <p className="p-6 text-sm text-slate-500">Carregando atendimento...</p>;

  const alergias = consulta.paciente_alergias || '';

  const salvarEvolucao = async () => {
    const saved = await saveEvolucao({
      id: evolucao.id,
      consulta: consulta.id,
      paciente: consulta.paciente,
      especialidade: evolucao.especialidade || '',
      subjetivo: evolucao.subjetivo || '',
      objetivo: evolucao.objetivo || '',
      avaliacao: evolucao.avaliacao || '',
      plano: evolucao.plano || '',
    });
    setEvolucao(saved);
    setMsg('Evolução salva.');
  };

  const emitirReceita = async () => {
    const limpos = itens.filter((i) => i.medicamento.trim());
    if (!limpos.length) {
      setMsg('Informe ao menos um medicamento.');
      return;
    }
    const presc = await createPrescricao(consulta.id, consulta.paciente, limpos);
    setPrescricoes((p) => [presc, ...p]);
    setItens([{ ...EMPTY_ITEM }]);
    setMsg(presc.itens.some((i) => i.alerta_alergia) ? 'Receita salva com alerta de alergia.' : 'Receita emitida.');
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">{consulta.paciente_nome}</h1>
          <p className="text-sm text-slate-500">
            {consulta.data} {formatHora(consulta.hora)} · {consulta.convenio}
          </p>
        </div>
        <button type="button" onClick={() => router.push(`/loja/${slug}/clinica-geral/agenda?data=${consulta.data}`)} className="text-sm text-teal-700">
          Voltar à agenda
        </button>
      </div>

      {alergias ? <p className="rounded-md bg-red-50 px-4 py-2 text-sm font-medium text-red-700">Alergias: {alergias}</p> : null}
      {msg ? <p className="text-sm text-teal-700">{msg}</p> : null}

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-semibold text-slate-800">Evolução SOAP</h2>
        {(['subjetivo', 'objetivo', 'avaliacao', 'plano'] as const).map((campo) => (
          <label key={campo} className="mb-3 block text-sm">
            <span className="mb-1 block capitalize text-slate-600">{campo}</span>
            <textarea
              value={evolucao[campo] || ''}
              onChange={(e) => setEvolucao((ev) => ({ ...ev, [campo]: e.target.value }))}
              rows={3}
              className="w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </label>
        ))}
        <div className="flex gap-2">
          <button type="button" onClick={() => void salvarEvolucao()} className="rounded-md px-4 py-2 text-sm text-white" style={{ backgroundColor: TEAL }}>
            Salvar evolução
          </button>
          {evolucao.id ? (
            <button type="button" onClick={() => void openPdf(evolucaoPdfUrl(evolucao.id!))} className="rounded-md border px-4 py-2 text-sm">
              PDF do prontuário
            </button>
          ) : null}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-semibold text-slate-800">Receituário ANVISA</h2>
        {itens.map((item, i) => {
          const alerta = alertaAlergia(alergias, item.medicamento);
          return (
            <div key={i} className="mb-2 grid gap-2 sm:grid-cols-4">
              <input
                placeholder="Medicamento"
                value={item.medicamento}
                onChange={(e) => patchItem(i, { medicamento: e.target.value })}
                className={`rounded-md border px-3 py-2 text-sm ${alerta ? 'border-red-500 bg-red-50' : 'border-slate-300'}`}
              />
              <input placeholder="Dosagem" value={item.dosagem} onChange={(e) => patchItem(i, { dosagem: e.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
              <input placeholder="Posologia" value={item.posologia} onChange={(e) => patchItem(i, { posologia: e.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
              <input placeholder="Qtde" value={item.quantidade} onChange={(e) => patchItem(i, { quantidade: e.target.value })} className="rounded-md border border-slate-300 px-3 py-2 text-sm" />
              {alerta ? <p className="sm:col-span-4 text-xs text-red-600">Conflito com alergia cadastrada.</p> : null}
            </div>
          );
        })}
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setItens((xs) => [...xs, { ...EMPTY_ITEM }])} className="text-sm text-teal-700">
            + medicamento
          </button>
          <button type="button" onClick={() => void emitirReceita()} className="rounded-md px-4 py-2 text-sm text-white" style={{ backgroundColor: TEAL }}>
            Emitir receita
          </button>
        </div>
        {prescricoes.map((p) => (
          <button key={p.id} type="button" onClick={() => void openPdf(receitaPdfUrl(p.id))} className="mt-2 block text-sm text-teal-700">
            Abrir receita #{p.id}
            {p.itens.some((i) => i.alerta_alergia) ? ' (alerta de alergia)' : ''}
          </button>
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 font-semibold text-slate-800">Valor e TISS</h2>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-sm">
            Valor (R$)
            <input value={valor} onChange={(e) => setValor(e.target.value)} className="ml-2 rounded-md border border-slate-300 px-3 py-2" />
          </label>
          <button
            type="button"
            onClick={async () => {
              const saved = await updateConsulta(consulta.id, { valor });
              setConsulta(saved);
              setMsg(`Valor ${formatBRL(valor)} salvo.`);
            }}
            className="rounded-md border px-3 py-2 text-sm"
          >
            Salvar valor
          </button>
          <button
            type="button"
            onClick={async () => {
              const guia = await createGuiaTiss(consulta.id, null, valor || consulta.valor);
              setMsg(`Guia ${guia.numero_guia} gerada.`);
            }}
            className="rounded-md border px-3 py-2 text-sm"
          >
            Gerar guia TISS
          </button>
        </div>
      </section>

      {consulta.modalidade === 'tele' && (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 font-semibold text-slate-800">Telemedicina (cota 10h/mês)</h2>
          {teleInfo ? <p className="mb-2 text-sm text-slate-600">{teleInfo}</p> : null}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={async () => {
                const r = await abrirTele(consulta.id);
                setConsulta(r);
                const rest = Math.max(0, (r.teto_tele_minutos || 600) - (r.tele_minutos_mes || 0));
                setTeleInfo(`Restam ${rest} min neste mês.`);
                if (r.tele_sala_url) window.open(r.tele_sala_url, '_blank');
              }}
              className="rounded-md px-4 py-2 text-sm text-white"
              style={{ backgroundColor: TEAL }}
            >
              Abrir sala
            </button>
            <button
              type="button"
              onClick={async () => {
                const r = await registrarTele(consulta.id, consulta.duracao_minutos || 15);
                setConsulta(r);
                setTeleInfo(`+${consulta.duracao_minutos || 15} min registrados.`);
              }}
              className="rounded-md border px-4 py-2 text-sm"
            >
              Registrar duração
            </button>
          </div>
        </section>
      )}

      <button
        type="button"
        onClick={async () => {
          await salvarEvolucao();
          await updateConsultaStatus(consulta.id, 'atendido');
          router.push(`/loja/${slug}/clinica-geral/agenda?data=${consulta.data}`);
        }}
        className="w-full rounded-xl py-3 font-semibold text-white"
        style={{ backgroundColor: TEAL }}
      >
        Encerrar atendimento
      </button>
    </div>
  );

  function patchItem(index: number, patch: Partial<PrescricaoItem>) {
    setItens((xs) => xs.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }
}

async function fetchConsultaFallback(id: number): Promise<Consulta | null> {
  try {
    const { default: apiClient } = await import('@/lib/api-client');
    const res = await apiClient.get(`/clinica-geral/consultas/${id}/`);
    return res.data as Consulta;
  } catch {
    return null;
  }
}
