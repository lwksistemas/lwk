'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, ClipboardList, Pencil, Save, Trash2 } from 'lucide-react';
import { ClinicaBelezaAPI } from '@/lib/clinica-beleza-api';
import {
  CLINICA_BELEZA_ONLINE_ONLY,
  CLINICA_FORM_INPUT,
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from '@/lib/clinica-beleza-crud';
import { entityName, procedureCategoria } from '@/lib/clinica-beleza-entities';
import { procedureMatchesModule } from '@/lib/clinica-beleza-categories';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import { ClinicaBelezaRelatedLinks } from '@/components/clinica-beleza/ClinicaBelezaRelatedLinks';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { EntityListTable } from '@/components/clinica-beleza/EntityListTable';
import { EntityListLoadMore } from '@/components/clinica-beleza/EntityListLoadMore';
import { useClinicaBelezaFormRouting } from '@/hooks/clinica-beleza/useClinicaBelezaFormRouting';
import { toUpperCase } from '@/lib/format-br';

interface Protocol {
  id: number;
  nome: string;
  procedure: number;
  procedure_name?: string;
  procedure_categoria?: string;
  descricao?: string;
  tempo_estimado: number;
  materiais_necessarios?: string;
  preparacao?: string;
  execucao?: string;
  pos_procedimento?: string;
  contraindicacoes?: string;
  cuidados_especiais?: string;
  created_at?: string;
}

interface Procedure {
  id: number;
  nome?: string;
  name?: string;
  categoria?: string;
}

const EMPTY_FORM = {
  nome: '',
  procedure: '',
  descricao: '',
  tempo_estimado: '30',
  materiais_necessarios: '',
  preparacao: '',
  execucao: '',
  pos_procedimento: '',
  contraindicacoes: '',
  cuidados_especiais: '',
};

function protocolToForm(p: Protocol) {
  return {
    nome: p.nome || '',
    procedure: String(p.procedure),
    descricao: p.descricao || '',
    tempo_estimado: String(p.tempo_estimado || 30),
    materiais_necessarios: p.materiais_necessarios || '',
    preparacao: p.preparacao || '',
    execucao: p.execucao || '',
    pos_procedimento: p.pos_procedimento || '',
    contraindicacoes: p.contraindicacoes || '',
    cuidados_especiais: p.cuidados_especiais || '',
  };
}

export interface ProtocolosPageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}

