'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { MessageCircle } from 'lucide-react';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { ClinicaBelezaAPI } from '@/lib/clinica-beleza-api';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import { WhatsAppConfigHelp, WhatsAppConfigStatus } from '@/components/whatsapp/WhatsAppConfigHelp';

interface WhatsAppConfigData {
  enviar_confirmacao: boolean;
  enviar_lembrete_24h: boolean;
  enviar_lembrete_2h: boolean;
  enviar_cobranca: boolean;
  whatsapp_numero: string;
  whatsapp_ativo: boolean;
  whatsapp_phone_id: string;
  whatsapp_token_set: boolean;
}

export default function ClinicaBelezaConfiguracoesWhatsappPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [whatsappNumero, setWhatsappNumero] = useState('');
  const [whatsappAtivo, setWhatsappAtivo] = useState(false);
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('');
  const [whatsappToken, setWhatsappToken] = useState('');
  const [whatsappTokenSet, setWhatsappTokenSet] = useState(false);
  const [enviarConfirmacao, setEnviarConfirmacao] = useState(true);
  const [enviarLembrete24h, setEnviarLembrete24h] = useState(true);
  const [enviarLembrete2h, setEnviarLembrete2h] = useState(true);
  const [enviarCobranca, setEnviarCobranca] = useState(true);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const data = (await ClinicaBelezaAPI.whatsapp.get()) as WhatsAppConfigData;
      setWhatsappNumero((data.whatsapp_numero ?? '').toString());
      setWhatsappAtivo(!!data.whatsapp_ativo);
      setWhatsappPhoneId((data.whatsapp_phone_id ?? '').toString());
      setWhatsappTokenSet(!!data.whatsapp_token_set);
      setWhatsappToken('');
      setEnviarConfirmacao(data.enviar_confirmacao ?? true);
      setEnviarLembrete24h(data.enviar_lembrete_24h ?? true);
      setEnviarLembrete2h(data.enviar_lembrete_2h ?? true);
      setEnviarCobranca(data.enviar_cobranca ?? true);
    } catch {
      /* defaults */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const saveConfig = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        whatsapp_numero: whatsappNumero,
        whatsapp_ativo: whatsappAtivo,
        whatsapp_phone_id: whatsappPhoneId.trim() || '',
        enviar_confirmacao: enviarConfirmacao,
        enviar_lembrete_24h: enviarLembrete24h,
        enviar_lembrete_2h: enviarLembrete2h,
        enviar_cobranca: enviarCobranca,
        ...(whatsappToken.trim() ? { whatsapp_token: whatsappToken.trim() } : {}),
      };
      await ClinicaBelezaAPI.whatsapp.save(body);
      setWhatsappTokenSet(!!(whatsappToken.trim() || whatsappTokenSet));
      setWhatsappToken('');
      alert('Configurações WhatsApp salvas.');
      await loadConfig();
    } catch {
      alert('Erro ao salvar. Tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Configurar WhatsApp"
        subtitle="Confirmações, lembretes e integração Meta"
        backHref={base}
        icon={MessageCircle}
        showOffline={false}
      />
      <ClinicaBelezaPageContent className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Confirmações de agendamento, lembretes para pacientes e integração com a API Meta (WhatsApp Business).
        </p>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <div className="space-y-6">
            <WhatsAppConfigHelp variant="clinica" />

            <div className="rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/40 px-4 py-3 space-y-3">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                Integração WhatsApp Business (Meta)
              </p>
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
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Meta → seu app → WhatsApp → API Setup → <strong>Phone number ID</strong>
                </p>
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

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Número WhatsApp da clínica
              </label>
              <input
                type="text"
                value={whatsappNumero}
                onChange={(e) => setWhatsappNumero(e.target.value)}
                placeholder="Ex: 5511999999999 (DDD + número)"
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
              />
            </div>

            <div className="rounded-lg border border-gray-200 dark:border-gray-600 px-4 py-3 space-y-3">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Mensagens automáticas</p>
              {[
                { checked: enviarConfirmacao, set: setEnviarConfirmacao, label: 'Enviar confirmação de agendamento' },
                { checked: enviarLembrete24h, set: setEnviarLembrete24h, label: 'Lembrete 24h antes da consulta' },
                { checked: enviarLembrete2h, set: setEnviarLembrete2h, label: 'Lembrete 2h antes da consulta' },
                { checked: enviarCobranca, set: setEnviarCobranca, label: 'Enviar cobrança' },
              ].map(({ checked, set, label }) => (
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

            <WhatsAppConfigStatus
              whatsappAtivo={whatsappAtivo}
              whatsappPhoneId={whatsappPhoneId}
              whatsappTokenSet={whatsappTokenSet}
              whatsappNumero={whatsappNumero}
              variant="clinica"
            />

            <div className="flex justify-end">
              <button
                type="button"
                onClick={saveConfig}
                disabled={saving}
                className="px-4 py-2 text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        )}
      </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
