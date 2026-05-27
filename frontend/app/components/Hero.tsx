'use client';

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import type { Hero as HeroType } from "@/types/homepage";

interface HeroProps {
  hero: HeroType | null;
  heroImagens?: Array<{ id: number; imagem: string; titulo: string }>;
}

export default function Hero({ hero, heroImagens = [] }: HeroProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imagesLoaded, setImagesLoaded] = useState<Set<number>>(new Set());

  const titulo = hero?.titulo ?? "Controle total da sua empresa em um único sistema";
  const subtitulo =
    hero?.subtitulo ??
    "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.";
  const botaoTexto = hero?.botao_texto ?? "Testar Gratuitamente";
  const mostrarBotaoPrincipal = hero?.botao_principal_ativo !== false;

  const temCarrossel = heroImagens.length > 0;

  // Rotação automática do carrossel
  useEffect(() => {
    if (heroImagens.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % heroImagens.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [heroImagens.length]);

  const handleImageLoad = (index: number) => {
    setImagesLoaded((prev) => new Set(prev).add(index));
  };

  return (
    <section
      className={
        'w-full min-w-full relative overflow-hidden ' +
        'flex flex-col justify-center min-h-[calc(100svh-5rem)] py-10 sm:py-12 ' +
        'bg-gradient-to-br from-slate-700 via-slate-600 to-slate-800'
      }
    >
      {/* Imagens do carrossel usando next/image para otimização */}
      {temCarrossel && heroImagens.map((img, index) => (
        <div
          key={img.id}
          className={`absolute inset-0 z-0 transition-opacity duration-1000 ${
            index === currentImageIndex ? 'opacity-100' : 'opacity-0'
          }`}
          aria-hidden
        >
          <Image
            src={img.imagem}
            alt={img.titulo || 'Imagem de fundo'}
            fill
            className="object-cover"
            sizes="100vw"
            priority={index === 0}
            quality={80}
            onLoad={() => handleImageLoad(index)}
          />
        </div>
      ))}

      {/* Decoração de fundo */}
      <div className="absolute inset-0 z-[1] bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE0YzMuMzEgMCA2LTIuNjkgNi02cy0yLjY5LTYtNi02LTYgMi42OS02IDYgMi42OSA2IDYgNnptMC0xMGMyLjIxIDAgNCAxLjc5IDQgNHMtMS43OSA0LTQgNC00LTEuNzktNC00IDEuNzktNCA0LTR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20 pointer-events-none"></div>

      {/* Indicadores do carrossel */}
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
