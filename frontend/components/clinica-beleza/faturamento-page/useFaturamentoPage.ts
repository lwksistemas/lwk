import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { getDefaultRelatorioPeriod } from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import type { AgrupamentoFaturamento, FaturamentoData } from "./faturamento-page-types";
import { downloadFaturamentoCsv, parseAgrupamentoFaturamento } from "./faturamento-page-utils";

export function useFaturamentoPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;

  const [agrupamento, setAgrupamento] = useState<AgrupamentoFaturamento>(() =>
    parseAgrupamentoFaturamento(searchParams.get("agrupar")),
  );
  const defaultPeriod = getDefaultRelatorioPeriod();
  const [dataInicio, setDataInicio] = useState(defaultPeriod.dataInicio);
  const [dataFim, setDataFim] = useState(defaultPeriod.dataFim);
  const [data, setData] = useState<FaturamentoData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const buscar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const qp = new URLSearchParams({
        data_inicio: dataInicio,
        data_fim: dataFim,
        agrupar: agrupamento,
      });
      const res = await clinicaBelezaFetch(`/relatorios/faturamento/?${qp.toString()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError("Erro ao carregar dados. Tente novamente.");
        setData(null);
      }
    } catch {
      setError("Erro ao carregar dados. Tente novamente.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dataInicio, dataFim, agrupamento]);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarCSV = useCallback(() => {
    if (!data) return;
    downloadFaturamentoCsv(data, agrupamento, dataInicio, dataFim);
  }, [data, agrupamento, dataInicio, dataFim]);

  return {
    slug,
    agrupamento,
    setAgrupamento,
    dataInicio,
    setDataInicio,
    dataFim,
    setDataFim,
    data,
    loading,
    error,
    buscar,
    exportarCSV,
  };
}
