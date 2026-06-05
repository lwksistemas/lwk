"use client";

/**
 * Cadastro de Clientes - Clínica da Beleza
 * Lista em tela cheia; novo/editar ocupa a página inteira (sem modal).
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, ChevronRight, Pencil, Save, Trash2, Users } from "lucide-react";
import {
  CLINICA_FORM_INPUT,
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from "@/lib/clinica-beleza-crud";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  entityEmail,
  entityName,
  entityPhone,
  entityActive,
  patientAddress,
  patientBirthDate,
  patientCpf,
  patientNotes,
} from "@/lib/clinica-beleza-entities";
import { formatClinicaApiValidationErrors } from "@/lib/clinica-beleza-form-errors";
import { formatTelefone, formatCpf } from "@/lib/format-br";
import {
  bloquearCriacaoDuplicadaOffline,
  deveVerificarDuplicataOffline,
  gerarIdTemporarioOffline,
  isBrowserOffline,
  isFetchNetworkError,
  isRegistroPendenteSync,
  temDuplicataNaLista,
} from "@/lib/clinica-beleza-offline";
import { buscarPacientesOffline, salvarPacientesOffline, adicionarNaFilaSync, getLojaSlug } from "@/lib/offline-db";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { CONVENIO_PARTICULAR_LABEL } from "@/lib/convenio-precos";
import { logger } from "@/lib/logger";

interface Patient {
  id: number;
  name?: string;
  nome?: string;
  phone?: string;
  telefone?: string;
  email?: string | null;
  cpf?: string | null;
  birth_date?: string | null;
  data_nascimento?: string | null;
  address?: string | null;
  endereco?: string | null;
  notes?: string | null;
  observacoes?: string | null;
  active?: boolean;
  is_active?: boolean;
  allow_whatsapp?: boolean;
  convenio?: number | null;
  convenio_name?: string | null;
}

const EMPTY_FORM = {
  name: "",
  phone: "",
  email: "",
  cpf: "",
  birth_date: "",
  address: "",
  notes: "",
  allow_whatsapp: true,
  convenio: "" as number | "",
};

const INPUT = CLINICA_FORM_INPUT;

function patientToForm(p: Patient) {
  return {
    name: entityName(p),
    phone: formatTelefone(entityPhone(p)),
    email: entityEmail(p) || "",
    cpf: formatCpf(patientCpf(p) || ""),
    birth_date: patientBirthDate(p) ? patientBirthDate(p)!.slice(0, 10) : "",
    address: patientAddress(p) || "",
    notes: patientNotes(p) || "",
    allow_whatsapp: p.allow_whatsapp !== false,
    convenio: p.convenio ?? "",
  };
}

export default function PacientesPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/pacientes`;

  const { list, setList, loading, load } = useClinicaBelezaEntityList<Patient>({
    path: "/patients/",
    fetchOffline: buscarPacientesOffline,
    saveOffline: salvarPacientesOffline,
  });
  const [editing, setEditing] = useState<Patient | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);

  const isNovo = searchParams.get("novo") === "1";
  const editIdParam = searchParams.get("id");
  const isFormView = isNovo || Boolean(editIdParam);

  useEffect(() => {
    if (isNovo) {
      setEditing(null);
      setForm(EMPTY_FORM);
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const p = list.find((x) => String(x.id) === editIdParam);
      if (p) {
        setEditing(p);
        setForm(patientToForm(p));
        setError("");
      }
    }
  }, [isNovo, editIdParam, list]);

  useEffect(() => {
    if (!isFormView) return;
    ClinicaBelezaAPI.convenios.list()
      .then((rows) => setConvenios(Array.isArray(rows) ? rows : []))
      .catch(() => setConvenios([]));
  }, [isFormView]);

  const voltarLista = () => {
    setEditing(null);
    setError("");
    router.replace(basePath, { scroll: false });
  };

  const openNew = () => {
    router.replace(`${basePath}?novo=1`, { scroll: false });
  };

  const openEdit = (p: Patient) => {
    router.replace(`${basePath}?id=${p.id}`, { scroll: false });
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    setSaving(true);
    setError("");
    const body = {
      name: form.name.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      cpf: form.cpf.trim() || null,
      birth_date: form.birth_date || null,
      address: form.address.trim() || null,
      notes: form.notes.trim() || null,
      active: true,
      allow_whatsapp: form.allow_whatsapp,
      convenio: form.convenio ? Number(form.convenio) : null,
    };

    const finishSave = () => {
      voltarLista();
      load();
    };

    if (isBrowserOffline()) {
      try {
        const lojaSlug = getLojaSlug();
        if (deveVerificarDuplicataOffline(editing)) {
          const jaExisteLocal = temDuplicataNaLista(list, (p) =>
            entityName(p).toLowerCase() === form.name.trim().toLowerCase() &&
            (form.phone.trim() ? entityPhone(p) === form.phone.trim() : true),
          );
          if (jaExisteLocal) {
            setError("Este cliente já foi adicionado. Aguarde a sincronização.");
            setSaving(false);
            return;
          }
        }
        if (editing && !isRegistroPendenteSync(editing.id)) {
          await adicionarNaFilaSync({ tipo: "paciente", payload: { action: "update", id: editing.id, body }, lojaSlug });
          const updatedList = list.map((p) =>
            p.id === editing.id ? { ...p, ...body, email: body.email ?? p.email, phone: body.phone ?? p.phone } : p
          );
          setList(updatedList);
          await salvarPacientesOffline(updatedList);
        } else {
          await adicionarNaFilaSync({ tipo: "paciente", payload: { action: "create", body }, lojaSlug });
          const tempId = gerarIdTemporarioOffline();
          const newPatient: Patient = {
            id: tempId,
            name: body.name,
            phone: body.phone ?? "",
            email: body.email ?? null,
            cpf: body.cpf ?? null,
            birth_date: body.birth_date ?? null,
            address: body.address ?? null,
            notes: body.notes ?? null,
            active: true,
            allow_whatsapp: body.allow_whatsapp ?? true,
            convenio: body.convenio ?? null,
          };
          const updatedList = [newPatient, ...list];
          setList(updatedList);
          await salvarPacientesOffline(updatedList);
        }
        voltarLista();
        alert("Salvo offline. O cliente será sincronizado quando você estiver online.");
        return;
      } catch (e) {
        logger.warn("Erro ao salvar offline:", e);
        setError("Erro ao salvar localmente. Tente novamente.");
        setSaving(false);
        return;
      }
    }

    try {
      if (editing) {
        await saveClinicaBelezaEntity(`/patients/${editing.id}/`, "PUT", body);
      } else {
        await saveClinicaBelezaEntity("/patients/", "POST", body);
      }
      finishSave();
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      const err = e && typeof e === "object" ? (e as Record<string, unknown>) : {};
      const msg = formatClinicaApiValidationErrors(err) || (e instanceof Error ? e.message : "Erro ao salvar");
      if (isFetchNetworkError(msg)) {
        try {
          const lojaSlug = getLojaSlug();
          if (bloquearCriacaoDuplicadaOffline(editing, list, (p) =>
            entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
          )) {
            setError("Este cliente já foi adicionado offline. Aguarde a sincronização.");
            setSaving(false);
            return;
          }
          if (editing && editing.id > 0) {
            await adicionarNaFilaSync({ tipo: "paciente", payload: { action: "update", id: editing.id, body }, lojaSlug });
            const updatedList = list.map((p) =>
              p.id === editing.id ? { ...p, ...body, email: body.email ?? p.email, phone: body.phone ?? p.phone } : p
            );
            setList(updatedList);
            await salvarPacientesOffline(updatedList);
          } else {
            await adicionarNaFilaSync({ tipo: "paciente", payload: { action: "create", body }, lojaSlug });
            const tempId = gerarIdTemporarioOffline();
            const newPatient: Patient = {
              id: tempId,
              name: body.name,
              phone: body.phone ?? "",
              email: body.email ?? null,
              cpf: body.cpf ?? null,
              birth_date: body.birth_date ?? null,
              address: body.address ?? null,
              notes: body.notes ?? null,
              active: true,
              allow_whatsapp: body.allow_whatsapp ?? true,
              convenio: body.convenio ?? null,
            };
            const updatedList = [newPatient, ...list];
            setList(updatedList);
            await salvarPacientesOffline(updatedList);
          }
          voltarLista();
          alert("Sem conexão. Cliente salvo offline e será sincronizado quando você estiver online.");
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

  const exclude = async (p: Patient) => {
    if (!confirm(`Desativar o cliente "${entityName(p)}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/patients/${p.id}/`);
      load();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  const activeList = list.filter((p) => entityActive(p));

  /* ── Formulário em tela cheia ── */
  if (isFormView) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? "Editar Cliente" : "Novo Cliente"}
          subtitle={editing ? entityName(editing) : "Preencha os dados do cliente"}
          backHref={basePath}
          icon={Users}
        />
          <ClinicaBelezaPageContent className="flex flex-col flex-1 !p-0">
          <div className="px-4 md:px-6 lg:px-8 pt-2 pb-3 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
            <button
              type="button"
              onClick={voltarLista}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            >
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
          </div>

          <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
            <ClinicaBelezaPanel className="p-5 md:p-8">
                {error && (
                  <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                    {error}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Nome *</label>
                    <input
                      value={form.name}
                      onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                      className={INPUT}
                      placeholder="Nome completo"
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Telefone</label>
                    <input
                      value={form.phone}
                      onChange={(e) => setForm((f) => ({ ...f, phone: formatTelefone(e.target.value) }))}
                      className={INPUT}
                      placeholder="(00) 00000-0000"
                      inputMode="tel"
                      maxLength={15}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">E-mail</label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                      className={INPUT}
                      placeholder="email@exemplo.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">CPF</label>
                    <input
                      value={form.cpf}
                      onChange={(e) => setForm((f) => ({ ...f, cpf: formatCpf(e.target.value) }))}
                      className={INPUT}
                      placeholder="000.000.000-00"
                      inputMode="numeric"
                      maxLength={14}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Data de Nascimento</label>
                    <input
                      type="date"
                      value={form.birth_date}
                      onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value }))}
                      className={INPUT}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                      Convênio padrão
                    </label>
                    <select
                      value={form.convenio}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          convenio: e.target.value ? Number(e.target.value) : "",
                        }))
                      }
                      className={INPUT}
                    >
                      <option value="">{CONVENIO_PARTICULAR_LABEL}</option>
                      {convenios.map((c) => (
                        <option key={c.id} value={c.id}>{c.nome}</option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                      Sugerido ao agendar ou abrir consulta. {CONVENIO_PARTICULAR_LABEL} usa o preço cadastrado do procedimento.
                    </p>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Endereço</label>
                    <input
                      value={form.address}
                      onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                      className={INPUT}
                      placeholder="Rua, número, bairro, cidade"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Observações</label>
                    <textarea
                      value={form.notes}
                      onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                      rows={4}
                      className={`${INPUT} resize-y min-h-[100px]`}
                      placeholder="Observações sobre o cliente"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="flex items-start gap-3 cursor-pointer p-4 rounded-lg bg-gray-50 dark:bg-neutral-900/50 border border-gray-100 dark:border-neutral-700">
                      <input
                        type="checkbox"
                        checked={form.allow_whatsapp}
                        onChange={(e) => setForm((f) => ({ ...f, allow_whatsapp: e.target.checked }))}
                        className="mt-0.5 rounded border-gray-300 dark:border-neutral-600"
                        style={{ accentColor: CLINICA_BELEZA_PRIMARY }}
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Permitir WhatsApp (lembretes e cobranças) — LGPD: o cliente pode optar por não receber
                      </span>
                    </label>
                  </div>
                </div>

                <div className="flex flex-col-reverse sm:flex-row gap-3 mt-8 pt-6 border-t border-gray-100 dark:border-neutral-700">
                  <button
                    type="button"
                    onClick={voltarLista}
                    className="flex-1 sm:flex-none sm:min-w-[140px] py-2.5 px-6 rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 text-sm font-medium"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={save}
                    disabled={saving}
                    className="flex-1 sm:flex-none sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-6 rounded-lg text-white disabled:opacity-50 text-sm font-medium"
                    style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                  >
                    <Save size={18} />
                    {saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar cliente"}
                  </button>
                </div>
            </ClinicaBelezaPanel>
          </div>
          </ClinicaBelezaPageContent>
      </>
    );
  }

  /* ── Lista em tela cheia ── */
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Clientes"
        subtitle="Cadastro de clientes da clínica"
        newLabel="Novo Cliente"
        onNew={openNew}
        icon={Users}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-20 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : activeList.length === 0 ? (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 p-12 text-center text-gray-500 dark:text-gray-400 shadow-sm">
            Nenhum cliente cadastrado. Clique em &quot;Novo Cliente&quot; para começar.
          </div>
        ) : (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                  <tr>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Nome</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Telefone</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden sm:table-cell">E-mail</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden lg:table-cell">CPF</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold hidden md:table-cell">Convênio</th>
                    <th className="text-right px-4 md:px-6 py-3.5 font-semibold w-32">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {activeList.map((p) => {
                    const isPendenteSync = p.id < 0;
                    return (
                      <tr
                        key={p.id}
                        className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/40 dark:hover:bg-neutral-700/30 transition-colors cursor-pointer"
                        onClick={() => openEdit(p)}
                      >
                        <td className="px-4 md:px-6 py-4 font-medium text-gray-900 dark:text-gray-100">
                          <div className="flex items-center gap-2">
                            {entityName(p)}
                            {isPendenteSync && (
                              <span className="text-xs text-amber-600 dark:text-amber-400 font-normal">(offline)</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 md:px-6 py-4 text-gray-700 dark:text-gray-300">{formatTelefone(entityPhone(p)) || "—"}</td>
                        <td className="px-4 md:px-6 py-4 hidden sm:table-cell text-gray-700 dark:text-gray-300">{entityEmail(p) || "—"}</td>
                        <td className="px-4 md:px-6 py-4 hidden lg:table-cell text-gray-700 dark:text-gray-300">{formatCpf(patientCpf(p) || "") || "—"}</td>
                        <td className="px-4 md:px-6 py-4 hidden md:table-cell text-gray-700 dark:text-gray-300">
                          {p.convenio_name || CONVENIO_PARTICULAR_LABEL}
                        </td>
                        <td className="px-4 md:px-6 py-4">
                          <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                            <button
                              type="button"
                              onClick={() => openEdit(p)}
                              className="p-2 rounded-lg hover:bg-[#F5E6EA] dark:hover:bg-neutral-600 transition-colors"
                              style={{ color: CLINICA_BELEZA_PRIMARY }}
                              title="Editar"
                            >
                              <Pencil size={18} />
                            </button>
                            {!isPendenteSync && (
                              <button
                                type="button"
                                onClick={() => exclude(p)}
                                className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                                title="Desativar"
                              >
                                <Trash2 size={18} />
                              </button>
                            )}
                            <ChevronRight size={18} className="text-gray-400 ml-1 hidden md:inline self-center" />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
