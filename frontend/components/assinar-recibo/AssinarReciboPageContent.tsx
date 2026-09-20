"use client";

import type { Dispatch, SetStateAction } from "react";
import { AlertCircle, CheckCircle, Download, Eye, FileText, Receipt, User } from "lucide-react";
import { type ReciboAssinaturaData, useAssinarRecibo } from "./useAssinarRecibo";

function ReciboLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 dark:border-purple-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-slate-300">Carregando recibo...</p>
      </div>
    </div>
  );
}

function ReciboSucesso() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 max-w-md w-full">
        <div className="flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/40 rounded-full mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-2">Recibo Assinado!</h2>
        <p className="text-gray-600 dark:text-slate-300 text-center mb-4">
          Sua assinatura foi registrada com sucesso. Você receberá o recibo assinado por e-mail e WhatsApp.
        </p>
        <button
          onClick={() => window.close()}
          className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 mb-3"
        >
          Fechar Página
        </button>
        <div className="p-3 bg-green-50 dark:bg-green-950/40 rounded-lg border border-green-200 dark:border-green-800">
          <p className="text-xs text-green-700 dark:text-green-300 text-center">
            Este documento possui validade jurídica e contém a assinatura digital do cliente,
            com registro de data, hora e endereço IP.
          </p>
        </div>
      </div>
    </div>
  );
}

function ReciboErro({ erro }: { erro: string }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <AlertCircle size={64} className="mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Link Inválido</h2>
        <p className="text-gray-600 dark:text-slate-300">{erro}</p>
      </div>
    </div>
  );
}

interface ReciboFormProps {
  recibo: ReciboAssinaturaData;
  erro: string;
  assinando: boolean;
  baixandoPdf: boolean;
  pdfBlobUrl: string | null;
  pdfInlineLoading: boolean;
  pdfInlineError: boolean;
  declarouLeituraCompleta: boolean;
  setDeclarouLeituraCompleta: (v: boolean) => void;
  setPdfReloadKey: Dispatch<SetStateAction<number>>;
  pdfPronto: boolean;
  pdfInteracaoFeita: boolean;
  podeAssinar: boolean;
  visualizarPdf: () => Promise<void>;
  baixarPdf: () => Promise<void>;
  assinar: () => Promise<void>;
}

