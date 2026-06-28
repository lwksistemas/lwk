"use client";

/**
 * Cadastro de Clientes - Clínica da Beleza
 * Lista em tela cheia; novo/editar ocupa a página inteira (sem modal).
 */

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ChevronRight, Pencil, Trash2, Users } from "lucide-react";
import { deleteClinicaBelezaEntity, saveClinicaBelezaEntity, useClinicaBelezaEntityList } from "@/lib/clinica-beleza-crud";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { PacienteCadastroForm, PACIENTE_EMPTY_FORM, type PacienteFormState } from "./components/PacienteCadastroForm";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { useOfflineSave } from "@/hooks/clinica-beleza/useOfflineSave";
import { entityEmail, entityName, entityPhone, entityActive, patientCpf } from "@/lib/clinica-beleza-entities";
import { formatClinicaApiValidationErrors } from "@/lib/clinica-beleza-form-errors";
import { formatTelefone, formatCpf, formatCep, applyTelefoneInternacionalPayload, toUpperCase } from "@/lib/format-br";
import { consultaCep } from "@/lib/consulta-cep";
import { buscarPacientesOffline, salvarPacientesOffline } from "@/lib/offline-db";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { CONVENIO_PARTICULAR_LABEL, findConvenioParticular } from "@/lib/convenio-precos";
import { Patient, montarEnderecoPaciente, patientToForm } from "./lib/paciente-form-utils";

const EMPTY_FORM = PACIENTE_EMPTY_FORM;

