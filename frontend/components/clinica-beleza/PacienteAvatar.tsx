"use client";

import { User } from "lucide-react";

const SIZE_CLASS = {
  sm: "w-8 h-8",
  md: "w-10 h-10",
  lg: "w-14 h-14",
} as const;

const ICON_SIZE = {
  sm: 14,
  md: 18,
  lg: 24,
} as const;

interface PacienteAvatarProps {
  fotoUrl?: string | null;
  name?: string;
  size?: keyof typeof SIZE_CLASS;
  className?: string;
}

/** Avatar circular do cliente — listagem, consulta, etc. */
export function PacienteAvatar({
  fotoUrl,
  name,
  size = "md",
  className = "",
}: PacienteAvatarProps) {
  const alt = name ? `Foto de ${name}` : "Foto do cliente";

  return (
    <div
      className={`${SIZE_CLASS[size]} rounded-full border border-gray-200 dark:border-neutral-600 overflow-hidden bg-gray-50 dark:bg-neutral-800 flex items-center justify-center shrink-0 ${className}`}
    >
      {fotoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={fotoUrl} alt={alt} className="w-full h-full object-cover" />
      ) : (
        <User size={ICON_SIZE[size]} className="text-gray-300 dark:text-neutral-600" />
      )}
    </div>
  );
}
