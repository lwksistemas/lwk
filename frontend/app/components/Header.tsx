'use client';

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="bg-white shadow w-full sticky top-0 z-50">
      <div className="w-full max-w-7xl mx-auto flex justify-between items-center px-4 sm:px-6 lg:px-8 py-4">
        <Link href="/" className="text-xl sm:text-2xl font-bold text-blue-600">
          LWKS SISTEMAS
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
          <Link
            href="/superadmin/login"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Login
          </Link>
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
            <Link
              href="/superadmin/login"
              onClick={() => setMenuOpen(false)}
              className="mt-3 mb-2 text-center bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Login
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}
