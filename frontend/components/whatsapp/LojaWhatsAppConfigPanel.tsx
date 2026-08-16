'use client';

import { useCallback, useEffect, useState } from 'react';
import { WhatsAppConfigHelp, WhatsAppConfigStatus } from '@/components/whatsapp/WhatsAppConfigHelp';
import {
  WhatsAppConnectionState,
  WhatsAppWebConnect,
} from '@/components/whatsapp/WhatsAppWebConnect';
import { formatTelefone, telefoneInternacionalBr } from '@/lib/format-br';
import {
  fetchEvolutionAvailableFromHealth,
  whatsappConfigApi,
  type WhatsAppConfigData,
  type WhatsAppFeatureFlags,
} from '@/lib/whatsapp-config-api';

interface LojaWhatsAppConfigPanelProps {
  features: WhatsAppFeatureFlags;
  accentColor?: string;
  /** Sem card externo — conteúdo embutido na página CRM/Clínica. */
  embedded?: boolean;
}

function normalizeAntecedencias(raw: unknown): number[] {
  if (!Array.isArray(raw)) return [1];
  const dias = [
    ...new Set(
      raw
        .map((n) => Number(n))
        .filter((n) => Number.isInteger(n) && n >= 1 && n <= 30),
    ),
  ];
  return dias.sort((a, b) => b - a);
}

