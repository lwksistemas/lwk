"use client";

/**
 * Dashboard Clínica da Beleza
 * Sistema completo de gestão de clínica estética
 */

import { useEffect, useState } from 'react';
import Image from "next/image";
import {
  CalendarDays,
  Users,
  Sparkles,
  Moon,
  Settings,
  CreditCard,
  LogOut,
  Bell,
} from "lucide-react";
import { LojaInfo } from '@/types/dashboard';

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
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clinica-beleza/dashboard/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
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
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-white p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando dashboard...</p>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-white p-4 sm:p-8 text-gray-800">
      {/* HEADER */}
      <header className="flex justify-between items-start mb-8">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-pink-200 flex items-center justify-center text-xl sm:text-2xl">
            💆‍♀️
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold">Bem-vinda, {loja.nome}</h1>
            <p className="text-xs sm:text-sm text-gray-500">Resumo da clínica hoje</p>
          </div>
        </div>

        <div className="relative">
          <div className="flex items-center gap-2 sm:gap-3">
            <IconButton onClick={() => setShowMenu(!showMenu)}>
              <Settings className="w-4 h-4 sm:w-5 sm:h-5" />
            </IconButton>
            <IconButton>
              <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
            </IconButton>
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white font-bold text-sm">
              {loja.nome.charAt(0).toUpperCase()}
            </div>
          </div>

          {/* MENU */}
          {showMenu && (
            <div className="absolute right-0 mt-4 w-64 bg-white rounded-xl shadow-lg p-3 space-y-2 z-50">
              <MenuItem icon={<Settings size={18} />} label="Configurações Gerais" />
              <MenuItem icon={<Moon size={18} />} label="Modo Escuro" />
              <MenuItem icon={<CreditCard size={18} />} label="Pagar Assinatura" />
              <MenuItem icon={<LogOut size={18} />} label="Sair" danger />
            </div>
          )}
        </div>
      </header>

      {/* CARDS */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-8">
        <StatCard
          icon={<CalendarDays />}
          title="Agendamentos"
          value={stats.appointments_today.toString()}
          subtitle="Hoje"
        />
        <StatCard
          icon={<Users />}
          title="Pacientes"
          value={stats.patients_total.toString()}
          subtitle="Ativos"
        />
        <StatCard
          icon={<Sparkles />}
          title="Procedimentos"
          value={stats.procedures_total.toString()}
          subtitle="Ativos"
        />
      </section>

      {/* TABELA */}
      <section className="bg-white/70 backdrop-blur-xl rounded-2xl shadow p-4 sm:p-6 mb-10">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
          <h2 className="text-base sm:text-lg font-semibold">Próximos Atendimentos</h2>
          <div className="flex gap-2 sm:gap-3 w-full sm:w-auto">
            <select className="flex-1 sm:flex-none border rounded-lg px-3 py-2 text-sm">
              <option>Hoje</option>
              <option>Esta Semana</option>
            </select>
            <select className="flex-1 sm:flex-none border rounded-lg px-3 py-2 text-sm">
              <option>Todos os Profissionais</option>
            </select>
          </div>
        </div>

        {appointments.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            Nenhum agendamento para hoje
          </div>
        ) : (
          <>
            {/* Desktop: Tabela */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-gray-500">
                  <tr className="border-b">
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

            {/* Mobile: Cards */}
            <div className="md:hidden space-y-3">
              {appointments.map((appointment) => (
                <AppointmentCard key={appointment.id} {...appointment} />
              ))}
            </div>
          </>
        )}
      </section>

      {/* ATALHOS */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <Shortcut label="Pacientes" icon={<Users />} />
        <Shortcut label="Procedimentos" icon={<Sparkles />} />
        <Shortcut label="Profissionais" icon={<Users />} />
        <Shortcut label="Calendário" icon={<CalendarDays />} />
      </section>
    </div>
  );
}

function IconButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-2 bg-white rounded-full shadow hover:shadow-md transition-shadow"
    >
      {children}
    </button>
  );
}

function MenuItem({
  icon,
  label,
  danger = false,
}: {
  icon: React.ReactNode;
  label: string;
  danger?: boolean;
}) {
  return (
    <button
      className={`flex items-center gap-3 px-3 py-2 rounded-lg w-full text-sm transition-colors ${
        danger ? "text-red-600 hover:bg-red-50" : "hover:bg-purple-50"
      }`}
    >
      {icon} {label}
    </button>
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
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl shadow p-4 sm:p-6 flex items-center gap-3 sm:gap-4 hover:shadow-md transition-shadow">
      <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600">
        {icon}
      </div>
      <div>
        <p className="text-xs sm:text-sm text-gray-500">{title}</p>
        <p className="text-xl sm:text-2xl font-bold">{value}</p>
        <p className="text-xs text-gray-400">{subtitle}</p>
      </div>
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
    CONFIRMED: "bg-green-100 text-green-700",
    SCHEDULED: "bg-blue-100 text-blue-700",
    PENDING: "bg-yellow-100 text-yellow-700",
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

  const getAvatar = (name: string) => {
    const inicial = name.charAt(0).toUpperCase();
    const colors = ['bg-purple-500', 'bg-pink-500', 'bg-blue-500', 'bg-indigo-500'];
    const color = colors[name.length % colors.length];
    return (
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-xs ${color}`}>
        {inicial}
      </div>
    );
  };

  return (
    <tr className="border-b last:border-none hover:bg-purple-50/50 transition-colors">
      <td className="py-4 font-medium">{time}</td>
      <td className="py-4">
        <div className="flex items-center gap-2">
          {getAvatar(patient_name)}
          {patient_name}
        </div>
      </td>
      <td className="py-4">{procedure_name}</td>
      <td className="py-4">{professional_name}</td>
      <td className="py-4">
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${colors[status] || colors.SCHEDULED}`}>
          {statusLabels[status] || status}
        </span>
      </td>
    </tr>
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
    CONFIRMED: "bg-green-100 text-green-700",
    SCHEDULED: "bg-blue-100 text-blue-700",
    PENDING: "bg-yellow-100 text-yellow-700",
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
    <div className="bg-purple-50/50 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-lg font-bold">{time}</span>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${colors[status] || colors.SCHEDULED}`}>
          {statusLabels[status] || status}
        </span>
      </div>
      <div className="space-y-2 text-sm">
        <div>
          <p className="text-xs text-gray-500">Paciente</p>
          <p className="font-medium">{patient_name}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Procedimento</p>
          <p>{procedure_name}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Profissional</p>
          <p>{professional_name}</p>
        </div>
      </div>
    </div>
  );
}

function Shortcut({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="bg-white/70 backdrop-blur-xl rounded-2xl shadow p-4 sm:p-6 flex flex-col items-center gap-3 cursor-pointer hover:shadow-md transition-shadow">
      <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600">
        {icon}
      </div>
      <p className="text-xs sm:text-sm font-medium text-center">{label}</p>
    </div>
  );
}
