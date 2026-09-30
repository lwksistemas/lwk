export interface RelatorioProfessionalOption {
  id: number;
  nome: string;
}

export function getDefaultRelatorioPeriod(): { dataInicio: string; dataFim: string } {
  const d = new Date();
  return {
    dataInicio: new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split("T")[0],
    dataFim: d.toISOString().split("T")[0],
  };
}

