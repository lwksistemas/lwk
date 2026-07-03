import { useCallback, useState } from "react";
import type { LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { locaisDisponiveisParaConsulta } from "./profissional-form-utils";
import type { ProfissionalCommission } from "./profissional-form-types";

export function useProfissionalComissoes(locais: LocalAtendimentoItem[]) {
  const [comissoes, setComissoes] = useState<ProfissionalCommission[]>([]);
  const [comissoesConsultaLocal, setComissoesConsultaLocal] = useState<ProfissionalCommission[]>([]);

  const addComissao = () => {
    setComissoes((prev) => [
      ...prev,
      { tipo: "procedimento", modo: "percentual", valor: "", procedure: null, convenio: null },
    ]);
  };

  const addComissaoConsultaLocal = () => {
    setComissoesConsultaLocal((prev) => [
      ...prev,
      { tipo: "consulta", modo: "percentual", valor: "", local_atendimento: null },
    ]);
  };

  const removeComissaoConsultaLocal = (idx: number) => {
    setComissoesConsultaLocal((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateComissaoConsultaLocal = (idx: number, field: string, value: string | number | null) => {
    setComissoesConsultaLocal((prev) => prev.map((c, i) => (i === idx ? { ...c, [field]: value } : c)));
  };

  const removeComissao = (idx: number) => {
    setComissoes((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateComissao = (idx: number, field: string, value: string | number | null) => {
    setComissoes((prev) => prev.map((c, i) => (i === idx ? { ...c, [field]: value } : c)));
  };

  const locaisDisponiveisConsulta = useCallback(
    (idx: number) => locaisDisponiveisParaConsulta(locais, comissoesConsultaLocal, idx),
    [comissoesConsultaLocal, locais],
  );

  return {
    comissoes,
    comissoesConsultaLocal,
    setComissoes,
    setComissoesConsultaLocal,
    addComissao,
    addComissaoConsultaLocal,
    removeComissaoConsultaLocal,
    updateComissaoConsultaLocal,
    removeComissao,
    updateComissao,
    locaisDisponiveisConsulta,
  };
}
