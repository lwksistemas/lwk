"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  CHAVE_PREVER_ANIMACOES,
  type ItemAnimacao,
  normalizarAnimacoes,
  estiloEfeito,
  estiloEntrada,
} from "@/lib/animacoes-home";

function movimentoReduzido() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function useAnimacaoPublica(bruto: unknown) {
  const [rascunho, setRascunho] = useState<unknown>(null);
  const [celular, setCelular] = useState(false);

  useEffect(() => {
    const tela = window.matchMedia("(max-width: 1023px)");
    const aplicar = () => setCelular(tela.matches);
    aplicar();
    tela.addEventListener("change", aplicar);
    if (new URLSearchParams(window.location.search).get("prever") === "1") {
      try {
        const salvo = localStorage.getItem(CHAVE_PREVER_ANIMACOES);
        if (salvo) setRascunho(JSON.parse(salvo));
      } catch {
        /* rascunho inválido fica de fora */
      }
    }
    return () => tela.removeEventListener("change", aplicar);
  }, []);

  const config = normalizarAnimacoes(rascunho ?? bruto);
  const dispositivo = !config.igual_celular && celular ? config.celular : config.computador;
  return { dispositivo, prever: rascunho != null };
}

function Digitando({ texto, item, className }: { texto: string; item: ItemAnimacao; className?: string }) {
  const [qtd, setQtd] = useState(texto.length);

  useLayoutEffect(() => {
    if (!texto || movimentoReduzido()) {
      setQtd(texto.length);
      return;
    }
    let cancelado = false;
    let quadro = 0;
    let espera = 0;
    const ciclo = () => {
      setQtd(0);
      const comecar = () => {
        const inicio = performance.now();
        const passo = (agora: number) => {
          if (cancelado) return;
          const feito = Math.min(texto.length, Math.round(((agora - inicio) / Math.max(item.duracao, 200)) * texto.length));
          setQtd(feito);
          if (feito < texto.length) quadro = requestAnimationFrame(passo);
          else if (item.repetir) espera = window.setTimeout(ciclo, 700);
        };
        quadro = requestAnimationFrame(passo);
      };
      espera = window.setTimeout(comecar, item.atraso);
    };
    ciclo();
    return () => {
      cancelado = true;
      cancelAnimationFrame(quadro);
      window.clearTimeout(espera);
    };
  }, [texto, item.duracao, item.atraso, item.repetir]);

  return (
    <span className={`relative block ${className || ""}`} aria-label={texto}>
      <span className="invisible">{texto}</span>
      <span className="absolute inset-0 overflow-hidden" aria-hidden="true">{texto.slice(0, qtd)}</span>
    </span>
  );
}

function Entrada({ item, reduzido, className, texto, children }: {
  item: ItemAnimacao;
  reduzido: boolean;
  className?: string;
  texto?: string;
  children?: React.ReactNode;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const [visivel, setVisivel] = useState(true);

  useLayoutEffect(() => {
    if (movimentoReduzido() || reduzido || !item.ativo || item.efeito === "nenhuma") {
      setVisivel(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    setVisivel(false);
    const obs = new IntersectionObserver(([entrada]) => {
      if (entrada.isIntersecting) {
        setVisivel(true);
        if (!item.repetir) obs.disconnect();
      } else if (item.repetir) {
        setVisivel(false);
      }
    }, { threshold: 0.2 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [item.ativo, item.efeito, item.repetir, item.duracao, item.atraso, item.direcao, reduzido]);

  return (
    <span ref={ref} className={`lwk-animar block ${className || ""}`} style={estiloEntrada(item, visivel, reduzido || movimentoReduzido())}>
      {children ?? texto}
    </span>
  );
}

export function TextoAnimado({
  texto,
  item,
  reduzido,
  className,
  children,
}: {
  texto?: string;
  item: ItemAnimacao;
  reduzido: boolean;
  className?: string;
  children?: React.ReactNode;
}) {
  const efeito = item.efeito === "typing" && children ? "reveal" : item.efeito;
  if (reduzido || !item.ativo || efeito === "nenhuma") {
    return <span className={className}>{children ?? texto}</span>;
  }
  if (efeito === "typing" && texto) {
    return <Digitando texto={texto} item={item} className={className} />;
  }
  if (efeito === "scroll") {
    return <Entrada item={{ ...item, efeito }} reduzido={reduzido} className={className} texto={texto}>{children}</Entrada>;
  }
  return (
    <span className={`lwk-animar ${className || ""}`} style={estiloEfeito({ ...item, efeito }, reduzido)}>
      {children ?? texto}
    </span>
  );
}

export function BlocoHome({
  id,
  className,
  animacoes,
  children,
}: {
  id?: string;
  className?: string;
  animacoes?: unknown;
  children: React.ReactNode;
}) {
  const { dispositivo } = useAnimacaoPublica(animacoes);
  const item = dispositivo.secoes;
  const ref = useRef<HTMLElement>(null);
  const [visivel, setVisivel] = useState(true);

  useLayoutEffect(() => {
    if (movimentoReduzido() || !item.ativo || item.efeito === "nenhuma") {
      setVisivel(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    setVisivel(false);
    const obs = new IntersectionObserver(([entrada]) => {
      if (entrada.isIntersecting) {
        setVisivel(true);
        if (!item.repetir) obs.disconnect();
      } else if (item.repetir) {
        setVisivel(false);
      }
    }, { threshold: 0.15 });
    obs.observe(el);
    return () => obs.disconnect();
  }, [item.ativo, item.efeito, item.repetir, item.duracao, item.atraso, item.direcao]);

  return (
    <section id={id} ref={ref} className={className} style={estiloEntrada(item, visivel, movimentoReduzido())}>
      {children}
    </section>
  );
}

export function FaixaPrever() {
  const [ativa, setAtiva] = useState(false);
  useEffect(() => {
    setAtiva(new URLSearchParams(window.location.search).get("prever") === "1");
  }, []);
  if (!ativa) return null;
  return (
    <div className="fixed bottom-4 left-1/2 z-50 max-w-[92vw] -translate-x-1/2 rounded-full bg-white px-4 py-2 text-center text-sm font-medium text-slate-900 shadow-lg">
      Pré-visualização neste navegador. Salve na aba Animações para publicar.
    </div>
  );
}
