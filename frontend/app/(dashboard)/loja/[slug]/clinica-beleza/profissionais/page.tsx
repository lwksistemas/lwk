"use client";

/**
 * Cadastro de Profissionais - Clínica da Beleza
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Pencil, Trash2, Clock } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ModalHorariosTrabalho } from "@/components/clinica-beleza/ModalHorariosTrabalho";
import { ProfissionalFormModal } from "./components/ProfissionalFormModal";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { deleteClinicaBelezaEntity, saveClinicaBelezaEntity, useClinicaBelezaEntityList } from "@/lib/clinica-beleza-crud";
import {
  entityActive,
  entityEmail,
  entityName,
  entityPhone,
  professionalSpecialty,
} from "@/lib/clinica-beleza-entities";
import { formatProfissionalApiErrors } from "@/lib/clinica-beleza-form-errors";
import {
  bloquearCriacaoDuplicadaOffline,
  deveVerificarDuplicataOffline,
  gerarIdTemporarioOffline,
  isBrowserOffline,
  isFetchNetworkError,
  isRegistroPendenteSync,
  temDuplicataNaLista,
} from "@/lib/clinica-beleza-offline";
import { buscarProfissionaisOffline, salvarProfissionaisOffline, adicionarNaFilaSync, getLojaSlug } from "@/lib/offline-db";
import { logger } from "@/lib/logger";

type PerfilAcesso = "administrador" | "profissional" | "recepcao";

interface Professional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
  especialidade?: string;
  phone?: string | null;
  telefone?: string | null;
  email?: string | null;
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
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const { list, setList, loading, load } = useClinicaBelezaEntityList<Professional>({
    path: "/professionals/",
    fetchOffline: buscarProfissionaisOffline,
    saveOffline: salvarProfissionaisOffline,
  });
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Professional | null>(null);
  const [form, setForm] = useState({
    name: "",
    specialty: "",
    phone: "",
    email: "",
    criar_acesso: false,
    perfil: "profissional" as PerfilAcesso,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
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

  useEffect(() => {
    loadLojaInfo();
  }, []);

  useEffect(() => {
    if (searchParams.get("novo") === "1") openNew();
  }, [searchParams]);

  const openNew = () => {
    setEditing(null);
    setForm({ name: "", specialty: "", phone: "", email: "", criar_acesso: false, perfil: "profissional" });
    setError("");
    setShowModal(true);
  };

  const openEdit = (p: Professional) => {
    setEditing(p);
    setForm({
      name: entityName(p),
      specialty: professionalSpecialty(p) || "",
      phone: entityPhone(p) || "",
      email: entityEmail(p) || "",
      criar_acesso: false,
      perfil: "profissional",
    });
    setError("");
    setShowModal(true);
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    if (!form.specialty.trim()) {
      setError("Especialidade é obrigatória.");
      return;
    }
    const criarAcesso = Boolean(form.criar_acesso);
    if (criarAcesso && !form.email.trim()) {
      setError("E-mail é obrigatório para criar acesso e enviar senha.");
      return;
    }
    setSaving(true);
    setError("");
    const body: Record<string, unknown> = {
      name: form.name.trim(),
      specialty: form.specialty.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      active: true,
    };
    if (!editing && criarAcesso) {
      body.criar_acesso = true;
      body.perfil = form.perfil;
    }

    if (isBrowserOffline()) {
      try {
        const lojaSlug = getLojaSlug();

        if (deveVerificarDuplicataOffline(editing)) {
          const jaExisteLocal = temDuplicataNaLista(list, (p) =>
            entityName(p).toLowerCase() === form.name.trim().toLowerCase() &&
            professionalSpecialty(p).toLowerCase() === form.specialty.trim().toLowerCase(),
          );
          if (jaExisteLocal) {
            setError("Este profissional já foi adicionado. Aguarde a sincronização.");
            setSaving(false);
            return;
          }
        }

        if (editing && !isRegistroPendenteSync(editing.id)) {
          await adicionarNaFilaSync({
            tipo: "profissional",
            payload: { action: "update", id: editing.id, body: { ...body, criar_acesso: undefined } },
            lojaSlug,
          });
          const updatedList = list.map((p) =>
            p.id === editing.id
              ? { ...p, name: String(body.name), specialty: String(body.specialty), phone: (body.phone as string) ?? entityPhone(p), email: (body.email as string) ?? entityEmail(p) }
              : p
          );
          setList(updatedList);
          await salvarProfissionaisOffline(updatedList);
        } else {
          await adicionarNaFilaSync({
            tipo: "profissional",
            payload: { action: "create", body },
            lojaSlug,
          });
          const tempId = gerarIdTemporarioOffline();
          const newProf: Professional = {
            id: tempId,
            name: String(body.name),
            specialty: String(body.specialty),
            phone: (body.phone as string) ?? null,
            email: (body.email as string) ?? null,
            active: true,
          };
          const updatedList = [newProf, ...list];
          setList(updatedList);
          await salvarProfissionaisOffline(updatedList);
        }
        setShowModal(false);
        alert("Salvo offline. O profissional será sincronizado quando você estiver online.");
      } catch (err) {
        logger.warn("Erro ao salvar offline:", err);
        setError("Erro ao salvar localmente. Tente novamente.");
      }
      setSaving(false);
      return;
    }

    try {
      if (editing) {
        await saveClinicaBelezaEntity(`/professionals/${editing.id}/`, "PUT", { ...body, criar_acesso: undefined });
      } else {
        await saveClinicaBelezaEntity("/professionals/", "POST", body);
      }
      setShowModal(false);
      load();
      if (!editing && criarAcesso) {
        alert("Profissional criado! A senha foi enviada por e-mail.");
      }
    } catch (e: unknown) {
      const err = e && typeof e === "object" ? e as Record<string, unknown> : {};
      const msg = formatProfissionalApiErrors(err) || (e instanceof Error ? e.message : "Erro ao salvar");
      if (isFetchNetworkError(msg)) {
        try {
          const lojaSlug = getLojaSlug();

          if (bloquearCriacaoDuplicadaOffline(editing, list, (p) =>
            entityName(p) === form.name.trim() && professionalSpecialty(p) === form.specialty.trim(),
          )) {
            setError("Este profissional já foi adicionado offline. Aguarde a sincronização.");
            setSaving(false);
            return;
          }
          
          if (editing && editing.id > 0) {
            await adicionarNaFilaSync({
              tipo: "profissional",
              payload: { action: "update", id: editing.id, body: { ...body, criar_acesso: undefined } },
              lojaSlug,
            });
            const updatedList = list.map((p) =>
              p.id === editing.id
                ? { ...p, name: String(body.name), specialty: String(body.specialty), phone: (body.phone as string) ?? entityPhone(p), email: (body.email as string) ?? entityEmail(p) }
                : p
            );
            setList(updatedList);
            await salvarProfissionaisOffline(updatedList);
          } else {
            await adicionarNaFilaSync({ tipo: "profissional", payload: { action: "create", body }, lojaSlug });
            const tempId = gerarIdTemporarioOffline();
            const newProf: Professional = {
              id: tempId,
              name: String(body.name),
              specialty: String(body.specialty),
              phone: (body.phone as string) ?? null,
              email: (body.email as string) ?? null,
              active: true,
            };
            const updatedList = [newProf, ...list];
            setList(updatedList);
            await salvarProfissionaisOffline(updatedList);
          }
          setShowModal(false);
          alert("Sem conexão. Profissional salvo offline e será sincronizado quando você estiver online.");
        } catch (err) {
          logger.warn("Erro ao salvar offline:", err);
          setError("Sem conexão. Não foi possível salvar offline. Tente novamente.");
        }
      } else {
        setError(msg);
      }
    } finally {
      setSaving(false);
    }
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
                    <th className="text-left p-3 hidden md:table-cell">Telefone</th>
                    <th className="w-40 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{professionalSpecialty(p) || "—"}</td>
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

      {showModal && (
        <ProfissionalFormModal
          editing={!!editing}
          form={form}
          saving={saving}
          error={error}
          onChange={setForm}
          onSave={save}
          onClose={() => setShowModal(false)}
        />
      )}

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
