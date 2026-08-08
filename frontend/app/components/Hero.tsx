'use client';

import Link from "next/link";
import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import type { Hero as HeroType } from "@/types/homepage";

interface HeroProps {
  hero: HeroType | null;
  heroImagens?: Array<{ id: number; imagem: string; titulo: string }>;
}

const ALLOWED_IMAGE_HOSTS = new Set([
  "media.lwksistemas.com.br",
  "api.lwksistemas.com.br",
  "i.pravatar.cc",
  "localhost",
]);

function isUsableHeroImage(url: string): boolean {
  if (!url || !url.startsWith("http")) return false;
  try {
    const host = new URL(url).hostname.toLowerCase();
    if (host.includes("cloudinary.com") || host.includes("res.cloudinary")) {
      return false;
    }
    return ALLOWED_IMAGE_HOSTS.has(host);
  } catch {
    return false;
  }
}

export default function Hero({ hero, heroImagens = [] }: HeroProps) {
  const imagensValidas = useMemo(
    () => (heroImagens || []).filter((img) => isUsableHeroImage(img.imagem)),
    [heroImagens]
  );

  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [failedIds, setFailedIds] = useState<Set<number>>(new Set());

  const imagens = useMemo(
    () => imagensValidas.filter((img) => !failedIds.has(img.id)),
    [imagensValidas, failedIds]
  );

  const titulo = hero?.titulo ?? "Controle total da sua empresa em um único sistema";
  const subtitulo =
    hero?.subtitulo ??
    "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.";
  const botaoTexto = hero?.botao_texto ?? "Testar Gratuitamente";
  const mostrarBotaoPrincipal = hero?.botao_principal_ativo !== false;

  const temCarrossel = imagens.length > 0;

  useEffect(() => {
    setCurrentImageIndex(0);
  }, [imagens.length]);

  useEffect(() => {
    if (imagens.length <= 1) return;
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % imagens.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [imagens.length]);

  return (
    <section
      className={
        "w-full min-w-full relative overflow-hidden " +
        "flex flex-col justify-center min-h-[calc(100svh-5rem)] py-10 sm:py-12 " +
        "bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700"
      }
    >
      {temCarrossel &&
        imagens.map((img, index) => (
          <div
            key={img.id}
            className={`absolute inset-0 z-0 transition-opacity duration-1000 ${
              index === currentImageIndex ? "opacity-100" : "opacity-0"
            }`}
            aria-hidden
          >
            <Image
              src={img.imagem}
              alt=""
              fill
              className="object-cover"
              sizes="100vw"
              priority={index === 0}
              quality={80}
              onError={() =>
                setFailedIds((prev) => {
                  const next = new Set(prev);
                  next.add(img.id);
                  return next;
                })
              }
            />
          </div>
        ))}

      {/* Overlay para legibilidade do texto */}
      <div className="absolute inset-0 z-[1] bg-gradient-to-br from-blue-900/75 via-blue-800/65 to-indigo-900/75 pointer-events-none" />

      <div className="absolute inset-0 z-[1] bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE0YzMuMzEgMCA2LTIuNjkgNi02cy0yLjY5LTYtNi02LTYgMi42OS02IDYgMi42OSA2IDYgNnptMC0xMGMyLjIxIDAgNCAxLjc5IDQgNHMtMS43OSA0LTQgNC00LTEuNzktNC00IDEuNzktNCA0LTR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-20 pointer-events-none" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4 sm:mb-6 text-white leading-tight drop-shadow-lg">
            {titulo}
          </h1>
          <p className="text-base sm:text-lg text-blue-50 mb-6 sm:mb-8 drop-shadow max-w-2xl">
            {subtitulo}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            {mostrarBotaoPrincipal && (
              <Link
                href="/cadastro"
                className="inline-block text-center bg-white text-blue-700 px-6 py-3 rounded-lg hover:bg-blue-50 transition-all font-medium shadow-lg hover:shadow-xl"
              >
                {botaoTexto}
              </Link>
            )}
            <Link
              href="/#modulos"
              className="inline-block text-center bg-blue-700/40 backdrop-blur-sm text-white border-2 border-white/35 px-6 py-3 rounded-lg hover:bg-blue-700/60 transition-all font-medium shadow-lg"
            >
              Ver planos e valores
            </Link>
          </div>
        </div>
      </div>

      {temCarrossel && imagens.length > 1 && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2 z-20">
          {imagens.map((_, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setCurrentImageIndex(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentImageIndex
                  ? "bg-white w-8"
                  : "bg-white/50 hover:bg-white/75"
              }`}
              aria-label={`Ir para imagem ${index + 1}`}
            />
          ))}
        </div>
      )}
    </section>
  );
}
