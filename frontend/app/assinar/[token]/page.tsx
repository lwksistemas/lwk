'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, AlertCircle, FileText, User, DollarSign, Download, Eye } from 'lucide-react';

interface DocumentoData {
  tipo_documento: string;
  titulo: string;
  valor_total: string;
  nome_assinante: string;
  tipo_assinante: string;
  tipo_assinante_display: string;
  lead_nome: string;
  lead_empresa: string;
}

export default function AssinaturaPage() {
  const params = useParams();
  const token = params.token as string;
  
  const [loading, setLoading] = useState(true);
  const [documento, setDocumento] = useState<DocumentoData | null>(null);
  const [erro, setErro] = useState('');
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [proximoStatus, setProximoStatus] = useState('');
  const [baixandoPdf, setBaixandoPdf] = useState(false);
  
  useEffect(() => {
    carregarDocumento();
  }, [token]);
  
  const carregarDocumento = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com/api';
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${token}/`);
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
  
  const assinarDocumento = async () => {
    setAssinando(true);
    setErro('');
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com/api';
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${token}/`, {
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
    setBaixandoPdf(true);
    setErro('');
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com/api';
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${token}/pdf/`);
      
      if (!res.ok) {
        setErro('Erro ao carregar PDF. Tente novamente.');
        return;
      }
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      
      // Limpar URL após um tempo
      setTimeout(() => window.URL.revokeObjectURL(url), 100);
    } catch (err) {
      setErro('Erro ao carregar PDF. Verifique sua conexão.');
    } finally {
      setBaixandoPdf(false);
    }
  };

  const baixarPdf = async () => {
    setBaixandoPdf(true);
    setErro('');
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com/api';
      const res = await fetch(`${backendUrl}/crm-vendas/assinar/${token}/pdf/`);
      
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
    } catch (err) {
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
  
  // Success state - fechar automaticamente após 3 segundos
  useEffect(() => {
    if (sucesso) {
      const timer = setTimeout(() => {
        window.close();
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [sucesso]);
  
  if (sucesso) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            Documento Assinado!
          </h2>
          <p className="text-gray-600 text-center mb-4">
            Sua assinatura foi registrada com sucesso.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-800 text-center">
              <strong>Status:</strong> {proximoStatus}
            </p>
          </div>
          <p className="text-sm text-gray-500 text-center mb-2">
            Você receberá uma cópia por email quando o processo for concluído.
          </p>
          <p className="text-xs text-gray-400 text-center italic">
            Esta página será fechada automaticamente em 3 segundos...
          </p>
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
              </div>
            </div>
          </div>
          
          {/* Botões de PDF */}
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm font-semibold text-gray-700 mb-3">Visualizar Documento</p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={visualizarPdf}
                disabled={baixandoPdf}
                className="flex items-center justify-center space-x-2 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {baixandoPdf ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700"></div>
                    <span className="text-sm">Carregando...</span>
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4" />
                    <span className="text-sm font-medium">Visualizar PDF</span>
                  </>
                )}
              </button>
              
              <button
                onClick={baixarPdf}
                disabled={baixandoPdf}
                className="flex items-center justify-center space-x-2 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {baixandoPdf ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700"></div>
                    <span className="text-sm">Baixando...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span className="text-sm font-medium">Baixar PDF</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Confira o documento antes de assinar
            </p>
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
                Ao clicar em "Assinar Documento", você concorda com os termos e condições deste documento.
                Sua assinatura será registrada com data, hora e endereço IP para fins de segurança e validade jurídica.
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
          <button
            onClick={assinarDocumento}
            disabled={assinando}
            className="w-full bg-blue-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            {assinando ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Assinando...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                <span>Assinar Documento</span>
              </>
            )}
          </button>
          
          <p className="text-xs text-gray-500 text-center mt-4">
            Ao assinar, você concorda que esta assinatura tem validade legal equivalente à assinatura manuscrita.
          </p>
        </div>
      </div>
    </div>
  );
}
