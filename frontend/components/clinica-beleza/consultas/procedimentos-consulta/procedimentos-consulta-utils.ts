import { formatApiErrorBody } from "@/lib/api-errors";
import type { ConsultaProcedimento } from "../consultas-types";
import type { AppointmentProcedureItem, ProcedureOption } from "./procedimentos-consulta-types";

export function mapProcedimentosFromConsulta(lista: ConsultaProcedimento[]): AppointmentProcedureItem[] {
  return lista
    .filter((p) => p.appointment_procedure_id)
    .map((p) => ({
      id: p.appointment_procedure_id!,
      procedure: p.id,
      procedure_name: p.nome,
      valor_efetivo: Number(p.valor ?? 0),
    }));
}

export function normalizarCatalogoProcedimentos(
  procs: { id: number; nome?: string; name?: string; categoria?: string; category?: string }[],
): ProcedureOption[] {
  return procs
    .map((p) => ({
      id: p.id,
      nome: String(p.nome || p.name || ""),
      categoria: String(p.categoria || p.category || ""),
    }))
    .filter((p) => p.nome)
    .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
}

export function extractProcedimentosConsultaError(err: unknown, fallback: string): string {
  return formatApiErrorBody(err) || fallback;
}

export function avisoTermoProcedimentoAdicionado(
  consulta: Record<string, unknown> | undefined,
  procedureId: number,
): string {
  const added = (consulta?.procedures_list as ConsultaProcedimento[] | undefined)?.find(
    (p) => p.id === procedureId,
  );
  return added?.exige_termo
    ? "Procedimento incluído. Envie o termo de consentimento na aba correspondente."
    : "";
}

export function deveExibirProcedimentosSection({
  loading,
  itensCount,
  podeAdicionar,
  showAddForm,
  erro,
  avisoTermo,
}: {
  loading: boolean;
  itensCount: number;
  podeAdicionar: boolean;
  showAddForm: boolean;
  erro: string;
  avisoTermo: string;
}): boolean {
  if (loading) return true;
  if (itensCount > 0 || podeAdicionar || showAddForm || erro || avisoTermo) return true;
  return false;
}
