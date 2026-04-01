'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  LogIn,
  Users,
  ChevronRight,
  Sliders,
  ArrowLeft,
} from 'lucide-react';

export default function ClinicaEsteticaConfiguracoesPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-estetica/configuracoes`;

  const opcoes = [
    {
      titulo: 'Configurar tela de login',
      descricao: 'Personalize a aparência da tela de login da sua clínica',
      href: `${base}/login`,
      icon: LogIn,
      itens: ['Logo', 'Cores e identidade visual'],
    },
    {
      titulo: 'Cadastrar funcionários',
      descricao: 'Gerencie profissionais e equipe da clínica',
      href: `${base}/funcionarios`,
      icon: Users,
      itens: ['Adicionar profissionais', 'Permissões'],
    },
    {
      titulo: 'Personalizar sistema',
      descricao: 'Personalize o sistema do jeito que você quiser trabalhar',
      href: `${base}/personalizar`,
      icon: Sliders,
      itens: ['Tipos de procedimentos', 'Configurações gerais'],
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold">Configurações</h1>
              <p className="text-pink-100 text-sm">Gerencie sua clínica</p>
            </div>
            <Link
              href={`/loja/${slug}/clinica-estetica`}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition-colors flex items-center gap-2"
            >
              <ArrowLeft size={16} />
              Voltar
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opcoes.map((op) => {
              const Icon = op.icon;
              return (
                <Link
                  key={op.href}
                  href={op.href}
                  className="block bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-pink-500/30 transition-all group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="p-2.5 rounded-lg bg-pink-100 text-pink-600">
                          <Icon size={22} />
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900">
                          {op.titulo}
                        </h2>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">
                        {op.descricao}
                      </p>
                      <ul className="space-y-1">
                        {op.itens.map((item) => (
                          <li
                            key={item}
                            className="text-xs text-gray-500 flex items-center gap-2"
                          >
                            <span>• {item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <ChevronRight
                      size={20}
                      className="text-gray-400 group-hover:text-pink-500 shrink-0 transition-colors"
                    />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}
