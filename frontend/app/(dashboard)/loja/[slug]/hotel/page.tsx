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
      className="block bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 sm:p-6 hover:shadow-md hover:border-sky-500/30 transition-all active:scale-[0.98]"
    >
      <div className="flex items-start gap-3 sm:gap-4">
        <div className="p-2 sm:p-2.5 rounded-lg bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300 shrink-0">
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
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
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <nav className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center min-h-[64px] py-3 gap-2">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold">Hotel / Pousada</h1>
              <p className="text-white/80 text-xs sm:text-sm">Administração hoteleira</p>
            </div>
            <button
              onClick={() => router.push(`/loja/${slug}/dashboard`)}
              className="px-3 sm:px-4 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm active:scale-95"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          <CardLink
            href={`/loja/${slug}/hotel/reservas`}
            title="Reservas"
            description="Criar e gerenciar reservas, check-in e check-out."
            icon={<CalendarDays className="w-5 h-5 sm:w-6 sm:h-6" />}
          />
          <CardLink
            href={`/loja/${slug}/hotel/quartos`}
            title="Quartos / Apartamentos"
            description="Cadastro de unidades, status e capacidade."
            icon={<BedDouble className="w-5 h-5 sm:w-6 sm:h-6" />}
          />
          <CardLink
            href={`/loja/${slug}/hotel/hospedes`}
            title="Hóspedes"
            description="Cadastro de hóspedes, documento e telefone."
            icon={<Users className="w-5 h-5 sm:w-6 sm:h-6" />}
          />
          <CardLink
            href={`/loja/${slug}/hotel/tarifas`}
            title="Tarifas"
            description="Configurar tarifário base e valores de diária."
            icon={<Tag className="w-5 h-5 sm:w-6 sm:h-6" />}
          />
          <CardLink
            href={`/loja/${slug}/hotel/governanca`}
            title="Governança"
            description="Pendências de limpeza/manutenção por quarto."
            icon={<Wrench className="w-5 h-5 sm:w-6 sm:h-6" />}
          />
          <CardLink
            href={`/loja/${slug}/hotel/configuracoes`}
            title="Configurações"
            description="Assinatura, funcionários, login e backup."
            icon={<Settings className="w-5 h-5 sm:w-6 sm:h-6" />}
          />
        </div>
      </main>
    </div>
  );
}
