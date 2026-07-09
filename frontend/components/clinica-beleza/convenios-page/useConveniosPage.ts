import { useCallback, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { isConvenioParticularNome } from "@/lib/convenio-precos";
import { useToast } from "@/components/ui/Toast";
import {
  buildConveniosBasePath,
  extractConvenioSaveError,
  isNovaConvenioQuery,
} from "./convenios-page-utils";

export function useConveniosPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const slug = params.slug as string;
  const basePath = buildConveniosBasePath(slug);

  const {
    list: convenios,
    loading,
    load: carregarLista,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
  } = useClinicaBelezaPaginatedList<ConvenioItem>({ path: "/convenios/" });

  const [novoNome, setNovoNome] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const isNovo = isNovaConvenioQuery(searchParams);

  const voltarLista = useCallback(() => {
    setErro("");
    router.replace(basePath, { scroll: false });
  }, [basePath, router]);

  const abrirNovo = useCallback(() => {
    router.replace(`${basePath}?novo=1`, { scroll: false });
  }, [basePath, router]);

  const criarConvenio = useCallback(async () => {
    if (!novoNome.trim()) {
      setErro("Informe o nome do convênio.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.convenios.create({ nome: novoNome.trim() });
      await carregarLista();
      voltarLista();
    } catch (e: unknown) {
      setErro(extractConvenioSaveError(e));
    } finally {
      setSalvando(false);
    }
  }, [carregarLista, novoNome, voltarLista]);

  const excluirConvenio = useCallback(
    async (c: ConvenioItem) => {
      if (isConvenioParticularNome(c.nome)) {
        toast.warning("O convênio Particular é padrão do sistema e não pode ser excluído.");
        return;
      }
      if (!confirm(`Excluir o convênio "${c.nome}"? Os preços vinculados nos procedimentos serão removidos.`)) {
        return;
      }
      setSalvando(true);
      setErro("");
      try {
        await ClinicaBelezaAPI.convenios.delete(c.id);
        await carregarLista();
      } catch (e: unknown) {
        toast.error(e instanceof Error ? e.message : "Erro ao excluir convênio.");
      } finally {
        setSalvando(false);
      }
    },
    [carregarLista, toast],
  );

  return {
    basePath,
    isNovo,
    convenios,
    loading,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
    novoNome,
    setNovoNome,
    salvando,
    erro,
    voltarLista,
    abrirNovo,
    criarConvenio,
    excluirConvenio,
  };
}
