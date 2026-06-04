'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  confirmMfa,
  disableMfa,
  fetchMfaStatus,
  setupMfa,
  type MfaSetupResponse,
} from '@/lib/mfa-api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, Copy, Shield, ShieldCheck, ShieldOff } from 'lucide-react';

type Theme = 'purple' | 'blue';

const THEME = {
  purple: {
    nav: 'bg-purple-900 dark:bg-purple-950',
    accent: 'bg-purple-600 hover:bg-purple-700',
    badge: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200',
  },
  blue: {
    nav: 'bg-blue-900 dark:bg-blue-950',
    accent: 'bg-blue-600 hover:bg-blue-700',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
  },
} as const;

export interface MfaSecurityPanelProps {
  theme: Theme;
  title: string;
  subtitle: string;
  backHref: string;
  backLabel?: string;
}

export default function MfaSecurityPanel({
  theme,
  title,
  subtitle,
  backHref,
  backLabel = 'Voltar',
}: MfaSecurityPanelProps) {
  const t = THEME[theme];
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaAvailable, setMfaAvailable] = useState(true);
  const [setupData, setSetupData] = useState<MfaSetupResponse | null>(null);
  const [confirmCode, setConfirmCode] = useState('');
  const [disableCode, setDisableCode] = useState('');

  const loadStatus = useCallback(async () => {
    try {
      setLoading(true);
      const status = await fetchMfaStatus();
      setMfaAvailable(status.mfa_available);
      setMfaEnabled(status.mfa_enabled);
      if (status.mfa_enabled) {
        setSetupData(null);
        setConfirmCode('');
      }
    } catch {
      setMessage({ type: 'error', text: 'Não foi possível carregar o status do MFA.' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleStartSetup = async () => {
    setMessage(null);
    setBusy(true);
    try {
      const data = await setupMfa();
      setSetupData(data);
      setConfirmCode('');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMessage({
        type: 'error',
        text: e.response?.data?.detail || 'Erro ao iniciar configuração do MFA.',
      });
    } finally {
      setBusy(false);
    }
  };

  const handleConfirm = async () => {
    if (confirmCode.length !== 6) {
      setMessage({ type: 'error', text: 'Informe o código de 6 dígitos do aplicativo.' });
      return;
    }
    setMessage(null);
    setBusy(true);
    try {
      await confirmMfa(confirmCode);
      setMessage({ type: 'success', text: 'Autenticação em duas etapas ativada com sucesso.' });
      setSetupData(null);
      await loadStatus();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMessage({
        type: 'error',
        text: e.response?.data?.detail || 'Código inválido. Tente novamente.',
      });
    } finally {
      setBusy(false);
    }
  };

  const handleDisable = async () => {
    if (disableCode.length !== 6) {
      setMessage({ type: 'error', text: 'Informe o código atual para desativar.' });
      return;
    }
    if (!confirm('Desativar a autenticação em duas etapas? Sua conta ficará menos protegida.')) {
      return;
    }
    setMessage(null);
    setBusy(true);
    try {
      await disableMfa(disableCode);
      setMessage({ type: 'success', text: 'MFA desativado.' });
      setDisableCode('');
      await loadStatus();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMessage({
        type: 'error',
        text: e.response?.data?.detail || 'Código inválido.',
      });
    } finally {
      setBusy(false);
    }
  };

  const copySecret = () => {
    if (!setupData?.secret) return;
    navigator.clipboard.writeText(setupData.secret).then(() => {
      setMessage({ type: 'success', text: 'Chave copiada para a área de transferência.' });
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className={`${t.nav} text-white shadow-lg`}>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">{title}</h1>
              <p className="text-sm opacity-80">{subtitle}</p>
            </div>
            <Link
              href={backHref}
              className="inline-flex items-center gap-2 text-sm text-white/90 hover:text-white"
            >
              <ArrowLeft className="h-4 w-4" />
              {backLabel}
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {message && (
          <Alert
            className={`mb-6 ${message.type === 'error' ? 'border-red-300 bg-red-50 dark:bg-red-950/30' : 'border-green-300 bg-green-50 dark:bg-green-950/30'}`}
          >
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Autenticação em duas etapas (2FA)
            </CardTitle>
            <CardDescription>
              Use Google Authenticator, Microsoft Authenticator ou outro app compatível com TOTP.
              No próximo login será solicitado um código de 6 dígitos além da senha.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {loading ? (
              <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
            ) : !mfaAvailable ? (
              <p className="text-gray-600 dark:text-gray-300">
                MFA não está disponível para seu perfil de usuário.
              </p>
            ) : mfaEnabled ? (
              <div className="space-y-4">
                <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${t.badge}`}>
                  <ShieldCheck className="h-4 w-4" />
                  MFA ativo
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Sua conta exige código do autenticador em cada login.
                </p>
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-3">
                  <Label htmlFor="disable_otp">Desativar MFA</Label>
                  <p className="text-xs text-gray-500">
                    Informe um código válido do aplicativo para confirmar a desativação.
                  </p>
                  <Input
                    id="disable_otp"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="000000"
                    value={disableCode}
                    onChange={(e) =>
                      setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                    }
                    className="max-w-xs font-mono text-lg tracking-widest"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    className="text-red-600 border-red-300 hover:bg-red-50"
                    disabled={busy}
                    onClick={handleDisable}
                  >
                    <ShieldOff className="h-4 w-4 mr-2" />
                    Desativar MFA
                  </Button>
                </div>
              </div>
            ) : setupData ? (
              <div className="space-y-4">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  1. Escaneie o QR code no aplicativo autenticador
                </p>
                {setupData.qr_code_base64 ? (
                  <div className="inline-block rounded-lg border border-gray-200 dark:border-gray-700 bg-white p-4">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={`data:image/png;base64,${setupData.qr_code_base64}`}
                      alt="QR code MFA"
                      width={200}
                      height={200}
                    />
                  </div>
                ) : (
                  <p className="text-sm text-amber-700 dark:text-amber-300">
                    QR indisponível — use a chave manual abaixo.
                  </p>
                )}
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Ou adicione manualmente esta chave:
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    <code className="rounded bg-gray-100 dark:bg-gray-800 px-2 py-1 text-sm break-all">
                      {setupData.secret}
                    </code>
                    <Button type="button" variant="outline" size="sm" onClick={copySecret}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 pt-2">
                  2. Digite o código de 6 dígitos gerado pelo app
                </p>
                <Input
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  value={confirmCode}
                  onChange={(e) =>
                    setConfirmCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                  }
                  className="max-w-xs font-mono text-lg tracking-widest"
                />
                <div className="flex flex-wrap gap-2">
                  <Button type="button" className={t.accent} disabled={busy} onClick={handleConfirm}>
                    Confirmar e ativar
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={busy}
                    onClick={() => {
                      setSetupData(null);
                      setConfirmCode('');
                    }}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full bg-gray-100 dark:bg-gray-800 px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
                  <ShieldOff className="h-4 w-4" />
                  MFA desativado
                </div>
                <Button type="button" className={t.accent} disabled={busy} onClick={handleStartSetup}>
                  Configurar autenticador
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
