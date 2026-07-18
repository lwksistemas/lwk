import type { ConvenioItem, LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { telefoneInternacionalBr } from "@/lib/format-br";
import type {
  ProfissionalCommission,
  ProfissionalFormState,
} from "./profissional-form-types";
import { DEFAULT_PROFISSIONAL_FORM } from "./profissional-form-types";

type ComissaoApiRow = {
  id?: number;
  tipo?: string;
  modo?: string;
  valor?: number | string;
  procedure?: number;
  procedure_name?: string;
  convenio?: number;
  convenio_nome?: string;
  convenio_codigo?: string;
  local_atendimento?: number;
  local_atendimento_nome?: string;
};

export type ProfissionalApiRow = {
  nome?: string;
  name?: string;
  especialidade?: string;
  specialty?: string;
  telefone?: string;
  phone?: string;
  email?: string;
  conselho?: string;
  registro_profissional?: string;
  conselho_uf?: string;
  cpf?: string;
  data_nascimento?: string;
  sexo?: string;
};

export function mapProfissionalFormFromApi(prof: ProfissionalApiRow): ProfissionalFormState {
  return {
    ...DEFAULT_PROFISSIONAL_FORM,
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
  };
}

export function mapComissoesProcedimentoFromApi(comissoesData: unknown): ProfissionalCommission[] {
  if (!Array.isArray(comissoesData)) return [];
  return (comissoesData as ComissaoApiRow[])
    .filter((c) => c.tipo === "procedimento")
    .map((c) => ({
      id: c.id,
      tipo: c.tipo!,
      modo: c.modo!,
      valor: String(c.valor),
      procedure: c.procedure,
      procedure_name: c.procedure_name,
      convenio: c.convenio,
      convenio_nome: c.convenio_nome,
      convenio_codigo: c.convenio_codigo,
    }));
}

export function mapComissoesConsultaFromApi(
  comissoesData: unknown,
  locaisAtivos: LocalAtendimentoItem[],
): ProfissionalCommission[] {
  if (!Array.isArray(comissoesData)) return [];
  const consultasComissao = (comissoesData as ComissaoApiRow[]).filter((c) => c.tipo === "consulta");
  const porLocal = consultasComissao.filter((c) => c.local_atendimento);
  const geral = consultasComissao.find((c) => !c.local_atendimento);
  if (porLocal.length > 0) {
    return porLocal.map((c) => ({
      tipo: "consulta",
      modo: c.modo!,
      valor: String(c.valor),
      local_atendimento: c.local_atendimento,
      local_atendimento_nome: c.local_atendimento_nome,
    }));
  }
  if (geral && locaisAtivos.length > 0) {
    return locaisAtivos.map((l) => ({
      tipo: "consulta",
      modo: geral.modo!,
      valor: String(geral.valor),
      local_atendimento: l.id,
      local_atendimento_nome: l.nome,
    }));
  }
  return [];
}

export function locaisDisponiveisParaConsulta(
  locais: LocalAtendimentoItem[],
  comissoesConsultaLocal: ProfissionalCommission[],
  idx: number,
): LocalAtendimentoItem[] {
  const usados = new Set(
    comissoesConsultaLocal
      .map((c, i) => (i !== idx ? c.local_atendimento : null))
      .filter((id): id is number => id != null),
  );
  const atual = comissoesConsultaLocal[idx]?.local_atendimento;
  return locais.filter((l) => !usados.has(l.id) || l.id === atual);
}

export function suggestUsernameFromName(name: string): string {
  return name
    .trim()
    .split(" ")[0]
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function validateProfissionalForm(
  form: ProfissionalFormState,
  comissoes: ProfissionalCommission[],
  comissoesConsultaLocal: ProfissionalCommission[],
  isEditing: boolean,
): string | null {
  if (!form.name.trim()) return "Nome é obrigatório.";
  if (!form.specialty.trim()) return "Especialidade é obrigatória.";
  if (!isEditing && form.criar_acesso && !form.username.trim()) {
    return "Usuário para login é obrigatório.";
  }
  if (!isEditing && form.criar_acesso && !form.email.trim()) {
    return "E-mail é obrigatório para enviar a senha.";
  }

  const locaisConsultaUsados = comissoesConsultaLocal
    .filter((c) => c.valor && Number(c.valor) > 0)
    .map((c) => c.local_atendimento)
    .filter((id): id is number => id != null);
  if (new Set(locaisConsultaUsados).size !== locaisConsultaUsados.length) {
    return "Não repita o mesmo local na comissão de consulta.";
  }
  if (comissoesConsultaLocal.some((c) => c.valor && Number(c.valor) > 0 && !c.local_atendimento)) {
    return "Selecione o local de atendimento em cada comissão de consulta.";
  }

  const paresProcedimento = comissoes
    .filter((c) => c.valor && Number(c.valor) > 0 && c.procedure)
    .map((c) => `${c.procedure}:${c.convenio ?? ""}`);
  if (new Set(paresProcedimento).size !== paresProcedimento.length) {
    return "Não repita o mesmo procedimento para o mesmo convênio.";
  }
  if (comissoes.some((c) => c.valor && Number(c.valor) > 0 && c.procedure && !c.convenio)) {
    return "Selecione o convênio em cada comissão de procedimento.";
  }

  return null;
}

export function buildProfissionalSaveBody(
  form: ProfissionalFormState,
  editId: string | null,
): Record<string, unknown> {
  const body: Record<string, unknown> = {
    name: form.name.trim(),
    specialty: form.specialty.trim(),
    phone: form.phone.trim() ? telefoneInternacionalBr(form.phone) : null,
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
    body.username = form.username.trim();
  }
  return body;
}

export function buildComissoesSavePayload(
  comissoes: ProfissionalCommission[],
  comissoesConsultaLocal: ProfissionalCommission[],
): Record<string, unknown>[] {
  const payload: Record<string, unknown>[] = [];
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
  return payload;
}

export function formatConvenioLabel(cv: ConvenioItem): string {
  return cv.nome;
}
