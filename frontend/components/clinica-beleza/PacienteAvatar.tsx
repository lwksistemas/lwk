"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
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
  const url = (fotoUrl || "").trim();
  const [quebrada, setQuebrada] = useState(false);
  useEffect(() => {
    setQuebrada(false);
  }, [url]);
  const mostrarFoto = Boolean(url) && !quebrada;
  const alt = name ? `Foto de ${name}` : "Foto do cliente";
  const ancoraRef = useRef<HTMLDivElement>(null);
  const [ampliada, setAmpliada] = useState<{ top: number; left: number } | null>(null);

  function posicionarAmpliacao() {
    const el = ancoraRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const margem = 8;
    const largura = 280;
    let left = rect.right + 10;
    if (left + largura > window.innerWidth - margem) {
      left = rect.left - largura - 10;
    }
    left = Math.max(margem, Math.min(left, window.innerWidth - largura - margem));
    const top = Math.max(margem, Math.min(rect.top, window.innerHeight - margem - 80));
    setAmpliada({ top, left });
  }

  return (
    <div
      ref={ancoraRef}
      className={`${SIZE_CLASS[size]} rounded-full border border-gray-200 dark:border-neutral-600 overflow-hidden bg-gray-50 dark:bg-neutral-800 flex items-center justify-center shrink-0 ${mostrarFoto ? "cursor-zoom-in" : ""} ${className}`}
      onMouseEnter={() => {
        if (mostrarFoto) posicionarAmpliacao();
      }}
      onMouseLeave={() => setAmpliada(null)}
    >
      {mostrarFoto ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url}
          alt={alt}
          className="w-full h-full object-cover"
          referrerPolicy="no-referrer"
          onError={() => {
            setQuebrada(true);
            setAmpliada(null);
          }}
        />
      ) : (
        <User size={ICON_SIZE[size]} className="text-gray-300 dark:text-neutral-600" />
      )}
      {ampliada && mostrarFoto
        ? createPortal(
            <div
              className="pointer-events-none fixed z-[80] rounded-lg border border-gray-200 bg-white p-1 shadow-xl dark:border-neutral-600 dark:bg-neutral-900"
              style={{ top: ampliada.top, left: ampliada.left }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={url}
                alt=""
                className="block h-auto w-auto max-h-[min(70vh,420px)] max-w-[min(70vw,280px)] rounded-md object-contain"
                referrerPolicy="no-referrer"
              />
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
