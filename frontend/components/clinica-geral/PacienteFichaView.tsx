'use client';

import { Printer, User } from 'lucide-react';
import { ImageUploadMedia } from '@/components/ImageUploadMedia';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, Paciente, PacienteAnexo } from '@/lib/clinica-geral-types';
import { SEXO_LABEL, STATUS_LABEL, TIPO_CONSULTA_LABEL } from '@/lib/clinica-geral-types';
import {
  daysFromToday,
  displayName,
  formatDateBR,
  formatDaysOffset,
  formatEndereco,
  formatHora,
  formatNascimentoIdade,
} from '@/lib/clinica-geral-utils';

type PacienteFichaViewProps = {
  slug: string;
  paciente: Paciente;
  consultas: Consulta[];
  anexos: PacienteAnexo[];
  onVerProntuario: () => void;
  onEditar: () => void;
  onArquivar: () => void;
  onExcluir: () => void;
  onAddAnexo: (url: string, nome: string) => Promise<void>;
  onRemoveAnexo: (id: number) => Promise<void>;
};

export function PacienteFichaView({
  slug,
  paciente,
  consultas,
  anexos,
  onVerProntuario,
  onEditar,
  onArquivar,
  onExcluir,
  onAddAnexo,
  onRemoveAnexo,
}: PacienteFichaViewProps) {
  const endereco = formatEndereco(paciente);
  const agendamentos = [...consultas].sort((a, b) => {
    const byDate = b.data.localeCompare(a.data);
    if (byDate !== 0) return byDate;
    return (b.hora || '').localeCompare(a.hora || '');
  });

  return (
    <div className="grid gap-8 p-6 lg:grid-cols-[220px_minmax(0,1fr)_260px]">
      <aside className="space-y-5">
        <button
          type="button"
          className="w-full rounded-md py-2.5 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
          onClick={onVerProntuario}
        >
          Ver prontuário
        </button>
        <div className="mx-auto flex h-36 w-36 items-center justify-center overflow-hidden rounded-full bg-slate-200 text-slate-400">
          {paciente.foto_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={paciente.foto_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <User className="h-16 w-16" />
          )}
        </div>
        <section>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700">Agendamentos</h3>
            <button
              type="button"
              className="text-slate-400 hover:text-slate-600"
              title="Imprimir agendamentos"
              onClick={() => window.print()}
            >
              <Printer className="h-4 w-4" />
            </button>
          </div>
          {agendamentos.length === 0 ? (
            <p className="text-xs text-slate-400">Nenhum agendamento.</p>
          ) : (
            <ul className="space-y-2">
              {agendamentos.map((c) => (
                <li
                  key={c.id}
                  className="rounded-md px-2 py-2 text-xs"
                  style={c.status === 'confirmado' ? { backgroundColor: '#EDE7F6' } : undefined}
                >
                  <a href={`/loja/${slug}/clinica-geral/consultas/${c.id}`} className="block hover:opacity-80">
                    <div className="flex flex-wrap items-baseline gap-x-2 text-slate-700">
                      <span className="font-medium">
                        {formatDateBR(c.data)} {formatHora(c.hora)}
                      </span>
                      <span className="text-slate-400">{formatDaysOffset(daysFromToday(c.data))}</span>
                    </div>
                    <div className="mt-0.5 flex flex-wrap gap-x-2 text-slate-500">
                      <span>{STATUS_LABEL[c.status]}</span>
                      <span>{TIPO_CONSULTA_LABEL[c.tipo]}</span>
                    </div>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>
      </aside>

      <section>
        <dl className="grid grid-cols-1 gap-x-10 gap-y-5 sm:grid-cols-2">
          <Field label="Número do prontuário" value={paciente.numero_prontuario} />
          <Field label="Nome" value={displayName(paciente.nome, paciente.nome_social)} />
          <Field label="Celular" value={paciente.telefone} />
          <Field label="Cpf" value={paciente.cpf} />
          <Field label="E-mail" value={paciente.email} />
          <Field label="Data de nascimento" value={formatNascimentoIdade(paciente.data_nascimento)} />
          <Field label="Sexo" value={SEXO_LABEL[paciente.sexo]} />
          <Field label="Estado civil" value={paciente.estado_civil} />
          <Field label="Nacionalidade" value={paciente.nacionalidade} />
          <Field label="Profissão" value={paciente.profissao} />
          <Field label="Tipo Sanguíneo" value={paciente.tipo_sanguineo} />
          <div className="sm:col-span-2">
            <dt className="text-xs text-slate-400">Endereço</dt>
            <dd className="whitespace-pre-line text-slate-800">{endereco || '—'}</dd>
          </div>
        </dl>

        {paciente.alergias ? (
          <p className="mt-5 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">Alergias: {paciente.alergias}</p>
        ) : null}

        <div className="mt-6 min-h-[88px] rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {paciente.observacoes || ''}
        </div>

        <div className="mt-8 flex flex-wrap justify-end gap-2">
          <button type="button" onClick={onArquivar} className="rounded-md border border-red-400 px-3 py-2 text-sm text-red-600">
            Arquivar paciente
          </button>
          <button type="button" onClick={onExcluir} className="rounded-md border border-red-400 px-3 py-2 text-sm text-red-600">
            Excluir paciente
          </button>
          <button
            type="button"
            onClick={onEditar}
            className="rounded-md border px-4 py-2 text-sm"
            style={{ borderColor: TEAL, color: TEAL }}
          >
            Editar
          </button>
        </div>
      </section>

      <aside>
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Anexos</h3>
        <ImageUploadMedia
          compact
          folder="docs"
          accept="image/*,.pdf,.doc,.docx"
          buttonLabel="Adicionar Documento"
          patientId={paciente.id}
          patientNome={paciente.nome}
          patientCpf={paciente.cpf}
          onChange={(url) => {
            if (!url) return;
            const nome = decodeURIComponent(url.split('/').pop() || 'Documento');
            void onAddAnexo(url, nome);
          }}
        />
        <ul className="mt-4 space-y-2">
          {anexos.map((a) => (
            <li key={a.id} className="flex items-start justify-between gap-2 text-sm">
              <a href={a.url} target="_blank" rel="noreferrer" className="break-all underline" style={{ color: TEAL }}>
                {a.nome}
              </a>
              <button type="button" className="shrink-0 text-xs text-red-500" onClick={() => void onRemoveAnexo(a.id)}>
                Remover
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="text-slate-800">{value || '—'}</dd>
    </div>
  );
}
