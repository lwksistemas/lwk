'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Clock, Info, Printer } from 'lucide-react';
import { AtendimentoAntecedentes } from '@/components/clinica-geral/AtendimentoAntecedentes';
import { AtendimentoEscalas } from '@/components/clinica-geral/AtendimentoEscalas';
import { AtendimentoExameFisico } from '@/components/clinica-geral/AtendimentoExameFisico';
import { AtendimentoHma } from '@/components/clinica-geral/AtendimentoHma';
import { AtendimentoPainelDireito } from '@/components/clinica-geral/AtendimentoPainelDireito';
import { AtendimentoTexto } from '@/components/clinica-geral/AtendimentoTexto';
import { AtendimentoTratamentos } from '@/components/clinica-geral/AtendimentoTratamentos';
import { ProntuarioExames } from '@/components/clinica-geral/ProntuarioExames';
import { ProntuarioFotoPerfil } from '@/components/clinica-geral/ProntuarioFotoPerfil';
import { EMPTY_ITEM, ReceitaForm } from '@/components/clinica-geral/ReceitaForm';
import { ValorTissForm } from '@/components/clinica-geral/ValorTissForm';
import {
  ABAS_ATENDIMENTO,
  fichaParaSoap,
  formatTimer,
  mergeFicha,
  type AbaAtendimento,
} from '@/lib/clinica-geral-atendimento';
import {
  abrirTele,
  createGuiaTiss,
  createPrescricao,
  enviarTele,
  evolucaoPdfUrl,
  getConfiguracao,
  getConsulta,
  getEvolucaoDaConsulta,
  getPaciente,
  listAnexosPaciente,
  listPrescricoes,
  openPdf,
  receitaPdfUrl,
  saveEvolucao,
  updateConsulta,
  updateConsultaStatus,
  updatePaciente,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import {
  emptyPaciente,
  type Consulta,
  type Evolucao,
  type FichaAtendimento,
  type Paciente,
  type PacienteAnexo,
  type Prescricao,
  type PrescricaoItem,
} from '@/lib/clinica-geral-types';
import { displayName, formatBRL, formatProntuarioSubtitulo, minutosTeleRestantes } from '@/lib/clinica-geral-utils';

export function AtendimentoPage() {
  const params = useParams();
  const slug = params.slug as string;
  const id = Number(params.id);
  const router = useRouter();
  const base = `/loja/${slug}/clinica-geral`;

  const [consulta, setConsulta] = useState<Consulta | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [evolucao, setEvolucao] = useState<Partial<Evolucao>>({});
  const [ficha, setFicha] = useState<FichaAtendimento>(mergeFicha());
  const [aba, setAba] = useState<AbaAtendimento>('HMA');
  const [itens, setItens] = useState<PrescricaoItem[]>([{ ...EMPTY_ITEM }]);
  const [prescricoes, setPrescricoes] = useState<Prescricao[]>([]);
  const [anexos, setAnexos] = useState<PacienteAnexo[]>([]);
  const [valor, setValor] = useState('');
  const [teleInfo, setTeleInfo] = useState('');
  const [medicoNome, setMedicoNome] = useState('');
  const [emChamada, setEmChamada] = useState(false);
  const [enviandoTele, setEnviandoTele] = useState(false);
  const [segundos, setSegundos] = useState(0);
  const [msg, setMsg] = useState('');
  const saveTimer = useRef<number | null>(null);

  useEffect(() => {
    if (!id) return;
    void (async () => {
      const achada = await getConsulta(id);
      if (!achada) return;
      setConsulta(achada);
      setValor(achada.valor || '');
      if (achada.status === 'agendado' || achada.status === 'confirmado') {
        setConsulta(await updateConsultaStatus(achada.id, 'recepcionado'));
      }
      const [ev, docs, fichaPaciente, config] = await Promise.all([
        getEvolucaoDaConsulta(id),
        listAnexosPaciente(achada.paciente),
        getPaciente(achada.paciente),
        getConfiguracao().catch(() => ({ medico_nome: '' })),
      ]);
      setMedicoNome(config.medico_nome || '');
      setPaciente({ ...emptyPaciente(), ...fichaPaciente });
      setAnexos(docs);
      if (ev) {
        setEvolucao(ev);
        setFicha(mergeFicha(ev.ficha));
      }
      setPrescricoes(await listPrescricoes(id));
    })();
  }, [id]);

  useEffect(() => {
    const t = window.setInterval(() => setSegundos((s) => s + 1), 1000);
    return () => window.clearInterval(t);
  }, []);

  const persistir = async (proxima = ficha) => {
    if (!consulta) return;
    const soap = fichaParaSoap(proxima);
    const saved = await saveEvolucao({
      id: evolucao.id,
      consulta: consulta.id,
      paciente: consulta.paciente,
      especialidade: evolucao.especialidade || '',
      ...soap,
      ficha: proxima,
    });
    setEvolucao(saved);
    return saved;
  };

  const patchFicha = (patch: Partial<FichaAtendimento>) => {
    setFicha((atual) => {
      const proxima = { ...atual, ...patch };
      if (saveTimer.current) window.clearTimeout(saveTimer.current);
      saveTimer.current = window.setTimeout(() => {
        void persistir(proxima);
      }, 700);
      return proxima;
    });
  };

  if (!consulta || !paciente) return <p className="p-6 text-sm text-slate-500">Carregando atendimento...</p>;

  const titulo = ABAS_ATENDIMENTO.find((a) => a.id === aba)?.titulo || aba;

  return (
    <div className="flex min-h-full flex-col bg-white">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-5 py-3">
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
                {displayName(paciente.nome, paciente.nome_social) || consulta.paciente_nome}
              </h1>
              <button type="button" title="Ficha" className="text-slate-400" onClick={() => router.push(`${base}/pacientes/${paciente.id}`)}>
                <Info className="h-4 w-4" />
              </button>
              <button type="button" title="Prontuário" className="text-slate-400" onClick={() => router.push(`${base}/pacientes/${paciente.id}/prontuario`)}>
                <Clock className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm text-slate-500">{formatProntuarioSubtitulo(paciente) || '—'}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1 text-sm tabular-nums text-slate-600">
            <Clock className="h-4 w-4" />
            {formatTimer(segundos)}
          </span>
          <button
            type="button"
            className="text-slate-400"
            title="Imprimir evolução"
            onClick={() => evolucao.id && void openPdf(evolucaoPdfUrl(evolucao.id))}
          >
            <Printer className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={async () => {
              await persistir();
              await updateConsultaStatus(consulta.id, 'atendido');
              router.push(`${base}/pacientes/${paciente.id}/prontuario`);
            }}
            className="rounded-md border bg-white px-4 py-2 text-sm font-medium"
            style={{ borderColor: TEAL, color: TEAL }}
          >
            Finalizar atendimento
          </button>
        </div>
      </header>

      {consulta.paciente_alergias ? (
        <p className="bg-red-50 px-5 py-2 text-sm text-red-700">Alergias: {consulta.paciente_alergias}</p>
      ) : null}
      {msg ? <p className="px-5 py-2 text-sm" style={{ color: TEAL }}>{msg}</p> : null}

      <div className="flex min-h-0 flex-1">
        <nav className="flex w-14 shrink-0 flex-col gap-1 bg-slate-100 py-2">
          {ABAS_ATENDIMENTO.map((item) => (
            <button
              key={item.id}
              type="button"
              title={item.titulo}
              onClick={() => setAba(item.id)}
              className={`mx-1 rounded px-1 py-2 text-center text-[11px] font-semibold ${aba === item.id ? 'text-white' : 'text-slate-600 hover:bg-white'}`}
              style={aba === item.id ? { backgroundColor: TEAL } : undefined}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="min-w-0 flex-1 overflow-auto p-4">
          {aba === 'HMA' ? <AtendimentoHma ficha={ficha} onChange={patchFicha} /> : null}
          {aba === 'TrA' ? <AtendimentoTratamentos ficha={ficha} onChange={patchFicha} /> : null}
          {aba === 'AP' ? <AtendimentoAntecedentes ficha={ficha} onChange={patchFicha} /> : null}
          {aba === 'EF' ? <AtendimentoExameFisico ficha={ficha} onChange={patchFicha} /> : null}
          {aba === 'EM' ? <AtendimentoEscalas /> : null}
          {aba === 'TA' ? <AtendimentoTexto titulo={titulo} value={ficha.terapeutica} onChange={(terapeutica) => patchFicha({ terapeutica })} /> : null}
          {aba === 'DIAG' ? <AtendimentoTexto titulo={titulo} value={ficha.diagnostico} onChange={(diagnostico) => patchFicha({ diagnostico })} /> : null}
          {aba === 'Lx' ? <ProntuarioExames /> : null}
          {aba === 'Rx' ? (
            <div className="space-y-4">
              <ReceitaForm
                alergias={consulta.paciente_alergias}
                itens={itens}
                prescricoes={prescricoes}
                onItensChange={setItens}
                onEmitir={async () => {
                  const limpos = itens.filter((i) => i.medicamento.trim());
                  if (!limpos.length) return;
                  const presc = await createPrescricao(consulta.id, consulta.paciente, limpos);
                  setPrescricoes((p) => [presc, ...p]);
                  setItens([{ ...EMPTY_ITEM }]);
                  setMsg(presc.itens.some((i) => i.alerta_alergia) ? 'Receita salva com alerta de alergia.' : 'Receita emitida.');
                }}
                onAbrirPdf={(prescId) => void openPdf(receitaPdfUrl(prescId))}
              />
              <ValorTissForm
                valor={valor}
                onValorChange={setValor}
                onSalvarValor={async () => {
                  setConsulta(await updateConsulta(consulta.id, { valor }));
                  setMsg(`Valor ${formatBRL(valor)} salvo.`);
                }}
                onGerarGuia={async () => {
                  const guia = await createGuiaTiss(consulta.id, null, valor || consulta.valor);
                  setMsg(`Guia ${guia.numero_guia} gerada.`);
                }}
              />
            </div>
          ) : null}
          {aba === 'ENC' ? <AtendimentoTexto titulo={titulo} value={ficha.encaminhamento} onChange={(encaminhamento) => patchFicha({ encaminhamento })} /> : null}
          {aba === 'SP' ? <AtendimentoTexto titulo={titulo} value={ficha.sumario} onChange={(sumario) => patchFicha({ sumario })} /> : null}
          {aba === 'AM' ? <AtendimentoTexto titulo={titulo} value={ficha.atestado} onChange={(atestado) => patchFicha({ atestado })} /> : null}
        </div>

        <AtendimentoPainelDireito
          consulta={consulta}
          anexos={anexos}
          teleInfo={teleInfo}
          medicoNome={medicoNome}
          emChamada={emChamada}
          enviandoTele={enviandoTele}
          onGerarTele={async () => {
            try {
              const r = await abrirTele(consulta.id);
              setConsulta(r);
              setTeleInfo(`Restam ${minutosTeleRestantes(r.tele_minutos_mes || 0, r.teto_tele_minutos || 600)} min neste mês.`);
            } catch {
              setTeleInfo('Não foi possível gerar a sala.');
            }
          }}
          onCopiarTele={async () => {
            let atual = consulta;
            if (!atual.tele_link) {
              atual = await abrirTele(consulta.id);
              setConsulta(atual);
            }
            const bruto = atual.tele_link || '';
            const path = bruto.replace(/^https?:\/\/[^/]+/, '');
            const link = path ? `${window.location.origin}${path}` : '';
            if (!link) {
              setTeleInfo('Gere a sala antes de copiar o link.');
              return;
            }
            try {
              await navigator.clipboard.writeText(link);
              setTeleInfo('Link copiado. Envie ao paciente ou use o WhatsApp.');
            } catch {
              setTeleInfo(link);
            }
          }}
          onEnviarTele={async () => {
            setEnviandoTele(true);
            try {
              const r = await enviarTele(consulta.id);
              setConsulta(r);
              setTeleInfo('Link enviado pelo WhatsApp do consultório.');
            } catch (err) {
              const detalhe = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
              setTeleInfo(detalhe || 'Não foi possível enviar o WhatsApp.');
            } finally {
              setEnviandoTele(false);
            }
          }}
          onEntrarTele={async () => {
            if (!consulta.tele_sala_url) {
              const r = await abrirTele(consulta.id);
              setConsulta(r);
            }
            setEmChamada(true);
          }}
          onSairTele={() => setEmChamada(false)}
        />
      </div>
    </div>
  );
}
