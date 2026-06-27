"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista em tela cheia; detalhe da consulta selecionada em shell dedicado.
 */

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { CalendarCog } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ModalCriarAgendamento } from "@/components/clinica-beleza/ModalCriarAgendamento";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { useAgendamentoCadastros } from "@/hooks/clinica-beleza/useAgendamentoCadastros";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { ConsultasListTable } from "@/components/clinica-beleza/consultas/ConsultasListTable";

const ConsultaDetailShell = dynamic(
  () => import("@/components/clinica-beleza/consultas/ConsultaDetailShell").then((m) => ({ default: m.ConsultaDetailShell })),
  {
    ssr: false,
    loading: () => <div className="text-center py-16 text-gray-500">Carregando consulta...</div>,
  },
);

const LocaisAtendimentoModal = dynamic(
  () => import("@/components/clinica-beleza/consultas/LocaisAtendimentoModal").then((m) => ({ default: m.LocaisAtendimentoModal })),
);

const NomesAgendaModal = dynamic(
  () => import("@/components/clinica-beleza/consultas/NomesAgendaModal").then((m) => ({ default: m.NomesAgendaModal })),
);

const MensagensWhatsAppAgendaModal = dynamic(
  () =>
    import("@/components/clinica-beleza/consultas/MensagensWhatsAppAgendaModal").then((m) => ({
      default: m.MensagensWhatsAppAgendaModal,
    })),
);

const ConfiguracaoAgendaMenuModal = dynamic(
  () => import("@/components/clinica-beleza/consultas/ConfiguracaoAgendaMenuModal").then((m) => ({ default: m.ConfiguracaoAgendaMenuModal })),
);

const NovoConvenioModal = dynamic(
  () => import("@/components/clinica-beleza/consultas/NovoConvenioModal").then((m) => ({ default: m.NovoConvenioModal })),
);

const RetornoAgendaModal = dynamic(
  () => import("@/components/clinica-beleza/consultas/RetornoAgendaModal").then((m) => ({ default: m.RetornoAgendaModal })),
);

