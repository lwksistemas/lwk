import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { Consulta } from "../consultas/consultas-types";
import {
  buildConsultaDetailHref,
  buildConsultasBasePath,
  extractConsultaDeepLinkError,
  findConsultaInList,
  isNovaConsultaQuery,
} from "./consultas-page-utils";

export function useConsultasDeepLink(slug: string, consultas: Consulta[]) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const basePath = buildConsultasBasePath(slug);

  const [selected, setSelected] = useState<Consulta | null>(null);
  const [detailPreloaded, setDetailPreloaded] = useState(false);
  const [deepLinkError, setDeepLinkError] = useState<string | null>(null);

  const abrirConsulta = useCallback(
    (consulta: Consulta, preloaded = false) => {
      setDetailPreloaded(preloaded);
      setSelected(consulta);
      router.replace(buildConsultaDetailHref(slug, consulta.id), { scroll: false });
    },
    [router, slug],
  );

  const voltarLista = useCallback(() => {
    setSelected(null);
    setDetailPreloaded(false);
    router.replace(basePath, { scroll: false });
  }, [basePath, router]);

  const limparDeepLinkError = useCallback(() => {
    setDeepLinkError(null);
    router.replace(basePath, { scroll: false });
  }, [basePath, router]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (!idParam) {
      if (selected) setSelected(null);
      setDeepLinkError(null);
      return;
    }
    const found = findConsultaInList(consultas, idParam);
    if (found) {
      setDeepLinkError(null);
      if (found.id !== selected?.id) {
        setDetailPreloaded(false);
        setSelected(found);
      }
      return;
    }
    let cancelled = false;
    ClinicaBelezaAPI.consultas
      .get(Number(idParam))
      .then((c) => {
        if (!cancelled) {
          setDeepLinkError(null);
          setDetailPreloaded(true);
          setSelected(c as Consulta);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setSelected(null);
          setDeepLinkError(extractConsultaDeepLinkError(e));
        }
      });
    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, consultas, selected?.id]);

  return {
    selected,
    detailPreloaded,
    deepLinkError,
    abrirConsulta,
    voltarLista,
    limparDeepLinkError,
  };
}

export function useConsultasNovaConsulta(slug: string) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const basePath = buildConsultasBasePath(slug);

  const [showNovaConsultaModal, setShowNovaConsultaModal] = useState(false);
  const [novaConsultaDate, setNovaConsultaDate] = useState<Date | null>(null);

  const abrirNovaConsulta = useCallback(() => {
    setNovaConsultaDate(new Date());
    setShowNovaConsultaModal(true);
    router.replace(`${basePath}?novo=1`, { scroll: false });
  }, [basePath, router]);

  const fecharNovaConsulta = useCallback(() => {
    setShowNovaConsultaModal(false);
    if (isNovaConsultaQuery(searchParams)) {
      router.replace(basePath, { scroll: false });
    }
  }, [basePath, router, searchParams]);

  useEffect(() => {
    if (isNovaConsultaQuery(searchParams)) {
      setNovaConsultaDate(new Date());
      setShowNovaConsultaModal(true);
    }
  }, [searchParams]);

  return {
    showNovaConsultaModal,
    novaConsultaDate,
    abrirNovaConsulta,
    fecharNovaConsulta,
  };
}

export function useConsultasAgendaModals() {
  const [showConfigAgendaMenu, setShowConfigAgendaMenu] = useState(false);
  const [showLocaisModal, setShowLocaisModal] = useState(false);
  const [showNomesAgendaModal, setShowNomesAgendaModal] = useState(false);
  const [showMensagensWhatsAppModal, setShowMensagensWhatsAppModal] = useState(false);
  const [showNovoConvenioModal, setShowNovoConvenioModal] = useState(false);
  const [showRetornoModal, setShowRetornoModal] = useState(false);

  return {
    showConfigAgendaMenu,
    setShowConfigAgendaMenu,
    showLocaisModal,
    setShowLocaisModal,
    showNomesAgendaModal,
    setShowNomesAgendaModal,
    showMensagensWhatsAppModal,
    setShowMensagensWhatsAppModal,
    showNovoConvenioModal,
    setShowNovoConvenioModal,
    showRetornoModal,
    setShowRetornoModal,
  };
}
