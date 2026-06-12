'use client';

import { useState, useEffect, type ReactNode } from 'react';
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

/** Mobile: página cheia. Desktop (md+): modal compacto centralizado. */
function ConfirmacaoShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-[100dvh] md:min-h-0 md:fixed md:inset-0 md:z-50 flex items-center justify-center p-4 bg-gradient-to-br from-pink-50 to-purple-50 md:bg-black/50 md:backdrop-blur-sm">
      {children}
    </div>
  );
}

function ConfirmacaoCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`bg-white rounded-2xl md:rounded-xl shadow-lg md:shadow-2xl w-full max-w-md md:max-w-sm p-6 md:p-5 md:max-h-[min(90dvh,480px)] md:overflow-y-auto ${className}`}
    >
      {children}
    </div>
  );
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
      <ConfirmacaoShell>
        <ConfirmacaoCard className="text-center text-gray-600 py-8 md:py-6">
          Carregando...
        </ConfirmacaoCard>
      </ConfirmacaoShell>
    );
  }

  if (erro && !agendamento) {
    return (
      <ConfirmacaoShell>
        <ConfirmacaoCard className="text-center">
          <AlertCircle className="w-10 h-10 md:w-9 md:h-9 text-red-500 mx-auto mb-3" />
          <h1 className="text-xl md:text-lg font-semibold text-gray-800 mb-2">Link indisponível</h1>
          <p className="text-gray-600 text-sm">{erro}</p>
        </ConfirmacaoCard>
      </ConfirmacaoShell>
    );
  }

  if (!agendamento) return null;

  const confirmado =
    agendamento.status === 'CLIENT_CONFIRMED' ||
    agendamento.status === 'PHONE_CONFIRMED' ||
    agendamento.status === 'CONFIRMED';
  const cancelado = agendamento.status === 'CANCELLED';

  return (
    <ConfirmacaoShell>
      <ConfirmacaoCard>
        {agendamento.clinica_nome && (
          <p className="text-sm md:text-xs text-purple-600 font-medium text-center mb-1">
            {agendamento.clinica_nome}
          </p>
        )}
        <h1 className="text-2xl md:text-lg font-bold text-gray-800 text-center mb-5 md:mb-4">
          Confirmação de consulta
        </h1>

        <div className="space-y-2.5 md:space-y-2 mb-5 md:mb-4 text-sm md:text-[13px]">
          <div className="flex items-center gap-2.5 text-gray-700">
            <User className="w-4 h-4 text-purple-500 shrink-0" />
            <span>{agendamento.paciente_nome}</span>
          </div>
          <div className="flex items-center gap-2.5 text-gray-700">
            <Calendar className="w-4 h-4 text-purple-500 shrink-0" />
            <span>{agendamento.data}</span>
          </div>
          <div className="flex items-center gap-2.5 text-gray-700">
            <Clock className="w-4 h-4 text-purple-500 shrink-0" />
            <span>{agendamento.hora}</span>
          </div>
          <div className="flex items-center gap-2.5 text-gray-700">
            <Stethoscope className="w-4 h-4 text-purple-500 shrink-0" />
            <span>{agendamento.procedimento}</span>
          </div>
          {agendamento.profissional_nome && (
            <div className="flex items-center gap-2.5 text-gray-700">
              <User className="w-4 h-4 text-purple-500 shrink-0" />
              <span>Profissional: {agendamento.profissional_nome}</span>
            </div>
          )}
        </div>

        {resultado?.ok && (
          <div className="mb-4 p-3 rounded-xl bg-green-50 border border-green-200 flex items-start gap-2.5 text-sm">
            <CheckCircle className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
            <p className="text-green-800">{resultado.message}</p>
          </div>
        )}

        {erro && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 flex items-start gap-2.5 text-sm">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <p className="text-red-800">{erro}</p>
          </div>
        )}

        {!resultado?.ok && agendamento.pode_responder && (
          <div className="flex flex-col sm:flex-row gap-2.5">
            <button
              type="button"
              disabled={processando}
              onClick={() => responder('confirmar')}
              className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold py-2.5 md:py-2 px-4 rounded-xl text-sm transition"
            >
              <CheckCircle className="w-4 h-4" />
              Confirmar
            </button>
            <button
              type="button"
              disabled={processando}
              onClick={() => responder('cancelar')}
              className="flex-1 flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-60 text-gray-800 font-semibold py-2.5 md:py-2 px-4 rounded-xl text-sm transition border border-gray-300"
            >
              <XCircle className="w-4 h-4" />
              Cancelar
            </button>
          </div>
        )}

        {(confirmado || cancelado) && !agendamento.pode_responder && !resultado && (
          <div
            className={`p-3 rounded-xl text-center text-sm ${
              confirmado ? 'bg-green-50 text-green-800' : 'bg-gray-50 text-gray-700'
            }`}
          >
            Status: <strong>{agendamento.status_display}</strong>
          </div>
        )}
      </ConfirmacaoCard>
    </ConfirmacaoShell>
  );
}
