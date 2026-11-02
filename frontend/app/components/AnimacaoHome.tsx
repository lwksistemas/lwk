"use client";

import { useEffect, useLayoutEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  CHAVE_PREVER_ANIMACOES,
  type ItemAnimacao,
  type ItemImagem,
  normalizarAnimacoes,
} from "@/lib/animacoes-home";

const FINAL = { opacity: 1, x: 0, y: 0, scale: 1, clipPath: "inset(0 0% 0 0)" };

function estadoInicial(item: ItemAnimacao) {
  if (item.efeito === "zoom") return { opacity: 0, scale: 0.96 };
  if (item.efeito === "slide" && item.direcao === "vertical") return { opacity: 0, y: 16 };
  if (item.efeito === "slide") return { opacity: 0, x: 24 };
  if (item.efeito === "scroll") return { opacity: 0, y: 18 };
  if (item.efeito === "reveal") return { clipPath: "inset(0 100% 0 0)" };
  return { opacity: 0 };
}

function transicao(item: ItemAnimacao) {
  return {
    duration: item.duracao / 1000,
    delay: item.atraso / 1000,
    ease: "easeOut" as const,
    repeat: item.repetir ? Infinity : 0,
    repeatType: "reverse" as const,
  };
}

function pulaEfeito(item: { ativo: boolean; celular: boolean }, telaCelular: boolean, reduzido: boolean | null) {
  return reduzido !== false || !item.ativo || (telaCelular && !item.celular);
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
  return { dispositivo, celular, prever: rascunho != null };
}

function Digitando({
  texto,
  item,
  className,
  esperaInicial,
}: {
  texto: string;
  item: ItemAnimacao;
  className?: string;
  esperaInicial?: number;
}) {
  const [qtd, setQtd] = useState(0);

  useLayoutEffect(() => {
    if (!texto) return;
    let cancelado = false;
    let quadro = 0;
    let espera = 0;
    let primeira = true;
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
      const pausa = primeira ? (esperaInicial ?? item.atraso) : item.atraso;
      primeira = false;
      espera = window.setTimeout(comecar, pausa);
    };
    ciclo();
    return () => {
      cancelado = true;
      cancelAnimationFrame(quadro);
      window.clearTimeout(espera);
    };
  }, [texto, item.duracao, item.atraso, item.repetir, esperaInicial]);

  return (
    <span className={`relative block ${className || ""}`}>
      <span className="invisible">{texto}</span>
      <span className="absolute inset-0 overflow-hidden" aria-hidden="true">{texto.slice(0, qtd)}</span>
    </span>
  );
}

export function TextoAnimado({
  texto,
  item,
  className,
  telaCelular = false,
  esperaInicial,
  children,
}: {
  texto?: string;
  item: ItemAnimacao;
  className?: string;
  telaCelular?: boolean;
  esperaInicial?: number;
  children?: React.ReactNode;
}) {
  const reduzido = useReducedMotion();
  const efeito = item.efeito === "typing" && children ? "reveal" : item.efeito;
  const conteudo = children ?? texto;
  if (pulaEfeito(item, telaCelular, reduzido) || efeito === "nenhuma") {
    return <span className={className}>{conteudo}</span>;
  }
  if (efeito === "typing" && texto) {
    return <Digitando texto={texto} item={item} className={className} esperaInicial={esperaInicial} />;
  }
  const alvo = { ...item, efeito };
  if (efeito === "scroll") {
    return (
      <motion.span
        className={`block ${className || ""}`}
        initial={estadoInicial(alvo)}
        whileInView={FINAL}
        viewport={{ once: !item.repetir, amount: 0.25 }}
        transition={transicao(alvo)}
      >
        {conteudo}
      </motion.span>
    );
  }
  return (
    <motion.span className={className} initial={estadoInicial(alvo)} animate={FINAL} transition={transicao(alvo)}>
      {conteudo}
    </motion.span>
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
  const { dispositivo, celular } = useAnimacaoPublica(animacoes);
  const item = dispositivo.secoes;
  const reduzido = useReducedMotion();
  if (pulaEfeito(item, celular, reduzido) || item.efeito === "nenhuma") {
    return <section id={id} className={className}>{children}</section>;
  }
  return (
    <motion.section
      id={id}
      className={className}
      initial={estadoInicial(item.efeito === "typing" ? { ...item, efeito: "reveal" } : item)}
      whileInView={FINAL}
      viewport={{ once: !item.repetir, amount: 0.15 }}
      transition={transicao(item)}
    >
      {children}
    </motion.section>
  );
}

export function ImagemAnimada({
  item,
  reduzido,
  celular,
  className,
  ...rest
}: {
  item: ItemImagem;
  reduzido: boolean;
  celular: boolean;
  className?: string;
} & React.ImgHTMLAttributes<HTMLImageElement>) {
  const pular = reduzido || !item.ativo || item.transicao === "nenhuma" || (celular && !item.celular);
  if (pular) return <img className={className} {...rest} />;
  const initial = item.transicao === "slide" ? { opacity: 0, x: 24 } : item.transicao === "zoom" ? { opacity: 0, scale: 1.03 } : { opacity: 0.45 };
  return (
    <motion.img
      className={className}
      initial={initial}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{ duration: item.duracao / 1000, delay: item.atraso / 1000, ease: "easeOut" }}
      {...rest}
    />
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
      Pré-visualização neste navegador. Use Salvar e publicar para aparecer no site.
    </div>
  );
}