export function LojaWhatsAppConfigPanel({
  features,
  accentColor = '#0176d3',
  embedded = false,
}: LojaWhatsAppConfigPanelProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [whatsappNumero, setWhatsappNumero] = useState('');
  const [whatsappAtivo, setWhatsappAtivo] = useState(false);
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('');
  const [whatsappToken, setWhatsappToken] = useState('');
  const [whatsappTokenSet, setWhatsappTokenSet] = useState(false);
  const [whatsappProvider, setWhatsappProvider] = useState<'meta' | 'evolution'>('meta');
  const [connectionStatus, setConnectionStatus] =
    useState<WhatsAppConnectionState['connection_status']>('disconnected');
  const [connectedPhone, setConnectedPhone] = useState('');
  const [evolutionAvailable, setEvolutionAvailable] = useState(false);
  const [enviarConfirmacao, setEnviarConfirmacao] = useState(true);
  const [antecedenciasDias, setAntecedenciasDias] = useState<number[]>([1]);
  const [novoDiaAntecedencia, setNovoDiaAntecedencia] = useState('');
  const [enviarLembrete24h, setEnviarLembrete24h] = useState(true);
  const [enviarLembrete2h, setEnviarLembrete2h] = useState(true);
  const [enviarCobranca, setEnviarCobranca] = useState(true);
  const [enviarLembreteTarefas, setEnviarLembreteTarefas] = useState(true);
  const [enviarPropostaWhatsapp, setEnviarPropostaWhatsapp] = useState(true);
  const [enviarContratoWhatsapp, setEnviarContratoWhatsapp] = useState(true);
  const [enviarTermoConsentimentoWhatsapp, setEnviarTermoConsentimentoWhatsapp] = useState(true);
  const [loadError, setLoadError] = useState('');

  const applyConfig = (data: WhatsAppConfigData) => {
    setWhatsappNumero(formatTelefone((data.whatsapp_numero ?? '').toString()));
    setWhatsappAtivo(!!data.whatsapp_ativo);
    setWhatsappPhoneId((data.whatsapp_phone_id ?? '').toString());
    setWhatsappTokenSet(!!data.whatsapp_token_set);
    setWhatsappProvider(data.whatsapp_provider === 'evolution' ? 'evolution' : 'meta');
    setConnectionStatus(data.connection_status ?? 'disconnected');
    setConnectedPhone((data.connected_phone ?? '').toString());
    // evolutionAvailable é definido em loadConfig (health + API)
    setEnviarConfirmacao(data.enviar_confirmacao ?? true);
    setAntecedenciasDias(normalizeAntecedencias(data.confirmacao_antecedencias_dias));
    setEnviarLembrete24h(data.enviar_lembrete_24h ?? true);
    setEnviarLembrete2h(data.enviar_lembrete_2h ?? true);
    setEnviarCobranca(data.enviar_cobranca ?? true);
    setEnviarLembreteTarefas(data.enviar_lembrete_tarefas ?? true);
    setEnviarPropostaWhatsapp(data.enviar_proposta_whatsapp ?? true);
    setEnviarContratoWhatsapp(data.enviar_contrato_whatsapp ?? true);
    setEnviarTermoConsentimentoWhatsapp(data.enviar_termo_consentimento_whatsapp ?? true);
  };

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const evolutionFromHealth = await fetchEvolutionAvailableFromHealth();
    if (evolutionFromHealth) {
      setEvolutionAvailable(true);
    }
    try {
      const data = await whatsappConfigApi.get();
      applyConfig(data);
      setEvolutionAvailable(!!data.evolution_available || evolutionFromHealth);
      setWhatsappToken('');
    } catch (err) {
      if (evolutionFromHealth) {
        setEvolutionAvailable(true);
      }
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { error?: string; detail?: string } } }).response?.data?.error ||
            (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setLoadError(
        msg ||
          'Não foi possível carregar as configurações salvas. Você ainda pode conectar o WhatsApp Web abaixo e salvar.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        whatsapp_numero: whatsappNumero.trim() ? telefoneInternacionalBr(whatsappNumero) : '',
        whatsapp_ativo: whatsappAtivo,
        whatsapp_provider: whatsappProvider,
        whatsapp_phone_id: whatsappPhoneId.trim() || '',
        enviar_confirmacao: enviarConfirmacao,
        confirmacao_antecedencias_dias: antecedenciasDias,
        enviar_lembrete_24h: enviarLembrete24h,
        enviar_lembrete_2h: enviarLembrete2h,
        enviar_cobranca: enviarCobranca,
        enviar_lembrete_tarefas: enviarLembreteTarefas,
        enviar_proposta_whatsapp: enviarPropostaWhatsapp,
        enviar_contrato_whatsapp: enviarContratoWhatsapp,
        enviar_termo_consentimento_whatsapp: enviarTermoConsentimentoWhatsapp,
        ...(whatsappToken.trim() ? { whatsapp_token: whatsappToken.trim() } : {}),
      };
      const saved = await whatsappConfigApi.save(body);
      applyConfig(saved);
      setWhatsappTokenSet(!!(whatsappToken.trim() || whatsappTokenSet));
      setWhatsappToken('');
      alert('Configurações WhatsApp salvas.');
    } catch (e) {
      const err = e as { response?: { data?: { error?: string } } };
      alert(err?.response?.data?.error || 'Erro ao salvar. Tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  const handleConnectionUpdate = (state: WhatsAppConnectionState) => {
    setConnectionStatus(state.connection_status);
    setConnectedPhone(state.connected_phone ?? '');
    if (state.connected_phone) setWhatsappNumero(formatTelefone(state.connected_phone));
  };

  const helpVariant = features.variant === 'generic' ? 'clinica' : features.variant;
  const statusVariant = features.variant === 'generic' ? 'clinica' : features.variant;

  const addAntecedencia = () => {
    const n = Number.parseInt(novoDiaAntecedencia, 10);
    if (!Number.isInteger(n) || n < 1 || n > 30) {
      alert('Informe um número de 1 a 30 dias.');
      return;
    }
    setAntecedenciasDias(normalizeAntecedencias([...antecedenciasDias, n]));
    setNovoDiaAntecedencia('');
  };

  const autoMessages: Array<{ checked: boolean; set: (v: boolean) => void; label: string }> = [];
  if (features.showAgendaMessages) {
    autoMessages.push(
      { checked: enviarLembrete24h, set: setEnviarLembrete24h, label: 'Lembrete 24h antes da consulta' },
      { checked: enviarLembrete2h, set: setEnviarLembrete2h, label: 'Lembrete 2h antes da consulta' },
      { checked: enviarCobranca, set: setEnviarCobranca, label: 'Enviar cobrança' },
    );
  }
  if (features.showCrmTasks) {
    autoMessages.push({
      checked: enviarLembreteTarefas,
      set: setEnviarLembreteTarefas,
      label: 'Enviar lembrete de tarefas do calendário (CRM)',
    });
  }
  if (features.showCrmDocumentos) {
    autoMessages.push(
      {
        checked: enviarPropostaWhatsapp,
        set: setEnviarPropostaWhatsapp,
        label: 'Permitir envio de proposta ao cliente por WhatsApp (PDF ou assinatura digital)',
      },
      {
        checked: enviarContratoWhatsapp,
        set: setEnviarContratoWhatsapp,
        label: 'Permitir envio de contrato ao cliente por WhatsApp (PDF ou assinatura digital)',
      },
    );
  }
  if (features.showTermoConsentimento) {
    autoMessages.push({
      checked: enviarTermoConsentimentoWhatsapp,
      set: setEnviarTermoConsentimentoWhatsapp,
      label: 'Permitir envio de termo de consentimento por WhatsApp',
    });
  }

  const inner = (
    <>
      {!embedded && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Meta Cloud API (oficial) ou WhatsApp Web via QR Code (Evolution). Cada loja usa sua própria conexão.
        </p>
      )}

      {loading ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
      ) : (
        <div className="space-y-6">
          {loadError && (
            <p className="text-sm text-amber-700 dark:text-amber-300 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-3 py-2">
              {loadError}
            </p>
          )}
          <WhatsAppWebConnect
            provider={whatsappProvider}
            connectionStatus={connectionStatus}
            connectedPhone={connectedPhone}
            evolutionAvailable={evolutionAvailable}
            onProviderChange={setWhatsappProvider}
            fetchConnection={(withQr) => whatsappConfigApi.connection(withQr)}
            connect={() => whatsappConfigApi.connect()}
            disconnect={() => whatsappConfigApi.disconnect()}
            resetSession={() => whatsappConfigApi.resetSession()}
            onConnectionUpdate={handleConnectionUpdate}
            accentColor={accentColor}
          />

          {whatsappProvider === 'meta' && <WhatsAppConfigHelp variant={helpVariant} />}

          {whatsappProvider === 'meta' && (
            <div className="rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/40 px-4 py-3 space-y-3">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                Integração WhatsApp Business (Meta)
              </p>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Phone Number ID (Meta)
                </label>
                <input
                  type="text"
                  value={whatsappPhoneId}
                  onChange={(e) => setWhatsappPhoneId(e.target.value)}
                  placeholder="Ex: 123456789012345"
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Token de acesso (Meta)
                </label>
                <input
                  type="password"
                  value={whatsappToken}
                  onChange={(e) => setWhatsappToken(e.target.value)}
                  placeholder={
                    whatsappTokenSet ? 'Deixe em branco para não alterar' : 'Cole o token permanente da API'
                  }
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  autoComplete="off"
                />
                {whatsappTokenSet && !whatsappToken && (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">Token já configurado</p>
                )}
              </div>
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={whatsappAtivo}
              onChange={(e) => setWhatsappAtivo(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-800 dark:text-gray-200">
              WhatsApp ativo — usar esta integração para enviar mensagens
            </span>
          </label>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Número WhatsApp da loja
            </label>
            <input
              type="text"
              value={whatsappNumero}
              onChange={(e) => setWhatsappNumero(formatTelefone(e.target.value))}
              placeholder="Ex: 5511999999999 (DDD + número)"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
            />
          </div>

          {(features.showAgendaMessages || autoMessages.length > 0) && (
            <div className="rounded-lg border border-gray-200 dark:border-gray-600 px-4 py-3 space-y-3">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Mensagens automáticas</p>
              {features.showAgendaMessages && (
                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enviarConfirmacao}
                      onChange={(e) => setEnviarConfirmacao(e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Enviar link de confirmação
                    </span>
                  </label>
                  {enviarConfirmacao && (
                    <div className="ml-6 space-y-2 rounded-lg bg-gray-50 dark:bg-gray-900/40 px-3 py-2">
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        O link <strong>não é enviado na hora do agendamento</strong>. Escolha quantos
                        dias antes da consulta enviar. Pode repetir (ex.: 3 dias e 1 dia antes).
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {antecedenciasDias.length === 0 && (
                          <span className="text-xs text-amber-700 dark:text-amber-300">
                            Nenhum dia configurado — o link só sai se a equipe reenviar manualmente.
                          </span>
                        )}
                        {antecedenciasDias.map((dias) => (
                          <span
                            key={dias}
                            className="inline-flex items-center gap-1 rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-0.5 text-xs text-gray-800 dark:text-gray-200"
                          >
                            {dias} {dias === 1 ? 'dia' : 'dias'} antes
                            <button
                              type="button"
                              onClick={() =>
                                setAntecedenciasDias(antecedenciasDias.filter((d) => d !== dias))
                              }
                              className="ml-0.5 text-gray-500 hover:text-red-600"
                              aria-label={`Remover ${dias} dias antes`}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min={1}
                          max={30}
                          value={novoDiaAntecedencia}
                          onChange={(e) => setNovoDiaAntecedencia(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              addAntecedencia();
                            }
                          }}
                          placeholder="Ex: 3"
                          className="w-20 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-sm"
                        />
                        <button
                          type="button"
                          onClick={addAntecedencia}
                          className="text-xs font-medium px-2 py-1 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
                        >
                          Adicionar dia
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              {autoMessages.map(({ checked, set, label }) => (
                <label key={label} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => set(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                </label>
              ))}
            </div>
          )}

          <WhatsAppConfigStatus
            whatsappAtivo={whatsappAtivo}
            whatsappPhoneId={whatsappPhoneId}
            whatsappTokenSet={whatsappTokenSet}
            whatsappNumero={whatsappNumero}
            whatsappProvider={whatsappProvider}
            whatsappConnectionStatus={connectionStatus}
            whatsappConnectedPhone={connectedPhone}
            variant={statusVariant}
          />

          <div className="flex justify-end">
            <button
              type="button"
              onClick={saveConfig}
              disabled={saving}
              className="px-4 py-2 text-white rounded-lg disabled:opacity-50"
              style={{ backgroundColor: accentColor }}
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>
      )}
    </>
  );

  if (embedded) return inner;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      {inner}
    </div>
  );
}
