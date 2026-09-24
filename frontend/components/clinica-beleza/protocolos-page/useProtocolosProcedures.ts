import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { resolveProcedureCategoriaSlug } from "@/lib/clinica-beleza-categories";
import { filterProceduresByModule } from "./protocolos-page-utils";
import type { ProtocoloProcedureOption } from "./protocolos-page-types";

export function useProtocolosProcedures(defaultCategoria: string) {
  const [procedures, setProcedures] = useState<ProtocoloProcedureOption[]>([]);

  const loadProcedures = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.procedures.list({ all: 1 });
      const arr = Array.isArray(data) ? (data as ProtocoloProcedureOption[]) : [];
      const doModulo = filterProceduresByModule(arr, defaultCategoria);
      const daCategoria = arr.filter(
        (item) => resolveProcedureCategoriaSlug(item.categoria) === "protocolo",
      );
      const ids = new Set(doModulo.map((item) => item.id));
      setProcedures([...doModulo, ...daCategoria.filter((item) => !ids.has(item.id))]);
    } catch {
      setProcedures([]);
    }
  }, [defaultCategoria]);

  useEffect(() => {
    void loadProcedures();
  }, [loadProcedures]);

  return { procedures };
}
