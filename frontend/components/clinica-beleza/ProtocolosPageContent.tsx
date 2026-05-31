'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { Pencil, Trash2, X, ClipboardList } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
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
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';

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

const emptyForm = {
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
  const protocolosPath = useMemo(
    () =>
      defaultCategoria
        ? `/protocolos?categoria=${encodeURIComponent(defaultCategoria)}`
        : '/protocolos',
    [defaultCategoria],
  );
  const { list, loading, load } = useClinicaBelezaEntityList<Protocol>({
    path: protocolosPath,
    ...CLINICA_BELEZA_ONLINE_ONLY,
    reloadDeps: [defaultCategoria],
  });
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Protocol | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadProcedures = useCallback(async () => {
    try {
      const procRes = await clinicaBelezaFetch('/procedures/');
      if (!procRes.ok) {
        setProcedures([]);
        return;
      }
      const data = await procRes.json();
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

  const openNew = () => {
    setEditing(null);
    setForm(emptyForm);
    setError('');
    setShowModal(true);
  };

  const openEdit = (p: Protocol) => {
    setEditing(p);
    setForm({
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
    });
    setError('');
    setShowModal(true);
  };

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
      setShowModal(false);
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

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        icon={ClipboardList}
        newLabel="Novo protocolo"
        onNew={openNew}
      />
      <ClinicaBelezaPageContent>

        {loading ? (
          <p className="text-center py-12 text-gray-500">Carregando...</p>
        ) : list.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center text-gray-500 border border-gray-100 dark:border-gray-700">
            <p className="mb-2">Nenhum protocolo cadastrado.</p>
            <p className="text-sm mb-4">Protocolos padronizam seus procedimentos e garantem qualidade.</p>
            <button
              type="button"
              onClick={openNew}
              className="px-5 py-2 text-white rounded-lg text-sm"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              Criar primeiro protocolo
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {list.map((p) => (
              <div
                key={p.id}
                className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700"
              >
                <div className="flex justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{p.nome}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {p.procedure_name}
                      {p.procedure_categoria ? ` · ${p.procedure_categoria}` : ''}
                    </p>
                    {p.descricao && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">{p.descricao}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">⏱ {p.tempo_estimado} min</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => openEdit(p)}
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                      title="Editar"
                    >
                      <Pencil size={18} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                    </button>
                    <button
                      type="button"
                      onClick={() => exclude(p)}
                      className="p-2 rounded-lg hover:bg-red-50 text-red-600"
                      title="Desativar"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                {editing ? 'Editar protocolo' : 'Novo protocolo'}
              </h2>
              <button type="button" onClick={() => setShowModal(false)}>
                <X className="w-5 h-5" />
              </button>
            </div>
            {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
            <div className="space-y-3">
              <input
                className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600"
                placeholder="Nome do protocolo *"
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
              />
              <select
                className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600"
                value={form.procedure}
                onChange={(e) => setForm((f) => ({ ...f, procedure: e.target.value }))}
              >
                <option value="">Procedimento *</option>
                {procedures.map((pr) => (
                  <option key={pr.id} value={pr.id}>
                    {entityName(pr)}
                  </option>
                ))}
              </select>
              <input
                type="number"
                className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600"
                placeholder="Tempo estimado (min) *"
                value={form.tempo_estimado}
                onChange={(e) => setForm((f) => ({ ...f, tempo_estimado: e.target.value }))}
              />
              {(
                [
                  ['descricao', 'Descrição'],
                  ['materiais_necessarios', 'Materiais necessários'],
                  ['preparacao', 'Preparação'],
                  ['execucao', 'Execução (passos)'],
                  ['pos_procedimento', 'Pós-procedimento'],
                  ['contraindicacoes', 'Contraindicações'],
                  ['cuidados_especiais', 'Cuidados especiais'],
                ] as const
              ).map(([key, label]) => (
                <textarea
                  key={key}
                  className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-700 dark:border-gray-600"
                  placeholder={label}
                  rows={key === 'execucao' ? 4 : 2}
                  value={form[key]}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                />
              ))}
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border rounded-lg text-sm"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={save}
                disabled={saving}
                className="px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}

    </>
  );
}
