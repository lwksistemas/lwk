'use client';

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

export default function Hero({ hero: _hero, heroImagens = [] }: HeroProps) {
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
        "min-h-[calc(100svh-5rem)] " +
        "bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700"
      }
      aria-label="Banner principal"
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
              alt={img.titulo || ""}
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

      {temCarrossel && imagens.length > 1 && (
        <div className="absolute bottom-4 left-1/2 z-20 flex -translate-x-1/2 gap-2">
          {imagens.map((_, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setCurrentImageIndex(index)}
              className={`h-2 w-2 rounded-full transition-all ${
                index === currentImageIndex
                  ? "w-8 bg-white"
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