export function ProtocolosPageContent({
  title = 'Protocolos',
  subtitle = 'Padronize procedimentos com etapas, materiais e cuidados',
  defaultCategoria = '',
  backHref,
  relatedLinks = [],
}: ProtocolosPageContentProps) {
  const params = useParams();
  const slug = params.slug as string;
  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting();

  const protocolosPath = useMemo(
    () =>
      defaultCategoria
        ? `/protocolos?categoria=${encodeURIComponent(defaultCategoria)}`
        : '/protocolos',
    [defaultCategoria],
  );

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } = useClinicaBelezaEntityList<Protocol>({
    path: protocolosPath,
    ...CLINICA_BELEZA_ONLINE_ONLY,
    reloadDeps: [defaultCategoria],
  });

  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [editing, setEditing] = useState<Protocol | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadProcedures = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.procedures.list();
      const arr = Array.isArray(data) ? data : [];
      setProcedures(
        defaultCategoria
          ? arr.filter((p: Procedure) => procedureMatchesModule(procedureCategoria(p), defaultCategoria))
          : arr,
      );
    } catch {
      setProcedures([]);
    }
  }, [defaultCategoria]);

  useEffect(() => {
    loadProcedures();
  }, [loadProcedures]);

  useEffect(() => {
    if (!isFormView) return;
    if (isNovo) {
      setEditing(null);
      setForm(EMPTY_FORM);
      setError('');
      return;
    }
    if (editIdParam && list.length > 0) {
      const p = list.find((x) => String(x.id) === editIdParam);
      if (p) {
        setEditing(p);
        setForm(protocolToForm(p));
        setError('');
      }
    }
  }, [isFormView, isNovo, editIdParam, list]);

  const save = async () => {
    if (!form.nome.trim() || !form.procedure) {
      setError('Nome e procedimento são obrigatórios.');
      return;
    }
    setSaving(true);
    setError('');
    const body = {
      nome: form.nome.trim(),
      procedure: Number(form.procedure),
      descricao: form.descricao.trim(),
      tempo_estimado: Number(form.tempo_estimado) || 30,
      materiais_necessarios: form.materiais_necessarios.trim(),
      preparacao: form.preparacao.trim(),
      execucao: form.execucao.trim(),
      pos_procedimento: form.pos_procedimento.trim(),
      contraindicacoes: form.contraindicacoes.trim(),
      cuidados_especiais: form.cuidados_especiais.trim(),
    };
    try {
      if (editing) {
        await saveClinicaBelezaEntity(`/protocolos/${editing.id}/`, 'PUT', body);
      } else {
        await saveClinicaBelezaEntity('/protocolos/', 'POST', body);
      }
      voltarLista();
      load();
    } catch (e: unknown) {
      if (e instanceof Error && e.message === 'SESSION_ENDED') return;
      const msg =
        e && typeof e === 'object' && 'error' in e && typeof (e as { error?: string }).error === 'string'
          ? (e as { error: string }).error
          : 'Erro ao salvar protocolo.';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const exclude = async (p: Protocol) => {
    if (!confirm(`Desativar o protocolo "${p.nome}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/protocolos/${p.id}/`);
      load();
    } catch {
      alert('Erro ao desativar.');
    }
  };

  const formFields = (
    [
      ['descricao', 'Descrição'],
      ['materiais_necessarios', 'Materiais necessários'],
      ['preparacao', 'Preparação'],
      ['execucao', 'Execução (passos)'],
      ['pos_procedimento', 'Pós-procedimento'],
      ['contraindicacoes', 'Contraindicações'],
      ['cuidados_especiais', 'Cuidados especiais'],
    ] as const
  );

  if (isFormView) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? 'Editar protocolo' : 'Novo protocolo'}
          subtitle={editing ? editing.nome : 'Padronize etapas e cuidados do procedimento'}
          onBack={voltarLista}
          icon={ClipboardList}
        />
        <ClinicaBelezaPageContent>
          <ClinicaBelezaPanel className="p-6 md:p-8 max-w-3xl">
            {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
            <div className="space-y-4">
              <input
                className={CLINICA_FORM_INPUT}
                placeholder="Nome do protocolo *"
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: toUpperCase(e.target.value) }))}
              />
              <select
                className={CLINICA_FORM_INPUT}
                value={form.procedure}
                onChange={(e) => setForm((f) => ({ ...f, procedure: e.target.value }))}
              >
                <option value="">Procedimento *</option>
                {procedures.map((pr) => (
                  <option key={pr.id} value={pr.id}>{entityName(pr)}</option>
                ))}
              </select>
              <input
                type="number"
                className={CLINICA_FORM_INPUT}
                placeholder="Tempo estimado (min) *"
                value={form.tempo_estimado}
                onChange={(e) => setForm((f) => ({ ...f, tempo_estimado: e.target.value }))}
              />
              {formFields.map(([key, label]) => (
                <textarea
                  key={key}
                  className={`${CLINICA_FORM_INPUT} resize-none`}
                  placeholder={label}
                  rows={key === 'execucao' ? 4 : 2}
                  value={form[key]}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                />
              ))}
            </div>
            <div className="flex gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-neutral-700">
              <button type="button" onClick={voltarLista} className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border text-sm font-medium">
                <ArrowLeft size={16} />
                Cancelar
              </button>
              <button
                type="button"
                onClick={save}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                <Save size={16} />
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </ClinicaBelezaPanel>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        icon={ClipboardList}
        newLabel="Novo protocolo"
        onNew={abrirNovo}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <p className="text-center py-16 text-gray-500">Carregando...</p>
        ) : list.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhum protocolo cadastrado. Clique em <strong>Novo protocolo</strong> para começar.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <EntityListTable
              rows={list}
              rowKey={(p) => p.id}
              onRowClick={(p) => abrirEditar(p.id)}
              columns={[
                {
                  key: 'nome',
                  header: 'Protocolo',
                  render: (p) => (
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{p.nome}</p>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {p.procedure_name}
                        {p.procedure_categoria ? ` · ${p.procedure_categoria}` : ''}
                      </p>
                    </div>
                  ),
                },
                {
                  key: 'tempo',
                  header: 'Duração',
                  className: 'hidden sm:table-cell',
                  render: (p) => <span className="text-gray-600">{p.tempo_estimado} min</span>,
                },
                {
                  key: 'desc',
                  header: 'Descrição',
                  className: 'hidden md:table-cell',
                  render: (p) => (
                    <span className="text-sm text-gray-500 line-clamp-1">{p.descricao || '—'}</span>
                  ),
                },
              ]}
              trailingCell={(p) => (
                <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                  <button type="button" onClick={() => abrirEditar(p.id)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700" title="Editar">
                    <Pencil size={16} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                  </button>
                  <button type="button" onClick={() => exclude(p)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="Desativar">
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            />
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount ?? 0}
              pageSize={pageSize}
              loading={loading}
              onPageChange={setPage}
              itemLabel="protocolos"
            />
          </ClinicaBelezaPanel>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>
    </>
  );
}
