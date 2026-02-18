"use client";

/**
 * Dashboard Clínica da Beleza v579
 * Mobile-First com menu hamburger e modo escuro
 * Design moderno com glassmorphism e gradiente rosa/lilás
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  CalendarDays,
  Users,
  Sparkles,
  Moon,
  Sun,
  Settings,
  CreditCard,
  LogOut,
  Menu,
  X,
  Wallet,
  ChevronDown,
  Megaphone,
  Headphones,
} from "lucide-react";
import { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';
import { NotificationBell } from '@/components/notifications/NotificationBell';

interface DashboardStats {
  appointments_today: number;
  patients_total: number;
  procedures_total: number;
  revenue_month: number;
}

interface Appointment {
  id: number;
  date: string;
  patient_name: string;
  procedure_name: string;
  professional_name: string;
  status: string;
}

interface DashboardData {
  statistics: DashboardStats;
  next_appointments: Appointment[];
}

export default function DashboardClinicaBeleza({ loja }: { loja: LojaInfo }) {
  const params = useParams();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useClinicaBelezaDark();
  const [headerMenuOpen, setHeaderMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);
  const [whatsappConfig, setWhatsappConfig] = useState<{
    enviar_confirmacao: boolean;
    enviar_lembrete_24h: boolean;
    enviar_lembrete_2h: boolean;
    enviar_cobranca: boolean;
  } | null>(null);
  const [whatsappNumero, setWhatsappNumero] = useState('');
  const [whatsappAtivo, setWhatsappAtivo] = useState(false);
  const [whatsappPhoneId, setWhatsappPhoneId] = useState('');
  const [whatsappToken, setWhatsappToken] = useState('');
  const [whatsappTokenSet, setWhatsappTokenSet] = useState(false);
  const [whatsappConfigSaving, setWhatsappConfigSaving] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [loja?.id, loja?.slug]);

  const getHeadersComTenant = (): Record<string, string> => {
    const token = typeof window !== 'undefined' ? (sessionStorage.getItem('access_token') || localStorage.getItem('token')) : null;
    const h: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) h['Authorization'] = `Bearer ${token}`;
    if (loja?.id) h['X-Loja-ID'] = String(loja.id);
    else if (loja?.slug) h['X-Tenant-Slug'] = loja.slug;
    return h;
  };

  const loadWhatsAppConfig = async () => {
    try {
      const { getClinicaBelezaBaseUrl } = await import('@/lib/clinica-beleza-api');
      const res = await fetch(`${getClinicaBelezaBaseUrl()}/whatsapp-config/`, { headers: getHeadersComTenant() });
      if (res.ok) {
        const data = await res.json();
        setWhatsappConfig({
          enviar_confirmacao: !!data.enviar_confirmacao,
          enviar_lembrete_24h: !!data.enviar_lembrete_24h,
          enviar_lembrete_2h: !!data.enviar_lembrete_2h,
          enviar_cobranca: !!data.enviar_cobranca,
        });
        setWhatsappNumero((data.whatsapp_numero ?? '').toString());
        setWhatsappAtivo(!!data.whatsapp_ativo);
        setWhatsappPhoneId((data.whatsapp_phone_id ?? '').toString());
        setWhatsappTokenSet(!!data.whatsapp_token_set);
        setWhatsappToken('');
      } else {
        setWhatsappConfig({ enviar_confirmacao: true, enviar_lembrete_24h: true, enviar_lembrete_2h: true, enviar_cobranca: true });
        setWhatsappNumero('');
        setWhatsappAtivo(false);
        setWhatsappPhoneId('');
        setWhatsappTokenSet(false);
      }
    } catch {
      setWhatsappConfig({ enviar_confirmacao: true, enviar_lembrete_24h: true, enviar_lembrete_2h: true, enviar_cobranca: true });
      setWhatsappNumero('');
      setWhatsappAtivo(false);
      setWhatsappPhoneId('');
      setWhatsappTokenSet(false);
    }
  };

  const saveWhatsAppConfig = async () => {
    if (!whatsappConfig) return;
    setWhatsappConfigSaving(true);
    try {
      const { getClinicaBelezaBaseUrl } = await import('@/lib/clinica-beleza-api');
      const body: Record<string, unknown> = {
        ...whatsappConfig,
        whatsapp_numero: whatsappNumero,
        whatsapp_ativo: whatsappAtivo,
        whatsapp_phone_id: whatsappPhoneId.trim() || '',
        ...(whatsappToken.trim() ? { whatsapp_token: whatsappToken.trim() } : {}),
      };
      const res = await fetch(`${getClinicaBelezaBaseUrl()}/whatsapp-config/`, {
        method: 'PATCH',
        headers: getHeadersComTenant(),
        body: JSON.stringify(body),
      });
      if (res.status === 401) {
        const { handle401SessionResponse } = await import('@/lib/clinica-beleza-api');
        if (await handle401SessionResponse(res)) return;
      }
      if (res.ok) {
        const data = await res.json();
        setWhatsappNumero((data.whatsapp_numero ?? '').toString());
        setWhatsappAtivo(!!data.whatsapp_ativo);
        setWhatsappPhoneId((data.whatsapp_phone_id ?? '').toString());
        setWhatsappTokenSet(!!data.whatsapp_token_set);
        setWhatsappToken('');
        alert('Configurações WhatsApp salvas.');
        setConfigOpen(false);
      } else {
        let msg = `Erro ao salvar (${res.status}).`;
        try {
          const err = await res.json();
          if (err?.error) msg = err.error;
          else if (err?.detail) msg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
        } catch {
          const text = await res.text();
          if (text) msg = text.slice(0, 200);
        }
        alert(msg);
      }
    } catch (e) {
      if (e instanceof Error && e.message === 'SESSION_ENDED') return;
      alert('Erro ao salvar. Tente novamente.');
    } finally {
      setWhatsappConfigSaving(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } = await import('@/lib/clinica-beleza-api');
      const headers = getClinicaBelezaHeaders() as Record<string, string>;
      if (loja?.id && !headers['X-Loja-ID']) {
        headers['X-Loja-ID'] = String(loja.id);
      }
      if (loja?.slug && !headers['X-Loja-ID'] && !headers['X-Tenant-Slug']) {
        headers['X-Tenant-Slug'] = loja.slug;
      }
      const response = await fetch(`${getClinicaBelezaBaseUrl()}/dashboard/`, {
        headers,
      });

      if (response.ok) {
        const result = await response.json();
        setData(result);
      } else {
        setData({
          statistics: { appointments_today: 0, patients_total: 0, procedures_total: 0, revenue_month: 0 },
          next_appointments: [],
        });
      }
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      setData({
        statistics: { appointments_today: 0, patients_total: 0, procedures_total: 0, revenue_month: 0 },
        next_appointments: [],
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-white dark:bg-gradient-to-br dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  const stats = data?.statistics || {
    appointments_today: 0,
    patients_total: 0,
    procedures_total: 0,
    revenue_month: 0,
  };

  const appointments = data?.next_appointments || [];

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      sessionStorage.removeItem('user_type');
      sessionStorage.removeItem('loja_slug');
      window.location.href = `/loja/${params.slug}/login`;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-white dark:bg-gradient-to-br dark:from-neutral-900 dark:via-neutral-800 dark:to-neutral-900 text-gray-800 dark:text-gray-100">
        
        {/* HEADER */}
        <header className="flex items-center justify-between p-4 shadow bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl sticky top-0 z-40">
          <button 
            onClick={() => setSidebarOpen(true)} 
            className="p-2 hover:bg-purple-50 dark:hover:bg-neutral-700 rounded-lg transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-pink-200 dark:bg-pink-900 flex items-center justify-center text-xl">
              💆‍♀️
            </div>
            <h1 className="text-lg font-semibold hidden sm:block">{loja.nome}</h1>
          </div>

          <div className="flex items-center gap-2 relative">
            <NotificationBell
              open={notificationsOpen}
              onOpenChange={setNotificationsOpen}
            />
            <a
              href={`/loja/${params.slug}/suporte`}
              className="p-2 hover:bg-purple-50 dark:hover:bg-neutral-700 rounded-lg transition-colors flex items-center gap-1.5 text-gray-700 dark:text-gray-200"
              title="Suporte - Meus chamados"
            >
              <Headphones className="w-5 h-5" />
              <span className="hidden sm:inline text-sm font-medium">Suporte</span>
            </a>
            <div className="relative">
              <button 
                onClick={() => { setHeaderMenuOpen(!headerMenuOpen); setNotificationsOpen(false); }}
                className="flex items-center gap-1 p-2 hover:bg-purple-50 dark:hover:bg-neutral-700 rounded-lg transition-colors"
                title="Menu"
              >
                <div className="w-8 h-8 rounded-full bg-pink-300 dark:bg-pink-800 flex items-center justify-center text-sm">
                  👤
                </div>
                <ChevronDown className="w-4 h-4 hidden sm:block" />
              </button>
              {headerMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setHeaderMenuOpen(false)} />
                  <div className="absolute right-0 top-full mt-1 z-50 w-56 py-1 bg-white dark:bg-neutral-800 rounded-xl shadow-lg border dark:border-neutral-700">
                    <a
                      href={`/loja/${params.slug}/assinatura`}
                      className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-purple-50 dark:hover:bg-neutral-700 text-orange-600 dark:text-orange-400"
                      onClick={() => setHeaderMenuOpen(false)}
                    >
                      <CreditCard className="w-4 h-4" />
                      Pagar Assinatura
                    </a>
                    <button
                      onClick={() => { setDarkMode(!darkMode); setHeaderMenuOpen(false); }}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm hover:bg-purple-50 dark:hover:bg-neutral-700 text-left"
                    >
                      {darkMode ? <Sun className="w-4 h-4 text-purple-600" /> : <Moon className="w-4 h-4 text-purple-600" />}
                      {darkMode ? "Modo Claro" : "Modo Escuro"}
                    </button>
                    <button
                      onClick={() => { setConfigOpen(true); setHeaderMenuOpen(false); loadWhatsAppConfig(); }}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm hover:bg-purple-50 dark:hover:bg-neutral-700 text-left"
                    >
                      <Settings className="w-4 h-4" />
                      Configurações
                    </button>
                    <button
                      onClick={() => { setHeaderMenuOpen(false); if (confirm('Deseja realmente sair?')) handleLogout(); }}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 text-left"
                    >
                      <LogOut className="w-4 h-4" />
                      Sair
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* SIDEBAR */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 z-50 bg-black/50" 
            onClick={() => setSidebarOpen(false)}
          >
            <aside 
              className="absolute left-0 top-0 h-full w-64 bg-white dark:bg-neutral-800 p-4 shadow-2xl" 
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">💆‍♀️</span>
                  <span className="font-bold">Menu</span>
                </div>
                <button 
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="space-y-2">
                <SidebarItem icon={<CalendarDays size={20} />} label="Agenda" onClick={() => window.location.href = `/loja/${params.slug}/agenda`} />
                <SidebarItem icon={<Users size={20} />} label="Pacientes" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/pacientes`} />
                <SidebarItem icon={<Users size={20} />} label="Profissionais" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/profissionais`} />
                <SidebarItem icon={<Sparkles size={20} />} label="Procedimentos" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/procedimentos`} />
                <SidebarItem icon={<Wallet size={20} />} label="Financeiro" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/financeiro`} />
                <SidebarItem icon={<Megaphone size={20} />} label="Campanhas" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/campanhas`} />
                <SidebarItem icon={<Settings size={20} />} label="Configurações" onClick={() => { setConfigOpen(true); setSidebarOpen(false); loadWhatsAppConfig(); }} />
                <SidebarItem icon={<CreditCard size={20} />} label="Assinatura" onClick={() => window.location.href = `/loja/${params.slug}/assinatura`} />
                <div className="pt-4 border-t dark:border-neutral-700">
                  <SidebarItem 
                    icon={<LogOut size={20} />} 
                    label="Sair" 
                    danger 
                    onClick={() => {
                      if (confirm('Deseja realmente sair?')) {
                        handleLogout();
                      }
                    }}
                  />
                </div>
              </nav>
            </aside>
          </div>
        )}

        {/* Modal Configurações (WhatsApp) */}
        {configOpen && (
          <>
            <div className="fixed inset-0 z-40 bg-black/50" onClick={() => setConfigOpen(false)} />
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-md border dark:border-neutral-700" onClick={e => e.stopPropagation()}>
                <div className="p-4 border-b dark:border-neutral-700 flex justify-between items-center">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">Configurações</h3>
                  <button type="button" onClick={() => setConfigOpen(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="p-4 space-y-4">
                  <h4 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                    <span>💬</span> WhatsApp
                  </h4>

                  {/* Integração API Meta: cada clínica configura na sua tela */}
                  <div className="rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/20 px-3 py-2 space-y-3">
                    <p className="text-xs font-medium text-purple-800 dark:text-purple-200">Integração WhatsApp Business (Meta)</p>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={whatsappAtivo}
                        onChange={e => setWhatsappAtivo(e.target.checked)}
                        className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
                      />
                      <span className="text-sm text-gray-800 dark:text-gray-200">WhatsApp ativo — usar esta integração para enviar mensagens</span>
                    </label>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Phone Number ID (Meta)</label>
                      <input
                        type="text"
                        value={whatsappPhoneId}
                        onChange={e => setWhatsappPhoneId(e.target.value)}
                        placeholder="Ex: 123456789012345"
                        className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Em developers.facebook.com → seu app → WhatsApp → API Setup</p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Token de acesso (Meta)</label>
                      <input
                        type="password"
                        value={whatsappToken}
                        onChange={e => setWhatsappToken(e.target.value)}
                        placeholder={whatsappTokenSet ? "Deixe em branco para não alterar" : "Cole o token permanente da API"}
                        className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500"
                        autoComplete="off"
                      />
                      {whatsappTokenSet && !whatsappToken && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">Token já configurado</p>
                      )}
                    </div>
                  </div>

                  {/* Número da loja (exibição / identificação) */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Número WhatsApp da loja (ex.: para exibir aos pacientes)
                    </label>
                    <input
                      type="text"
                      value={whatsappNumero}
                      onChange={e => setWhatsappNumero(e.target.value)}
                      placeholder="Ex: 5511999999999 (DDD + número)"
                      className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500"
                    />
                  </div>

                  {/* Status */}
                  <div className="rounded-lg border border-gray-200 dark:border-neutral-600 bg-gray-50 dark:bg-neutral-700/50 px-3 py-2">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-300 mb-0.5">Status</p>
                    <p className="text-sm text-gray-800 dark:text-gray-200">
                      {whatsappAtivo && (whatsappPhoneId || '').trim() && whatsappTokenSet ? (
                        <>✅ Integração ativa — mensagens podem ser enviadas.</>
                      ) : whatsappAtivo && ((whatsappPhoneId || '').trim() || whatsappTokenSet) ? (
                        <>⚠️ Preencha Phone ID e Token e marque &quot;WhatsApp ativo&quot; para enviar.</>
                      ) : (whatsappNumero || '').trim() ? (
                        <>Número da loja definido. Ative a integração acima para enviar confirmações e lembretes.</>
                      ) : (
                        <>Configure o número e a integração (Phone ID + Token) para enviar mensagens.</>
                      )}
                    </p>
                  </div>

                  <div className="rounded-lg border border-blue-100 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-900/20 px-3 py-2">
                    <p className="text-xs font-medium text-blue-800 dark:text-blue-200 mb-1">Onde as mensagens são enviadas?</p>
                    <p className="text-xs text-blue-700 dark:text-blue-300">
                      O sistema envia mensagens <strong>automaticamente</strong> aos pacientes: confirmação ao confirmar agendamento, lembretes 24h e 2h antes, e cobrança (financeiro). Quem recebe: apenas pacientes com &quot;Permitir WhatsApp&quot; marcado em <strong>Pacientes</strong> (menu lateral → Pacientes). Não há tela para enviar mensagem manual; tudo é automático conforme as opções abaixo.
                    </p>
                  </div>
                  {whatsappConfig === null ? (
                    <p className="text-sm text-gray-500">Carregando...</p>
                  ) : (
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={whatsappConfig.enviar_confirmacao} onChange={e => setWhatsappConfig(c => c ? { ...c, enviar_confirmacao: e.target.checked } : c)} className="rounded border-gray-300 dark:border-neutral-600 text-purple-600" />
                        <span className="text-sm">Enviar confirmação de agendamento</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={whatsappConfig.enviar_lembrete_24h} onChange={e => setWhatsappConfig(c => c ? { ...c, enviar_lembrete_24h: e.target.checked } : c)} className="rounded border-gray-300 dark:border-neutral-600 text-purple-600" />
                        <span className="text-sm">Enviar lembrete 24h antes</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={whatsappConfig.enviar_lembrete_2h} onChange={e => setWhatsappConfig(c => c ? { ...c, enviar_lembrete_2h: e.target.checked } : c)} className="rounded border-gray-300 dark:border-neutral-600 text-purple-600" />
                        <span className="text-sm">Enviar lembrete 2h antes</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={whatsappConfig.enviar_cobranca} onChange={e => setWhatsappConfig(c => c ? { ...c, enviar_cobranca: e.target.checked } : c)} className="rounded border-gray-300 dark:border-neutral-600 text-purple-600" />
                        <span className="text-sm">Enviar cobrança (financeiro)</span>
                      </label>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Opt-out por paciente: no cadastro de Pacientes, desmarque &quot;Permitir WhatsApp&quot; para quem não deseja receber.</p>
                    </div>
                  )}
                </div>
                <div className="p-4 border-t dark:border-neutral-700 flex justify-end gap-2">
                  <button type="button" onClick={() => setConfigOpen(false)} className="px-4 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg hover:bg-gray-50 dark:hover:bg-neutral-700">Cancelar</button>
                  <button type="button" onClick={saveWhatsAppConfig} disabled={whatsappConfigSaving || whatsappConfig === null} className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50">{whatsappConfigSaving ? 'Salvando...' : 'Salvar'}</button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* CONTENT */}
        <main className="p-4 md:p-6 lg:p-8">
          {/* ATALHOS - BOTÕES NO TOPO */}
          <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 md:gap-4 mb-6">
            <Shortcut 
              label="Pacientes" 
              icon={<Users className="w-7 h-7" size={28} />} 
              onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/pacientes`}
            />
            <Shortcut 
              label="Procedimentos" 
              icon={<Sparkles className="w-7 h-7" size={28} />} 
              onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/procedimentos`}
            />
            <Shortcut 
              label="Profissionais" 
              icon={<Users className="w-7 h-7" size={28} />} 
              onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/profissionais`}
            />
            <Shortcut 
              label="Agenda" 
              icon={<CalendarDays className="w-7 h-7" size={28} />} 
              onClick={() => window.location.href = `/loja/${params.slug}/agenda`}
            />
            <Shortcut 
              label="Campanhas de Promoções" 
              icon={<Megaphone className="w-7 h-7" size={28} />} 
              onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/campanhas`}
            />
          </section>

          {/* PRÓXIMOS ATENDIMENTOS - ABAIXO DOS BOTÕES */}
          <section className="bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl rounded-2xl shadow p-4 md:p-6 mb-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-4">
              <h2 className="text-lg font-semibold">Próximos Atendimentos</h2>
              <div className="flex gap-2">
                <select className="border dark:border-neutral-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-neutral-700">
                  <option>Hoje</option>
                </select>
                <select className="border dark:border-neutral-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-neutral-700">
                  <option>Todos</option>
                </select>
              </div>
            </div>

            {appointments.length === 0 ? (
              <div className="py-8 text-center text-gray-500 dark:text-gray-400">
                Nenhum agendamento para hoje
              </div>
            ) : (
              <>
                {/* TABELA DESKTOP */}
                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-gray-500 dark:text-gray-400">
                      <tr className="border-b dark:border-neutral-700">
                        <th className="text-left py-3">Horário</th>
                        <th className="text-left py-3">Paciente</th>
                        <th className="text-left py-3">Procedimento</th>
                        <th className="text-left py-3">Profissional</th>
                        <th className="text-left py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {appointments.map((appointment) => (
                        <TableRow key={appointment.id} {...appointment} />
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* CARDS MOBILE */}
                <div className="md:hidden space-y-3">
                  {appointments.map((appointment) => (
                    <AppointmentCard key={appointment.id} {...appointment} />
                  ))}
                </div>
              </>
            )}
          </section>
        </main>
      </div>
  );
}

// ============================================================================
// COMPONENTES
// ============================================================================

function SidebarItem({
  icon,
  label,
  danger = false,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  danger?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
        danger
          ? "text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
          : "hover:bg-purple-50 dark:hover:bg-neutral-700"
      }`}
    >
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}

