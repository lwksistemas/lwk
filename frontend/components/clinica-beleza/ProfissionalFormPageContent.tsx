"use client";

/**
 * Página dedicada para cadastro/edição de profissional — Clínica da Beleza.
 * Substitui o modal que ficava apertado com tantos campos.
 * Seções: Dados Básicos, Prescritor (Memed), Acesso, Comissões.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Save, Trash2, Plus } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, ConvenioItem, LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
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
interface Commission {
  id?: number;
  tipo: string;
  modo: string;
  valor: string;
  procedure?: number | null;
  procedure_name?: string;
  convenio?: number | null;
  convenio_nome?: string;
  convenio_codigo?: string;
  local_atendimento?: number | null;
  local_atendimento_nome?: string;
}

const inputClass = "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";
const labelClass = "block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1";

interface ProfissionalFormPageContentProps {
  slug: string;
  editId: string | null;
  onDone: () => void;
}

export function ProfissionalFormPageContent({ slug, editId, onDone }: ProfissionalFormPageContentProps) {
  const [form, setForm] = useState({
    name: "", specialty: "", phone: "", email: "",
    conselho: "", registro: "", uf: "", cpf: "",
    data_nascimento: "", sexo: "",
    criar_acesso: false, perfil: "profissional" as PerfilAcesso,
  });
  const [comissoes, setComissoes] = useState<Commission[]>([]);
  const [comissoesConsultaLocal, setComissoesConsultaLocal] = useState<Commission[]>([]);
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!!editId);

  const set = (field: string, value: string | boolean) => setForm((f) => ({ ...f, [field]: value }));

  // Carregar procedimentos para comissões
  useEffect(() => {
    ClinicaBelezaAPI.procedures.list().then((data) => {
      setProcedures(Array.isArray(data) ? data : []);
    }).catch(() => {});
    ClinicaBelezaAPI.locaisAtendimento.list().then((data) => {
      setLocais(Array.isArray(data) ? data : []);
    }).catch(() => {});
    ClinicaBelezaAPI.convenios.list().then((data) => {
      setConvenios(Array.isArray(data) ? data : []);
    }).catch(() => {});
  }, []);

  // Carregar dados do profissional para edição
  useEffect(() => {
    if (!editId) return;
    setLoading(true);
    (async () => {
      try {
        const [prof, comissoesData, locaisData] = await Promise.all([
          ClinicaBelezaAPI.professionals.get(Number(editId)),
          ClinicaBelezaAPI.professionals.comissoes.list(Number(editId)).catch(() => []),
          ClinicaBelezaAPI.locaisAtendimento.list().catch(() => []),
        ]);
        const locaisAtivos = Array.isArray(locaisData) ? locaisData : [];
        setLocais(locaisAtivos);
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
            ? comissoesData
                .filter((c: any) => c.tipo === "procedimento")
                .map((c: any) => ({
                  id: c.id, tipo: c.tipo, modo: c.modo,
                  valor: String(c.valor), procedure: c.procedure,
                  procedure_name: c.procedure_name,
                  convenio: c.convenio,
                  convenio_nome: c.convenio_nome,
                  convenio_codigo: c.convenio_codigo,
                }))
            : []
        );
        const consultasComissao = Array.isArray(comissoesData)
          ? comissoesData.filter((c: any) => c.tipo === "consulta")
          : [];
        const porLocal = consultasComissao.filter((c: any) => c.local_atendimento);
        const geral = consultasComissao.find((c: any) => !c.local_atendimento);
        if (porLocal.length > 0) {
          setComissoesConsultaLocal(
            porLocal.map((c: any) => ({
              tipo: "consulta",
              modo: c.modo,
              valor: String(c.valor),
              local_atendimento: c.local_atendimento,
              local_atendimento_nome: c.local_atendimento_nome,
            })),
          );
        } else if (geral && locaisAtivos.length > 0) {
          setComissoesConsultaLocal(
            locaisAtivos.map((l) => ({
              tipo: "consulta",
              modo: geral.modo,
              valor: String(geral.valor),
              local_atendimento: l.id,
              local_atendimento_nome: l.nome,
            })),
          );
        } else {
          setComissoesConsultaLocal([]);
        }
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
    setComissoes((prev) => [
      ...prev,
      { tipo: "procedimento", modo: "percentual", valor: "", procedure: null, convenio: null },
    ]);
  };
  const addComissaoConsultaLocal = () => {
    setComissoesConsultaLocal((prev) => [
      ...prev,
      { tipo: "consulta", modo: "percentual", valor: "", local_atendimento: null },
    ]);
  };
  const removeComissaoConsultaLocal = (idx: number) => {
    setComissoesConsultaLocal((prev) => prev.filter((_, i) => i !== idx));
  };
  const updateComissaoConsultaLocal = (idx: number, field: string, value: string | number | null) => {
    setComissoesConsultaLocal((prev) => prev.map((c, i) => (i === idx ? { ...c, [field]: value } : c)));
  };
  const removeComissao = (idx: number) => {
    setComissoes((prev) => prev.filter((_, i) => i !== idx));
  };
  const updateComissao = (idx: number, field: string, value: string | number | null) => {
    setComissoes((prev) => prev.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  };

  const locaisDisponiveisConsulta = useCallback(
    (idx: number) => {
      const usados = new Set(
        comissoesConsultaLocal
          .map((c, i) => (i !== idx ? c.local_atendimento : null))
          .filter((id): id is number => id != null),
      );
      const atual = comissoesConsultaLocal[idx]?.local_atendimento;
      return locais.filter((l) => !usados.has(l.id) || l.id === atual);
    },
    [comissoesConsultaLocal, locais],
  );

  const salvar = async () => {
    if (!form.name.trim()) { setError("Nome é obrigatório."); return; }
    if (!form.specialty.trim()) { setError("Especialidade é obrigatória."); return; }
    if (form.criar_acesso && !form.email.trim()) { setError("E-mail é obrigatório para criar acesso."); return; }

    const locaisConsultaUsados = comissoesConsultaLocal
      .filter((c) => c.valor && Number(c.valor) > 0)
      .map((c) => c.local_atendimento)
      .filter((id): id is number => id != null);
    if (new Set(locaisConsultaUsados).size !== locaisConsultaUsados.length) {
      setError("Não repita o mesmo local na comissão de consulta.");
      return;
    }
    if (comissoesConsultaLocal.some((c) => c.valor && Number(c.valor) > 0 && !c.local_atendimento)) {
      setError("Selecione o local de atendimento em cada comissão de consulta.");
      return;
    }

    const paresProcedimento = comissoes
      .filter((c) => c.valor && Number(c.valor) > 0 && c.procedure)
      .map((c) => `${c.procedure}:${c.convenio ?? ""}`);
    if (new Set(paresProcedimento).size !== paresProcedimento.length) {
      setError("Não repita o mesmo procedimento para o mesmo convênio.");
      return;
    }
    if (comissoes.some((c) => c.valor && Number(c.valor) > 0 && c.procedure && !c.convenio)) {
      setError("Selecione o convênio em cada comissão de procedimento.");
      return;
    }

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
        await ClinicaBelezaAPI.professionals.update(Number(editId), body);
      } else {
        const created = await ClinicaBelezaAPI.professionals.create(body) as { id: number };
        profId = String(created.id);
      }

      // Salvar comissões
      if (profId) {
        const payload: any[] = [];
        for (const c of comissoesConsultaLocal) {
          if (c.valor && Number(c.valor) > 0 && c.local_atendimento) {
            payload.push({
              tipo: "consulta",
              modo: c.modo,
              valor: c.valor,
              procedure: null,
              local_atendimento: c.local_atendimento,
            });
          }
        }
        // Comissões por procedimento
        for (const c of comissoes) {
          if (c.valor && Number(c.valor) > 0 && c.procedure && c.convenio) {
            payload.push({
              tipo: "procedimento",
              modo: c.modo,
              valor: c.valor,
              procedure: c.procedure,
              convenio: c.convenio,
            });
          }
        }
        await ClinicaBelezaAPI.professionals.comissoes.save(Number(profId), payload);
      }

      onDone();
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
        <div className="space-y-6">
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
          <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Comissões</h3>

            <div className="bg-purple-50 dark:bg-purple-900/10 border border-purple-200 dark:border-purple-800/40 rounded-lg p-4 space-y-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-xs font-semibold text-purple-800 dark:text-purple-300">
                    Comissão da consulta por local de atendimento
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Adicione cada local e defina percentual ou valor fixo. A regra vale só no local escolhido.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={addComissaoConsultaLocal}
                  disabled={comissoesConsultaLocal.length >= locais.length}
                  className="inline-flex items-center gap-1 text-xs font-medium text-purple-600 dark:text-purple-400 hover:underline disabled:opacity-40 disabled:no-underline"
                >
                  <Plus size={14} /> Adicionar local
                </button>
              </div>
              {comissoesConsultaLocal.length === 0 ? (
                <p className="text-xs text-gray-400 italic">
                  Ex.: Unidade Moema 35%, Spa Clínico R$ 140 fixo, Teleconsulta 20%.
                </p>
              ) : (
                comissoesConsultaLocal.map((c, idx) => (
                  <div key={idx} className="flex flex-wrap items-center gap-2 bg-white/60 dark:bg-neutral-800/40 rounded-lg px-3 py-2.5">
                    <div className="flex-1 min-w-[180px]">
                      <label className="sr-only">Local de atendimento</label>
                      <select
                        value={c.local_atendimento ?? ""}
                        onChange={(e) => updateComissaoConsultaLocal(idx, "local_atendimento", e.target.value ? Number(e.target.value) : null)}
                        className={inputClass}
                      >
                        <option value="">Selecione o local...</option>
                        {locaisDisponiveisConsulta(idx).map((l) => (
                          <option key={l.id} value={l.id}>{l.nome}</option>
                        ))}
                      </select>
                    </div>
                    <div className="w-36">
                      <select value={c.modo} onChange={(e) => updateComissaoConsultaLocal(idx, "modo", e.target.value)} className={inputClass}>
                        <option value="percentual">% do valor</option>
                        <option value="fixo">R$ fixo</option>
                      </select>
                    </div>
                    <div className="w-28">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={c.valor}
                        onChange={(e) => updateComissaoConsultaLocal(idx, "valor", e.target.value)}
                        className={inputClass}
                        placeholder={c.modo === "percentual" ? "35" : "140.00"}
                      />
                    </div>
                    <button type="button" onClick={() => removeComissaoConsultaLocal(idx)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded" aria-label="Remover">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Comissões por procedimento */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">Comissão por Procedimento</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Defina por procedimento e convênio. Ex.: Botox na Unimed R$ fixo; na Santa Casa percentual.
                  </p>
                </div>
                <button type="button" onClick={addComissao} className="inline-flex items-center gap-1 text-xs font-medium text-purple-600 dark:text-purple-400 hover:underline">
                  <Plus size={14} /> Adicionar
                </button>
              </div>
              {comissoes.length === 0 ? (
                <p className="text-xs text-gray-400 italic">Nenhuma comissão por procedimento configurada.</p>
              ) : (
                <div className="space-y-2">
                  {comissoes.map((c, idx) => (
                    <div key={idx} className="flex flex-wrap items-center gap-2 bg-gray-50 dark:bg-neutral-700/30 rounded-lg px-3 py-2.5">
                      <div className="flex-1 min-w-[160px]">
                        <label className="sr-only">Procedimento</label>
                        <select
                          value={c.procedure ?? ""}
                          onChange={(e) => updateComissao(idx, "procedure", e.target.value ? Number(e.target.value) : null)}
                          className={inputClass}
                        >
                          <option value="">Procedimento...</option>
                          {procedures.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
                        </select>
                      </div>
                      <div className="flex-1 min-w-[140px]">
                        <label className="sr-only">Convênio</label>
                        <select
                          value={c.convenio ?? ""}
                          onChange={(e) => updateComissao(idx, "convenio", e.target.value ? Number(e.target.value) : null)}
                          className={inputClass}
                        >
                          <option value="">Convênio...</option>
                          {convenios.map((cv) => (
                            <option key={cv.id} value={cv.id}>
                              {cv.codigo ? `${cv.codigo} — ${cv.nome}` : cv.nome}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="w-28">
                        <select value={c.modo} onChange={(e) => updateComissao(idx, "modo", e.target.value)} className={inputClass}>
                          <option value="percentual">%</option>
                          <option value="fixo">R$</option>
                        </select>
                      </div>
                      <div className="w-24">
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={c.valor}
                          onChange={(e) => updateComissao(idx, "valor", e.target.value)}
                          className={inputClass}
                          placeholder={c.modo === "percentual" ? "30" : "200.00"}
                        />
                      </div>
                      <button type="button" onClick={() => removeComissao(idx)} className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
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
              onClick={onDone}
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