export default function ConsultasPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/consultas`;

  const {
    list: consultas,
    loading,
    load: loadConsultas,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
  } = useClinicaBelezaPaginatedList<Consulta>({ path: "/consultas/" });
  const [selected, setSelected] = useState<Consulta | null>(null);
  const [detailPreloaded, setDetailPreloaded] = useState(false);
  const [showConfigAgendaMenu, setShowConfigAgendaMenu] = useState(false);
  const [showLocaisModal, setShowLocaisModal] = useState(false);
  const [showNomesAgendaModal, setShowNomesAgendaModal] = useState(false);
  const [showMensagensWhatsAppModal, setShowMensagensWhatsAppModal] = useState(false);
  const [showNovoConvenioModal, setShowNovoConvenioModal] = useState(false);
  const [showRetornoModal, setShowRetornoModal] = useState(false);
  const [showNovaConsultaModal, setShowNovaConsultaModal] = useState(false);
  const [novaConsultaDate, setNovaConsultaDate] = useState<Date | null>(null);

  const {
    patients,
    professionals,
    procedures,
    nomesAgenda,
    locaisAtendimento,
    setPatients,
    searchPatients,
    reload: reloadCadastros,
  } = useAgendamentoCadastros(true);

  const abrirConsulta = useCallback((consulta: Consulta, preloaded = false) => {
    setDetailPreloaded(preloaded);
    setSelected(consulta);
    router.replace(`/loja/${slug}/clinica-beleza/consultas?id=${consulta.id}`, { scroll: false });
  }, [router, slug]);

  const abrirNovaConsulta = useCallback(() => {
    setNovaConsultaDate(new Date());
    setShowNovaConsultaModal(true);
    router.replace(`${basePath}?novo=1`, { scroll: false });
  }, [basePath, router]);

  const fecharNovaConsulta = useCallback(() => {
    setShowNovaConsultaModal(false);
    if (searchParams.get("novo") === "1") {
      router.replace(basePath, { scroll: false });
    }
  }, [basePath, router, searchParams]);

  useEffect(() => {
    if (searchParams.get("novo") === "1") {
      setNovaConsultaDate(new Date());
      setShowNovaConsultaModal(true);
    }
  }, [searchParams]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (!idParam) {
      if (selected) setSelected(null);
      return;
    }
    const found = consultas.find((c) => String(c.id) === idParam);
    if (found) {
      if (found.id !== selected?.id) {
        setDetailPreloaded(false);
        setSelected(found);
      }
      return;
    }
    let cancelled = false;
    ClinicaBelezaAPI.consultas.get(Number(idParam))
      .then((c) => {
        if (!cancelled) {
          setDetailPreloaded(true);
          setSelected(c as Consulta);
        }
      })
      .catch(() => {
        if (!cancelled) setSelected(null);
      });
    return () => {
      cancelled = true;
    };
  }, [searchParams, consultas, selected?.id]);

  const voltarLista = () => {
    setSelected(null);
    setDetailPreloaded(false);
    router.replace(basePath, { scroll: false });
  };

  const formatData = (d?: string | null) =>
    d ? formatClinicaDateTime(new Date(d)) : "—";

  if (selected) {
    return (
      <ConsultaDetailShell
        consulta={selected}
        detailPreloaded={detailPreloaded}
        onBack={voltarLista}
        onSelectConsulta={(c) => abrirConsulta(c, false)}
        onListRefresh={loadConsultas}
      />
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Consultas"
        subtitle="Confirme na Agenda · inicie e finalize aqui"
        onNew={abrirNovaConsulta}
        newLabel="Nova consulta"
        extraActions={
          <button
            type="button"
            onClick={() => setShowConfigAgendaMenu(true)}
            className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
            title="Configuração da Agenda"
          >
            <CalendarCog className="w-4 h-4 shrink-0" style={{ color: CLINICA_BELEZA_PRIMARY }} />
            <span className="hidden sm:inline text-gray-700 dark:text-gray-300">Configuração da Agenda</span>
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
              onSelect={(c) => abrirConsulta(c, false)}
              formatData={formatData}
            />
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount ?? 0}
              pageSize={pageSize}
              loading={loading}
              onPageChange={setPage}
              itemLabel="consultas"
            />
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>

      <ModalCriarAgendamento
        open={showNovaConsultaModal}
        onClose={fecharNovaConsulta}
        mode="consulta"
        selectedDate={novaConsultaDate}
        professionals={professionals}
        patients={patients}
        procedures={procedures}
        nomesAgenda={nomesAgenda}
        locaisAtendimento={locaisAtendimento}
        onPatientsChange={setPatients}
        onSearchPatients={searchPatients}
        onSuccess={() => {
          loadConsultas();
          reloadCadastros();
        }}
        onConsultaCreated={(consultaId) => {
          ClinicaBelezaAPI.consultas.get(consultaId).then((c) => abrirConsulta(c as Consulta, true)).catch(() => {});
        }}
      />

      {showConfigAgendaMenu && (
        <ConfiguracaoAgendaMenuModal
          open={showConfigAgendaMenu}
          onClose={() => setShowConfigAgendaMenu(false)}
          onLocais={() => setShowLocaisModal(true)}
          onNomesAgenda={() => setShowNomesAgendaModal(true)}
          onMensagensWhatsApp={() => setShowMensagensWhatsAppModal(true)}
          onNovoConvenio={() => setShowNovoConvenioModal(true)}
          onRetorno={() => setShowRetornoModal(true)}
        />
      )}
      {showLocaisModal && (
        <LocaisAtendimentoModal
          open={showLocaisModal}
          onClose={() => setShowLocaisModal(false)}
        />
      )}
      {showNomesAgendaModal && (
        <NomesAgendaModal
          open={showNomesAgendaModal}
          onClose={() => setShowNomesAgendaModal(false)}
        />
      )}
      {showMensagensWhatsAppModal && (
        <MensagensWhatsAppAgendaModal
          open={showMensagensWhatsAppModal}
          onClose={() => setShowMensagensWhatsAppModal(false)}
        />
      )}
      {showNovoConvenioModal && (
        <NovoConvenioModal
          open={showNovoConvenioModal}
          onClose={() => setShowNovoConvenioModal(false)}
        />
      )}
      {showRetornoModal && (
        <RetornoAgendaModal
          open={showRetornoModal}
          onClose={() => setShowRetornoModal(false)}
        />
      )}
    </>
  );
}
