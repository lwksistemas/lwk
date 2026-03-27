'use client';

import Link from "next/link";
import { useState } from "react";
import { Menu, X, LogIn } from "lucide-react";
import AcessoRapidoModal from "./AcessoRapidoModal";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <header className="bg-white shadow w-full sticky top-0 z-50">
        <div className="w-full max-w-7xl mx-auto flex justify-between items-center px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="text-xl sm:text-2xl font-bold text-blue-600">
            LWK SISTEMAS
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <a
              href="#funcionalidades"
              className="text-gray-600 hover:text-blue-600 transition-colors"
            >
              Funcionalidades
            </a>
            <a
              href="#beneficios"
              className="text-gray-600 hover:text-blue-600 transition-colors"
            >
              Benefícios
            </a>
            <a
              href="#modulos"
              className="text-gray-600 hover:text-blue-600 transition-colors"
            >
              Módulos
            </a>
            
            {/* Botão Acesso Rápido - Centralizado */}
            <button
              onClick={() => setModalOpen(true)}
              className="bg-green-600 text-white px-5 py-2.5 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2 shadow-md hover:shadow-lg"
            >
              <LogIn className="w-4 h-4" />
              Acesso Rápido
            </button>
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-blue-600"
            aria-label="Menu"
          >
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {menuOpen && (
          <nav className="md:hidden bg-white border-t border-gray-200">
            <div className="flex flex-col px-4 py-2">
              <a
                href="#funcionalidades"
                onClick={() => setMenuOpen(false)}
                className="py-3 text-gray-600 hover:text-blue-600 transition-colors border-b border-gray-100"
              >
                Funcionalidades
              </a>
              <a
                href="#beneficios"
                onClick={() => setMenuOpen(false)}
                className="py-3 text-gray-600 hover:text-blue-600 transition-colors border-b border-gray-100"
              >
                Benefícios
              </a>
              <a
                href="#modulos"
                onClick={() => setMenuOpen(false)}
                className="py-3 text-gray-600 hover:text-blue-600 transition-colors border-b border-gray-100"
              >
                Módulos
              </a>
              
              {/* Botão Acesso Rápido Mobile */}
              <button
                onClick={() => {
                  setMenuOpen(false);
                  setModalOpen(true);
                }}
                className="mt-3 mb-2 text-center bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2"
              >
                <LogIn className="w-5 h-5" />
                Acesso Rápido (CPF/CNPJ)
              </button>
            </div>
          </nav>
        )}
      </header>

      {/* Modal de Acesso Rápido */}
      <AcessoRapidoModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
      />
    </>
  );
}
