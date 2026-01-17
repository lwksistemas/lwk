'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-blue-600">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-4">
            LWK SISTEMAS
          </h1>
          <p className="text-xl text-blue-100">
            Sistema Gestão de Lojas
          </p>
        </div>

        {/* Login Options */}
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* SuperAdmin Login */}
          <Link href="/superadmin/login">
            <div className="bg-white rounded-lg shadow-2xl p-8 hover:shadow-3xl transition-all cursor-pointer transform hover:scale-105">
              <div className="text-center">
                <div className="w-20 h-20 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  SuperAdmin
                </h2>
                <p className="text-gray-600 mb-4">
                  Gerenciar lojas, planos e usuários do sistema
                </p>
                <div className="inline-block px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700">
                  Acessar →
                </div>
              </div>
            </div>
          </Link>

          {/* Suporte Login */}
          <Link href="/suporte/login">
            <div className="bg-white rounded-lg shadow-2xl p-8 hover:shadow-3xl transition-all cursor-pointer transform hover:scale-105">
              <div className="text-center">
                <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Suporte
                </h2>
                <p className="text-gray-600 mb-4">
                  Atendimento e suporte aos clientes
                </p>
                <div className="inline-block px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700">
                  Acessar →
                </div>
              </div>
            </div>
          </Link>
        </div>

        {/* Footer */}
        <div className="text-center mt-16 text-blue-200">
          <p>© 2026 LWK Sistemas - Todos os direitos reservados</p>
        </div>
      </div>
    </div>
  );
}
