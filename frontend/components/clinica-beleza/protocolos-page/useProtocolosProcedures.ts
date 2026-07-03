import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { filterProceduresByModule } from "./protocolos-page-utils";
import type { ProtocoloProcedureOption } from "./protocolos-page-types";

export function useProtocolosProcedures(defaultCategoria: string) {
  const [procedures, setProcedures] = useState<ProtocoloProcedureOption[]>([]);

  const loadProcedures = useCallback(async () => {
    try {
      const data = await ClinicaBelezaAPI.procedures.list();
      const arr = Array.isArray(data) ? (data as ProtocoloProcedureOption[]) : [];
      setProcedures(filterProceduresByModule(arr, defaultCategoria));
    } catch {
      setProcedures([]);
    }
  }, [defaultCategoria]);

  useEffect(() => {
    void loadProcedures();
  }, [loadProcedures]);

  return { procedures };
}
