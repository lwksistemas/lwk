import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";

export type UseConsultaDetailLoaderArgs = {
  consulta: Consulta;
  detailPreloaded?: boolean;
  onSelectConsulta: (c: Consulta) => void;
  onLoadStart?: () => void;
  onListRefresh?: () => void | Promise<void>;
};
