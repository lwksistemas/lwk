'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, AlertCircle, FileText, User, DollarSign, Download, Eye } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

interface DocumentoData {
  tipo_documento: string;
  titulo: string;
  valor_total: string;
  nome_assinante: string;
  tipo_assinante: string;
  tipo_assinante_display: string;
  lead_nome: string;
  lead_email?: string;
  lead_empresa: string;
  vendedor_email?: string;
}

export default function AssinaturaPage() {
  const params = useParams();
  // Token do path (Next já decodifica um nível); evitar decodeURIComponent quebrar em '%' solto
  const tokenRaw = params.token as string;
  let token: string;
  try {
    token = decodeURIComponent(tokenRaw);
  } catch {
    token = tokenRaw;
  }
  /** Segmento seguro para colocar na URL da API (evita cortes em ':', '%', etc.) */
  const tokenApiSegment = encodeURIComponent(token);
  
  const [loading, setLoading] = useState(true);
  const [documento, setDocumento] = useState<DocumentoData | null>(null);
  const [erro, setErro] = useState('');
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [proximoStatus, setProximoStatus] = useState('');
  const [baixandoPdf, setBaixandoPdf] = useState(false);
  /** PDF exibido na própria página (obrigatório antes de assinar). */
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfInlineLoading, setPdfInlineLoading] = useState(false);
  const [pdfInlineError, setPdfInlineError] = useState(false);
  /** Usuário abriu o PDF em nova aba ou acionou baixar (sem iframe — evita botão nativo "Abrir" no iOS). */
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
    carregarDocumento();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);
  
  // Success state - tentar fechar automaticamente após 3 segundos
  useEffect(() => {
    if (sucesso) {
      const timer = setTimeout(() => {
        // Tentar fechar a janela (só funciona se foi aberta via JavaScript)
        window.close();
        
        // Se não conseguiu fechar, o usuário verá o botão "Fechar Página"
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [sucesso]);
  
  const carregarDocumento = async () => {
    try {
      const backendUrl = getPrimaryApiBaseUrl();
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${tokenApiSegment}/`);
      const data = await res.json();
      
      if (!res.ok) {
        setErro(data.error || 'Erro ao carregar documento');
        return;
      }
      
      setDocumento(data);
    } catch (err) {
      setErro('Erro ao carregar documento. Verifique sua conexão.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!documento) return;
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
        const backendUrl = getPrimaryApiBaseUrl();
        const res = await fetch(`${backendUrl}/crm-vendas/assinar/${tokenApiSegment}/pdf/`);
        if (!res.ok) {
          if (!cancelled) setPdfInlineError(true);
          return;
        }
        const blob = await res.blob();
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        setPdfBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
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
  }, [documento, tokenApiSegment, pdfReloadKey]);
  
  const assinarDocumento = async () => {
    if (!podeAssinar) return;
    setAssinando(true);
    setErro('');
    
    try {
      const backendUrl = getPrimaryApiBaseUrl();
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${tokenApiSegment}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        setErro(data.error || 'Erro ao assinar documento');
        return;
      }
      
      setSucesso(true);
      setProximoStatus(data.proximo_status_display || data.proximo_status);
    } catch (err) {
      setErro('Erro ao assinar documento. Tente novamente.');
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
    setErro('');
    try {
      const backendUrl = getPrimaryApiBaseUrl();
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${tokenApiSegment}/pdf/`);
      if (!res.ok) {
        setErro('Erro ao carregar PDF. Tente novamente.');
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank', 'noopener,noreferrer');
      setPdfInteracaoFeita(true);
      setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
    } catch {
      setErro('Erro ao carregar PDF. Verifique sua conexão.');
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
        a.download = `${documento?.tipo_documento}_${documento?.titulo || 'documento'}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setPdfInteracaoFeita(true);
        return;
      }
      const backendUrl = getPrimaryApiBaseUrl();
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${tokenApiSegment}/pdf/`);
      if (!res.ok) {
        setErro('Erro ao baixar PDF. Tente novamente.');
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${documento?.tipo_documento}_${documento?.titulo || 'documento'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setPdfInteracaoFeita(true);
    } catch {
      setErro('Erro ao baixar PDF. Verifique sua conexão.');
    } finally {
      setBaixandoPdf(false);
    }
  };

  
  
  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando documento...</p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (erro && !documento) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            Erro ao Carregar
          </h2>
          <p className="text-gray-600 text-center">{erro}</p>
        </div>
      </div>
    );
  }
  
  // Success state
  if (sucesso) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            ✅ Documento Assinado!
          </h2>
          <p className="text-gray-600 text-center mb-4">
            Sua assinatura foi registrada com sucesso.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-800 text-center">
              <strong>Status:</strong> {proximoStatus}
            </p>
          </div>
          <p className="text-sm text-gray-500 text-center mb-4">
            Você receberá uma cópia por email quando o processo for concluído.
          </p>
          
          {/* Botão para fechar página */}
          <button
            onClick={() => window.close()}
            className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 mb-3"
          >
            Fechar Página
          </button>
          
          <p className="text-xs text-gray-400 text-center">
            Você pode fechar esta página agora.
          </p>
          <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
            <p className="text-xs text-green-700 text-center">
              Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.
            </p>
          </div>
        </div>
      </div>
    );
  }
  
  // Main form
  const tipoDocumento = documento?.tipo_documento === 'proposta' ? 'Proposta' : 'Contrato';
  const valorFormatado = parseFloat(documento?.valor_total || '0').toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-t-2xl shadow-xl p-8 border-b-4 border-blue-600">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-blue-100 p-3 rounded-full">
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 text-center mb-2">
            Assinatura Digital
          </h1>
          <p className="text-gray-600 text-center">
            {tipoDocumento} para assinatura eletrônica
          </p>
        </div>
        
        {/* Document Info */}
        <div className="bg-white shadow-xl p-8">
          <div className="space-y-4">
            {/* Tipo e Título */}
            <div className="flex items-start space-x-3">
              <FileText className="w-5 h-5 text-gray-400 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Tipo de Documento</p>
                <p className="text-lg font-semibold text-gray-900">{tipoDocumento}</p>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <p className="text-sm text-gray-500 mb-1">Título</p>
              <p className="text-lg font-semibold text-gray-900">{documento?.titulo}</p>
            </div>
            
            {/* Valor */}
            <div className="flex items-start space-x-3 border-t pt-4">
              <DollarSign className="w-5 h-5 text-gray-400 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Valor Total</p>
                <p className="text-2xl font-bold text-green-600">{valorFormatado}</p>
              </div>
            </div>
            
            {/* Cliente */}
            {documento?.lead_nome && (
              <div className="flex items-start space-x-3 border-t pt-4">
                <User className="w-5 h-5 text-gray-400 mt-1" />
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Cliente</p>
                  <p className="text-lg font-semibold text-gray-900">{documento.lead_nome}</p>
                  {documento.lead_email && (
                    <p className="text-sm text-gray-600">{documento.lead_email}</p>
                  )}
                  {documento.lead_empresa && (
                    <p className="text-sm text-gray-600">{documento.lead_empresa}</p>
                  )}
                </div>
              </div>
            )}
            
            {/* Assinante */}
            <div className="flex items-start space-x-3 border-t pt-4">
              <User className="w-5 h-5 text-gray-400 mt-1" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Você está assinando como</p>
                <p className="text-lg font-semibold text-gray-900">{documento?.nome_assinante}</p>
                <span className="inline-block mt-1 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                  {documento?.tipo_assinante_display}
                </span>
                {documento?.vendedor_email && (
                  <p className="mt-2 text-xs text-gray-500">
                    E-mail do vendedor: <span className="font-medium text-gray-700">{documento.vendedor_email}</span>
                  </p>
                )}
              </div>
            </div>
          </div>
          
          {/* PDF obrigatório na página antes de assinar */}
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm font-semibold text-gray-800 mb-1">Documento completo (PDF)</p>
            <p className="text-xs text-gray-500 mb-3">
              Use um dos botões abaixo para abrir o PDF em nova aba ou baixar. Por segurança, a assinatura só é liberada depois dessa etapa e da confirmação de leitura.
            </p>

            {pdfInlineLoading && !pdfBlobUrl && (
              <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-gray-50 py-16 text-gray-600">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-3" />
                <span className="text-sm">Carregando PDF…</span>
              </div>
            )}

            {pdfInlineError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
                <p className="text-sm text-red-800 mb-3">Não foi possível carregar o PDF. Verifique a conexão ou tente outro navegador.</p>
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
                className="flex items-center justify-center space-x-2 rounded-lg bg-gray-100 px-4 py-3 text-gray-700 transition-colors duration-200 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Eye className="h-4 w-4" />
                <span className="text-sm font-medium">Abrir PDF em nova aba</span>
              </button>
              <button
                type="button"
                onClick={() => void baixarPdf()}
                disabled={baixandoPdf || !pdfBlobUrl}
                className="flex items-center justify-center space-x-2 rounded-lg bg-gray-100 px-4 py-3 text-gray-700 transition-colors duration-200 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                <span className="text-sm font-medium">Baixar PDF</span>
              </button>
            </div>

            {pdfBlobUrl && !pdfInlineError && (
              <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-lg border border-blue-200 bg-blue-50/80 p-4 text-sm text-gray-800">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 shrink-0 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={declarouLeituraCompleta}
                  onChange={(e) => setDeclarouLeituraCompleta(e.target.checked)}
                />
                <span>
                  Declaro que li integralmente o conteúdo do PDF (aberto em nova aba ou baixado) e estou ciente das cláusulas antes de assinar digitalmente.
                </span>
              </label>
            )}
          </div>
        </div>
        
        {/* Warning */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 shadow-xl">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                Atenção - Assinatura Digital
              </h3>
              <p className="text-sm text-yellow-700">
                Ao clicar em &quot;Assinar documento&quot;, você concorda com os termos deste documento.
                A assinatura só pode ser feita após abrir ou baixar o PDF e após a confirmação de leitura. O registro inclui data, hora e endereço IP.
              </p>
            </div>
          </div>
        </div>
        
        {/* Error message */}
        {erro && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 shadow-xl">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <p className="text-sm text-red-700">{erro}</p>
            </div>
          </div>
        )}
        
        {/* Action Button */}
        <div className="bg-white rounded-b-2xl shadow-xl p-8">
          {!podeAssinar && !assinando && (
            <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-center text-xs text-amber-900">
              {!pdfPronto
                ? 'Aguarde o carregamento do documento.'
                : !pdfInteracaoFeita
                  ? 'Toque em &quot;Abrir PDF em nova aba&quot; ou em &quot;Baixar PDF&quot; antes de assinar.'
                  : 'Marque a caixa confirmando que leu o PDF para habilitar a assinatura.'}
            </p>
          )}
          <button
            type="button"
            onClick={() => void assinarDocumento()}
            disabled={!podeAssinar || assinando}
            className="flex w-full items-center justify-center space-x-2 rounded-lg bg-blue-600 py-4 px-6 text-lg font-semibold text-white transition-colors duration-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
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
              Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, com registro de data, hora e endereço IP.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
