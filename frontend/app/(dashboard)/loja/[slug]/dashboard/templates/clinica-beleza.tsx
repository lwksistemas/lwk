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
  Bell,
  Menu,
  X,
  Wallet,
  ChevronDown,
  Tablet,
} from "lucide-react";
import { LojaInfo } from '@/types/dashboard';
import { useClinicaBelezaDark } from '@/hooks/useClinicaBelezaDark';

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

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } = await import('@/lib/clinica-beleza-api');
      const response = await fetch(`${getClinicaBelezaBaseUrl()}/dashboard/`, {
        headers: getClinicaBelezaHeaders(),
      });

      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
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
            {/* Notificações - dropdown ao clicar */}
            <div className="relative">
              <button 
                onClick={() => { setNotificationsOpen(!notificationsOpen); setHeaderMenuOpen(false); }}
                className="p-2 hover:bg-purple-50 dark:hover:bg-neutral-700 rounded-lg transition-colors relative"
                title="Notificações"
              >
                <Bell className="w-5 h-5" />
              </button>
              {notificationsOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setNotificationsOpen(false)} />
                  <div className="absolute right-0 top-full mt-1 z-50 w-72 max-h-80 bg-white dark:bg-neutral-800 rounded-xl shadow-lg border dark:border-neutral-700 py-2 animate-scale-in overflow-hidden flex flex-col">
                    <div className="px-4 py-2 border-b dark:border-neutral-700">
                      <h3 className="font-semibold text-sm">Notificações</h3>
                    </div>
                    <div className="overflow-y-auto flex-1 p-4">
                      <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-6">
                        Nenhuma notificação no momento.
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>
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
                      onClick={() => { alert('Página de Configurações em desenvolvimento'); setHeaderMenuOpen(false); }}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm hover:bg-purple-50 dark:hover:bg-neutral-700 text-left"
                    >
                      <Settings className="w-4 h-4" />
                      Configurações Gerais
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
                <SidebarItem icon={<Tablet size={20} />} label="Modo Tablet (Recepção)" onClick={() => window.location.href = `/loja/${params.slug}/tablet`} />
                <SidebarItem icon={<Users size={20} />} label="Pacientes" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/pacientes`} />
                <SidebarItem icon={<Users size={20} />} label="Profissionais" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/profissionais`} />
                <SidebarItem icon={<Sparkles size={20} />} label="Procedimentos" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/procedimentos`} />
                <SidebarItem icon={<Wallet size={20} />} label="Financeiro" onClick={() => window.location.href = `/loja/${params.slug}/clinica-beleza/financeiro`} />
                <SidebarItem icon={<Settings size={20} />} label="Configurações" onClick={() => alert('Página de Configurações em desenvolvimento')} />
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

        {/* CONTENT */}
        <main className="p-4 md:p-6 lg:p-8">
          
          {/* BEM-VINDA */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold">
              Bem-vinda à {loja.nome}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Resumo da clínica hoje
            </p>
          </div>

          {/* CARDS DE ESTATÍSTICAS - GRID RESPONSIVO */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              icon={<CalendarDays className="w-7 h-7" size={28} />}
              title="Agendamentos"
              value={stats.appointments_today.toString()}
              subtitle="Hoje"
            />
            <StatCard
              icon={<Users className="w-7 h-7" size={28} />}
              title="Pacientes"
              value={stats.patients_total.toString()}
              subtitle="Ativos"
            />
            <StatCard
              icon={<Sparkles className="w-7 h-7" size={28} />}
              title="Procedimentos"
              value={stats.procedures_total.toString()}
              subtitle="Ativos"
            />
          </section>

          {/* PRÓXIMOS ATENDIMENTOS - MOBILE FRIENDLY */}
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

          {/* ATALHOS - GRID RESPONSIVO (Financeiro só no menu lateral) */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              label="Calendário" 
              icon={<CalendarDays className="w-7 h-7" size={28} />} 
              onClick={() => window.location.href = `/loja/${params.slug}/agenda`}
            />
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
        <p className="text-xs text-gray-400 dark:text-gray-500">{subtitle}</p>
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
