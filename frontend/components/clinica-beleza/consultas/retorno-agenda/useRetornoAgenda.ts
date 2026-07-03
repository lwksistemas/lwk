import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ClinicaBelezaAPI,
  type AgendaRetornoConfigItem,
  type RetornoProcedimentoRegraItem,
} from "@/lib/clinica-beleza-api";
import { extractRetornoAgendaError } from "./retorno-agenda-utils";

export function useRetornoAgenda(open: boolean) {
  const [config, setConfig] = useState<AgendaRetornoConfigItem | null>(null);
  const [regras, setRegras] = useState<RetornoProcedimentoRegraItem[]>([]);
  const [procedures, setProcedures] = useState<{ id: number; nome?: string; name?: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [novaRegraProc, setNovaRegraProc] = useState<number | "">("");
  const [novaRegraDias, setNovaRegraDias] = useState("30");

  const loadAll = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const cfg = await ClinicaBelezaAPI.retorno.getConfig();
      const [regs, procs] = await Promise.all([
        ClinicaBelezaAPI.retorno.listRegras(),
        ClinicaBelezaAPI.procedures.list({ active: true, page_size: 500 }),
      ]);
      setConfig(cfg);
      setRegras(Array.isArray(regs) ? regs : []);
      setProcedures(Array.isArray(procs) ? procs : []);
    } catch (e: unknown) {
      setErro(extractRetornoAgendaError(e, "Erro ao carregar configuração de retorno."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      void loadAll();
      setNovaRegraProc("");
      setNovaRegraDias("30");
      setErro("");
    }
  }, [open, loadAll]);

  const proceduresDisponiveis = useMemo(() => {
    const usados = new Set(regras.map((r) => r.procedure));
    return procedures.filter((p) => !usados.has(p.id));
  }, [procedures, regras]);

  const salvarConfig = async (patch: Partial<AgendaRetornoConfigItem>) => {
    if (!config) return;
    setSalvando(true);
    setErro("");
    try {
      const updated = await ClinicaBelezaAPI.retorno.updateConfig(patch);
      setConfig(updated);
    } catch (e: unknown) {
      setErro(extractRetornoAgendaError(e, "Erro ao salvar configuração."));
    } finally {
      setSalvando(false);
    }
  };

  const atualizarDiasConsultaLocal = (dias: number) => {
    if (!config) return;
    setConfig({ ...config, dias_retorno_consulta: dias });
  };

  const salvarDiasConsulta = () => {
    if (!config) return;
    void salvarConfig({ dias_retorno_consulta: config.dias_retorno_consulta });
  };

  const adicionarRegra = async () => {
    if (!novaRegraProc) {
      setErro("Selecione o procedimento.");
      return;
    }
    const dias = parseInt(novaRegraDias, 10);
    if (!dias || dias < 1) {
      setErro("Informe o prazo em dias (mínimo 1).");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.retorno.createRegra({ procedure: Number(novaRegraProc), dias_retorno: dias });
      setNovaRegraProc("");
      setNovaRegraDias("30");
      await loadAll();
    } catch (e: unknown) {
      setErro(extractRetornoAgendaError(e, "Erro ao adicionar regra."));
    } finally {
      setSalvando(false);
    }
  };

  const excluirRegra = async (id: number) => {
    if (!confirm("Remover esta regra de retorno por procedimento?")) return;
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.retorno.deleteRegra(id);
      await loadAll();
    } catch (e: unknown) {
      setErro(extractRetornoAgendaError(e, "Erro ao excluir regra."));
    } finally {
      setSalvando(false);
    }
  };

  return {
    config,
    regras,
    loading,
    salvando,
    erro,
    novaRegraProc,
    novaRegraDias,
    proceduresDisponiveis,
    setNovaRegraProc,
    setNovaRegraDias,
    loadAll,
    salvarConfig,
    atualizarDiasConsultaLocal,
    salvarDiasConsulta,
    adicionarRegra,
    excluirRegra,
  };
}
