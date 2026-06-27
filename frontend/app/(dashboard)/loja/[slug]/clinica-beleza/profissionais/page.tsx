'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Pencil, Trash2, Clock, Timer } from 'lucide-react';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { EntityListLoadMore } from '@/components/clinica-beleza/EntityListLoadMore';
import { EntityListTable } from '@/components/clinica-beleza/EntityListTable';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { ModalHorariosTrabalho } from '@/components/clinica-beleza/ModalHorariosTrabalho';
import { ModalTempoConsulta } from '@/components/clinica-beleza/ModalTempoConsulta';
import { ClinicaBelezaAPI } from '@/lib/clinica-beleza-api';
import { ProfissionalFormPageContent } from '@/components/clinica-beleza/ProfissionalFormPageContent';
import { AdminProfissionalToggle } from '@/components/clinica-beleza/AdminProfissionalToggle';
import { deleteClinicaBelezaEntity, useClinicaBelezaEntityList } from '@/lib/clinica-beleza-crud';
import { useClinicaBelezaFormRouting } from '@/hooks/clinica-beleza/useClinicaBelezaFormRouting';
import {
  entityActive,
  entityName,
  entityPhone,
  professionalSpecialty,
  type ClinicaProfessional,
} from '@/lib/clinica-beleza-entities';
import { buscarProfissionaisOffline, salvarProfissionaisOffline } from '@/lib/offline-db';
import { useState } from 'react';

export default function ProfissionaisPage() {
  const params = useParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/profissionais`;
  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting(basePath);

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<ClinicaProfessional>({
      path: '/professionals/',
      fetchOffline: buscarProfissionaisOffline,
      saveOffline: salvarProfissionaisOffline,
    });

  const [horariosProfessional, setHorariosProfessional] = useState<ClinicaProfessional | null>(null);
  const [tempoConsultaProfessional, setTempoConsultaProfessional] =
    useState<ClinicaProfessional | null>(null);

  const exclude = async (p: ClinicaProfessional) => {
    if (!confirm(`Desativar o profissional "${entityName(p)}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/professionals/${p.id}/`);
      load();
    } catch {
      alert('Erro ao desativar.');
    }
  };

  const toggleProfissional = async (p: ClinicaProfessional) => {
    const novoValor = !(p.is_profissional ?? true);
    try {
      await ClinicaBelezaAPI.patch(`/professionals/${p.id}/`, { is_profissional: novoValor });
      load();
    } catch (err: unknown) {
      const msg =
        (err as { error?: string })?.error ||
        (err as { detail?: string })?.detail ||
        'Erro ao alterar status.';
      alert(msg);
    }
  };

  const activeList = list.filter((p) => entityActive(p));

  if (isFormView) {
    return (
      <ProfissionalFormPageContent
        slug={slug}
        editId={isNovo ? null : editIdParam}
        onDone={() => {
          voltarLista();
          load();
        }}
      />
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Profissionais"
        subtitle="Cadastro de profissionais da clínica"
        newLabel="Novo Profissional"
        onNew={abrirNovo}
      />
      <ClinicaBelezaPageContent>
        <AdminProfissionalToggle onToggled={load} />
        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
            <EntityListTable
              rows={activeList}
              rowKey={(p) => p.id}
              emptyMessage={
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  Nenhum profissional cadastrado. Clique em &quot;Novo Profissional&quot; para começar.
                </div>
              }
              columns={[
                {
                  key: 'nome',
                  header: 'Nome',
                  render: (p) => (
                    <span className="font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</span>
                  ),
                },
                {
                  key: 'especialidade',
                  header: 'Especialidade',
                  render: (p) => (
                    <span className="text-gray-700 dark:text-gray-300">
                      {professionalSpecialty(p) || '—'}
                    </span>
                  ),
                },
                {
                  key: 'telefone',
                  header: 'Telefone',
                  className: 'hidden md:table-cell',
                  render: (p) => (
                    <span className="text-gray-700 dark:text-gray-300">{entityPhone(p) || '—'}</span>
                  ),
                },
                {
                  key: 'acoes',
                  header: 'Ações',
                  render: (p) => (
                    <div className="flex flex-wrap gap-1.5" onClick={(e) => e.stopPropagation()}>
                      {p.is_administrador_vinculado && (
                        <label
                          className="inline-flex items-center gap-2 cursor-pointer select-none"
                          title={
                            (p.is_profissional ?? true)
                              ? 'Desmarcar para ficar só como administrador'
                              : 'Marcar para atuar também como profissional'
                          }
                        >
                          <input
                            type="checkbox"
                            checked={p.is_profissional ?? true}
                            onChange={() => toggleProfissional(p)}
                            className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500 dark:border-neutral-600 dark:bg-neutral-700"
                          />
                        </label>
                      )}
                      {(p.is_profissional ?? true) && (
                        <>
                          <button
                            type="button"
                            onClick={() => setHorariosProfessional(p)}
                            className="p-2 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded"
                            title="Dias e horários de trabalho"
                          >
                            <Clock size={18} />
                          </button>
                          <button
                            type="button"
                            onClick={() => setTempoConsultaProfessional(p)}
                            className="p-2 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/30 rounded"
                            title="Tempo da consulta (min)"
                          >
                            <Timer size={18} />
                          </button>
                        </>
                      )}
                      <button
                        type="button"
                        onClick={() => abrirEditar(p.id)}
                        className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                        title="Editar"
                      >
                        <Pencil size={18} />
                      </button>
                      {!p.is_owner && (
                        <button
                          type="button"
                          onClick={() => exclude(p)}
                          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                          title="Desativar"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  ),
                },
              ]}
            />
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount ?? 0}
              pageSize={pageSize}
              loading={loading}
              onPageChange={setPage}
              itemLabel="profissionais"
            />
          </div>
        )}
      </ClinicaBelezaPageContent>

      {horariosProfessional && (
        <ModalHorariosTrabalho
          professionalId={horariosProfessional.id}
          professionalName={entityName(horariosProfessional)}
          onClose={() => setHorariosProfessional(null)}
          onSaved={() => load()}
        />
      )}

      {tempoConsultaProfessional && (
        <ModalTempoConsulta
          professionalId={tempoConsultaProfessional.id}
          professionalName={entityName(tempoConsultaProfessional)}
          onClose={() => setTempoConsultaProfessional(null)}
          onSaved={() => load()}
        />
      )}
    </>
  );
}
