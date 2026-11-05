export type PeriodoFinanceiro = "" | "atual" | "passado" | "personalizado";

export function intervaloMes(ano: number, mes: number): { inicio: string; fim: string } {
  const ultimo = new Date(ano, mes, 0).getDate();
  const mm = String(mes).padStart(2, "0");
  return {
    inicio: `${ano}-${mm}-01`,
    fim: `${ano}-${mm}-${String(ultimo).padStart(2, "0")}`,
  };
}

export function periodoFinanceiro(
  tipo: PeriodoFinanceiro,
  hoje: Date,
  inicio: string,
  fim: string,
): { inicio: string; fim: string } {
  if (tipo === "atual") return intervaloMes(hoje.getFullYear(), hoje.getMonth() + 1);
  if (tipo === "passado") {
    const anterior = new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1);
    return intervaloMes(anterior.getFullYear(), anterior.getMonth() + 1);
  }
  if (tipo === "personalizado") return { inicio, fim };
  return { inicio: "", fim: "" };
}
