'use client';

import Link from "next/link";
import { useState, useEffect } from "react";
import type { Hero as HeroType } from "@/types/homepage";

interface HeroProps {
  hero: HeroType | null;
  heroImagens?: Array<{ id: number; imagem: string; titulo: string }>;
}

export default function Hero({ hero, heroImagens = [] }: HeroProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const titulo = hero?.titulo ?? "Controle total da sua empresa em um único sistema";
  const subtitulo =
    hero?.subtitulo ??
    "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.";
  const botaoTexto = hero?.botao_texto ?? "Testar Gratuitamente";
  const mostrarBotaoPrincipal = hero?.botao_principal_ativo !== false;

  // Carrossel automático de imagens
  useEffect(() => {
    if (heroImagens.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % heroImagens.length);
    }, 5000); // Muda a cada 5 segundos

    return () => clearInterval(interval);
  }, [heroImagens.length]);

  const imagemAtual = heroImagens[currentImageIndex]?.imagem;

  return (
    <section 
      className="w-full min-w-full py-12 sm:py-16 md:py-24 relative overflow-hidden transition-all duration-1000"
      style={{
        backgroundImage: imagemAtual 
          ? `linear-gradient(rgba(37, 99, 235, 0.7), rgba(79, 70, 229, 0.7)), url(${imagemAtual})` 
          : 'none',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Gradiente de fundo quando não há imagem */}
      {!imagemAtual && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-600"></div>
      )}
      
      {/* Decoração de fundo */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE0YzMuMzEgMCA2LTIuNjkgNi02cy0yLjY5LTYtNi02LTYgMi42OS02IDYgMi42OSA2IDYgNnptMC0xMGMyLjIxIDAgNCAxLjc5IDQgNHMtMS43OSA0LTQgNC00LTEuNzktNC00IDEuNzktNCA0LTR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20"></div>
      
      <div className="w-full max-w-7xl mx-auto grid md:grid-cols-2 gap-8 md:gap-12 items-center px-4 sm:px-6 lg:px-8 relative z-10">
        <div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6 text-white leading-tight drop-shadow-lg">
            {titulo}
          </h1>
          <p className="text-base sm:text-lg text-blue-50 mb-6 sm:mb-8 drop-shadow">{subtitulo}</p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            {mostrarBotaoPrincipal && (
              <Link
                href="/superadmin/login"
                className="inline-block text-center bg-white text-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50 transition-all font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                {botaoTexto}
              </Link>
            )}
            <Link
              href="/cadastro"
              className="inline-block text-center bg-blue-700/50 backdrop-blur-sm text-white border-2 border-white/30 px-6 py-3 rounded-lg hover:bg-blue-700/70 transition-all font-medium shadow-lg"
            >
              Fazer Cadastro
            </Link>
          </div>
        </div>
        <div className="hidden md:block">
          <div className="rounded-xl shadow-2xl bg-white/10 backdrop-blur-sm p-4 border border-white/20 overflow-hidden">
            <div className="aspect-video bg-gradient-to-br from-blue-100/20 to-indigo-100/20 rounded-lg flex items-center justify-center">
              <div className="text-center p-8">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  {[40, 70, 55].map((h, i) => (
                    <div
                      key={i}
                      className="bg-white/30 backdrop-blur-sm rounded"
                      style={{ height: `${h}px` }}
                    />
                  ))}
                </div>
                <div className="flex gap-2 justify-center">
                  <div className="w-16 h-16 rounded-full bg-white/30 backdrop-blur-sm" />
                  <div className="w-24 h-12 rounded bg-white/30 backdrop-blur-sm" />
                </div>
                <p className="text-white font-semibold mt-4 text-lg drop-shadow-lg">Dashboard</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Indicadores do carrossel */}
      {heroImagens.length > 1 && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2 z-20">
          {heroImagens.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentImageIndex(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentImageIndex 
                  ? 'bg-white w-8' 
                  : 'bg-white/50 hover:bg-white/75'
              }`}
              aria-label={`Ir para imagem ${index + 1}`}
            />
          ))}
        </div>
      )}
    </section>
  );
}
