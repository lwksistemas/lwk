"use client";

import { FileText, RefreshCw, Upload } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { formatTimbradoBytes } from "./memed-page-utils";
import { useMemedPage } from "./useMemedPage";

export function MemedPageContent() {
  const { base, loading, saving, status, arquivo, setArquivo, msg, erro, memedDiag, enviarPdf } =
    useMemedPage();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Receituário Memed — Timbrado"
        subtitle="Papel timbrado A4 para receitas e pedidos de exames"
        showOffline={false}
        backHref={base}
      />
      <ClinicaBelezaPageContent className="max-w-2xl space-y-6">
        {memedDiag && (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 text-sm space-y-1">
            <p className="font-medium text-gray-900 dark:text-white">Status da integração Memed</p>
            <p className="text-gray-600 dark:text-gray-400">
              Ambiente:{" "}
              <strong>{memedDiag.environment === "production" ? "Produção" : "Homologação"}</strong>
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              Credenciais no servidor: {memedDiag.credentials_configured ? "OK" : "Pendente"}
              {memedDiag.environment === "production" && !memedDiag.production_keys_configured && (
                <span className="text-amber-600"> — configure MEMED_*_PROD no Railway</span>
              )}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              Profissionais com CPF (prescrição): {memedDiag.profissionais_com_cpf ?? 0}
            </p>
            {memedDiag.ready_for_production ? (
              <p className="text-green-700 dark:text-green-400">Pronto para prescrição em produção.</p>
            ) : (
              <p className="text-amber-700 dark:text-amber-400">
                Complete credenciais, CPF dos prescritores e timbrado antes de ir a produção.
              </p>
            )}
          </div>
        )}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
              <FileText size={22} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Timbrado A4 (PDF)</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Envie o <strong>modelo</strong> PDF timbrado da clínica (ex.: <strong>Timbrado A4.pdf</strong>, ~900
                KB). Não use a receita já emitida (ex.: <strong>receita.pdf</strong> de poucos KB) — esse arquivo é a
                saída da Memed, não o papel timbrado de entrada.
              </p>
            </div>
          </div>

          {loading ? (
            <p className="text-sm text-gray-500">Carregando…</p>
          ) : status.tem_timbrado ? (
            <div className="rounded-lg bg-gray-50 dark:bg-neutral-900/50 p-3 text-sm text-gray-700 dark:text-gray-300">
              <p>
                <strong>Arquivo atual:</strong> {status.pdf_nome}
              </p>
              <p>
                <strong>Tamanho:</strong> {formatTimbradoBytes(status.tamanho_bytes)}
              </p>
              {status.updated_at && (
                <p>
                  <strong>Atualizado:</strong> {new Date(status.updated_at).toLocaleString("pt-BR")}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-amber-700 dark:text-amber-400">
              Nenhum timbrado configurado ainda. Envie o PDF abaixo.
            </p>
          )}

          {erro && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {erro}
            </div>
          )}
          {msg && (
            <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300 text-sm">
              {msg}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              PDF timbrado (A4)
            </label>
            <label className="flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#8B3D52]/50 transition-colors">
              <Upload size={20} className="text-gray-400 shrink-0" />
              <span className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {arquivo ? arquivo.name : "Clique para selecionar Timbrado A4.pdf"}
              </span>
              <input
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
              />
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Máx. 5 MB. O timbrado é aplicado automaticamente a todos os profissionais com CPF cadastrado na Memed.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 pt-2">
            <button
              type="button"
              disabled={saving || !arquivo}
              onClick={() => void enviarPdf(false)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Upload size={16} />
              {saving ? "Enviando…" : "Salvar e aplicar na Memed"}
            </button>
            {status.tem_timbrado && (
              <button
                type="button"
                disabled={saving}
                onClick={() => void enviarPdf(true)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50"
              >
                <RefreshCw size={16} />
                Reaplicar aos prescritores
              </button>
            )}
          </div>
        </div>

        <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          <p>• Novos profissionais cadastrados com CPF recebem o timbrado automaticamente.</p>
          <p>• A assinatura digital (certificado A1 da Nayara) continua sendo feita na Memed, no computador dela.</p>
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
