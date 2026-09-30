export const MSG_CONSULTA_EM_ANDAMENTO =
  "Consulta em andamento. Só o profissional deste atendimento pode abri-la até finalizar.";

export const MSG_REABRIR_SO_QUEM_FEZ =
  "Só o profissional que realizou esta consulta pode reabri-la.";

type ConsultaAcesso = {
  status?: string;
  professional?: number | null;
};

/** null = ainda não sabemos quem está logado. true = outro profissional, bloqueia. */
export function consultaEmAndamentoDeOutro(
  consulta: ConsultaAcesso,
  meuProfessionalId: number | null | undefined,
): boolean | null {
  if (consulta.status !== "IN_PROGRESS") return false;
  if (meuProfessionalId === undefined) return null;
  if (meuProfessionalId == null) return true;
  return Number(consulta.professional) !== Number(meuProfessionalId);
}

export type PassoInicio =
  | { tipo: "modal" }
  | { tipo: "trocar"; professionalId: number; iniciarDepois: boolean }
  | { tipo: "iniciar" };

/** Quem inicia é o profissional da agenda. Outro nome só entra depois da troca. */
export function passoInicioConsulta(
  consulta: { professional?: number | null },
  meuProfessionalId: number | null,
  professionalEscolhido?: number,
): PassoInicio {
  if (professionalEscolhido == null) {
    if (
      meuProfessionalId != null
      && consulta.professional != null
      && Number(consulta.professional) === Number(meuProfessionalId)
    ) {
      return { tipo: "iniciar" };
    }
    return { tipo: "modal" };
  }
  const mudou = consulta.professional == null
    || Number(consulta.professional) !== Number(professionalEscolhido);
  const souEu = meuProfessionalId != null
    && Number(professionalEscolhido) === Number(meuProfessionalId);
  if (mudou) {
    return { tipo: "trocar", professionalId: professionalEscolhido, iniciarDepois: souEu };
  }
  if (souEu) return { tipo: "iniciar" };
  return { tipo: "modal" };
}

export function textoModalProfissional(consulta: {
  professional?: number | null;
  professional_name?: string | null;
}): { titulo: string; descricao: string } {
  if (consulta.professional) {
    const nome = consulta.professional_name || "o profissional da agenda";
    return {
      titulo: "Trocar profissional",
      descricao: `A agenda está com ${nome}. Se essa pessoa não puder atender, escolha quem vai realizar a consulta.`,
    };
  }
  return {
    titulo: "Selecione o Profissional",
    descricao: "Este agendamento não possui profissional. Informe quem realizará o atendimento.",
  };
}

export function podeReabrirConsulta(
  consulta: ConsultaAcesso,
  meuProfessionalId: number | null | undefined,
): boolean {
  if (consulta.status !== "COMPLETED" || meuProfessionalId == null) return false;
  return Number(consulta.professional) === Number(meuProfessionalId);
}
