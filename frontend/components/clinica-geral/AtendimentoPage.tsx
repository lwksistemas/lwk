'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { EvolucaoForm } from '@/components/clinica-geral/EvolucaoForm';
import { PainelTele } from '@/components/clinica-geral/PainelTele';
import { EMPTY_ITEM, ReceitaForm } from '@/components/clinica-geral/ReceitaForm';
import { ValorTissForm } from '@/components/clinica-geral/ValorTissForm';
import {
  abrirTele,
  createGuiaTiss,
  createPrescricao,
  evolucaoPdfUrl,
  getConsulta,
  getEvolucaoDaConsulta,
  listPrescricoes,
  openPdf,
  receitaPdfUrl,
  registrarTele,
  saveEvolucao,
  updateConsulta,
  updateConsultaStatus,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, Evolucao, Prescricao, PrescricaoItem } from '@/lib/clinica-geral-types';
import { formatBRL, formatHora, minutosTeleRestantes } from '@/lib/clinica-geral-utils';

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
      const achada = await getConsulta(id);
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

      <EvolucaoForm
        evolucao={evolucao}
        onChange={(patch) => setEvolucao((ev) => ({ ...ev, ...patch }))}
        onSave={() => void salvarEvolucao()}
        onPdf={evolucao.id ? () => void openPdf(evolucaoPdfUrl(evolucao.id!)) : undefined}
      />
      <ReceitaForm
        alergias={alergias}
        itens={itens}
        prescricoes={prescricoes}
        onItensChange={setItens}
        onEmitir={() => void emitirReceita()}
        onAbrirPdf={(prescId) => void openPdf(receitaPdfUrl(prescId))}
      />
      <ValorTissForm
        valor={valor}
        onValorChange={setValor}
        onSalvarValor={async () => {
          const saved = await updateConsulta(consulta.id, { valor });
          setConsulta(saved);
          setMsg(`Valor ${formatBRL(valor)} salvo.`);
        }}
        onGerarGuia={async () => {
          const guia = await createGuiaTiss(consulta.id, null, valor || consulta.valor);
          setMsg(`Guia ${guia.numero_guia} gerada.`);
        }}
      />
      <PainelTele
        consulta={consulta}
        info={teleInfo}
        onAbrir={async () => {
          const r = await abrirTele(consulta.id);
          setConsulta(r);
          setTeleInfo(`Restam ${minutosTeleRestantes(r.tele_minutos_mes || 0, r.teto_tele_minutos || 600)} min neste mês.`);
          if (r.tele_sala_url) window.open(r.tele_sala_url, '_blank');
        }}
        onRegistrar={async () => {
          const r = await registrarTele(consulta.id, consulta.duracao_minutos || 15);
          setConsulta(r);
          setTeleInfo(`+${consulta.duracao_minutos || 15} min registrados.`);
        }}
      />

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
}
