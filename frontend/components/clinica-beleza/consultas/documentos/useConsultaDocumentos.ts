import { useCallback, useEffect, useState } from "react";
import { ClinicaBelezaAPI, type DocumentoClinicoItem, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { parseListaDocumentos } from "../historico/historico-utils";
import type { DocumentoAcao, DocumentoTipo } from "./documentos-types";

export function useConsultaDocumentos(consultaId: number, refreshPrescricoes = 0) {
  const [openDropdown, setOpenDropdown] = useState<DocumentoTipo | null>(null);
  const [documentos, setDocumentos] = useState<DocumentoClinicoItem[]>([]);
  const [prescricoesMemed, setPrescricoesMemed] = useState<PrescricaoMemedItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [templateModalTipo, setTemplateModalTipo] = useState<DocumentoTipo | null>(null);
  const [manualModalTipo, setManualModalTipo] = useState<DocumentoTipo | null>(null);
  const [savingManualDoc, setSavingManualDoc] = useState(false);

  const fetchDocumentos = useCallback(async () => {
    try {
      setLoadingDocs(true);
      const [data, presc] = await Promise.all([
        ClinicaBelezaAPI.documentos.list(consultaId).catch(() => []),
        ClinicaBelezaAPI.memed.listarPrescricoesConsulta(consultaId).catch(() => []),
      ]);
      setDocumentos(parseListaDocumentos(data));
      setPrescricoesMemed(Array.isArray(presc) ? presc : []);
    } catch (e) {
      logger.warn("Erro ao listar documentos da consulta:", e);
      setDocumentos([]);
      setPrescricoesMemed([]);
    } finally {
      setLoadingDocs(false);
    }
  }, [consultaId]);

  const registrarDocumentoCriado = useCallback(
    async (created: DocumentoClinicoItem) => {
      setDocumentos((prev) => {
        if (prev.some((d) => d.id === created.id)) return prev;
        return [created, ...prev];
      });
      await fetchDocumentos();
    },
    [fetchDocumentos],
  );

  useEffect(() => {
    void fetchDocumentos();
  }, [fetchDocumentos, refreshPrescricoes]);

  const handleDelete = async (docId: number) => {
    setDeletingId(docId);
    try {
      await ClinicaBelezaAPI.documentos.delete(consultaId, docId);
      await fetchDocumentos();
    } catch {
      // documento pode já ter sido excluído
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  };

  const toggleDropdown = (tipo: DocumentoTipo) => {
    setOpenDropdown((prev) => (prev === tipo ? null : tipo));
  };

  const handleAcao = (tipo: DocumentoTipo, acao: DocumentoAcao, onUsarMemed?: () => void) => {
    setOpenDropdown(null);
    switch (acao) {
      case "memed":
        onUsarMemed?.();
        break;
      case "template":
        setTemplateModalTipo(tipo);
        break;
      case "manual":
        setManualModalTipo(tipo);
        break;
    }
  };

  const salvarDocumentoManual = async (data: { tipo: DocumentoTipo; conteudo: string; titulo: string }) => {
    setSavingManualDoc(true);
    try {
      const created = await ClinicaBelezaAPI.documentos.create(consultaId, {
        tipo: data.tipo,
        conteudo: data.conteudo,
        titulo: data.titulo || undefined,
      });
      setManualModalTipo(null);
      await registrarDocumentoCriado(created);
    } catch (e) {
      logger.warn("Erro ao salvar documento manual:", e);
      alert("Erro ao salvar documento. Tente novamente.");
    } finally {
      setSavingManualDoc(false);
    }
  };

  const atualizarPdfUrlPrescricao = (prescricaoId: number, url: string) => {
    setPrescricoesMemed((prev) =>
      prev.map((item) => (item.id === prescricaoId ? { ...item, pdf_url: url } : item)),
    );
  };

  return {
    openDropdown,
    documentos,
    prescricoesMemed,
    loadingDocs,
    deletingId,
    confirmDeleteId,
    setConfirmDeleteId,
    templateModalTipo,
    setTemplateModalTipo,
    manualModalTipo,
    setManualModalTipo,
    savingManualDoc,
    fetchDocumentos,
    registrarDocumentoCriado,
    handleDelete,
    toggleDropdown,
    handleAcao,
    salvarDocumentoManual,
    atualizarPdfUrlPrescricao,
  };
}
