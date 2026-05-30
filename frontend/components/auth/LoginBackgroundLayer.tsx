'use client';

import { useEffect } from 'react';
import { preloadLoginBackground } from '@/lib/login-default-backgrounds';

interface LoginBackgroundLayerProps {
  imageUrl: string;
}

/** Fundo full-screen da tela de login (foto + overlay para legibilidade do card). */
export function LoginBackgroundLayer({ imageUrl }: LoginBackgroundLayerProps) {
  useEffect(() => {
    if (imageUrl) preloadLoginBackground(imageUrl);
  }, [imageUrl]);

  if (!imageUrl) return null;

  return (
    <>
      {/* Cor de fallback enquanto o JPEG progresivo carrega */}
      <div className="absolute inset-0 bg-[#3d1a24]" aria-hidden />
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${imageUrl})` }}
        aria-hidden
      />
      <div className="absolute inset-0 bg-gradient-to-br from-black/50 via-black/35 to-black/55" aria-hidden />
    </>
  );
}
