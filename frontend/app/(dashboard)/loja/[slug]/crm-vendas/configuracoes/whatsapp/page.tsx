'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, MessageCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

interface WhatsAppConfigData {
  enviar_confirmacao: boolean;
  enviar_lembrete_24h: boolean;
  enviar_lembrete_2h: boolean;
  enviar_cobranca: boolean;
  enviar_lembrete_tarefas: boolean;
  whatsapp_numero: string;
  whatsapp_ativo: boolean;
  whatsapp_phone_id: string;
  whatsapp_token_set: boolean;
}

export default function ConfiguracoesWhatsappPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [whatsappNumero, setWhatsappNumero] = useState('');
  const [whatsappAtivo, setWhatsappAtivo] = useState(false);
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('');
  const [whatsappToken, setWhatsappToken] = useState('');
  const [whatsappTokenSet, setWhatsappTokenSet] = useState(false);
  const [enviarLembreteTarefas, setEnviarLembreteTarefas] = useState(true);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<WhatsAppConfigData>('/crm-vendas/whatsapp-config/');
      setWhatsappNumero((data.whatsapp_numero ?? '').toString());
      setWhatsappAtivo(!!data.whatsapp_ativo);
      setWhatsappPhoneId((data.whatsapp_phone_id ?? '').toString());
      setWhatsappTokenSet(!!data.whatsapp_token_set);
      setWhatsappToken('');
      setEnviarLembreteTarefas(data.enviar_lembrete_tarefas ?? true);
    } catch {
      setWhatsappNumero('');
      setWhatsappAtivo(false);
      setWhatsappPhoneId('');
      setWhatsappTokenSet(false);
      setEnviarLembreteTarefas(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authService.isVendedor()) {
      router.replace(`/loja/${slug}/crm-vendas`);
      return;
    }
    loadConfig();
  }, [router, slug]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        whatsapp_numero: whatsappNumero,
        whatsapp_ativo: whatsappAtivo,
        whatsapp_phone_id: whatsappPhoneId.trim() || '',
        enviar_lembrete_tarefas: enviarLembreteTarefas,
        ...(whatsappToken.trim() ? { whatsapp_token: whatsappToken.trim() } : {}),
      };
      await apiClient.patch('/crm-vendas/whatsapp-config/', body);
      setWhatsappTokenSet(!!(whatsappToken.trim() || whatsappTokenSet));
      setWhatsappToken('');
      alert('Configurações WhatsApp salvas.');
    } catch (e) {
      const err = e as { response?: { data?: { error?: string; detail?: string } } };
      const msg =
        err?.response?.data?.error ||
        (typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : null) ||
        'Erro ao salvar. Tente novamente.';
      alert(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3] dark:hover:text-[#0d9dda]"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
            <MessageCircle size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Configurar WhatsApp
          </h1>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Use a mesma integração WhatsApp configurada na loja (Clínica da Beleza ou outro app) para
          enviar lembretes de tarefas do calendário CRM.
        </p>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <div className="space-y-6">
            {/* Integração API Meta */}
            <div className="rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/20 px-4 py-3 space-y-3">
              <p className="text-sm font-medium text-purple-800 dark:text-purple-200">
                Integração WhatsApp Business (Meta)
              </p>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={whatsappAtivo}
                  onChange={(e) => setWhatsappAtivo(e.target.checked)}
                  className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
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
                  className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Em developers.facebook.com → seu app → WhatsApp → API Setup. Use o{' '}
                  <strong>Phone number ID</strong> do número que envia.
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
                  className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500"
                  autoComplete="off"
                />
                {whatsappTokenSet && !whatsappToken && (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">Token já configurado</p>
                )}
              </div>
            </div>

            {/* Número da loja */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Número WhatsApp para receber lembretes (ex.: para o dono da loja)
              </label>
              <input
                type="text"
                value={whatsappNumero}
                onChange={(e) => setWhatsappNumero(e.target.value)}
                placeholder="Ex: 5511999999999 (DDD + número)"
                className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500"
              />
            </div>

            {/* Opção CRM */}
            <div className="rounded-lg border border-gray-200 dark:border-neutral-600 bg-gray-50 dark:bg-[#0d1f3c] px-4 py-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enviarLembreteTarefas}
                  onChange={(e) => setEnviarLembreteTarefas(e.target.checked)}
                  className="rounded border-gray-300 dark:border-neutral-600 text-[#0176d3]"
                />
                <span className="text-sm text-gray-800 dark:text-gray-200">
                  Enviar lembrete de tarefas do calendário (CRM) — 24h antes
                </span>
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Receba lembretes por WhatsApp das atividades do dia seguinte.
              </p>
            </div>

            {/* Status */}
            <div className="rounded-lg border border-gray-200 dark:border-neutral-600 bg-gray-50 dark:bg-neutral-700/50 px-4 py-4">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-0.5">Status</p>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                {whatsappAtivo && (whatsappPhoneId || '').trim() && whatsappTokenSet ? (
                  <>✅ Integração ativa — lembretes de tarefas podem ser enviados.</>
                ) : whatsappAtivo && ((whatsappPhoneId || '').trim() || whatsappTokenSet) ? (
                  <>⚠️ Preencha Phone ID e Token e marque &quot;WhatsApp ativo&quot; para enviar.</>
                ) : (whatsappNumero || '').trim() ? (
                  <>Número definido. Ative a integração acima para enviar lembretes de tarefas.</>
                ) : (
                  <>Configure o número e a integração (Phone ID + Token) para enviar mensagens.</>
                )}
              </p>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={saveConfig}
                disabled={saving}
                className="px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50"
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
