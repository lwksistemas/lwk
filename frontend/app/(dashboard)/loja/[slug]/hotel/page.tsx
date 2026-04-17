'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { BedDouble, Users, CalendarDays, Tag, Wrench, Settings } from 'lucide-react';

function CardLink({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="block bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6 hover:shadow-md hover:border-sky-500/30 transition-all"
    >
      <div className="flex items-start gap-4">
        <div className="p-2.5 rounded-lg bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300">
          {icon}
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
        </div>
      </div>
    </Link>
  );
}

export default function HotelHomePage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center min-h-[64px] py-3">
            <div>
              <h1 className="text-2xl font-bold">Hotel / Pousada</h1>
              <p className="text-white/80 text-sm">Administração hoteleira</p>
            </div>
            <button
              onClick={() => router.push(`/loja/${slug}/dashboard`)}
              className="px-4 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <CardLink
              href={`/loja/${slug}/hotel/reservas`}
              title="Reservas"
              description="Criar e gerenciar reservas, check-in e check-out."
              icon={<CalendarDays className="w-6 h-6" />}
            />
            <CardLink
              href={`/loja/${slug}/hotel/quartos`}
              title="Quartos / Apartamentos"
              description="Cadastro de unidades, status (disponível/ocupado/limpeza/manutenção) e capacidade."
              icon={<BedDouble className="w-6 h-6" />}
            />
            <CardLink
              href={`/loja/${slug}/hotel/hospedes`}
              title="Hóspedes"
              description="Cadastro de hóspedes, documento, telefone e histórico de reservas."
              icon={<Users className="w-6 h-6" />}
            />
            <CardLink
              href={`/loja/${slug}/hotel/tarifas`}
              title="Tarifas"
              description="Configurar tarifário base e valores de diária."
              icon={<Tag className="w-6 h-6" />}
            />
            <CardLink
              href={`/loja/${slug}/hotel/governanca`}
              title="Governança"
              description="Pendências de limpeza/manutenção/enxoval por quarto."
              icon={<Wrench className="w-6 h-6" />}
            />
            <CardLink
              href={`/loja/${slug}/hotel/configuracoes`}
              title="Configurações"
              description="Assinatura, funcionários, login e backup de dados."
              icon={<Settings className="w-6 h-6" />}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