/** Avatar com iniciais (evita 400 do next/image com domínios externos) */
function AvatarPlaceholder({ name, size = 32 }: { name: string; size?: number }) {
  const initials = name
    .trim()
    .split(/\s+/)
    .map((s) => s[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
  return (
    <div
      className="rounded-full bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-200 flex items-center justify-center font-semibold shrink-0"
      style={{ width: size, height: size, fontSize: Math.max(10, size * 0.4) }}
    >
      {initials || "?"}
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  subtitle,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl rounded-2xl shadow p-4 md:p-6 flex items-center gap-4 group">
      <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900 flex items-center justify-center text-purple-600 dark:text-purple-300 [&_svg]:w-7 [&_svg]:h-7 [&_svg]:shrink-0 animate-icon-float group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-gray-400 dark:text-gray-400">{subtitle}</p>
      </div>
    </div>
  );
}

function AppointmentCard({
  date,
  patient_name,
  procedure_name,
  professional_name,
  status,
}: Appointment) {
  const colors: Record<string, string> = {
    CONFIRMED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    SCHEDULED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };

  const statusLabels: Record<string, string> = {
    CONFIRMED: "Confirmado",
    SCHEDULED: "Agendado",
    PENDING: "A Confirmar",
  };

  const time = new Date(date).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-white dark:bg-neutral-800 p-4 rounded-xl shadow flex justify-between items-start">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <AvatarPlaceholder name={patient_name} size={32} />
          <div>
            <p className="font-semibold text-sm">{patient_name}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{procedure_name}</p>
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Profissional: {professional_name}
        </p>
        <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs ${colors[status] || colors.SCHEDULED}`}>
          {statusLabels[status] || status}
        </span>
      </div>
      <span className="font-bold text-purple-600 dark:text-purple-400">{time}</span>
    </div>
  );
}

function TableRow({
  date,
  patient_name,
  procedure_name,
  professional_name,
  status,
}: Appointment) {
  const colors: Record<string, string> = {
    CONFIRMED: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    SCHEDULED: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    PENDING: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  };

  const statusLabels: Record<string, string> = {
    CONFIRMED: "Confirmado",
    SCHEDULED: "Agendado",
    PENDING: "A Confirmar",
  };

  const time = new Date(date).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <tr className="border-b dark:border-neutral-700 last:border-none">
      <td className="py-4 font-medium">{time}</td>
      <td className="py-4 flex items-center gap-2">
        <AvatarPlaceholder name={patient_name} size={32} />
        {patient_name}
      </td>
      <td className="py-4">{procedure_name}</td>
      <td className="py-4">{professional_name}</td>
      <td className="py-4">
        <span className={`px-3 py-1 rounded-full text-xs ${colors[status] || colors.SCHEDULED}`}>
          {statusLabels[status] || status}
        </span>
      </td>
    </tr>
  );
}

function Shortcut({ 
  icon, 
  label,
  onClick 
}: { 
  icon: React.ReactNode; 
  label: string;
  onClick?: () => void;
}) {
  return (
    <div 
      onClick={onClick}
      className="group bg-white/70 dark:bg-neutral-800/70 backdrop-blur-xl rounded-2xl shadow p-4 md:p-6 flex flex-col items-center gap-3 cursor-pointer hover:shadow-md hover:scale-105 transition-all"
    >
      <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900 flex items-center justify-center text-purple-600 dark:text-purple-300 [&_svg]:w-7 [&_svg]:h-7 [&_svg]:shrink-0 animate-icon-float group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <p className="text-sm font-medium text-center">{label}</p>
    </div>
  );
}
