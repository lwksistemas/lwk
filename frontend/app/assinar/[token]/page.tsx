'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, AlertCircle, FileText, User, DollarSign, Download, Eye } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import DocumentoJaAssinado, { type ConfirmacaoAssinatura } from '@/components/assinatura/DocumentoJaAssinado';

interface DocumentoData {
  tipo_documento: string;
  titulo: string;
  valor_total: string;
  valor_adesao?: string;
  valor_mensal?: string;
  valor_trimestral?: string;
  valor_semestral?: string;
  valor_anual?: string;
  tem_desconto?: boolean;
  desconto_tipo?: string;
  desconto_valor?: string;
  desconto_display?: string;
  valor_com_desconto?: string;
  nome_assinante: string;
  tipo_assinante: string;
  tipo_assinante_display: string;
  lead_nome: string;
  lead_email?: string;
  lead_empresa: string;
  vendedor_nome?: string;
  vendedor_email?: string;
  logo_loja?: string;
  logo_prestadora?: string;
  nome_loja?: string;
  nome_prestadora?: string;
  link_anterior?: boolean;
  aviso?: string;
}

function LogoMarca({ src, alt, className }: { src?: string; alt: string; className?: string }) {
  const [visivel, setVisivel] = useState(Boolean(src));
  if (!src || !visivel) return null;
  return (
    <img
      src={src}
      alt={alt}
      className={className || 'mx-auto h-12 w-auto max-w-[200px] object-contain sm:h-16 sm:max-w-[240px]'}
      onError={() => setVisivel(false)}
    />
  );
}

