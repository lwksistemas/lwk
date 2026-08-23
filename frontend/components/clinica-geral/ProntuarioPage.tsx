'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Clock, Info } from 'lucide-react';
import { ProntuarioExames } from '@/components/clinica-geral/ProntuarioExames';
import { ProntuarioFotoPerfil } from '@/components/clinica-geral/ProntuarioFotoPerfil';
import { ProntuarioResumoClinico } from '@/components/clinica-geral/ProntuarioResumoClinico';
import { EMPTY_ITEM, ReceitaForm } from '@/components/clinica-geral/ReceitaForm';
import {
  createConsulta,
  createPrescricao,
  evolucaoPdfUrl,
  getProntuario,
  listAnexosPaciente,
  listConsultasPaciente,
  openPdf,
  receitaPdfUrl,
  updatePaciente,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import {
  emptyPaciente,
  STATUS_LABEL,
  TIPO_CONSULTA_LABEL,
  type Consulta,
  type Evolucao,
  type Paciente,
  type PacienteAnexo,
  type Prescricao,
  type PrescricaoItem,
} from '@/lib/clinica-geral-types';
import { displayName, formatDateBR, formatHora, formatProntuarioSubtitulo, toISODate } from '@/lib/clinica-geral-utils';

type AbaProntuario = 'resumo' | 'exames';

export function ProntuarioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const id = Number(params.id);
  const router = useRouter();
  const base = `/loja/${slug}/clinica-geral`;

  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [prescricoes, setPrescricoes] = useState<Prescricao[]>([]);
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [anexos, setAnexos] = useState<PacienteAnexo[]>([]);
  const [aba, setAba] = useState<AbaProntuario>('resumo');
  const [prescrever, setPrescrever] = useState(false);
  const [itens, setItens] = useState<PrescricaoItem[]>([{ ...EMPTY_ITEM }]);
  const [erro, setErro] = useState('');

  useEffect(() => {
    if (!id) return;
    void Promise.all([getProntuario(id), listConsultasPaciente(id), listAnexosPaciente(id)])
      .then(([prontuario, agenda, docs]) => {
        setPaciente({ ...emptyPaciente(), ...prontuario.paciente });
        setEvolucoes(prontuario.evolucoes);
        setPrescricoes(prontuario.prescricoes);
        setConsultas(agenda);
        setAnexos(docs);
      })
      .catch(() => setErro('Não foi possível carregar o prontuário.'));
  }, [id]);

  if (!paciente) {
    return <p className="p-6 text-sm text-slate-500">{erro || 'Carregando prontuário...'}</p>;
  }

  const consultasOrdenadas = [...consultas].sort((a, b) => {
    const byDate = b.data.localeCompare(a.data);
    return byDate !== 0 ? byDate : (b.hora || '').localeCompare(a.hora || '');
  });

  const garantirConsulta = async () => {
    const hoje = toISODate(new Date());
    const atual = consultasOrdenadas.find((c) => c.data === hoje && c.status !== 'desmarcado' && c.status !== 'faltou');
    if (atual) return atual;
    const agora = new Date();
    const hora = `${String(agora.getHours()).padStart(2, '0')}:${String(agora.getMinutes()).padStart(2, '0')}`;
    const criada = await createConsulta({
      paciente: paciente.id,
      data: hoje,
      hora,
      tipo: consultas.length ? 'retorno' : 'primeira',
      modalidade: 'presencial',
      convenio: 'PARTICULAR',
      status: 'recepcionado',
    });
    setConsultas((lista) => [criada, ...lista]);
    return criada;
  };

  return (
    <div className="flex min-h-full flex-col bg-white">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-5 py-4">
        <div className="flex min-w-0 items-center gap-4">
          <ProntuarioFotoPerfil
            paciente={paciente}
            onChange={async (url) => {
              const atualizado = await updatePaciente(paciente.id, { foto_url: url });
              setPaciente({ ...emptyPaciente(), ...atualizado });
            }}
          />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="truncate text-lg font-semibold text-slate-800">
                {displayName(paciente.nome, paciente.nome_social)}
              </h1>
              <button
                type="button"
                title="Ficha do paciente"
                className="text-slate-400 hover:text-slate-600"
                onClick={() => router.push(`${base}/pacientes/${paciente.id}`)}
              >
                <Info className="h-4 w-4" />
              </button>
              <button
                type="button"
                title="Agendamentos"
                className="text-slate-400 hover:text-slate-600"
                onClick={() => setAba('resumo')}
              >
                <Clock className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm text-slate-500">{formatProntuarioSubtitulo(paciente) || '—'}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setPrescrever(true)}
            className="rounded-md border bg-white px-4 py-2 text-sm font-medium"
            style={{ borderColor: TEAL, color: TEAL }}
          >
            Prescrever
          </button>
          <button
            type="button"
            onClick={async () => {
              try {
                const consulta = await garantirConsulta();
                router.push(`${base}/consultas/${consulta.id}`);
              } catch {
                setErro('Não foi possível iniciar o atendimento.');
              }
            }}
            className="rounded-md px-4 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: TEAL }}
          >
            Iniciar atendimento
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <nav className="flex w-[108px] shrink-0 flex-col gap-1 bg-slate-100 py-3">
          <AbaLateral label="Resumo" ativo={aba === 'resumo'} onClick={() => setAba('resumo')} />
          <AbaLateral label="Exames" ativo={aba === 'exames'} onClick={() => setAba('exames')} />
        </nav>

        {aba === 'resumo' ? (
          <section className="min-w-0 flex-1 p-6">
            {erro ? <p className="mb-3 text-sm text-red-600">{erro}</p> : null}
            {consultasOrdenadas.length === 0 && evolucoes.length === 0 ? (
              <p className="pt-16 text-center text-slate-400">Este paciente não possui atendimentos</p>
            ) : (
              <ul className="space-y-3">
                {consultasOrdenadas.map((c) => {
                  const ev = evolucoes.find((e) => e.consulta === c.id);
                  return (
                    <li key={c.id}>
                      <button
                        type="button"
                        onClick={() => router.push(`${base}/consultas/${c.id}`)}
                        className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-left hover:border-teal-400"
                      >
                        <p className="text-sm font-medium text-slate-800">
                          {formatDateBR(c.data)} {formatHora(c.hora)} · {TIPO_CONSULTA_LABEL[c.tipo]} · {STATUS_LABEL[c.status]}
                        </p>
                        {ev ? (
                          <p className="mt-1 line-clamp-2 text-sm text-slate-500">
                            {ev.avaliacao || ev.subjetivo || ev.plano || 'Atendimento registrado'}
                          </p>
                        ) : (
                          <p className="mt-1 text-sm text-slate-400">Sem evolução</p>
                        )}
                        {ev ? (
                          <span
                            role="link"
                            className="mt-2 inline-block text-xs"
                            style={{ color: TEAL }}
                            onClick={(e) => {
                              e.stopPropagation();
                              void openPdf(evolucaoPdfUrl(ev.id));
                            }}
                          >
                            Abrir PDF
                          </span>
                        ) : null}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        ) : (
          <ProntuarioExames />
        )}

        <ProntuarioResumoClinico
          paciente={paciente}
          evolucoes={evolucoes}
          prescricoes={prescricoes}
          anexos={anexos}
        />
      </div>

      {prescrever ? (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40 p-4" onClick={() => setPrescrever(false)}>
          <div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded-xl bg-white p-4" onClick={(e) => e.stopPropagation()}>
            <ReceitaForm
              alergias={paciente.alergias}
              itens={itens}
              prescricoes={prescricoes}
              onItensChange={setItens}
              onEmitir={async () => {
                const limpos = itens.filter((i) => i.medicamento.trim());
                if (!limpos.length) return;
                const consulta = await garantirConsulta();
                const criada = await createPrescricao(consulta.id, paciente.id, limpos);
                setPrescricoes((lista) => [criada, ...lista]);
                setItens([{ ...EMPTY_ITEM }]);
              }}
              onAbrirPdf={(prescId) => void openPdf(receitaPdfUrl(prescId))}
            />
            <button type="button" onClick={() => setPrescrever(false)} className="mt-3 text-sm text-slate-500">
              Fechar
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function AbaLateral({ label, ativo, onClick }: { label: string; ativo: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative mx-2 rounded-l-md px-3 py-2 text-left text-sm ${ativo ? 'font-medium text-white' : 'text-slate-600 hover:bg-white'}`}
      style={ativo ? { backgroundColor: TEAL } : undefined}
    >
      {label}
      {ativo ? (
        <span
          className="absolute -right-2 top-1/2 h-0 w-0 -translate-y-1/2 border-y-8 border-l-8 border-y-transparent"
          style={{ borderLeftColor: TEAL }}
        />
      ) : null}
    </button>
  );
}
