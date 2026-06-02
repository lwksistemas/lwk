"use client";

/**
 * Cadastro de Profissionais - Clínica da Beleza
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Pencil, Trash2, Clock } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ModalHorariosTrabalho } from "@/components/clinica-beleza/ModalHorariosTrabalho";
import { MemedStatusBadge, type MemedStatusInfo } from "./components/MemedStatusBadge";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { deleteClinicaBelezaEntity, useClinicaBelezaEntityList } from "@/lib/clinica-beleza-crud";
import {
  entityActive,
  entityName,
  entityPhone,
  professionalSpecialty,
} from "@/lib/clinica-beleza-entities";
import { buscarProfissionaisOffline, salvarProfissionaisOffline } from "@/lib/offline-db";
import { logger } from "@/lib/logger";

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
}

interface LojaOwnerInfo {
  owner_username: string;
  owner_email: string;
  owner_telefone: string;
}

export default function ProfissionaisPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { list, setList, loading, load } = useClinicaBelezaEntityList<Professional>({
    path: "/professionals/",
    fetchOffline: buscarProfissionaisOffline,
    saveOffline: salvarProfissionaisOffline,
  });
  const [memedStatus, setMemedStatus] = useState<Record<number, MemedStatusInfo>>({});
  const [memedStatusLoading, setMemedStatusLoading] = useState(false);
  const [lojaOwnerInfo, setLojaOwnerInfo] = useState<LojaOwnerInfo | null>(null);
  const [horariosProfessional, setHorariosProfessional] = useState<Professional | null>(null);

  const loadLojaInfo = async () => {
    if (!navigator.onLine) return;
    try {
      const res = await clinicaBelezaFetch("/loja-info/");
      if (res.ok) {
        const data = await res.json();
        setLojaOwnerInfo({
          owner_username: data.owner_username ?? "",
          owner_email: data.owner_email ?? "",
          owner_telefone: data.owner_telefone ?? "",
        });
      }
    } catch {
      setLojaOwnerInfo(null);
    }
  };

  const loadMemedStatus = useCallback(async () => {
    if (!navigator.onLine) return;
    setMemedStatusLoading(true);
    try {
      const data = await ClinicaBelezaAPI.professionals.memedStatus();
      const parsed: Record<number, MemedStatusInfo> = {};
      for (const [k, v] of Object.entries(data || {})) {
        parsed[Number(k)] = v;
      }
      setMemedStatus(parsed);
    } catch (err) {
      logger.warn("Erro ao carregar status Memed:", err);
    } finally {
      setMemedStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLojaInfo();
  }, []);

  useEffect(() => {
    if (!loading) void loadMemedStatus();
  }, [loading, list, loadMemedStatus]);

  const openNew = () => {
    router.push(`/loja/${slug}/clinica-beleza/profissionais/novo`);
  };

  const openEdit = (p: Professional) => {
    router.push(`/loja/${slug}/clinica-beleza/profissionais/novo?id=${p.id}`);
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

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Profissionais"
        subtitle="Cadastro de profissionais da clínica"
        newLabel="Novo Profissional"
        onNew={openNew}
      />
      <ClinicaBelezaPageContent>
        {lojaOwnerInfo && (
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
            <span className="text-amber-700 dark:text-amber-400">O administrador da loja aparece na tabela abaixo (linha &quot;Administrador - somente leitura&quot;) e não pode ser editado nem excluído.</span>
          </p>
        )}

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
                    <th className="text-left p-3 hidden lg:table-cell">Memed</th>
                    <th className="text-left p-3 hidden md:table-cell">Telefone</th>
                    <th className="w-40 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{professionalSpecialty(p) || "—"}</td>
                      <td className="p-3 hidden lg:table-cell">
                        <MemedStatusBadge info={memedStatus[p.id]} loading={memedStatusLoading} />
                      </td>
                      <td className="p-3 hidden md:table-cell text-gray-700 dark:text-gray-300">{entityPhone(p) || "—"}</td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          {p.is_administrador_vinculado ? (
                            <span className="text-xs text-amber-700 dark:text-amber-400" title="O administrador da loja não pode ser editado nem excluído">
                              Administrador (somente leitura)
                            </span>
                          ) : (
                            <>
                              <button
                                onClick={() => setHorariosProfessional(p)}
                                className="p-2 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded"
                                title="Dias e horários de trabalho"
                              >
                                <Clock size={18} />
                              </button>
                              <button
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
          </div>
        )}
      </ClinicaBelezaPageContent>

      {horariosProfessional && (
        <ModalHorariosTrabalho
          professionalId={horariosProfessional.id}
          professionalName={horariosProfessional.name}
          onClose={() => setHorariosProfessional(null)}
          onSaved={() => load()}
        />
      )}
    </>
  );
}
