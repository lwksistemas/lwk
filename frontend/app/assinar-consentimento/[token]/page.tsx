'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, AlertCircle, FileText, User, Stethoscope, Download, Eye } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

interface TermoData {
  tipo_documento: string;
  titulo: string;
  procedimentos_nomes?: string;
  nome_assinante: string;
  tipo_assinante: string;
  tipo_assinante_display: string;
  paciente_nome: string;
  profissional_nome: string;
  clinica_nome: string;
  conteudo_termo: string;
}

export default function AssinarConsentimentoPage() {
  const params = useParams();
  const tokenRaw = params.token as string;
  let token: string;
  try {
    token = decodeURIComponent(tokenRaw);
  } catch {
    token = tokenRaw;
  }
  const tokenApiSegment = encodeURIComponent(token);

  const [loading, setLoading] = useState(true);
  const [termo, setTermo] = useState<TermoData | null>(null);
  const [erro, setErro] = useState('');
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [proximoStatus, setProximoStatus] = useState('');
  const [baixandoPdf, setBaixandoPdf] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfInlineLoading, setPdfInlineLoading] = useState(false);
  const [pdfInlineError, setPdfInlineError] = useState(false);
  const [pdfInteracaoFeita, setPdfInteracaoFeita] = useState(false);
  const [declarouLeituraCompleta, setDeclarouLeituraCompleta] = useState(false);
  const [pdfReloadKey, setPdfReloadKey] = useState(0);
  const pdfBlobUrlRef = useRef<string | null>(null);

  const pdfPronto = Boolean(pdfBlobUrl) && !pdfInlineLoading && !pdfInlineError;
  const podeAssinar = pdfPronto && pdfInteracaoFeita && declarouLeituraCompleta;

  useEffect(() => {
    pdfBlobUrlRef.current = pdfBlobUrl;
  }, [pdfBlobUrl]);

  useEffect(() => {
    return () => {
      if (pdfBlobUrlRef.current) {
        URL.revokeObjectURL(pdfBlobUrlRef.current);
        pdfBlobUrlRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}/clinica-beleza/assinar-consentimento/${tokenApiSegment}/`);
        const data = await res.json();
        if (!res.ok) {
          setErro(data.error || 'Erro ao carregar termo');
          return;
        }
        setTermo(data);
      } catch {
        setErro('Erro ao carregar. Verifique sua conexão.');
      } finally {
        setLoading(false);
      }
    })();
  }, [tokenApiSegment]);

  useEffect(() => {
    if (!termo) return;
    let cancelled = false;
    (async () => {
      setPdfBlobUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setPdfInlineLoading(true);
      setPdfInlineError(false);
      setPdfInteracaoFeita(false);
      setDeclarouLeituraCompleta(false);
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}/clinica-beleza/assinar-consentimento/${tokenApiSegment}/pdf/`);
        if (!res.ok) {
          if (!cancelled) setPdfInlineError(true);
          return;
        }
        const blob = await res.blob();
        if (cancelled) return;
        const blobUrl = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(blobUrl);
          return;
        }
        setPdfBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return blobUrl;
        });
      } catch {
        if (!cancelled) setPdfInlineError(true);
      } finally {
        if (!cancelled) setPdfInlineLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [termo, tokenApiSegment, pdfReloadKey]);

  useEffect(() => {
    if (sucesso) {
      const t = setTimeout(() => window.close(), 3000);
      return () => clearTimeout(t);
    }
  }, [sucesso]);

  const assinar = async () => {
    if (!podeAssinar) return;
    setAssinando(true);
    setErro('');
    try {
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}/clinica-beleza/assinar-consentimento/${tokenApiSegment}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.error || 'Erro ao assinar');
        return;
      }
      setSucesso(true);
      setProximoStatus(data.proximo_status_display || data.proximo_status);
    } catch {
      setErro('Erro ao assinar. Tente novamente.');
    } finally {
      setAssinando(false);
    }
  };

  const visualizarPdf = async () => {
    if (pdfBlobUrl) {
      window.open(pdfBlobUrl, '_blank', 'noopener,noreferrer');
      setPdfInteracaoFeita(true);
      return;
    }
    setBaixandoPdf(true);
    try {
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}/clinica-beleza/assinar-consentimento/${tokenApiSegment}/pdf/`);
      if (!res.ok) {
        setErro('Erro ao carregar PDF.');
        return;
      }
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      window.open(blobUrl, '_blank', 'noopener,noreferrer');
      setPdfInteracaoFeita(true);
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60_000);
    } catch {
      setErro('Erro ao carregar PDF.');
    } finally {
      setBaixandoPdf(false);
    }
  };

  const baixarPdf = async () => {
    setBaixandoPdf(true);
    setErro('');
    try {
      if (pdfBlobUrl) {
        const a = document.createElement('a');
        a.href = pdfBlobUrl;
        a.download = 'termo_consentimento.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setPdfInteracaoFeita(true);
        return;
      }
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}/clinica-beleza/assinar-consentimento/${tokenApiSegment}/pdf/`);
      if (!res.ok) {
        setErro('Erro ao baixar PDF.');
        return;
      }
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = 'termo_consentimento.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
      setPdfInteracaoFeita(true);
    } catch {
      setErro('Erro ao baixar PDF.');
    } finally {
      setBaixandoPdf(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">Carregando termo...</p>
        </div>
      </div>
    );
  }

  if (sucesso) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">Termo Assinado!</h2>
          <p className="text-gray-600 text-center mb-4">Sua assinatura foi registrada com sucesso.</p>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-purple-800 text-center">
              <strong>Status:</strong> {proximoStatus}
            </p>
          </div>
          <p className="text-sm text-gray-500 text-center mb-4">
            Você receberá uma cópia por e-mail quando o processo for concluído.
          </p>
          <button
            onClick={() => window.close()}
            className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 mb-3"
          >
            Fechar Página
          </button>
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <p className="text-xs text-green-700 text-center">
              Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes,
              com registro de data, hora e endereço IP.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (erro && !termo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <AlertCircle size={64} className="mx-auto text-red-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Link Inválido</h2>
          <p className="text-gray-600">{erro}</p>
        </div>
      </div>
    );
  }

  if (!termo) return null;

  const procedimentos = termo.procedimentos_nomes || termo.titulo;
  const assinandoComoPaciente = termo.tipo_assinante === 'paciente';
  const assinandoComoProfissional = termo.tipo_assinante === 'profissional';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-t-2xl shadow-xl p-8 border-b-4 border-purple-700">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-purple-100 p-3 rounded-full">
              <Stethoscope className="w-8 h-8 text-purple-700" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 text-center mb-2">Assinatura Digital</h1>
          <p className="text-gray-600 text-center">Termo de Consentimento Esclarecido</p>
        </div>

        <div className="bg-white shadow-xl p-8">
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <FileText className="w-5 h-5 text-gray-400 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Procedimento(s)</p>
                <p className="text-lg font-semibold text-gray-900">{procedimentos}</p>
              </div>
            </div>

            <div className="flex items-start space-x-3 border-t pt-4">
              <Stethoscope className="w-5 h-5 text-gray-400 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Clínica</p>
                <p className="text-lg font-semibold text-gray-900">{termo.clinica_nome || '—'}</p>
              </div>
            </div>

            {assinandoComoProfissional && termo.paciente_nome && (
              <div className="flex items-start space-x-3 border-t pt-4">
                <User className="w-5 h-5 text-gray-400 mt-1" />
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Paciente</p>
                  <p className="text-lg font-semibold text-gray-900">{termo.paciente_nome}</p>
                </div>
              </div>
            )}

            {assinandoComoPaciente && termo.profissional_nome && (
              <div className="flex items-start space-x-3 border-t pt-4">
                <User className="w-5 h-5 text-gray-400 mt-1" />
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Profissional responsável</p>
                  <p className="text-lg font-semibold text-gray-900">{termo.profissional_nome}</p>
                </div>
              </div>
            )}

            <div className="flex items-start space-x-3 border-t pt-4">
              <User className="w-5 h-5 text-gray-400 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Você está assinando como</p>
                <p className="text-lg font-semibold text-gray-900">{termo.nome_assinante}</p>
                <span className="inline-block mt-1 px-3 py-1 bg-purple-100 text-purple-800 text-sm font-medium rounded-full">
                  {termo.tipo_assinante_display}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t">
            <p className="text-sm font-semibold text-gray-800 mb-1">Documento completo (PDF)</p>
            <p className="text-xs text-gray-500 mb-3">
              Abra ou baixe o PDF antes de assinar. A assinatura só é liberada após a confirmação de leitura.
            </p>

            {pdfInlineLoading && !pdfBlobUrl && (
              <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-gray-50 py-16 text-gray-600">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mb-3" />
                <span className="text-sm">Carregando PDF…</span>
              </div>
            )}

            {pdfInlineError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
                <p className="text-sm text-red-800 mb-3">Não foi possível carregar o PDF.</p>
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
              <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-center">
                <FileText className="mx-auto mb-2 h-10 w-10 text-gray-400" aria-hidden />
                <p className="text-sm font-medium text-gray-800">Documento pronto</p>
                <p className="mt-1 text-xs text-gray-600">
                  Abra em nova aba ou baixe o arquivo para ler com calma antes de assinar.
                </p>
              </div>
            )}

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => void visualizarPdf()}
                disabled={baixandoPdf || !pdfBlobUrl}
                className="flex items-center justify-center space-x-2 rounded-lg bg-gray-100 px-4 py-3 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
              >
                <Eye className="h-4 w-4" />
                <span className="text-sm font-medium">Abrir PDF em nova aba</span>
              </button>
              <button
                type="button"
                onClick={() => void baixarPdf()}
                disabled={baixandoPdf || !pdfBlobUrl}
                className="flex items-center justify-center space-x-2 rounded-lg bg-gray-100 px-4 py-3 text-gray-700 hover:bg-gray-200 disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                <span className="text-sm font-medium">Baixar PDF</span>
              </button>
            </div>

            {pdfBlobUrl && !pdfInlineError && (
              <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-lg border border-purple-200 bg-purple-50/80 p-4 text-sm text-gray-800">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 shrink-0 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  checked={declarouLeituraCompleta}
                  onChange={(e) => setDeclarouLeituraCompleta(e.target.checked)}
                />
                <span>
                  Declaro que li integralmente o conteúdo do PDF e estou ciente do termo de consentimento
                  antes de assinar digitalmente.
                </span>
              </label>
            )}
          </div>
        </div>

        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 shadow-xl">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 shrink-0" />
            <p className="text-sm text-yellow-700">
              A assinatura só pode ser feita após abrir ou baixar o PDF e confirmar a leitura.
              O registro inclui data, hora e endereço IP.
            </p>
          </div>
        </div>

        {erro && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 shadow-xl">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <p className="text-sm text-red-700">{erro}</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-b-2xl shadow-xl p-8">
          {!podeAssinar && !assinando && (
            <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-center text-xs text-amber-900">
              {!pdfPronto
                ? 'Aguarde o carregamento do documento.'
                : !pdfInteracaoFeita
                  ? 'Abra ou baixe o PDF antes de assinar.'
                  : 'Marque a caixa confirmando que leu o PDF para habilitar a assinatura.'}
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
                <span>Assinar documento</span>
              </>
            )}
          </button>
          <p className="mt-4 text-center text-xs text-gray-500">
            Ao assinar, você concorda que esta assinatura tem validade legal equivalente à assinatura manuscrita.
          </p>
          <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes,
              com registro de data, hora e endereço IP. A logo da clínica aparece como marca d&apos;água nas assinaturas.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
