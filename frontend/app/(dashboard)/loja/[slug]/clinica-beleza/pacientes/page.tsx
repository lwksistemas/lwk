"use client";

/**
 * Cadastro de Clientes - Clínica da Beleza
 * Lista em tela cheia; novo/editar ocupa a página inteira (sem modal).
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ChevronRight, Pencil, Trash2, Users } from "lucide-react";
import {
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from "@/lib/clinica-beleza-crud";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  PacienteCadastroForm,
  PACIENTE_EMPTY_FORM,
  type PacienteFormState,
} from "./components/PacienteCadastroForm";
import { useLojaTheme } from "@/hooks/useLojaTheme";
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
import { formatTelefone, formatCpf, formatCep, applyTelefoneInternacionalPayload, toUpperCase } from "@/lib/format-br";
import { consultaCep } from "@/lib/consulta-cep";
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
import {
  CONVENIO_PARTICULAR_LABEL,
  findConvenioParticular,
  isConvenioParticularNome,
  ordenarConveniosComParticularPrimeiro,
} from "@/lib/convenio-precos";
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
  cidade?: string | null;
  estado?: string | null;
  city?: string | null;
  state?: string | null;
  notes?: string | null;
  observacoes?: string | null;
  active?: boolean;
  is_active?: boolean;
  allow_whatsapp?: boolean;
  convenio?: number | null;
  convenio_name?: string | null;
  foto_url?: string | null;
}

const EMPTY_FORM = PACIENTE_EMPTY_FORM;

function montarEnderecoPaciente(form: PacienteFormState): string {
  const partes: string[] = [];
  if (form.logradouro.trim()) partes.push(form.logradouro.trim());
  if (form.numero.trim()) partes.push(`Nº ${form.numero.trim()}`);
  if (form.complemento.trim()) partes.push(form.complemento.trim());
  if (form.bairro.trim()) partes.push(form.bairro.trim());
  if (form.cep.trim()) partes.push(`CEP ${form.cep.trim()}`);
  return partes.join(", ");
}

function patientToForm(p: Patient) {
  const endereco = patientAddress(p) || "";
  const cepMatch = endereco.match(/CEP\s*(\d{5}-?\d{3})/i);
  const enderecoSemCep = endereco.replace(/,?\s*CEP\s*\d{5}-?\d{3}/i, "").trim();
  const partes = enderecoSemCep.split(",").map((s) => s.trim()).filter(Boolean);
  let logradouro = partes[0] || "";
  let numero = "";
  let complemento = "";
  let bairro = "";
  for (let i = 1; i < partes.length; i += 1) {
    const parte = partes[i];
    const numMatch = parte.match(/^N[º°o\.]?\s*(.+)$/i);
    if (numMatch && !numero) {
      numero = numMatch[1].trim();
    } else if (!bairro) {
      bairro = parte;
    } else if (!complemento) {
      complemento = parte;
    }
  }
  if (!logradouro && enderecoSemCep) {
    logradouro = enderecoSemCep;
  }
  return {
    name: entityName(p),
    phone: formatTelefone(entityPhone(p)),
    email: entityEmail(p) || "",
    cpf: formatCpf(patientCpf(p) || ""),
    birth_date: patientBirthDate(p) ? patientBirthDate(p)!.slice(0, 10) : "",
    cep: cepMatch ? formatCep(cepMatch[1]) : "",
    logradouro,
    numero,
    complemento,
    bairro,
    cidade: (p.cidade || p.city || "").trim(),
    uf: (p.estado || p.state || "").trim(),
    notes: patientNotes(p) || "",
    allow_whatsapp: p.allow_whatsapp !== false,
    convenio: p.convenio ?? "",
    foto_url: (p as Patient).foto_url || "",
  };
}

export default function PacientesPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/pacientes`;
  const { theme } = useLojaTheme(slug);

  const { list, setList, loading, load, page, setPage, totalPages, pageSize, totalCount } = useClinicaBelezaEntityList<Patient>({
    path: "/patients/",
    fetchOffline: buscarPacientesOffline,
    saveOffline: salvarPacientesOffline,
  });
  const [editing, setEditing] = useState<Patient | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
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
    if (!editIdParam) return;
    const p = list.find((x) => String(x.id) === editIdParam);
    if (p) {
      setEditing(p);
      setForm(patientToForm(p));
      setError("");
      return;
    }
    let cancelled = false;
    ClinicaBelezaAPI.patients.get(Number(editIdParam))
      .then((fetched) => {
        if (!cancelled) {
          setEditing(fetched as Patient);
          setForm(patientToForm(fetched as Patient));
          setError("");
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [isNovo, editIdParam, list]);

  useEffect(() => {
    if (!isFormView) return;
    ClinicaBelezaAPI.convenios.list()
      .then((rows) => setConvenios(Array.isArray(rows) ? rows : []))
      .catch(() => setConvenios([]));
  }, [isFormView]);

  useEffect(() => {
    if (!isFormView) return;
    const particular = findConvenioParticular(convenios);
    if (!particular) return;
    setForm((f) => {
      if (isNovo) return { ...f, convenio: particular.id };
      if (f.convenio === "") return { ...f, convenio: particular.id };
      return f;
    });
  }, [isFormView, isNovo, convenios]);

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

  const handleCepChange = (value: string) => {
    setForm((f) => ({ ...f, cep: formatCep(value) }));
  };

  const handleBuscarCep = async () => {
    const cep = form.cep.replace(/\D/g, "");
    if (cep.length !== 8) {
      setError("Informe um CEP válido com 8 dígitos.");
      return;
    }
    setBuscarCepLoading(true);
    setError("");
    try {
      const endereco = await consultaCep(form.cep);
      if (endereco) {
        setForm((f) => ({
          ...f,
          logradouro: toUpperCase(endereco.logradouro),
          bairro: toUpperCase(endereco.bairro),
          cidade: toUpperCase(endereco.cidade),
          uf: endereco.uf.toUpperCase(),
        }));
      } else {
        setError("CEP não encontrado. Verifique o número ou tente novamente.");
      }
    } finally {
      setBuscarCepLoading(false);
    }
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    setSaving(true);
    setError("");
    const body = applyTelefoneInternacionalPayload({
      name: form.name.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      cpf: form.cpf.trim() || null,
      birth_date: form.birth_date || null,
      address: montarEnderecoPaciente(form) || null,
      cidade: form.cidade.trim() || null,
      estado: form.uf.trim().toUpperCase() || null,
      notes: form.notes.trim() || null,
      active: true,
      allow_whatsapp: form.allow_whatsapp,
      convenio: form.convenio ? Number(form.convenio) : null,
      foto_url: form.foto_url.trim() || null,
    });

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
            cidade: body.cidade ?? null,
            estado: body.estado ?? null,
            notes: body.notes ?? null,
            active: true,
            allow_whatsapp: body.allow_whatsapp ?? true,
            convenio: body.convenio ?? null,
            foto_url: body.foto_url ?? null,
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
      const msg =
        formatClinicaApiValidationErrors(err) ||
        (typeof err?.error === 'string' ? err.error : '') ||
        (typeof err?.detail === 'string' ? err.detail : '') ||
        (e instanceof Error ? e.message : 'Erro ao salvar');
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
            cidade: body.cidade ?? null,
            estado: body.estado ?? null,
              notes: body.notes ?? null,
              active: true,
              allow_whatsapp: body.allow_whatsapp ?? true,
              convenio: body.convenio ?? null,
              foto_url: body.foto_url ?? null,
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

  /* ── Formulário tela inteira ── */
  if (isFormView) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? "Editar cliente" : "Novo cliente"}
          subtitle={editing ? undefined : "Cadastro de cliente da clínica"}
          onBack={voltarLista}
          icon={Users}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[#f7f2f4] dark:!bg-gray-950">
          <PacienteCadastroForm
            showHeader={false}
            editing={Boolean(editing)}
            form={form}
            setForm={setForm}
            error={error}
            saving={saving}
            convenios={convenios}
            buscarCepLoading={buscarCepLoading}
            onCepChange={handleCepChange}
            onBuscarCep={handleBuscarCep}
            onSave={save}
            onCancel={voltarLista}
            accentColor={theme.corPrimaria || CLINICA_BELEZA_PRIMARY}
            lojaSlug={slug}
          />
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
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold w-14" aria-label="Foto" />
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
                        <td className="px-4 md:px-6 py-4">
                          <PacienteAvatar
                            fotoUrl={p.foto_url}
                            name={entityName(p)}
                            size="sm"
                          />
                        </td>
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
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount ?? 0}
              pageSize={pageSize}
              loading={loading}
              onPageChange={setPage}
              itemLabel="pacientes"
            />
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
