'use client';

import { useEffect, useState } from 'react';
import {
  getLoginBackgroundFallbackColor,
  preloadImageUrl,
  preloadLoginBackground,
} from '@/lib/login-default-backgrounds';

interface LoginBackgroundLayerProps {
  imageUrl: string;
  /** Cor sólida instantânea; se omitida, inferida pela URL do fundo padrão */
  fallbackColor?: string;
}

/** Fundo full-screen da tela de login (foto + overlay para legibilidade do card). */
export function LoginBackgroundLayer({ imageUrl, fallbackColor }: LoginBackgroundLayerProps) {
  const [displayUrl, setDisplayUrl] = useState(imageUrl);

  useEffect(() => {
    if (!imageUrl) return;
    if (imageUrl === displayUrl) {
      preloadLoginBackground(imageUrl);
      return;
    }
    let cancelled = false;
    preloadImageUrl(imageUrl).then(() => {
      if (!cancelled) setDisplayUrl(imageUrl);
    });
    return () => {
      cancelled = true;
    };
  }, [imageUrl, displayUrl]);

  if (!displayUrl) return null;

  const bgFallback = fallbackColor ?? getLoginBackgroundFallbackColor(displayUrl);

  return (
    <>
      <div className="absolute inset-0" style={{ backgroundColor: bgFallback }} aria-hidden />
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-200"
        style={{ backgroundImage: `url(${displayUrl})` }}
        aria-hidden
      />
      <div className="absolute inset-0 bg-gradient-to-br from-black/50 via-black/35 to-black/55" aria-hidden />
    </>
  );
}
