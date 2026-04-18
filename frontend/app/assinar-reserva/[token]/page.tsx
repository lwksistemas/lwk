'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, AlertCircle, Hotel, User, Calendar, DollarSign, FileText, Download } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

interface ReservaData {
  tipo_documento: string;
  titulo: string;
  valor_total: string;
  nome_assinante: string;
  tipo_assinante: string;
  tipo_assinante_display: string;
  hospede_nome: string;
  quarto: string;
  data_checkin: string;
  data_checkout: string;
  conteudo_confirmacao: string;
}

export default function AssinarReservaPage() {
  const params = useParams();
  const tokenRaw = params.token as string;
  let token: string;
  try { token = decodeURIComponent(tokenRaw); } catch { token = tokenRaw; }
  const tokenApi = encodeURIComponent(token);

  const [loading, setLoading] = useState(true);
  const [reserva, setReserva] = useState<ReservaData | null>(null);
  const [erro, setErro] = useState('');
  const [assinando, setAssinando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [proximoStatus, setProximoStatus] = useState('');
  const [aceitouTermos, setAceitouTermos] = useState(false);
  const [baixandoPdf, setBaixandoPdf] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}/hotel/assinar-reserva/${tokenApi}/`);
        const data = await res.json();
        if (!res.ok) { setErro(data.error || 'Erro ao carregar reserva'); return; }
        setReserva(data);
      } catch { setErro('Erro ao carregar. Verifique sua conexão.'); }
      finally { setLoading(false); }
    })();
  }, [tokenApi]);

  useEffect(() => {
    if (sucesso) { const t = setTimeout(() => window.close(), 5000); return () => clearTimeout(t); }
  }, [sucesso]);

  const assinar = async () => {
    setAssinando(true);
    setErro('');
    try {
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}/hotel/assinar-reserva/${tokenApi}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) { setErro(data.error || 'Erro ao assinar'); return; }
      setSucesso(true);
      setProximoStatus(data.proximo_status_display || data.proximo_status);
    } catch { setErro('Erro ao assinar. Tente novamente.'); }
    finally { setAssinando(false); }
  };

  const baixarPdf = async () => {
    setBaixandoPdf(true);
    try {
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}/hotel/assinar-reserva/${tokenApi}/pdf/`);
      if (!res.ok) { alert('Erro ao baixar PDF.'); return; }
      const blob = await res.blob();
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = 'confirmacao_reserva.pdf';
      link.click();
      window.URL.revokeObjectURL(link.href);
    } catch { alert('Erro ao baixar PDF.'); }
    finally { setBaixandoPdf(false); }
  };

  const formatDate = (d: string) => {
    if (!d) return '—';
    const [y, m, day] = d.split('-');
    return `${day}/${m}/${y}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (sucesso) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <CheckCircle size={64} className="mx-auto text-green-500 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Assinatura Registrada!</h1>
          <p className="text-gray-600 mb-4">
            {proximoStatus === 'Concluído'
              ? 'Ambas as partes assinaram. O PDF será enviado por email.'
              : 'Aguardando assinatura do funcionário do hotel.'}
          </p>
          <button onClick={() => window.close()} className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            Fechar Página
          </button>
        </div>
      </div>
    );
  }

  if (erro && !reserva) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-100 p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <AlertCircle size={64} className="mx-auto text-red-500 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Link Inválido</h1>
          <p className="text-gray-600">{erro}</p>
        </div>
      </div>
    );
  }

  if (!reserva) return null;

  const temTermos = !!reserva.conteudo_confirmacao?.trim();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-lg mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white text-center">
            <Hotel size={40} className="mx-auto mb-2" />
            <h1 className="text-xl font-bold">Confirmação de Reserva</h1>
            <p className="text-indigo-200 text-sm mt-1">Assinatura Digital</p>
          </div>

          <div className="p-6 space-y-4">
            {/* Info do assinante */}
            <div className="bg-indigo-50 rounded-lg p-4">
              <p className="text-sm text-indigo-600 font-medium">
                Assinando como: {reserva.tipo_assinante_display}
              </p>
              <p className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <User size={18} /> {reserva.nome_assinante}
              </p>
            </div>

            {/* Dados da reserva */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-gray-700">
                <Hotel size={16} className="text-gray-400" />
                <span className="text-sm font-medium">Quarto:</span>
                <span className="text-sm">{reserva.quarto}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <Calendar size={16} className="text-gray-400" />
                <span className="text-sm font-medium">Check-in:</span>
                <span className="text-sm">{formatDate(reserva.data_checkin)}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <Calendar size={16} className="text-gray-400" />
                <span className="text-sm font-medium">Check-out:</span>
                <span className="text-sm">{formatDate(reserva.data_checkout)}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <DollarSign size={16} className="text-gray-400" />
                <span className="text-sm font-medium">Valor Total:</span>
                <span className="text-sm font-bold text-green-600">
                  R$ {parseFloat(reserva.valor_total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Botão baixar PDF */}
            <button
              onClick={baixarPdf}
              disabled={baixandoPdf}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition font-medium text-sm border border-red-200 disabled:opacity-50"
            >
              <Download size={16} />
              {baixandoPdf ? 'Baixando...' : 'Baixar PDF da Confirmação'}
            </button>

            {/* Termos e Condições */}
            {temTermos && (
              <div className="border border-amber-200 bg-amber-50 rounded-lg overflow-hidden">
                <div className="px-4 py-2 bg-amber-100 border-b border-amber-200">
                  <h3 className="text-sm font-semibold text-amber-800 flex items-center gap-1">
                    <FileText size={14} /> Regras e Termos do Hotel — Leia antes de assinar
                  </h3>
                </div>
                <div className="p-4 text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto leading-relaxed">
                  {reserva.conteudo_confirmacao}
                </div>
              </div>
            )}

            {/* Checkbox de aceite */}
            {temTermos && (
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={aceitouTermos}
                  onChange={(e) => setAceitouTermos(e.target.checked)}
                  className="mt-0.5 h-5 w-5 text-indigo-600 rounded border-gray-300"
                />
                <span className="text-sm text-gray-700">
                  Li e aceito os termos, regras e condições do hotel descritos acima.
                </span>
              </label>
            )}

            {erro && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
                <AlertCircle size={16} className="text-red-500 shrink-0" />
                <span className="text-sm text-red-700">{erro}</span>
              </div>
            )}

            {/* Botão assinar */}
            <button
              onClick={assinar}
              disabled={assinando || (temTermos && !aceitouTermos)}
              className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {assinando ? 'Assinando...' : '✍️ Assinar Digitalmente'}
            </button>

            {temTermos && !aceitouTermos && (
              <p className="text-xs text-amber-600 text-center">
                Você precisa aceitar os termos acima para assinar.
              </p>
            )}

            <p className="text-xs text-gray-500 text-center">
              Ao assinar, sua assinatura será registrada com data, hora e IP.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
