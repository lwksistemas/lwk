"use client";

/**
 * Consultas — Clínica da Beleza
 * Lista em tela cheia; detalhe da consulta selecionada em shell dedicado.
 */

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Settings } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { logger } from "@/lib/logger";
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

  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Consulta | null>(null);
  const [showLocaisModal, setShowLocaisModal] = useState(false);

  const loadConsultas = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.consultas.list();
      setConsultas(Array.isArray(data) ? data : []);
    } catch (e) {
      logger.warn("Erro ao carregar consultas:", e);
      setConsultas([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConsultas();
  }, [loadConsultas]);

  const abrirConsulta = useCallback((consulta: Consulta) => {
    setSelected(consulta);
    router.replace(`/loja/${slug}/clinica-beleza/consultas?id=${consulta.id}`, { scroll: false });
  }, [router, slug]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (!idParam || consultas.length === 0) return;
    const found = consultas.find((c) => String(c.id) === idParam);
    if (found && found.id !== selected?.id) {
      setSelected(found);
    }
    if (!idParam && selected) {
      setSelected(null);
    }
  }, [searchParams, consultas, selected?.id]);

  const voltarLista = () => {
    setSelected(null);
    router.replace(`/loja/${slug}/clinica-beleza/consultas`, { scroll: false });
  };

  const formatData = (d?: string | null) =>
    d ? formatClinicaDateTime(new Date(d)) : "—";

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
        onNew={() => router.push(`/loja/${slug}/clinica-beleza/consultas/nova`)}
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
