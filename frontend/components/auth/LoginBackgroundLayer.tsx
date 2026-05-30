'use client';

interface LoginBackgroundLayerProps {
  imageUrl: string;
}

/** Fundo full-screen da tela de login (foto + overlay para legibilidade do card). */
export function LoginBackgroundLayer({ imageUrl }: LoginBackgroundLayerProps) {
  if (!imageUrl) return null;

  return (
    <>
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${imageUrl})` }}
        aria-hidden
      />
      <div className="absolute inset-0 bg-gradient-to-br from-black/50 via-black/35 to-black/55" aria-hidden />
    </>
  );
}
