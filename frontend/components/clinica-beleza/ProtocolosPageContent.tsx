'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { ClipboardList, Loader2, Pencil, Save, Trash2 } from 'lucide-react';
import { ClinicaBelezaAPI } from '@/lib/clinica-beleza-api';
import {
  CLINICA_BELEZA_ONLINE_ONLY,
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
import { useLojaTheme } from '@/hooks/useLojaTheme';
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
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;
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

  const formFieldsLeft = [['descricao', 'Descrição']] as const;
  const formFieldsRight = (
    [
      ['materiais_necessarios', 'Materiais necessários'],
      ['preparacao', 'Preparação'],
      ['execucao', 'Execução (passos)'],
      ['pos_procedimento', 'Pós-procedimento'],
      ['contraindicacoes', 'Contraindicações'],
      ['cuidados_especiais', 'Cuidados especiais'],
    ] as const
  );

  if (isFormView) {
    const inputClass =
      'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0';
    const labelClass = 'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';
    const sectionTitleClass =
      'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2';

    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? 'Editar protocolo' : 'Novo protocolo'}
          subtitle={editing ? editing.nome : 'Cadastro de protocolo da clínica'}
          onBack={voltarLista}
          icon={ClipboardList}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[#f7f2f4] dark:!bg-gray-950">
          <div className="flex flex-col flex-1 min-h-0 w-full">
            <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f7f2f4] dark:bg-gray-950">
              {error && (
                <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                  {error}
                </div>
              )}

              <ClinicaBelezaPanel className="p-5 md:p-6 lg:p-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full max-w-none">
                  <div className="space-y-4">
                    <p className={sectionTitleClass}>Dados do protocolo</p>
                    <div>
                      <label className={labelClass}>Nome *</label>
                      <input
                        value={form.nome}
                        onChange={(e) => setForm((f) => ({ ...f, nome: toUpperCase(e.target.value) }))}
                        className={inputClass}
                        placeholder="Ex.: Protocolo limpeza de pele"
                        autoFocus
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className={labelClass}>Procedimento *</label>
                        <select
                          value={form.procedure}
                          onChange={(e) => setForm((f) => ({ ...f, procedure: e.target.value }))}
                          className={inputClass}
                        >
                          <option value="">Selecione...</option>
                          {procedures.map((pr) => (
                            <option key={pr.id} value={pr.id}>
                              {entityName(pr)}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className={labelClass}>Tempo estimado (min) *</label>
                        <input
                          type="number"
                          min={1}
                          value={form.tempo_estimado}
                          onChange={(e) => setForm((f) => ({ ...f, tempo_estimado: e.target.value }))}
                          className={inputClass}
                        />
                      </div>
                    </div>
                    {formFieldsLeft.map(([key, label]) => (
                      <div key={key}>
                        <label className={labelClass}>{label}</label>
                        <textarea
                          value={form[key]}
                          onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                          rows={4}
                          className={`${inputClass} resize-y min-h-[96px]`}
                          placeholder="Opcional"
                        />
                      </div>
                    ))}
                  </div>

                  <div className="space-y-4">
                    <p className={sectionTitleClass}>Etapas e cuidados</p>
                    {formFieldsRight.map(([key, label]) => (
                      <div key={key}>
                        <label className={labelClass}>{label}</label>
                        <textarea
                          value={form[key]}
                          onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                          rows={key === 'execucao' ? 5 : 3}
                          className={`${inputClass} resize-y min-h-[72px]`}
                          placeholder={label}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </ClinicaBelezaPanel>
            </div>

            <div className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/80 px-4 md:px-6 lg:px-8 py-4">
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 w-full">
                <button
                  type="button"
                  onClick={voltarLista}
                  className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-neutral-800"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={save}
                  disabled={saving}
                  className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                  style={{ backgroundColor: accentColor }}
                >
                  {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                  {saving ? 'Salvando...' : editing ? 'Salvar alterações' : 'Cadastrar protocolo'}
                </button>
              </div>
            </div>
          </div>
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
