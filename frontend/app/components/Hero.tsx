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

  const temCarrossel = heroImagens.length > 0;

  // Fundo: imagens da aba "Imagens" (carrossel) no superadmin.
  useEffect(() => {
    if (heroImagens.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % heroImagens.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [heroImagens.length]);

  const imagemFundoCarrossel = temCarrossel ? heroImagens[currentImageIndex]?.imagem : '';

  return (
    <section
      className={
        'w-full min-w-full relative overflow-hidden transition-all duration-1000 ' +
        /* Tela cheia: altura da viewport menos o header (~5rem); conteúdo centralizado */
        'flex flex-col justify-center min-h-[calc(100svh-5rem)] py-10 sm:py-12 ' +
        (!imagemFundoCarrossel ? 'bg-gradient-to-br from-slate-700 via-slate-600 to-slate-800' : '')
      }
    >
      {/* Camada de fundo do carrossel (preenche o bloco em tela cheia) */}
      {imagemFundoCarrossel && (
        <div
          aria-hidden
          className="absolute inset-0 z-0 pointer-events-none"
          style={{
            /* Overlay neutro (escuro) para o texto continuar legível sem tingir tudo de azul */
            backgroundImage: `linear-gradient(rgba(15, 23, 42, 0.45), rgba(30, 41, 59, 0.55)), url(${imagemFundoCarrossel})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
          }}
        />
      )}

      {/* Decoração de fundo */}
      <div className="absolute inset-0 z-[1] bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE0YzMuMzEgMCA2LTIuNjkgNi02cy0yLjY5LTYtNi02LTYgMi42OS02IDYgMi42OSA2IDYgNnptMC0xMGMyLjIxIDAgNCAxLjc5IDQgNHMtMS43OSA0LTQgNC00LTEuNzktNC00IDEuNzktNCA0LTR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20 pointer-events-none"></div>

      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-[2]">
        <div className="max-w-2xl">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6 text-white leading-tight drop-shadow-lg">
            {titulo}
          </h1>
          <p className="text-base sm:text-lg text-white/90 mb-6 sm:mb-8 drop-shadow">{subtitulo}</p>
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
              className="inline-block text-center bg-white/15 backdrop-blur-sm text-white border-2 border-white/40 px-6 py-3 rounded-lg hover:bg-white/25 transition-all font-medium shadow-lg"
            >
              Fazer Cadastro
            </Link>
          </div>
        </div>
      </div>

      {/* Indicadores do carrossel de fundo */}
      {temCarrossel && heroImagens.length > 1 && (
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
