'use client';

import { useState } from 'react';
import { CalendarX, Check, Clock, MessageCircle, Pencil, X } from 'lucide-react';
import { cancelarConsulta, listHorariosLivres, updateConsulta, updateConsultaStatus } from '@/lib/clinica-geral-api';
import type { Consulta, DiaHorariosLivres, StatusConsulta } from '@/lib/clinica-geral-types';
import { MODALIDADE_LABEL, STATUS_LABEL, TIPO_CONSULTA_LABEL } from '@/lib/clinica-geral-types';
import { formatHora, formatShortDate, whatsappHref } from '@/lib/clinica-geral-utils';

type ResumoAgendamentoProps = {
  consulta: Consulta;
  slug: string;
  onClose: () => void;
  onChanged: () => Promise<void>;
  onRecepcionar: () => void;
};

export function ResumoAgendamento({ consulta, slug, onClose, onChanged, onRecepcionar }: ResumoAgendamentoProps) {
  const [busy, setBusy] = useState<string | null>(null);
  const [remarcar, setRemarcar] = useState(false);
  const [livres, setLivres] = useState<DiaHorariosLivres[]>([]);

  const wa = whatsappHref(consulta.paciente_telefone);

  const agir = async (acao: StatusConsulta | 'desmarcar') => {
    setBusy(acao);
    try {
      if (acao === 'desmarcar') await cancelarConsulta(consulta.id);
      else await updateConsultaStatus(consulta.id, acao);
      await onChanged();
    } finally {
      setBusy(null);
    }
  };

  const abrirRemarcar = async () => {
    setRemarcar(true);
    const dias = await listHorariosLivres(consulta.data);
    setLivres(dias);
  };

  const escolherSlot = async (data: string, hora: string) => {
    setBusy('remarcar');
    try {
      await updateConsulta(consulta.id, { data, hora: `${hora}:00`, status: 'agendado' });
      await onChanged();
    } finally {
      setBusy(null);
      setRemarcar(false);
    }
  };

  const acoes = acoesDoStatus(consulta.status);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/20">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between px-5 py-4">
          <h2 className="text-lg font-semibold text-slate-800">Resumo do agendamento</h2>
          <button type="button" onClick={onClose} aria-label="Fechar">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-auto px-5 pb-4 text-sm">
          <p className="text-lg font-medium">
            {consulta.paciente_nome}
            {consulta.paciente_prontuario ? ` — ${consulta.paciente_prontuario}` : ''}
          </p>
          <p className="capitalize text-slate-500">
            {formatShortDate(consulta.data)} às {formatHora(consulta.hora)}
          </p>
          <div className="flex gap-2">
            <a
              href={`/loja/${slug}/clinica-geral/pacientes/${consulta.paciente}`}
              className="rounded border border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
              title="Editar paciente"
            >
              <Pencil className="h-4 w-4" />
            </a>
            {wa && (
              <a href={wa} target="_blank" rel="noreferrer" className="rounded border border-slate-200 p-2 text-green-600 hover:bg-green-50" title="WhatsApp">
                <MessageCircle className="h-4 w-4" />
              </a>
            )}
          </div>
          <dl className="space-y-2 border-t border-slate-100 pt-3">
            <Linha label="Tipo de consulta" value={TIPO_CONSULTA_LABEL[consulta.tipo]} />
            <Linha label="Tipo de atendimento" value={MODALIDADE_LABEL[consulta.modalidade]} />
            <Linha label="Convênio" value={consulta.convenio || 'PARTICULAR'} />
            <Linha label="E-mail" value={consulta.paciente_email || '—'} />
            <Linha label="Celular" value={consulta.paciente_telefone || '—'} />
            <Linha label="Agendado por" value={consulta.agendado_por || '—'} />
            <Linha label="Status" value={STATUS_LABEL[consulta.status]} />
          </dl>

          {remarcar && (
            <div className="rounded-md border border-slate-200 p-3">
              <p className="mb-2 text-sm font-medium">Escolha o novo horário</p>
              {livres.map((dia) => (
                <div key={dia.data} className="mb-2">
                  <p className="mb-1 text-xs capitalize text-slate-500">{formatShortDate(dia.data)}</p>
                  <div className="grid grid-cols-4 gap-1">
                    {dia.horarios.slice(0, 24).map((h) => (
                      <button
                        key={h}
                        type="button"
                        disabled={busy !== null}
                        onClick={() => void escolherSlot(dia.data, h)}
                        className="rounded border border-slate-200 px-1 py-1 text-xs hover:border-teal-400"
                      >
                        {h}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="border-t border-slate-100 px-5 py-4">
          <p className="mb-2 text-sm font-medium text-slate-700">O que você gostaria de fazer agora?</p>
          <div className="grid grid-cols-2 gap-2">
            {acoes.map((a) => (
              <button
                key={a.id}
                type="button"
                disabled={busy !== null}
                onClick={() => {
                  if (a.id === 'recepcionar') onRecepcionar();
                  else if (a.id === 'remarcar') void abrirRemarcar();
                  else void agir(a.id);
                }}
                className="flex items-center justify-center gap-1.5 rounded-md border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-60"
              >
                {a.icon}
                {busy === a.id ? '...' : a.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Linha({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function acoesDoStatus(status: StatusConsulta) {
  const confirmar = { id: 'confirmado' as const, label: 'Confirmar', icon: <Check className="h-4 w-4" /> };
  const recepcionar = { id: 'recepcionar' as const, label: 'Recepcionar', icon: <Clock className="h-4 w-4" /> };
  const atendido = { id: 'atendido' as const, label: 'Atendido', icon: <Check className="h-4 w-4" /> };
  const desmarcar = { id: 'desmarcar' as const, label: 'Desmarcar', icon: <CalendarX className="h-4 w-4" /> };
  const remarcar = { id: 'remarcar' as const, label: 'Remarcar', icon: <Clock className="h-4 w-4" /> };
  const faltou = { id: 'faltou' as const, label: 'Faltou', icon: <X className="h-4 w-4" /> };

  if (status === 'recepcionado') return [atendido, desmarcar, remarcar];
  if (status === 'atendido') return [desmarcar, remarcar];
  if (status === 'confirmado') return [recepcionar, desmarcar, remarcar, faltou];
  if (status === 'faltou') return [remarcar];
  return [confirmar, recepcionar, desmarcar, remarcar, faltou];
}
