'use client';

import { useEffect } from 'react';
import {
  getLoginBackgroundFallbackColor,
  preloadLoginBackground,
} from '@/lib/login-default-backgrounds';

interface LoginBackgroundLayerProps {
  imageUrl: string;
  /** Cor sólida instantânea; se omitida, inferida pela URL do fundo padrão */
  fallbackColor?: string;
}

/** Fundo full-screen da tela de login (foto + overlay para legibilidade do card). */
export function LoginBackgroundLayer({ imageUrl, fallbackColor }: LoginBackgroundLayerProps) {
  useEffect(() => {
    if (imageUrl) preloadLoginBackground(imageUrl);
  }, [imageUrl]);

  if (!imageUrl) return null;

  const bgFallback = fallbackColor ?? getLoginBackgroundFallbackColor(imageUrl);

  return (
    <>
      <div className="absolute inset-0" style={{ backgroundColor: bgFallback }} aria-hidden />
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${imageUrl})` }}
        aria-hidden
      />
      <div className="absolute inset-0 bg-gradient-to-br from-black/50 via-black/35 to-black/55" aria-hidden />
    </>
  );
}
