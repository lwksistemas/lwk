import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { fetchClinicaSchedulingProfessionals } from "@/lib/clinica-beleza-cadastros-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { passoInicioConsulta } from "./consulta-acesso";
import type { Consulta } from "./consultas-types";

export type ProfissionalOpcao = { id: number; nome?: string; name?: string };

export type PreparoInicio =
  | { acao: "modal"; profissionais: ProfissionalOpcao[] }
  | { acao: "trocou"; atualizada: Partial<Consulta>; seguir: boolean }
  | { acao: "iniciar" }
  | { acao: "erro" };

/** Decide se abre o modal, troca o profissional ou segue para iniciar. */
export async function prepararInicioConsulta(
  consulta: { id: number; professional?: number | null },
  professionalId: number | undefined,
  avisar: { sucesso: (mensagem: string) => void; erro: (mensagem: string) => void },
): Promise<PreparoInicio> {
  const me = await ClinicaBelezaAPI.me.get().catch(() => null);
  const passo = passoInicioConsulta(consulta, me?.professional_id ?? null, professionalId);
  if (passo.tipo === "modal") {
    let profissionais: ProfissionalOpcao[] = [];
    try {
      const profs = await fetchClinicaSchedulingProfessionals();
      profissionais = Array.isArray(profs) ? profs : [];
    } catch {
      profissionais = [];
    }
    return { acao: "modal", profissionais };
  }
  if (passo.tipo === "trocar") {
    try {
      const atualizada = await ClinicaBelezaAPI.consultas.trocarProfissional(
        consulta.id,
        passo.professionalId,
      );
      if (!passo.iniciarDepois) {
        avisar.sucesso("Profissional da agenda atualizado. Quem for atender inicia a consulta.");
      }
      return { acao: "trocou", atualizada, seguir: passo.iniciarDepois };
    } catch (e: unknown) {
      avisar.erro(formatApiErrorBody(e) || "Erro ao trocar o profissional.");
      return { acao: "erro" };
    }
  }
  return { acao: "iniciar" };
}
