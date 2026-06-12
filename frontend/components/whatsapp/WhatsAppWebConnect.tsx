'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertTriangle, Loader2, Smartphone, Unplug } from 'lucide-react';

export interface WhatsAppConnectionState {
  provider?: string;
  connection_status: 'disconnected' | 'qr_pending' | 'connected' | 'error';
  connected_phone?: string;
  connected_at?: string | null;
  qr_base64?: string | null;
  pairing_code?: string | null;
  error?: string | null;
  evolution_available?: boolean;
}

interface WhatsAppWebConnectProps {
  provider: 'meta' | 'evolution';
  connectionStatus: WhatsAppConnectionState['connection_status'];
  connectedPhone?: string;
  evolutionAvailable?: boolean;
  onProviderChange: (provider: 'meta' | 'evolution') => void;
  fetchConnection: (withQr?: boolean) => Promise<WhatsAppConnectionState>;
  connect: () => Promise<WhatsAppConnectionState>;
  disconnect: () => Promise<WhatsAppConnectionState>;
  onConnectionUpdate: (state: WhatsAppConnectionState) => void;
}

function qrSrc(base64?: string | null) {
  if (!base64) return '';
  if (base64.startsWith('data:image')) return base64;
  return `data:image/png;base64,${base64}`;
}

export function WhatsAppWebConnect({
  provider,
  connectionStatus,
  connectedPhone = '',
  evolutionAvailable = false,
  onProviderChange,
  fetchConnection,
  connect,
  disconnect,
  onConnectionUpdate,
}: WhatsAppWebConnectProps) {
  const [loading, setLoading] = useState(false);
  const [qrBase64, setQrBase64] = useState<string | null>(null);
  const [pairingCode, setPairingCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generatingQr, setGeneratingQr] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollStatus = useCallback(async () => {
    try {
      const data = await fetchConnection(false);
      onConnectionUpdate(data);
      if (data.qr_base64) {
        setQrBase64(data.qr_base64);
        setGeneratingQr(false);
      }
      if (data.pairing_code) {
        setPairingCode(data.pairing_code);
        setGeneratingQr(false);
      }
      if (data.connection_status === 'connected') {
        stopPolling();
        setQrBase64(null);
        setPairingCode(null);
        setError(null);
        setGeneratingQr(false);
      }
    } catch {
      /* ignore transient poll errors */
    }
  }, [fetchConnection, onConnectionUpdate, stopPolling]);

  useEffect(() => {
    if (provider !== 'evolution') {
      stopPolling();
      return;
    }
    if (connectionStatus === 'qr_pending') {
      pollStatus();
      stopPolling();
      pollRef.current = setInterval(pollStatus, 5000);
    } else {
      stopPolling();
    }
    return stopPolling;
  }, [provider, connectionStatus, pollStatus, stopPolling]);

  const handleConnect = async () => {
    setLoading(true);
    setGeneratingQr(true);
    setError(null);
    setQrBase64(null);
    setPairingCode(null);
    try {
      const data = await connect();
      onConnectionUpdate(data);
      if (data.qr_base64) {
        setQrBase64(data.qr_base64);
        setGeneratingQr(false);
      }
      if (data.pairing_code) {
        setPairingCode(data.pairing_code);
        setGeneratingQr(false);
      }
      if (data.error) {
        setError(data.error);
        setGeneratingQr(false);
      }
    } catch (e) {
      const err = e as { response?: { data?: { error?: string } }; message?: string };
      setError(err?.response?.data?.error || err?.message || 'Erro ao iniciar conexão.');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await disconnect();
      onConnectionUpdate(data);
      setQrBase64(null);
    } catch (e) {
      const err = e as { response?: { data?: { error?: string } }; message?: string };
      setError(err?.response?.data?.error || err?.message || 'Erro ao desconectar.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/40 px-4 py-3 space-y-3">
        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Tipo de integração</p>
        <div className="flex flex-col sm:flex-row gap-3">
          <label className="flex items-start gap-2 cursor-pointer flex-1 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2">
            <input
              type="radio"
              name="whatsapp_provider"
              checked={provider === 'meta'}
              onChange={() => onProviderChange('meta')}
              className="mt-1"
            />
            <span>
              <span className="block text-sm font-medium text-gray-800 dark:text-gray-200">Meta Cloud API</span>
              <span className="block text-xs text-gray-500 dark:text-gray-400">Oficial — Phone ID + token</span>
            </span>
          </label>
          <label
            className={`flex items-start gap-2 flex-1 rounded-lg border px-3 py-2 ${
              evolutionAvailable
                ? 'cursor-pointer border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800'
                : 'opacity-60 cursor-not-allowed border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900'
            }`}
          >
            <input
              type="radio"
              name="whatsapp_provider"
              checked={provider === 'evolution'}
              disabled={!evolutionAvailable}
              onChange={() => evolutionAvailable && onProviderChange('evolution')}
              className="mt-1"
            />
            <span>
              <span className="block text-sm font-medium text-gray-800 dark:text-gray-200">WhatsApp Web (QR)</span>
              <span className="block text-xs text-gray-500 dark:text-gray-400">
                Não oficial — risco de banimento pela Meta
              </span>
            </span>
          </label>
        </div>
        {!evolutionAvailable && (
          <p className="text-xs text-amber-700 dark:text-amber-300">
            WhatsApp Web indisponível no servidor LWK. Use a Meta Cloud API abaixo ou peça ao suporte LWK para
            habilitar a Evolution API.
          </p>
        )}
      </div>

      {provider === 'evolution' && (
        <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-900/20 px-4 py-4 space-y-4">
          <div className="flex items-start gap-2 text-amber-900 dark:text-amber-100">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            <p className="text-xs">
              Conexão via WhatsApp Web (Baileys). A Meta pode banir números que usam clientes não oficiais.
              Use um número dedicado da clínica e aceite o risco. A sessão pode cair e exigir novo QR.
            </p>
          </div>

          {connectionStatus === 'connected' ? (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-300">
                <Smartphone size={18} />
                Conectado{connectedPhone ? `: ${connectedPhone}` : ''}
              </div>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={loading}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-red-300 text-red-700 dark:border-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Unplug size={14} />}
                Desconectar
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {connectionStatus === 'qr_pending' && (qrBase64 || pairingCode) ? (
                <div className="flex flex-col items-center gap-2">
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    Abra o WhatsApp no celular → Dispositivos conectados → Conectar dispositivo
                  </p>
                  {qrBase64 ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={qrSrc(qrBase64)}
                      alt="QR Code WhatsApp"
                      className="w-56 h-56 rounded-lg border border-gray-200 dark:border-gray-600 bg-white p-2"
                    />
                  ) : (
                    <div className="rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-6 py-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">Código de pareamento</p>
                      <p className="text-2xl font-mono tracking-widest text-gray-900 dark:text-gray-100">
                        {pairingCode}
                      </p>
                    </div>
                  )}
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <Loader2 size={12} className="animate-spin" />
                    Aguardando leitura do QR…
                  </p>
                </div>
              ) : connectionStatus === 'qr_pending' && (loading || generatingQr) ? (
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                  <Loader2 size={16} className="animate-spin" />
                  Gerando QR Code… aguarde alguns segundos.
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleConnect}
                  disabled={loading || !evolutionAvailable}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <Smartphone size={16} />}
                  Gerar QR Code
                </button>
              )}
            </div>
          )}

          {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
        </div>
      )}
    </div>
  );
}