function formatarMoeda(valor: string | number | undefined): string {
  return parseFloat(String(valor || '0')).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

function formatarDesconto(doc: DocumentoData): string {
  if (!doc.tem_desconto) return '';
  if (doc.desconto_tipo === 'percentual') {
    return doc.desconto_display || `${doc.desconto_valor || '0'}%`;
  }
  return formatarMoeda(doc.desconto_valor);
}

function BlocoValores({ documento }: { documento: DocumentoData }) {
  const valorTotal = formatarMoeda(documento.valor_total);
  const valorComDesconto = formatarMoeda(documento.valor_com_desconto || documento.valor_total);
  const adesao = parseFloat(documento.valor_adesao || '0');
  const mensal = parseFloat(documento.valor_mensal || '0');
  const trimestral = parseFloat(documento.valor_trimestral || '0');
  const semestral = parseFloat(documento.valor_semestral || '0');
  const anual = parseFloat(documento.valor_anual || '0');
  const temDesconto = Boolean(documento.tem_desconto);
  const temParcelas = adesao > 0 || mensal > 0 || trimestral > 0 || semestral > 0 || anual > 0;

  const linhaDesconto = temDesconto ? (
    <>
      <div>
        <p className="text-sm text-gray-500">Desconto</p>
        <p className="text-lg font-bold text-red-600">{formatarDesconto(documento)}</p>
      </div>
      <div className="rounded-lg bg-blue-50 px-3 py-2">
        <p className="text-sm text-blue-700">Valor com Desconto</p>
        <p className="text-2xl font-bold text-blue-700">{valorComDesconto}</p>
      </div>
    </>
  ) : null;

  if (temParcelas) {
    return (
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        {adesao > 0 && (
          <div>
            <p className="text-sm text-gray-500">Adesão/Implantação</p>
            <p className="text-lg font-bold text-gray-800">{formatarMoeda(adesao)}</p>
          </div>
        )}
        {mensal > 0 && (
          <div>
            <p className="text-sm text-gray-500">Valor Mensal</p>
            <p className="text-lg font-bold text-blue-600">{formatarMoeda(mensal)}/mês</p>
          </div>
        )}
        {trimestral > 0 && (
          <div>
            <p className="text-sm text-gray-500">Valor Trimestral</p>
            <p className="text-lg font-bold text-indigo-600">{formatarMoeda(trimestral)}/trimestre</p>
          </div>
        )}
        {semestral > 0 && (
          <div>
            <p className="text-sm text-gray-500">Valor Semestral</p>
            <p className="text-lg font-bold text-teal-600">{formatarMoeda(semestral)}/semestre</p>
          </div>
        )}
        {anual > 0 && (
          <div>
            <p className="text-sm text-gray-500">Valor Anual</p>
            <p className="text-lg font-bold text-purple-600">{formatarMoeda(anual)}/ano</p>
          </div>
        )}
        <div className="pt-1 border-t lg:col-span-3 lg:border-t-0 lg:pt-0">
          <p className="text-sm text-gray-500">Valor Total</p>
          <p className={`text-2xl font-bold ${temDesconto ? 'text-gray-700 line-through decoration-red-400' : 'text-green-600'}`}>
            {valorTotal}
          </p>
        </div>
        {linhaDesconto}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div>
        <p className="text-sm text-gray-500">Valor Total</p>
        <p className={`text-2xl font-bold ${temDesconto ? 'text-gray-700 line-through decoration-red-400' : 'text-green-600'}`}>
          {valorTotal}
        </p>
      </div>
      {linhaDesconto}
    </div>
  );
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
  const [errorCode, setErrorCode] = useState('');
  const [jaAssinado, setJaAssinado] = useState<ConfirmacaoAssinatura | null>(null);
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

      if (data.ja_assinado) {
        setJaAssinado(data);
        return;
      }

      if (!res.ok) {
        setErro(data.error || 'Erro ao carregar documento');
        setErrorCode(data.error_code || 'invalido');
        return;
      }
      
      setDocumento(data);
      setErrorCode('');
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
        setErrorCode(data.error_code || 'invalido');
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

  const baixarPdfAssinado = async () => {
    const backendUrl = getPrimaryApiBaseUrl();
    const res = await fetch(`${backendUrl}/crm-vendas/assinar/${tokenApiSegment}/pdf/`);
    if (!res.ok) {
      throw new Error('pdf');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${documento?.tipo_documento || 'proposta'}_assinada.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
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
  
  if (jaAssinado) {
    return (
      <DocumentoJaAssinado
        dados={jaAssinado}
        onBaixarPdf={jaAssinado.pode_baixar_pdf ? baixarPdfAssinado : undefined}
      />
    );
  }

  // Error state
  if (erro && !documento) {
    const linkSubstituido = errorCode === 'link_substituido';
    const documentoIndisponivel = errorCode === 'indisponivel';
    const aviso = linkSubstituido || documentoIndisponivel;
    return (
      <div className={`min-h-screen flex items-center justify-center p-4 ${aviso ? 'bg-gradient-to-br from-amber-50 to-orange-100' : 'bg-gradient-to-br from-red-50 to-pink-100'}`}>
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className={`flex items-center justify-center w-16 h-16 rounded-full mx-auto mb-4 ${aviso ? 'bg-amber-100' : 'bg-red-100'}`}>
            <AlertCircle className={`w-8 h-8 ${aviso ? 'text-amber-600' : 'text-red-600'}`} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            {documentoIndisponivel ? 'Documento indisponível' : linkSubstituido ? 'Link desatualizado' : 'Erro ao Carregar'}
          </h2>
          <p className="text-gray-600 text-center">{erro}</p>
          {linkSubstituido && (
            <p className="mt-4 text-sm text-amber-800 text-center bg-amber-50 border border-amber-200 rounded-lg p-3">
              Verifique seu e-mail ou WhatsApp e abra a mensagem mais recente com o link de assinatura.
            </p>
          )}
        </div>
      </div>
    );
  }
  
  // Success state
  if (sucesso) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 max-w-md w-full">
          <LogoMarca src={documento?.logo_loja} alt={documento?.nome_loja || 'Logo da empresa'} />
          <div className={`flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mx-auto mb-4 ${documento?.logo_loja ? 'mt-4' : ''}`}>
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
          {documento?.logo_prestadora && (
            <div className="mt-6 border-t border-gray-100 pt-5">
              <LogoMarca src={documento.logo_prestadora} alt={documento.nome_prestadora || 'Logo da prestadora'} />
            </div>
          )}
        </div>
      </div>
    );
  }
  
  // Main form
  const tipoDocumento = documento?.tipo_documento === 'proposta' ? 'Proposta' : 'Contrato';
  const assinanteEhCliente = documento?.tipo_assinante === 'cliente';
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-4 px-3 sm:py-8 sm:px-6">
      <div className="mx-auto w-full max-w-lg lg:max-w-6xl">
        <div className="rounded-t-2xl border-b-4 border-blue-600 bg-white px-5 py-5 shadow-xl sm:px-8">
          <div className="flex flex-col items-center gap-3 lg:grid lg:grid-cols-[minmax(180px,1fr)_auto_minmax(180px,1fr)] lg:items-center">
            <div className="lg:justify-self-start">
              {documento?.logo_loja ? (
                <LogoMarca
                  src={documento.logo_loja}
                  alt={documento.nome_loja || 'Logo da empresa'}
                  className="mx-auto h-20 w-auto max-w-[260px] object-contain lg:mx-0 lg:h-24 lg:max-h-none lg:max-w-[320px]"
                />
              ) : (
                <div className="mx-auto w-fit rounded-full bg-blue-100 p-3 lg:mx-0">
                  <FileText className="h-8 w-8 text-blue-600" />
                </div>
              )}
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Assinatura Digital</h1>
              <p className="text-gray-600">{tipoDocumento} para assinatura eletrônica</p>
            </div>
            <div className="hidden lg:flex lg:justify-end">
              {documento?.logo_prestadora && (
                <LogoMarca
                  src={documento.logo_prestadora}
                  alt={documento.nome_prestadora || 'Logo da prestadora'}
                  className="h-auto max-h-20 w-auto max-w-[240px] object-contain"
                />
              )}
            </div>
          </div>
        </div>

        <div className={`bg-white shadow-xl lg:grid lg:grid-cols-[minmax(0,1.15fr)_minmax(300px,0.85fr)] lg:rounded-b-2xl ${documento?.logo_prestadora ? '' : 'rounded-b-2xl'}`}>
          <div className="space-y-4 p-5 sm:p-8 lg:border-r lg:border-gray-100">
            <div className="flex items-start space-x-3">
              <FileText className="mt-1 h-5 w-5 shrink-0 text-gray-400" />
              <p className="min-w-0 break-words text-lg font-semibold text-gray-900">
                {tipoDocumento}: {documento?.titulo}
              </p>
            </div>

            <div className="flex items-start space-x-3 border-t pt-4">
              <DollarSign className="mt-1 h-5 w-5 text-gray-400" />
              <div className="min-w-0 flex-1">
                {documento && <BlocoValores documento={documento} />}
              </div>
            </div>

            <div className="flex items-start space-x-3 border-t pt-4">
              <User className="mt-1 h-5 w-5 shrink-0 text-gray-400" />
              <div className="min-w-0 flex-1 space-y-1 text-sm text-gray-700 sm:text-base">
                <p className="break-words">
                  <span className="text-gray-500">Cliente: </span>
                  <span className="font-semibold text-gray-900">
                    {assinanteEhCliente ? documento?.nome_assinante : documento?.lead_nome}
                  </span>
                </p>
                {(documento?.lead_email) && (
                  <p className="break-words">
                    <span className="text-gray-500">E-mail: </span>
                    {documento.lead_email}
                  </p>
                )}
                {(documento?.vendedor_nome || documento?.vendedor_email) && (
                  <p className="break-words pt-2">
                    <span className="text-gray-500">Vendedor: </span>
                    <span className="font-semibold text-gray-900">{documento?.vendedor_nome}</span>
                  </p>
                )}
                {documento?.vendedor_email && (
                  <p className="break-words">
                    <span className="text-gray-500">E-mail: </span>
                    {documento.vendedor_email}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="border-t border-gray-100 p-5 sm:p-8 lg:border-t-0">
            {pdfInlineLoading && !pdfBlobUrl && (
              <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-gray-50 py-10 text-gray-600 mb-4">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-3" />
                <span className="text-sm">Carregando PDF…</span>
              </div>
            )}

            {pdfInlineError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center mb-4">
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

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-1">
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

            <label className="mt-4 flex cursor-pointer items-start gap-3 border-l-4 border-yellow-400 bg-yellow-50 p-4">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 shrink-0 rounded border-gray-300 text-yellow-600 focus:ring-yellow-500 disabled:cursor-not-allowed"
                checked={declarouLeituraCompleta}
                disabled={!pdfBlobUrl || Boolean(pdfInlineError)}
                onChange={(e) => setDeclarouLeituraCompleta(e.target.checked)}
              />
              <span className="text-sm text-yellow-800">
                Ao clicar em &quot;Assinar documento&quot;, você concorda com os termos deste documento.
                A assinatura só pode ser feita após abrir ou baixar o PDF e após a confirmação de leitura. O registro inclui data, hora e endereço IP.
              </span>
            </label>

            {erro && (
              <div className={`mt-4 border-l-4 p-4 ${errorCode === 'link_substituido' ? 'border-amber-400 bg-amber-50' : 'border-red-400 bg-red-50'}`}>
                <div className="flex items-center">
                  <AlertCircle className={`mr-3 h-5 w-5 ${errorCode === 'link_substituido' ? 'text-amber-600' : 'text-red-600'}`} />
                  <p className={`text-sm ${errorCode === 'link_substituido' ? 'text-amber-900' : 'text-red-700'}`}>{erro}</p>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={() => void assinarDocumento()}
              disabled={!podeAssinar || assinando}
              className="mt-4 flex min-h-12 w-full items-center justify-center space-x-2 rounded-lg bg-blue-600 px-6 py-4 text-lg font-semibold text-white transition-colors duration-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
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
          </div>
        </div>

        {documento?.logo_prestadora && (
          <div className="rounded-b-2xl bg-white px-5 pb-5 shadow-xl lg:hidden">
            <div className="border-t border-gray-100 pt-4">
              <LogoMarca src={documento.logo_prestadora} alt={documento.nome_prestadora || 'Logo da prestadora'} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