export default function PacientesPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/pacientes`;
  const { theme } = useLojaTheme(slug);

  const { list, setList, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaEntityList<Patient>({
      path: "/patients/",
      fetchOffline: buscarPacientesOffline,
      saveOffline: salvarPacientesOffline,
    });

  const [editing, setEditing] = useState<Patient | null>(null);
  const [form, setForm] = useState<PacienteFormState>(EMPTY_FORM);
  const [error, setError] = useState("");
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);

  const isNovo = searchParams.get("novo") === "1";
  const editIdParam = searchParams.get("id");
  const isFormView = isNovo || Boolean(editIdParam);

  const { save: offlineSave, saving } = useOfflineSave<Patient>({
    entityType: "paciente",
    saveOnline: async (body, ed) => {
      if (ed) {
        await saveClinicaBelezaEntity(`/patients/${ed.id}/`, "PUT", body);
      } else {
        await saveClinicaBelezaEntity("/patients/", "POST", body);
      }
    },
    list,
    setList,
    saveOffline: salvarPacientesOffline,
    buildNewEntity: (body, tempId) => ({
      id: tempId,
      ...(body as Omit<Patient, "id">),
    }),
    duplicatePredicate: (p) =>
      entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
  });

  // Carrega dados do paciente ao abrir edição
  useEffect(() => {
    if (isNovo) { setEditing(null); setForm(EMPTY_FORM); setError(""); return; }
    if (!editIdParam) return;
    const found = list.find((x) => String(x.id) === editIdParam);
    if (found) { setEditing(found); setForm(patientToForm(found)); setError(""); return; }
    let cancelled = false;
    ClinicaBelezaAPI.patients.get(Number(editIdParam))
      .then((fetched) => { if (!cancelled) { setEditing(fetched as Patient); setForm(patientToForm(fetched as Patient)); setError(""); } })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [isNovo, editIdParam, list]);

  // Carrega convênios ao abrir formulário
  useEffect(() => {
    if (!isFormView) return;
    ClinicaBelezaAPI.convenios.list()
      .then((rows) => setConvenios(Array.isArray(rows) ? rows : []))
      .catch(() => setConvenios([]));
  }, [isFormView]);

  // Pré-seleciona convênio particular
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

  const voltarLista = () => { setEditing(null); setError(""); router.replace(basePath, { scroll: false }); };
  const openNew = () => router.replace(`${basePath}?novo=1`, { scroll: false });
  const openEdit = (p: Patient) => router.replace(`${basePath}?id=${p.id}`, { scroll: false });

  const handleCepChange = (value: string) => setForm((f) => ({ ...f, cep: formatCep(value) }));

  const handleBuscarCep = async () => {
    const cep = form.cep.replace(/\D/g, "");
    if (cep.length !== 8) { setError("Informe um CEP válido com 8 dígitos."); return; }
    setBuscarCepLoading(true);
    setError("");
    try {
      const endereco = await consultaCep(form.cep);
      if (endereco) {
        setForm((f) => ({ ...f, logradouro: toUpperCase(endereco.logradouro), bairro: toUpperCase(endereco.bairro), cidade: toUpperCase(endereco.cidade), uf: endereco.uf.toUpperCase() }));
      } else {
        setError("CEP não encontrado. Verifique o número ou tente novamente.");
      }
    } finally { setBuscarCepLoading(false); }
  };

  const save = async () => {
    if (!form.name.trim()) { setError("Nome é obrigatório."); return; }
    setError("");
    const body = applyTelefoneInternacionalPayload({
      name: form.name.trim(), phone: form.phone.trim() || null, email: form.email.trim() || null,
      cpf: form.cpf.trim() || null, birth_date: form.birth_date || null,
      address: montarEnderecoPaciente(form) || null, cidade: form.cidade.trim() || null,
      estado: form.uf.trim().toUpperCase() || null, notes: form.notes.trim() || null,
      active: true, allow_whatsapp: form.allow_whatsapp,
      convenio: form.convenio ? Number(form.convenio) : null, foto_url: form.foto_url.trim() || null,
    });

    const result = await offlineSave(body, editing);
    if (!result.ok) {
      if (result.error) setError(result.error);
      return;
    }
    if (result.offline) alert(result.message);
    voltarLista();
    load();
  };

  const exclude = async (p: Patient) => {
    if (!confirm(`Desativar o cliente "${entityName(p)}"?`)) return;
    try { await deleteClinicaBelezaEntity(`/patients/${p.id}/`); load(); }
    catch { alert("Erro ao desativar."); }
  };

  const activeList = list.filter((p) => entityActive(p));

  // ── Formulário tela inteira ──
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

  // ── Lista em tela cheia ──
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
        ) : (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full">
            <EntityListTable
              rows={activeList}
              rowKey={(p) => p.id}
              onRowClick={openEdit}
              emptyMessage={
                <div className="p-12 text-center text-gray-500 dark:text-gray-400">
                  Nenhum cliente cadastrado. Clique em &quot;Novo Cliente&quot; para começar.
                </div>
              }
              columns={[
                { key: 'avatar', header: '', render: (p) => <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" /> },
                {
                  key: 'nome', header: 'Nome',
                  render: (p) => (
                    <div className="flex items-center gap-2 font-medium text-gray-900 dark:text-gray-100">
                      {entityName(p)}
                      {p.id < 0 && <span className="text-xs text-amber-600 dark:text-amber-400 font-normal">(offline)</span>}
                    </div>
                  ),
                },
                { key: 'telefone', header: 'Telefone', render: (p) => <span className="text-gray-700 dark:text-gray-300">{formatTelefone(entityPhone(p)) || '—'}</span> },
                { key: 'email', header: 'E-mail', className: 'hidden sm:table-cell', render: (p) => <span className="text-gray-700 dark:text-gray-300">{entityEmail(p) || '—'}</span> },
                { key: 'cpf', header: 'CPF', className: 'hidden lg:table-cell', render: (p) => <span className="text-gray-700 dark:text-gray-300">{formatCpf(patientCpf(p) || '') || '—'}</span> },
                { key: 'convenio', header: 'Convênio', className: 'hidden md:table-cell', render: (p) => <span className="text-gray-700 dark:text-gray-300">{p.convenio_name || CONVENIO_PARTICULAR_LABEL}</span> },
                {
                  key: 'acoes', header: 'Ações',
                  render: (p) => (
                    <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                      <button type="button" onClick={() => openEdit(p)} className="p-2 rounded-lg hover:bg-[#F5E6EA] dark:hover:bg-neutral-600 transition-colors" style={{ color: CLINICA_BELEZA_PRIMARY }} title="Editar">
                        <Pencil size={18} />
                      </button>
                      {p.id >= 0 && (
                        <button type="button" onClick={() => exclude(p)} className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title="Desativar">
                          <Trash2 size={18} />
                        </button>
                      )}
                      <ChevronRight size={18} className="text-gray-400 ml-1 hidden md:inline self-center" />
                    </div>
                  ),
                },
              ]}
            />
            <EntityListLoadMore page={page} totalPages={totalPages} totalCount={totalCount ?? 0} pageSize={pageSize} loading={loading} onPageChange={setPage} itemLabel="pacientes" />
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
