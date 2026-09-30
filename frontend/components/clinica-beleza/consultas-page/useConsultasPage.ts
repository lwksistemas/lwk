import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import {
  MSG_CONSULTA_EM_ANDAMENTO,
  consultaEmAndamentoDeOutro,
} from "../consultas/consulta-acesso";
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

  const [selected, setSelected] = useState<Consulta | null>(null);
  const [detailPreloaded, setDetailPreloaded] = useState(false);
  const [deepLinkError, setDeepLinkError] = useState<string | null>(null);
  const [meuProfessionalId, setMeuProfessionalId] = useState<number | null | undefined>(undefined);

  useEffect(() => {
    let ativo = true;
    ClinicaBelezaAPI.me
      .get()
      .then((me) => {
        if (ativo) setMeuProfessionalId(me.professional_id ?? null);
      })
      .catch(() => {
        if (ativo) setMeuProfessionalId(null);
      });
    return () => {
      ativo = false;
    };
  }, []);

  const abrirConsulta = useCallback(
    (consulta: Consulta, preloaded = false) => {
      const bloqueio = consultaEmAndamentoDeOutro(consulta, meuProfessionalId);
      if (bloqueio !== false) {
        if (bloqueio === true) setDeepLinkError(MSG_CONSULTA_EM_ANDAMENTO);
        return;
      }
      setDeepLinkError(null);
      setDetailPreloaded(preloaded);
      setSelected(consulta);
      router.replace(buildConsultaDetailHref(slug, consulta.id), { scroll: false });
    },
    [meuProfessionalId, router, slug],
  );

  const voltarLista = useCallback(() => {
    setSelected(null);
    setDetailPreloaded(false);
    router.replace(buildConsultasBasePath(slug), { scroll: false });
  }, [router, slug]);

  const limparDeepLinkError = useCallback(() => {
    setDeepLinkError(null);
    router.replace(buildConsultasBasePath(slug), { scroll: false });
  }, [router, slug]);

  useEffect(() => {
    const idParam = searchParams.get("id");
    if (!idParam) {
      if (selected) setSelected(null);
      setDeepLinkError(null);
      return;
    }
    const found = findConsultaInList(consultas, idParam);
    if (found) {
      const bloqueio = consultaEmAndamentoDeOutro(found, meuProfessionalId);
      if (bloqueio === null) return;
      if (bloqueio) {
        setSelected(null);
        setDeepLinkError(MSG_CONSULTA_EM_ANDAMENTO);
        return;
      }
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
  }, [searchParams, consultas, selected?.id, meuProfessionalId]);

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
