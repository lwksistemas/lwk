"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ScrollText } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { ClinicaBelezaAPI, type TermoConsentimentoTemplateItem } from "@/lib/clinica-beleza-api";
import { useToast } from "@/components/ui/Toast";
import { TermosConsentimentoListView } from "./TermosConsentimentoListView";
import { buildTermoNovoPath } from "./termos-consentimento-utils";

export function TermosConsentimentoPageContent() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const slug = params.slug as string;
  const [deleteTarget, setDeleteTarget] = useState<TermoConsentimentoTemplateItem | null>(null);
  const [pdfCabecalho, setPdfCabecalho] = useState<"logo" | "timbrado">("logo");

  const { list, loading, load, page, setPage, totalPages, pageSize, totalCount } =
    useClinicaBelezaPaginatedList<TermoConsentimentoTemplateItem>({
      path: "/termos-consentimento/",
    });

  useEffect(() => {
    ClinicaBelezaAPI.termosConsentimento
      .getConfig()
      .then((cfg) => setPdfCabecalho(cfg.pdf_cabecalho === "timbrado" ? "timbrado" : "logo"))
      .catch(() => undefined);
  }, []);

  const salvarCabecalho = useCallback(
    async (value: "logo" | "timbrado") => {
      setPdfCabecalho(value);
      try {
        await ClinicaBelezaAPI.termosConsentimento.saveConfig({ pdf_cabecalho: value });
      } catch {
        toast.error("Não foi possível salvar o cabeçalho do PDF.");
      }
    },
    [toast],
  );

  const confirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      await ClinicaBelezaAPI.termosConsentimento.delete(deleteTarget.id);
      setDeleteTarget(null);
      load();
    } catch {
      toast.error("Erro ao desativar o termo.");
    }
  }, [deleteTarget, load, toast]);

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Termos de Consentimento"
        subtitle="Um termo por procedimento — simples ou TCLE Interativo"
        icon={ScrollText}
        newLabel="Novo termo"
        onNew={() => router.push(buildTermoNovoPath(slug))}
      />
      <ClinicaBelezaPageContent>
        <div className="mb-5 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-4 py-3">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Cabeçalho do PDF</p>
          <div className="flex flex-wrap gap-4 text-sm text-gray-700 dark:text-gray-300">
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="pdf_cabecalho"
                checked={pdfCabecalho === "logo"}
                onChange={() => void salvarCabecalho("logo")}
              />
              Logomarca da clínica
            </label>
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="pdf_cabecalho"
                checked={pdfCabecalho === "timbrado"}
                onChange={() => void salvarCabecalho("timbrado")}
              />
              Papel timbrado
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Vale para termo simples e TCLE Interativo. O papel timbrado é o mesmo da Memed/prontuário.
          </p>
        </div>

        <TermosConsentimentoListView
          termos={list}
          loading={loading}
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalCount={totalCount ?? 0}
          onPageChange={setPage}
          onEdit={(t) => router.push(buildTermoNovoPath(slug, t.id))}
          onDelete={setDeleteTarget}
        />
      </ClinicaBelezaPageContent>

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white dark:bg-neutral-900 rounded-xl p-5 max-w-sm w-full shadow-xl">
            <p className="text-sm text-gray-800 dark:text-gray-200 mb-4">
              Desativar o termo “{deleteTarget.nome}”? Os procedimentos vinculados passam a ficar sem template.
            </p>
            <div className="flex justify-end gap-2">
              <button type="button" className="px-3 py-1.5 text-sm" onClick={() => setDeleteTarget(null)}>
                Cancelar
              </button>
              <button
                type="button"
                className="px-3 py-1.5 text-sm rounded-lg bg-red-600 text-white"
                onClick={() => void confirmDelete()}
              >
                Desativar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
