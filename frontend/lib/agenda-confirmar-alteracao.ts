import { formatClinicaDataCurta, formatClinicaHora } from "@/lib/clinica-beleza-datetime";

export type DescricaoAlteracaoAgenda = {
  titulo: string;
  linhas: string[];
};

function mesmoInstante(a: Date, b: Date): boolean {
  return a.getTime() === b.getTime();
}

function trechoHorario(antes: Date, depois: Date): string {
  if (antes.toDateString() === depois.toDateString()) {
    return `${formatClinicaHora(antes)} para ${formatClinicaHora(depois)}`;
  }
  return `${formatClinicaDataCurta(antes)} ${formatClinicaHora(antes)} para ${formatClinicaDataCurta(depois)} ${formatClinicaHora(depois)}`;
}

export function descreverAlteracaoAgenda(input: {
  nome: string;
  inicioAntes: Date;
  inicioDepois: Date;
  duracaoAntes?: number;
  duracaoDepois?: number;
  profissionalAntes?: string;
  profissionalDepois?: string;
}): DescricaoAlteracaoAgenda {
  const nome = input.nome.trim() || "este horário";
  const linhas: string[] = [];
  if (!mesmoInstante(input.inicioAntes, input.inicioDepois)) {
    linhas.push(`Mover ${nome} de ${trechoHorario(input.inicioAntes, input.inicioDepois)}.`);
  }
  const profAntes = (input.profissionalAntes || "").trim();
  const profDepois = (input.profissionalDepois || "").trim();
  if (profAntes && profDepois && profAntes !== profDepois) {
    linhas.push(`Trocar o profissional de ${profAntes} para ${profDepois}.`);
  }
  if (
    input.duracaoAntes != null
    && input.duracaoDepois != null
    && input.duracaoAntes !== input.duracaoDepois
  ) {
    linhas.push(`Alterar a duração de ${input.duracaoAntes} min para ${input.duracaoDepois} min.`);
  }
  return {
    titulo: "Confirmar alteração",
    linhas: linhas.length > 0 ? linhas : [`Aplicar a alteração de ${nome}.`],
  };
}

export function nomeProfissionalAgenda(
  id: number | null | undefined,
  professionals: { id: number; nome?: string; name?: string }[],
  atual?: string,
): string {
  if (id == null) return (atual || "").trim();
  const found = professionals.find((p) => p.id === Number(id));
  return (found?.nome || found?.name || atual || "").trim();
}
