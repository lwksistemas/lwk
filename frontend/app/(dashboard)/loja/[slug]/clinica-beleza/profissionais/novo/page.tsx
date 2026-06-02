"use client";

/**
 * Página dedicada para cadastro/edição de profissional — Clínica da Beleza.
 * Substitui o modal que ficava apertado com tantos campos.
 * Seções: Dados Básicos, Prescritor (Memed), Acesso, Comissões.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Save, Trash2, Plus } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { formatTelefone, formatCpf } from "@/lib/format-br";
import { formatProfissionalApiErrors } from "@/lib/clinica-beleza-form-errors";
import { logger } from "@/lib/logger";

type PerfilAcesso = "administrador" | "profissional" | "recepcao" | "recepcionista" | "caixa" | "limpeza" | "estoque";

const UFS_BR = [
  "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
  "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
];
const CONSELHOS = [
  ["CRM","CRM - Medicina"],["CRO","CRO - Odontologia"],["COREN","COREN - Enfermagem"],
  ["CRF","CRF - Farmácia"],["CRP","CRP - Psicologia"],["CRN","CRN - Nutrição"],
  ["CREFITO","CREFITO - Fisioterapia/TO"],["CRBM","CRBM - Biomedicina"],
  ["CRMV","CRMV - Veterinária"],["CRFa","CRFa - Fonoaudiologia"],
];

interface Procedure { id: number; nome: string; preco?: number; }
interface Commission { id?: number; tipo: string; modo: string; valor: string; procedure?: number | null; procedure_name?: string; }

const inputClass = "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";
const labelClass = "block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1";

export default function NovoProfissionalPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const editId = searchParams.get("id"); // ?id=5 para edição

  const [form, setForm] = useState({
    name: "", specialty: "", phone: "", email: "",
    conselho: "", registro: "", uf: "", cpf: "",
    data_nascimento: "", sexo: "",
    criar_acesso: false, perfil: "profissional" as PerfilAcesso,
  });
  const [comissoes, setComissoes] = useState<Commission[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!!editId);

  const set = (field: string, value: string | boolean) => setForm((f) => ({ ...f, [field]: value }));

  // Carregar procedimentos para comissões
  useEffect(() => {
    ClinicaBelezaAPI.get<Procedure[]>("/procedures/").then((data) => {
      setProcedures(Array.isArray(data) ? data : []);
    }).catch(() => {});
  }, []);

  // Carregar dados do profissional para edição
  useEffect(() => {
    if (!editId) return;
    setLoading(true);
    (async () => {
      try {
        const [prof, comissoesData] = await Promise.all([
          clinicaBelezaFetch(`/professionals/${editId}/`).then((r) => r.json()),
          clinicaBelezaFetch(`/professionals/${editId}/comissoes/`).then((r) => r.ok ? r.json() : []),
        ]);
        setForm({
          name: prof.nome || prof.name || "",
          specialty: prof.especialidade || prof.specialty || "",
          phone: prof.telefone || prof.phone || "",
          email: prof.email || "",
          conselho: prof.conselho || "",
          registro: prof.registro_profissional || "",
          uf: prof.conselho_uf || "",
          cpf: prof.cpf || "",
          data_nascimento: prof.data_nascimento || "",
          sexo: prof.sexo || "",
          criar_acesso: false,
          perfil: "profissional",
        });
        setComissoes(
          Array.isArray(comissoesData)
            ? comissoesData.map((c: any) => ({
                id: c.id, tipo: c.tipo, modo: c.modo,
                valor: String(c.valor), procedure: c.procedure,
                procedure_name: c.procedure_name,
              }))
            : []
        );
      } catch (e) {
        logger.warn("Erro ao carregar profissional:", e);
        setError("Erro ao carregar dados do profissional.");
      } finally {
        setLoading(false);
      }
    })();
  }, [editId]);

  // Comissões helpers
  const addComissao = () => {
    setComissoes((prev) => [...prev, { tipo: "consulta", modo: "percentual", valor: "", procedure: null }]);
  };
  const removeComissao = (idx: number) => {
    setComissoes((prev) => prev.filter((_, i) => i !== idx));
  };
  const updateComissao = (idx: number, field: string, value: string | number | null) => {
    setComissoes((prev) => prev.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  };

  const salvar = async () => {
    if (!form.name.trim()) { setError("Nome é obrigatório."); return; }
    if (!form.specialty.trim()) { setError("Especialidade é obrigatória."); return; }
    if (form.criar_acesso && !form.email.trim()) { setError("E-mail é obrigatório para criar acesso."); return; }

    setSaving(true);
    setError("");

    const body: Record<string, unknown> = {
      name: form.name.trim(),
      specialty: form.specialty.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      registro_profissional: form.registro.trim() || null,
      conselho: form.conselho || null,
      conselho_uf: form.uf || null,
      cpf: form.cpf.trim() || null,
      data_nascimento: form.data_nascimento || null,
      sexo: form.sexo || null,
      active: true,
    };
    if (!editId && form.criar_acesso) {
      body.criar_acesso = true;
      body.perfil = form.perfil;
    }

    try {
      let profId = editId;
      if (editId) {
        await clinicaBelezaFetch(`/professionals/${editId}/`, {
          method: "PUT", body: JSON.stringify(body),
        }).then((r) => { if (!r.ok) throw r; });
      } else {
        const res = await clinicaBelezaFetch("/professionals/", {
          method: "POST", body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw err;
        }
        const created = await res.json();
        profId = String(created.id);
      }

      // Salvar comissões
      if (profId && comissoes.length > 0) {
        const payload = comissoes
          .filter((c) => c.valor && Number(c.valor) > 0)
          .map((c) => ({
            tipo: c.tipo,
            modo: c.modo,
            valor: c.valor,
            procedure: c.tipo === "procedimento" ? c.procedure : null,
          }));
        if (payload.length > 0) {
          await clinicaBelezaFetch(`/professionals/${profId}/comissoes/`, {
            method: "POST", body: JSON.stringify(payload),
          });
        }
      }

      router.push(`/loja/${slug}/clinica-beleza/profissionais`);
    } catch (e: any) {
      const msg = formatProfissionalApiErrors(e) || (e?.message || e?.detail || "Erro ao salvar.");
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader title="Profissional" />
        <ClinicaBelezaPageContent>
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={editId ? "Editar Profissional" : "Novo Profissional"}
        backHref={`/loja/${slug}/clinica-beleza/profissionais`}
      />
      <ClinicaBelezaPageContent>
        <div className="max-w-2xl mx-auto space-y-6">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-800 dark:text-red-300 whitespace-pre-line">{error}</p>
            </div>
          )}

          {/* Seção: Dados Básicos */}
          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Dados Básicos</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Nome *</label>
                <input value={form.name} onChange={(e) => set("name", e.target.value)} className={inputClass} placeholder="Nome completo" />
              </div>
              <div>
                <label className={labelClass}>Especialidade *</label>
                <input value={form.specialty} onChange={(e) => set("specialty", e.target.value)} className={inputClass} placeholder="Ex.: Esteticista" />
              </div>
              <div>
                <label className={labelClass}>Telefone</label>
                <input value={form.phone} onChange={(e) => set("phone", formatTelefone(e.target.value))} className={inputClass} placeholder="(00) 00000-0000" maxLength={15} />
              </div>
              <div>
                <label className={labelClass}>E-mail</label>
                <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} className={inputClass} placeholder="email@exemplo.com" />
              </div>
            </div>
          </section>

          {/* Seção: Prescritor (Memed) */}
          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Prescritor (Memed)</h3>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
              <div className="col-span-3 sm:col-span-2">
                <label className={labelClass}>Conselho</label>
                <select value={form.conselho} onChange={(e) => set("conselho", e.target.value)} className={inputClass}>
                  <option value="">—</option>
                  {CONSELHOS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              <div className="col-span-2 sm:col-span-2">
                <label className={labelClass}>Nº registro</label>
                <input value={form.registro} onChange={(e) => set("registro", e.target.value)} className={inputClass} placeholder="016964" />
              </div>
              <div className="col-span-1 sm:col-span-2">
                <label className={labelClass}>UF</label>
                <select value={form.uf} onChange={(e) => set("uf", e.target.value)} className={inputClass}>
                  <option value="">—</option>
                  {UFS_BR.map((uf) => <option key={uf} value={uf}>{uf}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className={labelClass}>CPF</label>
                <input value={form.cpf} onChange={(e) => set("cpf", formatCpf(e.target.value))} className={inputClass} placeholder="000.000.000-00" maxLength={14} />
              </div>
              <div>
                <label className={labelClass}>Data de nascimento</label>
                <input type="date" value={form.data_nascimento} onChange={(e) => set("data_nascimento", e.target.value)} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>Sexo</label>
                <select value={form.sexo} onChange={(e) => set("sexo", e.target.value)} className={inputClass}>
                  <option value="">—</option>
                  <option value="M">Masculino</option>
                  <option value="F">Feminino</option>
                </select>
              </div>
            </div>
          </section>

          {/* Seção: Comissões */}
          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Comissões</h3>
              <button type="button" onClick={addComissao} className="inline-flex items-center gap-1 text-xs font-medium text-purple-600 dark:text-purple-400 hover:underline">
                <Plus size={14} /> Adicionar
              </button>
            </div>
            {comissoes.length === 0 ? (
              <p className="text-xs text-gray-500 dark:text-gray-400">Nenhuma comissão configurada.</p>
            ) : (
              <div className="space-y-3">
                {comissoes.map((c, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end bg-gray-50 dark:bg-neutral-700/30 rounded-lg p-3">
                    <div className="col-span-3">
                      <label className={labelClass}>Tipo</label>
                      <select value={c.tipo} onChange={(e) => updateComissao(idx, "tipo", e.target.value)} className={inputClass}>
                        <option value="consulta">Consulta</option>
                        <option value="procedimento">Procedimento</option>
                      </select>
                    </div>
                    <div className="col-span-3">
                      <label className={labelClass}>Modo</label>
                      <select value={c.modo} onChange={(e) => updateComissao(idx, "modo", e.target.value)} className={inputClass}>
                        <option value="percentual">% Percentual</option>
                        <option value="fixo">R$ Fixo</option>
                      </select>
                    </div>
                    <div className="col-span-2">
                      <label className={labelClass}>{c.modo === "percentual" ? "%" : "R$"}</label>
                      <input type="number" step="0.01" value={c.valor} onChange={(e) => updateComissao(idx, "valor", e.target.value)} className={inputClass} placeholder="0.00" />
                    </div>
                    {c.tipo === "procedimento" && (
                      <div className="col-span-3">
                        <label className={labelClass}>Procedimento</label>
                        <select value={c.procedure ?? ""} onChange={(e) => updateComissao(idx, "procedure", e.target.value ? Number(e.target.value) : null)} className={inputClass}>
                          <option value="">Todos</option>
                          {procedures.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
                        </select>
                      </div>
                    )}
                    <div className={c.tipo === "procedimento" ? "col-span-1" : "col-span-4"}>
                      <button type="button" onClick={() => removeComissao(idx)} className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Seção: Acesso (apenas novo) */}
          {!editId && (
            <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Acesso ao sistema</h3>
              <div>
                <label className={labelClass}>Perfil de permissão</label>
                <select value={form.perfil} onChange={(e) => set("perfil", e.target.value)} className={inputClass}>
                  <option value="administrador">Administrador</option>
                  <option value="profissional">Profissional</option>
                  <option value="recepcionista">Recepcionista</option>
                  <option value="caixa">Caixa</option>
                  <option value="estoque">Estoque</option>
                </select>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.criar_acesso} onChange={(e) => set("criar_acesso", e.target.checked)} className="rounded border-gray-300 dark:border-neutral-600 text-purple-600" />
                <span className="text-sm text-gray-700 dark:text-gray-300">Criar login e enviar senha por e-mail</span>
              </label>
            </section>
          )}

          {/* Botões */}
          <div className="flex gap-3 pb-8">
            <button
              type="button"
              onClick={() => router.push(`/loja/${slug}/clinica-beleza/profissionais`)}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={salvar}
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-50 inline-flex items-center justify-center gap-2"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Save size={16} />
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
