"use client";

/**
 * Cadastro de Profissionais - Clínica da Beleza
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Pencil, Trash2, Clock, Timer } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ModalHorariosTrabalho } from "@/components/clinica-beleza/ModalHorariosTrabalho";
import { ModalTempoConsulta } from "@/components/clinica-beleza/ModalTempoConsulta";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { ProfissionalFormPageContent } from "@/components/clinica-beleza/ProfissionalFormPageContent";
import { deleteClinicaBelezaEntity, useClinicaBelezaEntityList } from "@/lib/clinica-beleza-crud";
import {
  entityActive,
  entityName,
  entityPhone,
  professionalSpecialty,
} from "@/lib/clinica-beleza-entities";
import { buscarProfissionaisOffline, salvarProfissionaisOffline } from "@/lib/offline-db";

interface Professional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
  especialidade?: string;
  phone?: string | null;
  telefone?: string | null;
  email?: string | null;
  registro_profissional?: string | null;
  conselho?: string | null;
  conselho_uf?: string | null;
  cpf?: string | null;
  data_nascimento?: string | null;
  sexo?: string | null;
  active?: boolean;
  is_active?: boolean;
  is_administrador_vinculado?: boolean;
  tempo_consulta_minutos?: number | null;
}

interface LojaOwnerInfo {
  owner_username: string;
  owner_email: string;
  owner_telefone: string;
}

export default function ProfissionaisPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/profissionais`;
  const isNovo = searchParams.get("novo") === "1";
  const editIdParam = searchParams.get("id");
  const isFormView = isNovo || Boolean(editIdParam);
  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } = useClinicaBelezaEntityList<Professional>({
    path: "/professionals/",
    fetchOffline: buscarProfissionaisOffline,
    saveOffline: salvarProfissionaisOffline,
  });
  const [lojaOwnerInfo, setLojaOwnerInfo] = useState<LojaOwnerInfo | null>(null);
  const [horariosProfessional, setHorariosProfessional] = useState<Professional | null>(null);
  const [tempoConsultaProfessional, setTempoConsultaProfessional] = useState<Professional | null>(null);

  const loadLojaInfo = async () => {
    if (!navigator.onLine) return;
    try {
      const data = await ClinicaBelezaAPI.loja.info();
      setLojaOwnerInfo({
        owner_username: data.owner_username ?? "",
        owner_email: data.owner_email ?? "",
        owner_telefone: data.owner_telefone ?? "",
      });
    } catch {
      setLojaOwnerInfo(null);
    }
  };

  useEffect(() => {
    loadLojaInfo();
  }, []);

  const voltarLista = () => {
    router.replace(basePath, { scroll: false });
  };

  const openNew = () => {
    router.replace(`${basePath}?novo=1`, { scroll: false });
  };

  const openEdit = (p: Professional) => {
    router.replace(`${basePath}?id=${p.id}`, { scroll: false });
  };

  const exclude = async (p: Professional) => {
    if (!confirm(`Desativar o profissional "${entityName(p)}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/professionals/${p.id}/`);
      load();
    } catch {
      alert("Erro ao desativar.");
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
        onNew={openNew}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : activeList.length === 0 ? (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
            Nenhum profissional cadastrado. Clique em &quot;Novo Profissional&quot; para começar.
          </div>
        ) : (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300">
                  <tr>
                    <th className="text-left p-3">Nome</th>
                    <th className="text-left p-3">Especialidade</th>
                    <th className="text-left p-3 hidden md:table-cell">Telefone</th>
                    <th className="min-w-[140px] p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{professionalSpecialty(p) || "—"}</td>
                      <td className="p-3 hidden md:table-cell text-gray-700 dark:text-gray-300">{entityPhone(p) || "—"}</td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1.5">
                          {p.is_administrador_vinculado ? (
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
                              <button
                                type="button"
                                onClick={() => openEdit(p)}
                                className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                                title="Editar"
                              >
                                <Pencil size={18} />
                              </button>
                            </>
                          ) : (
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
                              <button
                                type="button"
                                onClick={() => openEdit(p)}
                                className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                                title="Editar"
                              >
                                <Pencil size={18} />
                              </button>
                              <button
                                onClick={() => exclude(p)}
                                className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                                title="Desativar"
                              >
                                <Trash2 size={18} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
