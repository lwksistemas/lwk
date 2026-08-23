'use client';

import { useState, type ReactNode } from 'react';
import { BriefcaseMedical, ChevronRight, ClipboardList, MessageCircle, Paperclip, Video } from 'lucide-react';
import { coletarCirurgias, coletarDiagnosticos, coletarTratamentos } from '@/lib/clinica-geral-atendimento';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, Evolucao, Paciente, PacienteAnexo, Prescricao } from '@/lib/clinica-geral-types';
import { formatMesAnoCurto, formatRelativo } from '@/lib/clinica-geral-utils';

const ABAS = [
  { id: 'DIAG', label: 'DIAG' },
  { id: 'TRAT', label: 'TRAT' },
  { id: 'ALEG', label: 'ALEG' },
  { id: 'HAB', label: 'HAB' },
  { id: 'CIR', label: 'CIR' },
  { id: 'AF', label: 'AF' },
] as const;

type Painel = 'clinico' | 'evolucoes' | 'anexos' | 'chat' | 'tele';

type ProntuarioResumoClinicoProps = {
  paciente: Paciente;
  consultas: Consulta[];
  evolucoes: Evolucao[];
  prescricoes: Prescricao[];
  anexos: PacienteAnexo[];
};

export function ProntuarioResumoClinico({
  paciente,
  consultas,
  evolucoes,
  prescricoes,
  anexos,
}: ProntuarioResumoClinicoProps) {
  const [aba, setAba] = useState<(typeof ABAS)[number]['id']>('DIAG');
  const [painel, setPainel] = useState<Painel>('clinico');
  const [aberto, setAberto] = useState(true);

  const diagnosticos = coletarDiagnosticos(evolucoes, consultas);
  const tratamentos = coletarTratamentos(evolucoes, prescricoes);
  const alergias = paciente.alergias.trim() ? [paciente.alergias] : [];
  const cirurgias = coletarCirurgias(evolucoes);

  return (
    <aside className="flex min-h-[420px] border-l border-slate-200 bg-white">
      <div className="flex w-10 flex-col items-center gap-3 border-r border-slate-100 py-3 text-slate-400">
        <IconBtn ativo={painel === 'clinico'} title="Resumo clínico" onClick={() => setPainel('clinico')}>
          <BriefcaseMedical className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'evolucoes'} title="Evoluções" onClick={() => setPainel('evolucoes')}>
          <ClipboardList className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'anexos'} title="Anexos" onClick={() => setPainel('anexos')}>
          <Paperclip className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'chat'} title="Mensagens" onClick={() => setPainel('chat')}>
          <MessageCircle className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'tele'} title="Teleconsulta" onClick={() => setPainel('tele')}>
          <Video className="h-4 w-4" />
        </IconBtn>
      </div>

      <div className="w-[300px] min-w-[240px] p-3">
        {painel === 'clinico' ? (
          <>
            <button type="button" onClick={() => setAberto((v) => !v)} className="mb-3 flex w-full items-center justify-between text-left">
              <span className="text-xs font-bold tracking-wide text-slate-700">RESUMO CLÍNICO</span>
              <ChevronRight className={`h-4 w-4 text-slate-400 transition ${aberto ? 'rotate-90' : ''}`} />
            </button>
            {aberto ? (
              <>
                <div className="mb-3 flex flex-wrap gap-2 text-xs">
                  {ABAS.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setAba(item.id)}
                      className={`inline-flex items-center gap-1 pb-0.5 ${aba === item.id ? 'font-semibold' : 'text-slate-400'}`}
                      style={aba === item.id ? { boxShadow: `inset 0 -2px 0 ${TEAL}`, color: TEAL } : undefined}
                    >
                      {item.label}
                      {item.id === 'DIAG' && diagnosticos.length > 0 ? (
                        <span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-400" />
                      ) : null}
                    </button>
                  ))}
                </div>
                {aba === 'DIAG' ? (
                  <TabelaDiag linhas={diagnosticos} />
                ) : (
                  <ListaSimples
                    vazio="Ainda não há informações"
                    itens={aba === 'TRAT' ? tratamentos : aba === 'ALEG' ? alergias : aba === 'CIR' ? cirurgias : []}
                  />
                )}
              </>
            ) : null}
          </>
        ) : null}

        {painel === 'evolucoes' ? (
          <ListaSimples
            titulo="Evoluções"
            vazio="Nenhuma evolução."
            itens={evolucoes.map((e) => e.avaliacao || e.subjetivo || `Consulta #${e.consulta}`)}
          />
        ) : null}
        {painel === 'anexos' ? (
          <div>
            <p className="mb-2 text-xs font-bold tracking-wide text-slate-700">ANEXOS</p>
            {anexos.length === 0 ? (
              <p className="text-sm text-slate-400">Nenhum anexo.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {anexos.map((a) => (
                  <li key={a.id}>
                    <a href={a.url} target="_blank" rel="noreferrer" className="underline" style={{ color: TEAL }}>
                      {a.nome}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
        {painel === 'chat' ? <p className="text-sm text-slate-400">Mensagens entram na agenda e no WhatsApp do consultório.</p> : null}
        {painel === 'tele' ? (
          <p className="text-sm text-slate-400">Gere o link e entre na sala pela tela do atendimento em andamento.</p>
        ) : null}
      </div>
    </aside>
  );
}

function TabelaDiag({ linhas }: { linhas: { texto: string; data: string; hora?: string }[] }) {
  if (linhas.length === 0) {
    return <p className="text-sm text-slate-400">Ainda não há informações</p>;
  }
  return (
    <div>
      <div className="mb-1 grid grid-cols-[1fr_auto] gap-2 text-[11px] text-slate-400">
        <span>Diagnósticos</span>
        <span>Data</span>
      </div>
      <ul className="space-y-2">
        {linhas.map((linha) => (
          <li key={`${linha.texto}-${linha.data}`} className="grid grid-cols-[1fr_auto] items-start gap-2 text-sm">
            <span className="line-clamp-2 text-slate-700">{linha.texto}</span>
            {linha.data ? (
              <span className="whitespace-nowrap text-[11px] text-slate-500">
                {formatMesAnoCurto(linha.data)} ({formatRelativo(linha.data, linha.hora)})
              </span>
            ) : (
              <span />
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function IconBtn({
  ativo,
  title,
  onClick,
  children,
}: {
  ativo: boolean;
  title: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className="rounded p-1.5"
      style={ativo ? { color: TEAL } : undefined}
    >
      {children}
    </button>
  );
}

function ListaSimples({ titulo, vazio, itens }: { titulo?: string; vazio: string; itens: string[] }) {
  return (
    <div>
      {titulo ? <p className="mb-2 text-xs font-bold tracking-wide text-slate-700">{titulo.toUpperCase()}</p> : null}
      {itens.length === 0 ? <p className="text-sm text-slate-400">{vazio}</p> : (
        <ul className="space-y-2 text-sm text-slate-700">
          {itens.map((texto, i) => (
            <li key={`${titulo || 'item'}-${i}`}>{texto}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
