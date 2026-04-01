'use client';

import { useParams, useRouter } from 'next/navigation';
import { Calendar, Settings } from 'lucide-react';
import Link from 'next/link';

export default function ClinicaEsteticaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold">Clínica de Estética</h1>
              <p className="text-pink-100 text-sm">Sistema de gestão</p>
            </div>
            <button
              onClick={() => router.push(`/loja/${slug}/dashboard`)}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition-colors"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card Agenda */}
            <Link
              href={`/loja/${slug}/clinica-estetica/agenda`}
              className="block bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-pink-500/30 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2.5 rounded-lg bg-pink-100 text-pink-600">
                      <Calendar size={22} />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900">Agenda</h2>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Gerencie agendamentos e consultas
                  </p>
                  <ul className="space-y-1">
                    <li className="text-xs text-gray-500">• Visualizar agenda</li>
                    <li className="text-xs text-gray-500">• Agendar consultas</li>
                    <li className="text-xs text-gray-500">• Gerenciar horários</li>
                  </ul>
                </div>
              </div>
            </Link>

            {/* Card Configurações */}
            <Link
              href={`/loja/${slug}/clinica-estetica/configuracoes`}
              className="block bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-purple-500/30 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2.5 rounded-lg bg-purple-100 text-purple-600">
                      <Settings size={22} />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900">Configurações</h2>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Configure sua clínica
                  </p>
                  <ul className="space-y-1">
                    <li className="text-xs text-gray-500">• Tela de login</li>
                    <li className="text-xs text-gray-500">• Funcionários</li>
                    <li className="text-xs text-gray-500">• Personalização</li>
                  </ul>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