function ReciboForm({
  recibo,
  erro,
  assinando,
  baixandoPdf,
  pdfBlobUrl,
  pdfInlineLoading,
  pdfInlineError,
  declarouLeituraCompleta,
  setDeclarouLeituraCompleta,
  setPdfReloadKey,
  pdfPronto,
  pdfInteracaoFeita,
  podeAssinar,
  visualizarPdf,
  baixarPdf,
  assinar,
}: ReciboFormProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 dark:from-slate-950 dark:to-slate-900 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white dark:bg-slate-800 rounded-t-2xl shadow-xl p-8 border-b-4 border-purple-700 dark:border-purple-500">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-purple-100 dark:bg-purple-900/60 p-3 rounded-full">
              <Receipt className="w-8 h-8 text-purple-700 dark:text-purple-300" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-2">Assinatura do Recibo</h1>
          <p className="text-gray-600 dark:text-slate-400 text-center">Recibo de Pagamento</p>
        </div>

        <div className="bg-white dark:bg-slate-800 shadow-xl p-8">
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <FileText className="w-5 h-5 text-gray-400 dark:text-slate-500 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500 dark:text-slate-400">Referente a</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{recibo.titulo || "Recibo"}</p>
                {recibo.valor && (
                  <p className="text-base font-semibold text-emerald-600 dark:text-emerald-400 mt-1">{recibo.valor}</p>
                )}
              </div>
            </div>

            <div className="flex items-start space-x-3 border-t border-gray-200 dark:border-slate-700 pt-4">
              <Receipt className="w-5 h-5 text-gray-400 dark:text-slate-500 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500 dark:text-slate-400">Clínica</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">{recibo.clinica_nome || "—"}</p>
              </div>
            </div>

            {recibo.profissional_nome && (
              <div className="flex items-start space-x-3 border-t border-gray-200 dark:border-slate-700 pt-4">
                <User className="w-5 h-5 text-gray-400 dark:text-slate-500 mt-1" />
                <div className="flex-1">
                  <p className="text-sm text-gray-500 dark:text-slate-400">Profissional</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">{recibo.profissional_nome}</p>
                </div>
              </div>
            )}

            <div className="flex items-start space-x-3 border-t border-gray-200 dark:border-slate-700 pt-4">
              <User className="w-5 h-5 text-gray-400 dark:text-slate-500 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500 dark:text-slate-400">Cliente</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {recibo.nome_assinante || recibo.paciente_nome || "—"}
                </p>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                  Este link é exclusivo para você assinar o recibo do procedimento realizado.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-slate-700">
            <p className="text-sm font-semibold text-gray-800 dark:text-slate-100 mb-1">Documento completo (PDF)</p>
            <p className="text-xs text-gray-500 dark:text-slate-400 mb-3">
              Abra ou baixe o PDF do recibo antes de assinar. A assinatura só é liberada após confirmar a leitura.
            </p>

            {pdfInlineLoading && !pdfBlobUrl && (
              <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-900 py-16 text-gray-600 dark:text-slate-300">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 dark:border-purple-400 mb-3" />
                <span className="text-sm">Carregando PDF…</span>
              </div>
            )}

            {pdfInlineError && (
              <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/40 p-4 text-center">
                <p className="text-sm text-red-800 dark:text-red-200 mb-3">Não foi possível carregar o PDF.</p>
                <button
                  type="button"
                  onClick={() => setPdfReloadKey((k) => k + 1)}
                  className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                >
                  Tentar novamente
                </button>
              </div>
            )}

            {pdfBlobUrl && !pdfInlineError && (
              <div className="rounded-lg border border-dashed border-gray-300 dark:border-slate-500 bg-gray-50 dark:bg-slate-900 px-4 py-6 text-center">
                <FileText className="mx-auto mb-2 h-10 w-10 text-gray-400 dark:text-slate-400" aria-hidden />
                <p className="text-sm font-medium text-gray-800 dark:text-slate-100">Documento pronto</p>
                <p className="mt-1 text-xs text-gray-600 dark:text-slate-300">
                  Abra em nova aba ou baixe o arquivo para ler com calma antes de assinar.
                </p>
              </div>
            )}

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => void visualizarPdf()}
                disabled={baixandoPdf || !pdfBlobUrl}
                className="flex items-center justify-center space-x-2 rounded-lg bg-gray-100 dark:bg-slate-700 px-4 py-3 text-gray-800 dark:text-white hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <Eye className="h-4 w-4" />
                <span className="text-sm font-medium">Abrir PDF em nova aba</span>
              </button>
              <button
                type="button"
                onClick={() => void baixarPdf()}
                disabled={baixandoPdf || !pdfBlobUrl}
                className="flex items-center justify-center space-x-2 rounded-lg bg-gray-100 dark:bg-slate-700 px-4 py-3 text-gray-800 dark:text-white hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                <span className="text-sm font-medium">Baixar PDF</span>
              </button>
            </div>

            {pdfBlobUrl && !pdfInlineError && (
              <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-lg border border-purple-200 dark:border-purple-700 bg-purple-50/80 dark:bg-purple-950/40 p-4 text-sm text-gray-800 dark:text-slate-100">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 shrink-0 rounded border-gray-300 dark:border-slate-500 text-purple-600 focus:ring-purple-500"
                  checked={declarouLeituraCompleta}
                  onChange={(e) => setDeclarouLeituraCompleta(e.target.checked)}
                />
                <span>
                  Declaro que li integralmente o recibo e confirmo os valores e o procedimento antes de assinar
                  digitalmente.
                </span>
              </label>
            )}
          </div>
        </div>

        <div className="bg-yellow-50 dark:bg-amber-950/40 border-l-4 border-yellow-400 dark:border-amber-500 p-6 shadow-xl">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-amber-400 mt-0.5 mr-3 shrink-0" />
            <p className="text-sm text-yellow-800 dark:text-amber-100">
              A assinatura só pode ser feita após abrir ou baixar o PDF e confirmar a leitura. O registro inclui
              data, hora e endereço IP.
            </p>
          </div>
        </div>

        {erro && (
          <div className="bg-red-50 dark:bg-red-950/40 border-l-4 border-red-400 dark:border-red-500 p-4 shadow-xl">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-3" />
              <p className="text-sm text-red-700 dark:text-red-200">{erro}</p>
            </div>
          </div>
        )}

        <div className="bg-white dark:bg-slate-800 rounded-b-2xl shadow-xl p-8">
          {!podeAssinar && !assinando && (
            <p className="mb-4 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 px-3 py-2 text-center text-xs text-amber-900 dark:text-amber-100">
              {!pdfPronto
                ? "Aguarde o carregamento do documento."
                : !pdfInteracaoFeita
                  ? "Abra ou baixe o PDF antes de assinar."
                  : "Marque a caixa confirmando que leu o recibo para habilitar a assinatura."}
            </p>
          )}
          <button
            type="button"
            onClick={() => void assinar()}
            disabled={!podeAssinar || assinando}
            className="flex w-full items-center justify-center space-x-2 rounded-lg bg-purple-700 py-4 px-6 text-lg font-semibold text-white hover:bg-purple-800 disabled:opacity-50"
          >
            {assinando ? (
              <>
                <div className="h-5 w-5 animate-spin rounded-full border-b-2 border-white" />
                <span>Assinando...</span>
              </>
            ) : (
              <>
                <CheckCircle className="h-5 w-5" />
                <span>Assinar recibo</span>
              </>
            )}
          </button>
          <p className="mt-4 text-center text-xs text-gray-500 dark:text-slate-400">
            Ao assinar, você concorda que esta assinatura tem validade legal equivalente à assinatura manuscrita.
          </p>
          <div className="mt-4 p-3 bg-gray-50 dark:bg-slate-900 rounded-lg border border-gray-200 dark:border-slate-600">
            <p className="text-xs text-gray-600 dark:text-slate-300 text-center">
              Este documento possui validade jurídica e contém a assinatura digital do cliente, com registro de
              data, hora e endereço IP.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AssinarReciboPageContent({ tokenRaw }: { tokenRaw: string }) {
  const state = useAssinarRecibo(tokenRaw);

  if (state.loading) return <ReciboLoading />;
  if (state.sucesso) return <ReciboSucesso />;
  if (state.erro && !state.recibo) return <ReciboErro erro={state.erro} />;
  if (!state.recibo) return null;

  return (
    <ReciboForm
      recibo={state.recibo}
      erro={state.erro}
      assinando={state.assinando}
      baixandoPdf={state.baixandoPdf}
      pdfBlobUrl={state.pdfBlobUrl}
      pdfInlineLoading={state.pdfInlineLoading}
      pdfInlineError={state.pdfInlineError}
      declarouLeituraCompleta={state.declarouLeituraCompleta}
      setDeclarouLeituraCompleta={state.setDeclarouLeituraCompleta}
      setPdfReloadKey={state.setPdfReloadKey}
      pdfPronto={state.pdfPronto}
      pdfInteracaoFeita={state.pdfInteracaoFeita}
      podeAssinar={state.podeAssinar}
      visualizarPdf={state.visualizarPdf}
      baixarPdf={state.baixarPdf}
      assinar={state.assinar}
    />
  );
}
