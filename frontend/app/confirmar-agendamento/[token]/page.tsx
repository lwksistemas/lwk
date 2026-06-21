'use client';

import { useState, useEffect, useCallback, type ReactNode } from 'react';
import { useParams } from 'next/navigation';
import { Calendar, Clock, User, CheckCircle, XCircle, AlertCircle, Stethoscope, X } from 'lucide-react';
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

const MOBILE_MAX_WIDTH = 639;

function useIsMobileViewport() {
  const [isMobile, setIsMobile] = useState(true);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_MAX_WIDTH}px)`);
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener('change', update);
    return () => mq.removeEventListener('change', update);
  }, []);

  return isMobile;
}

function mensagemPacientePosResposta(status: string): string {
  if (status === "CANCELLED") {
    return "Consulta cancelada. Se precisar remarcar, entre em contato conosco.";
  }
  return "Consulta confirmada! Aguardamos você no horário marcado.";
}

function fecharPagina() {
  window.close();
  setTimeout(() => {
    if (typeof window.history.length === 'number' && window.history.length > 1) {
      window.history.back();
    }
  }, 150);
}

/** Mobile: página cheia. Desktop: só o modal sobre fundo escuro. */
function ConfirmacaoShell({ isMobile, children }: { isMobile: boolean; children: ReactNode }) {
  if (isMobile) {
    return (
      <div className="min-h-[100dvh] flex items-center justify-center p-4 bg-gradient-to-br from-pink-50 to-purple-50">
        {children}
      </div>
    );
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {children}
    </div>
  );
}

function ConfirmacaoCard({
  isMobile,
  children,
  className = '',
  onFechar,
}: {
  isMobile: boolean;
  children: ReactNode;
  className?: string;
  onFechar?: () => void;
}) {
  return (
    <div
      className={`relative bg-white shadow-2xl w-full ${
        isMobile
          ? 'rounded-2xl shadow-lg max-w-md p-6'
          : 'rounded-xl max-w-sm p-5 max-h-[min(90dvh,440px)] overflow-y-auto'
      } ${className}`}
    >
      {onFechar && (
        <button
          type="button"
          onClick={onFechar}
          className="absolute top-3 right-3 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          aria-label="Fechar"
        >
          <X className="w-4 h-4" />
        </button>
      )}
      {children}
    </div>
  );
}

export default function ConfirmarAgendamentoPage() {
  const isMobile = useIsMobileViewport();
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
  const [fechando, setFechando] = useState(false);

  const tentarFechar = useCallback(() => {
    setFechando(true);
    fecharPagina();
  }, []);

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

  useEffect(() => {
    if (!resultado?.ok) return;
    const timer = window.setTimeout(() => tentarFechar(), 2200);
    return () => window.clearTimeout(timer);
  }, [resultado, tentarFechar]);

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

  const mostrarDetalhes = !resultado?.ok;

  if (loading) {
    return (
      <ConfirmacaoShell isMobile={isMobile}>
        <ConfirmacaoCard isMobile={isMobile} className="text-center text-gray-600 py-8 md:py-6">
          Carregando...
        </ConfirmacaoCard>
      </ConfirmacaoShell>
    );
  }

  if (erro && !agendamento) {
    return (
      <ConfirmacaoShell isMobile={isMobile}>
        <ConfirmacaoCard isMobile={isMobile} className="text-center" onFechar={!isMobile ? tentarFechar : undefined}>
          <AlertCircle className="w-10 h-10 md:w-9 md:h-9 text-red-500 mx-auto mb-3" />
          <h1 className="text-xl md:text-lg font-semibold text-gray-800 mb-2">Link indisponível</h1>
          <p className="text-gray-600 text-sm">{erro}</p>
          {!isMobile && (
            <button
              type="button"
              onClick={tentarFechar}
              className="mt-4 w-full py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50"
            >
              Fechar
            </button>
          )}
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
  const jaRespondido = (confirmado || cancelado) && !agendamento.pode_responder;

  return (
    <ConfirmacaoShell isMobile={isMobile}>
      <ConfirmacaoCard
        isMobile={isMobile}
        onFechar={!isMobile && (resultado?.ok || jaRespondido) ? tentarFechar : undefined}
      >
        {mostrarDetalhes && (
          <>
            {agendamento.clinica_nome && (
              <p className="text-sm md:text-xs text-purple-600 font-medium text-center mb-1 pr-6">
                {agendamento.clinica_nome}
              </p>
            )}
            <h1 className="text-2xl md:text-base font-bold text-gray-800 text-center mb-5 md:mb-3 pr-6">
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
          </>
        )}

        {resultado?.ok && (
          <div className="p-3 md:p-4 rounded-xl bg-green-50 border border-green-200 text-center">
            <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-green-800 text-sm font-medium">{resultado.message}</p>
            <p className="text-green-700/80 text-xs mt-2">
              {fechando ? 'Fechando…' : 'Esta janela fechará em instantes.'}
            </p>
            <button
              type="button"
              onClick={tentarFechar}
              className="mt-3 w-full py-2 text-sm font-medium text-green-800 border border-green-300 rounded-xl hover:bg-green-100 transition"
            >
              Fechar agora
            </button>
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
              className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-60 text-white font-semibold py-2.5 md:py-2 px-4 rounded-xl text-sm transition"
            >
              <XCircle className="w-4 h-4" />
              Cancelar
            </button>
          </div>
        )}

        {jaRespondido && !resultado && (
          <div
            className={`p-3 rounded-xl text-center text-sm ${
              cancelado ? "bg-gray-50 text-gray-700" : "bg-green-50 text-green-800"
            }`}
          >
            <p className="mb-2">{mensagemPacientePosResposta(agendamento.status)}</p>
            <button
              type="button"
              onClick={tentarFechar}
              className="w-full py-2 text-sm font-medium border border-gray-300 rounded-xl hover:bg-white/80 transition"
            >
              Fechar
            </button>
          </div>
        )}
      </ConfirmacaoCard>
    </ConfirmacaoShell>
  );
}
