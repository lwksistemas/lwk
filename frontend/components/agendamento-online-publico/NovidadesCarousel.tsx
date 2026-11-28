"use client";

import { useEffect, useState } from "react";
import { CalendarCheck, ChevronLeft, ChevronRight, Megaphone } from "lucide-react";
import type { Novidade } from "@/lib/clinica-beleza-api/novidades";
import { formatarPrecoBRL } from "@/lib/agendamento-online-format";

type Props = {
  itens: Novidade[];
  intervaloSegundos?: number;
  primary: string;
  onAgendar?: () => void;
  className?: string;
};

export function NovidadesCarousel({
  itens,
  intervaloSegundos = 5,
  primary,
  onAgendar,
  className = "",
}: Props) {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    setIdx(0);
  }, [itens.length]);

  useEffect(() => {
    if (itens.length <= 1) return;
    const ms = Math.max(3, Math.min(30, intervaloSegundos)) * 1000;
    const t = window.setInterval(() => {
      setIdx((i) => (i + 1) % itens.length);
    }, ms);
    return () => window.clearInterval(t);
  }, [itens.length, intervaloSegundos]);

  if (!itens.length) return null;

  const item = itens[idx] || itens[0];
  const ir = (delta: number) => {
    setIdx((i) => (i + delta + itens.length) % itens.length);
  };

  const handleCta = () => {
    if (item.botao_url) {
      window.open(item.botao_url, "_blank", "noopener,noreferrer");
      return;
    }
    onAgendar?.();
  };

  return (
    <div className={`relative flex h-full min-h-[420px] flex-col overflow-hidden rounded-[1.5rem] text-white shadow-lg ${className}`}>
      {item.imagem_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={item.imagem_url} alt="" className="absolute inset-0 h-full w-full object-cover" />
      ) : null}
      <div
        className="absolute inset-0"
        style={{
          background: item.imagem_url
            ? `linear-gradient(120deg, color-mix(in srgb, ${primary} 88%, #4a044e) 0%, color-mix(in srgb, ${primary} 55%, transparent) 55%, transparent 100%)`
            : `linear-gradient(145deg, ${primary}, color-mix(in srgb, ${primary} 70%, #831843))`,
        }}
      />

      <div className="relative z-[1] flex flex-1 flex-col justify-between p-5 sm:p-7">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide backdrop-blur">
            <Megaphone className="h-3.5 w-3.5" />
            {item.selo || "Novidades"}
          </span>
          <h3 className="mt-4 text-2xl font-bold leading-tight sm:text-3xl">{item.titulo}</h3>
          {item.descricao ? (
            <p className="mt-2 max-w-md text-sm leading-relaxed text-white/90 sm:text-base">{item.descricao}</p>
          ) : null}

          {item.beneficios?.length ? (
            <ul className="mt-4 space-y-1.5 text-sm text-white/95">
              {item.beneficios.slice(0, 4).map((b) => (
                <li key={b} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-300" />
                  {b}
                </li>
              ))}
            </ul>
          ) : null}

          {(item.condicao_especial || item.preco_por || item.preco_de) ? (
            <div className="mt-5 inline-block rounded-2xl border-2 border-amber-300/80 bg-black/20 px-4 py-3 backdrop-blur-sm">
              {item.condicao_especial ? (
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-200">
                  {item.condicao_especial}
                </p>
              ) : (
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-200">Condição especial</p>
              )}
              <p className="mt-1 text-lg font-bold text-amber-100">
                {item.preco_de ? (
                  <span className="mr-2 text-sm font-medium text-white/60 line-through">
                    {formatarPrecoBRL(item.preco_de)}
                  </span>
                ) : null}
                {item.preco_por ? formatarPrecoBRL(item.preco_por) : null}
              </p>
            </div>
          ) : null}
        </div>

        <div className="mt-6">
          <button
            type="button"
            onClick={handleCta}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full bg-white px-5 text-sm font-semibold shadow transition hover:bg-pink-50"
            style={{ color: primary }}
          >
            <CalendarCheck className="h-4 w-4" />
            {item.botao_texto || "Agende agora"}
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {itens.length > 1 ? (
        <>
          <button
            type="button"
            aria-label="Anterior"
            onClick={() => ir(-1)}
            className="absolute left-3 top-1/2 z-[2] flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/25 text-white backdrop-blur hover:bg-white/40"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            type="button"
            aria-label="Próximo"
            onClick={() => ir(1)}
            className="absolute right-3 top-1/2 z-[2] flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/25 text-white backdrop-blur hover:bg-white/40"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
          <div className="absolute bottom-4 left-0 right-0 z-[2] flex justify-center gap-1.5">
            {itens.map((n, i) => (
              <button
                key={n.id}
                type="button"
                aria-label={`Slide ${i + 1}`}
                onClick={() => setIdx(i)}
                className={`h-2 rounded-full transition-all ${i === idx ? "w-6 bg-white" : "w-2 bg-white/40"}`}
              />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
