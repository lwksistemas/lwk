'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Calendar, Clock, User, CheckCircle, XCircle, AlertCircle, Stethoscope } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

interface AgendamentoData {
  appointment_id: number;
  paciente_nome: string;
  profissional_nome: string;
  procedimento: string;
  data: string;
  hora: string;
  status: string;
  status_display: string;
  clinica_nome: string;
  pode_responder: boolean;
}

export default function ConfirmarAgendamentoPage() {
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
  const [agendamento, setAgendamento] = useState<AgendamentoData | null>(null);
  const [erro, setErro] = useState('');
  const [processando, setProcessando] = useState(false);
  const [resultado, setResultado] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}/clinica-beleza/confirmar-agendamento/${tokenApiSegment}/`);
        const data = await res.json();
        if (!res.ok) {
          setErro(data.error || 'Link inválido ou expirado.');
          return;
        }
        setAgendamento(data);
      } catch {
        setErro('Erro ao carregar. Verifique sua conexão.');
      } finally {
        setLoading(false);
      }
    })();
  }, [tokenApiSegment]);

  const responder = async (acao: 'confirmar' | 'cancelar') => {
    setProcessando(true);
    setErro('');
    try {
      const url = getPrimaryApiBaseUrl();
      const res = await fetch(`${url}/clinica-beleza/confirmar-agendamento/${tokenApiSegment}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acao }),
      });
      const data = await res.json();
      if (!res.ok) {
        setErro(data.error || 'Não foi possível registrar sua resposta.');
        return;
      }
      setResultado({ ok: true, message: data.message });
      setAgendamento((prev) =>
        prev
          ? {
              ...prev,
              status: data.status,
              status_display: data.status_display || prev.status_display,
              pode_responder: false,
            }
          : prev
      );
    } catch {
      setErro('Erro ao enviar. Tente novamente.');
    } finally {
      setProcessando(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50 flex items-center justify-center p-4">
        <div className="text-center text-gray-600">Carregando...</div>
      </div>
    );
  }

  if (erro && !agendamento) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-800 mb-2">Link indisponível</h1>
          <p className="text-gray-600">{erro}</p>
        </div>
      </div>
    );
  }

  if (!agendamento) return null;

  const confirmado =
    agendamento.status === 'CLIENT_CONFIRMED' ||
    agendamento.status === 'PHONE_CONFIRMED' ||
    agendamento.status === 'CONFIRMED';
  const cancelado = agendamento.status === 'CANCELLED';

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8 max-w-md w-full">
        {agendamento.clinica_nome && (
          <p className="text-sm text-purple-600 font-medium text-center mb-1">{agendamento.clinica_nome}</p>
        )}
        <h1 className="text-2xl font-bold text-gray-800 text-center mb-6">Confirmação de consulta</h1>

        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-3 text-gray-700">
            <User className="w-5 h-5 text-purple-500 shrink-0" />
            <span>{agendamento.paciente_nome}</span>
          </div>
          <div className="flex items-center gap-3 text-gray-700">
            <Calendar className="w-5 h-5 text-purple-500 shrink-0" />
            <span>{agendamento.data}</span>
          </div>
          <div className="flex items-center gap-3 text-gray-700">
            <Clock className="w-5 h-5 text-purple-500 shrink-0" />
            <span>{agendamento.hora}</span>
          </div>
          <div className="flex items-center gap-3 text-gray-700">
            <Stethoscope className="w-5 h-5 text-purple-500 shrink-0" />
            <span>{agendamento.procedimento}</span>
          </div>
          {agendamento.profissional_nome && (
            <div className="flex items-center gap-3 text-gray-700">
              <User className="w-5 h-5 text-purple-500 shrink-0" />
              <span>Profissional: {agendamento.profissional_nome}</span>
            </div>
          )}
        </div>

        {resultado?.ok && (
          <div className="mb-6 p-4 rounded-xl bg-green-50 border border-green-200 flex items-start gap-3">
            <CheckCircle className="w-6 h-6 text-green-600 shrink-0 mt-0.5" />
            <p className="text-green-800">{resultado.message}</p>
          </div>
        )}

        {erro && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
            <p className="text-red-800">{erro}</p>
          </div>
        )}

        {!resultado?.ok && agendamento.pode_responder && (
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              type="button"
              disabled={processando}
              onClick={() => responder('confirmar')}
              className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold py-3 px-4 rounded-xl transition"
            >
              <CheckCircle className="w-5 h-5" />
              Confirmar
            </button>
            <button
              type="button"
              disabled={processando}
              onClick={() => responder('cancelar')}
              className="flex-1 flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-60 text-gray-800 font-semibold py-3 px-4 rounded-xl transition border border-gray-300"
            >
              <XCircle className="w-5 h-5" />
              Cancelar
            </button>
          </div>
        )}

        {(confirmado || cancelado) && !agendamento.pode_responder && !resultado && (
          <div className={`p-4 rounded-xl text-center ${confirmado ? 'bg-green-50 text-green-800' : 'bg-gray-50 text-gray-700'}`}>
            Status: <strong>{agendamento.status_display}</strong>
          </div>
        )}
      </div>
    </div>
  );
}
