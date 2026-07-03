import { useEffect } from "react";
import type { ReactNode } from "react";
import type { TabId } from "./consultas-types";

export function useConsultaDetailShellEffects({
  tab,
  setTab,
  temHistoricoAnterior,
  setFotosToolbar,
}: {
  tab: TabId;
  setTab: (tab: TabId) => void;
  temHistoricoAnterior: boolean;
  setFotosToolbar: (node: ReactNode | null) => void;
}) {
  useEffect(() => {
    if (tab !== "fotos") setFotosToolbar(null);
  }, [tab, setFotosToolbar]);

  useEffect(() => {
    if (tab === "historico" && !temHistoricoAnterior) {
      setTab("atendimento");
    }
  }, [tab, temHistoricoAnterior, setTab]);
}
