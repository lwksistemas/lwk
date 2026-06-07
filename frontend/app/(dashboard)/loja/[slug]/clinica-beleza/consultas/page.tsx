"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista em tela cheia; detalhe da consulta selecionada em shell dedicado.
 */

import { useCallback, useEffect, useState } from "react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Settings } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza/useClinicaBelezaPaginatedList";
import { NovaConsultaPageContent } from "@/components/clinica-beleza/NovaConsultaPageContent";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import {
  type Consulta,
  ConsultasListTable,
  ConsultaDetailShell,
  LocaisAtendimentoModal,
} from "./components";

export default function ConsultasPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/consultas`;
  const isNovo = searchParams.get("novo") === "1";

  const {
    list: consultas,
    loading,
    load: loadConsultas,
    loadMore,
    loadingMore,
    hasMore,
    totalCount,
  } = useClinicaBelezaPaginatedList<Consulta>({ path: "/consultas/" });
  const [selected, setSelected] = useState<Consulta | null>(null);
  const [showLocaisModal, setShowLocaisModal] = useState(false);

  const abrirConsulta = useCallback((consulta: Consulta) => {
    setSelected(consulta);
    router.replace(`/loja/${slug}/clinica-beleza/consultas?id=${consulta.id}`, { scroll: false });
  }, [router, slug]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (!idParam) {
      if (selected) setSelected(null);
      return;
    }
    const found = consultas.find((c) => String(c.id) === idParam);
    if (found) {
      if (found.id !== selected?.id) setSelected(found);
      return;
    }
    let cancelled = false;
    ClinicaBelezaAPI.consultas.get(Number(idParam))
      .then((c) => {
        if (!cancelled) setSelected(c as Consulta);
      })
      .catch(() => {
        if (!cancelled) setSelected(null);
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams, consultas]);

  const voltarLista = () => {
    setSelected(null);
    router.replace(basePath, { scroll: false });
  };

  const formatData = (d?: string | null) =>
    d ? formatClinicaDateTime(new Date(d)) : "—";

  if (isNovo) {
    return (
      <NovaConsultaPageContent
        slug={slug}
        onDone={() => {
          router.replace(basePath, { scroll: false });
          loadConsultas();
        }}
      />
    );
  }

  if (selected) {
    return (
      <ConsultaDetailShell
        consulta={selected}
        onBack={voltarLista}
        onSelectConsulta={abrirConsulta}
        onListRefresh={loadConsultas}
      />
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Consultas"
        subtitle="Confirme na Agenda · inicie e finalize aqui"
        onNew={() => router.replace(`${basePath}?novo=1`, { scroll: false })}
        newLabel="Nova consulta"
        extraActions={
          <button
            type="button"
            onClick={() => setShowLocaisModal(true)}
            className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Configurar locais de atendimento"
            title="Locais de atendimento"
          >
            <Settings className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 dark:text-gray-300" />
          </button>
        }
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : consultas.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhuma consulta ainda. Confirme um agendamento na Agenda ou clique em <strong>Nova consulta</strong> para
            abrir um atendimento direto pelo cadastro do cliente.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <ConsultasListTable
              consultas={consultas}
              onSelect={abrirConsulta}
              formatData={formatData}
            />
            <EntityListLoadMore
              hasMore={hasMore}
              loading={loading}
              loadingMore={loadingMore}
              onLoadMore={loadMore}
              loadedCount={consultas.length}
              totalCount={totalCount}
            />
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>

      <LocaisAtendimentoModal
        open={showLocaisModal}
        onClose={() => setShowLocaisModal(false)}
      />
    </>
  );
}
