'use client';

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { Calendar, ChevronLeft, ChevronRight, Code2, Pause, Play, UserRound, Users } from "lucide-react";
import type { Funcionalidade, Hero as HeroType, HeroImagem } from "@/types/homepage";

interface HeroProps {
  hero: HeroType | null;
  heroImagens?: HeroImagem[];
  destaques?: Funcionalidade[];
}

type Slide = {
  id: number;
  titulo: string;
  descricao: string;
  link?: string;
  imagem?: string;
  tipo: "crm" | "clinica" | "imagem";
  inteiro?: boolean;
};

const TEXTO = {
  selo: "Software House",
  titulo: "Soluções de software",
  destaque: "para sua empresa.",
  subtitulo:
    "Desenvolvemos sistemas e soluções personalizadas para clínicas de estética, CRM de vendas e diversos outros segmentos, com tecnologia, segurança e suporte especializado.",
  botao: "Solicite uma demonstração",
  botaoUrl: "/demonstracao",
  botao2: "Conheça nossas soluções",
  botao2Url: "#solucoes",
};

function IconeDoBotao({ texto }: { texto: string }) {
  if (texto.toLowerCase().includes("demonstr")) {
    return <Calendar className="h-4 w-4" aria-hidden />;
  }
  return <Play className="h-4 w-4 fill-current" aria-hidden />;
}

const LINK_CARTAO: Record<string, string> = {
  "Clínicas de Estética": "/solucoes/clinicas-estetica",
  "CRM de Vendas": "/solucoes/crm-vendas",
  "CRM Vendas": "/solucoes/crm-vendas",
  "Sistemas Personalizados": "/solucoes/personalizados",
  "Todos os Segmentos": "/segmentos",
};

function IconeRosto() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12 shrink-0 text-cyan-300" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M30 14c-1-6-8-8-12-4-3 3-3 8-1 11" strokeLinecap="round" />
      <circle cx="22" cy="18" r="7.5" />
      <path d="M14 17c2-1 4-1 6 0" strokeLinecap="round" />
      <path d="M10 40c1.5-8 6-12 12-12s10.5 4 12 12" strokeLinecap="round" />
    </svg>
  );
}

function IconePessoas() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12 shrink-0 text-cyan-300" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <circle cx="17" cy="16" r="5" />
      <circle cx="31" cy="16" r="5" />
      <path d="M7 38c1-7 5-11 10-11s9 4 10 11" strokeLinecap="round" />
      <path d="M23 38c1-6 4-9 8-9s7 3 8 9" strokeLinecap="round" />
    </svg>
  );
}

function IconeCodigo() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12 shrink-0 text-cyan-300" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M18 14 8 24l10 10" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M30 14 40 24 30 34" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconeLoja() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12 shrink-0 text-cyan-300" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
      <path d="M8 20 13 10h22l5 10" strokeLinejoin="round" />
      <path d="M8 20h32v3c0 2-2 4-4 4s-4-2-4-4c0 2-2 4-4 4s-4-2-4-4c0 2-2 4-4 4s-4-2-4-4c0 2-2 4-4 4s-4-2-4-4v-3Z" strokeLinejoin="round" />
      <path d="M14 27v11h20V27" />
      <path d="M21 38v-7h6v7" />
    </svg>
  );
}

const ICONE_CARTAO = {
  "Clínicas de Estética": IconeRosto,
  "CRM de Vendas": IconePessoas,
  "CRM Vendas": IconePessoas,
  "Sistemas Personalizados": IconeCodigo,
  "Todos os Segmentos": IconeLoja,
} as const;

const QUEBRA_TITULO: Record<string, [string, string]> = {
  "Clínicas de Estética": ["Clínicas de", "Estética"],
  "CRM de Vendas": ["CRM", "Vendas"],
  "CRM Vendas": ["CRM", "Vendas"],
  "Sistemas Personalizados": ["Sistemas", "Personalizados"],
  "Todos os Segmentos": ["Todos os", "Segmentos"],
};

const DESTAQUES_FOTO: Funcionalidade[] = [
  { id: -1, titulo: "Clínicas de Estética", descricao: "Gestão completa da sua clínica", icone: "face", link: "/solucoes/clinicas-estetica" },
  { id: -2, titulo: "CRM Vendas", descricao: "Organize seus leads, vendas e relacionamento", icone: "users", link: "/solucoes/crm-vendas" },
  { id: -3, titulo: "Sistemas Personalizados", descricao: "Soluções sob medida para a sua operação", icone: "code", link: "/solucoes/personalizados" },
  { id: -4, titulo: "Todos os Segmentos", descricao: "Atendemos empresas de diferentes áreas e portes", icone: "store", link: "/segmentos" },
];

const SLIDES_PADRAO: Slide[] = [
  {
    id: -1,
    titulo: "CRM Vendas",
    descricao: "Notebook com o painel do CRM Vendas: receita, leads, pipeline e funil.",
    link: "/solucoes/crm-vendas",
    imagem: "/homepage/crm-tela.webp",
    tipo: "crm",
  },
  {
    id: -2,
    titulo: "Gestão para Clínicas de Estética",
    descricao: "Notebook com o painel da clínica de estética: agenda, faturamento e procedimentos.",
    link: "/solucoes/clinicas-estetica",
    imagem: "/homepage/clinica-tela.webp",
    tipo: "clinica",
  },
];

const ALLOWED_IMAGE_HOSTS = new Set([
  "media.lwksistemas.com.br",
  "api.lwksistemas.com.br",
  "i.pravatar.cc",
  "localhost",
]);

function imagemUsavel(url: string): boolean {
  if (!url) return false;
  if (url.startsWith("/")) return true;
  if (!url.startsWith("http")) return false;
  try {
    return ALLOWED_IMAGE_HOSTS.has(new URL(url).hostname.toLowerCase());
  } catch {
    return false;
  }
}

function TelaCrm() {
  const barras = [46, 62, 40, 78, 55, 88];
  return (
    <div className="flex h-full bg-[#f3f6fb] text-[9px] text-slate-600">
      <aside className="flex w-[23%] flex-col bg-[#0b63ce] px-2 py-2 text-white">
        <p className="mb-2 text-[8px] font-semibold leading-tight">CRM Vendas</p>
        {["Home", "Leads", "Oportunidades", "Empresas", "Contatos"].map((item, i) => (
          <span key={item} className={`mb-1 rounded px-1.5 py-1 ${i === 0 ? "bg-white/20" : ""}`}>{item}</span>
        ))}
      </aside>
      <div className="min-w-0 flex-1 p-2">
        <p className="mb-1.5 text-[11px] font-bold text-slate-800">Home</p>
        <div className="grid grid-cols-3 gap-1">
          {[
            ["Receita do mês", "R$ 18.450"],
            ["Novos leads", "24"],
            ["Conversão", "32%"],
          ].map(([rotulo, valor]) => (
            <div key={rotulo} className="rounded-md bg-white p-1.5 shadow-sm">
              <p className="text-[7px] uppercase tracking-wide text-slate-400">{rotulo}</p>
              <p className="text-[11px] font-bold text-slate-800">{valor}</p>
            </div>
          ))}
        </div>
        <div className="mt-1.5 grid grid-cols-2 gap-1">
          <div className="rounded-md bg-white p-1.5 shadow-sm">
            <p className="mb-1 font-semibold text-slate-700">Pipeline</p>
            <div className="flex h-12 items-end gap-1">
              {barras.map((altura) => (
                <span key={altura} className="flex-1 rounded-sm bg-[#3b82f6]" style={{ height: `${altura}%` }} />
              ))}
            </div>
          </div>
          <div className="rounded-md bg-white p-1.5 shadow-sm">
            <p className="mb-1 font-semibold text-slate-700">Funil</p>
            {[["Proposta", "70%"], ["Negociação", "45%"], ["Fechado", "28%"]].map(([nome, largura]) => (
              <div key={nome} className="mb-1">
                <div className="mb-0.5 flex justify-between text-[7px]"><span>{nome}</span><span>{largura}</span></div>
                <div className="h-1.5 rounded-full bg-slate-100">
                  <div className="h-1.5 rounded-full bg-[#22c55e]" style={{ width: largura }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function TelaClinica() {
  return (
    <div className="flex h-full bg-[#f7f4fb] text-[9px] text-slate-600">
      <aside className="w-[23%] bg-[#7c3aed] px-2 py-2 text-white">
        <p className="mb-2 text-[8px] font-semibold leading-tight">Clínica</p>
        {["Agenda", "Clientes", "Procedimentos", "Estoque", "Financeiro"].map((item, i) => (
          <span key={item} className={`mb-1 block rounded px-1.5 py-1 ${i === 0 ? "bg-white/20" : ""}`}>{item}</span>
        ))}
      </aside>
      <div className="min-w-0 flex-1 p-2">
        <p className="mb-1.5 text-[11px] font-bold text-slate-800">Agenda de hoje</p>
        <div className="space-y-1">
          {[
            ["09:00", "Avaliação"],
            ["10:30", "Procedimento"],
            ["14:00", "Retorno"],
            ["16:15", "Protocolo"],
          ].map(([hora, nome]) => (
            <div key={hora} className="flex items-center gap-2 rounded-md bg-white px-2 py-1 shadow-sm">
              <span className="font-bold text-violet-700">{hora}</span>
              <span>{nome}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Hero({ hero, heroImagens = [], destaques = [] }: HeroProps) {
  const selo = hero?.selo?.trim() || TEXTO.selo;
  const titulo = hero?.titulo?.trim() || TEXTO.titulo;
  const destaque = hero?.titulo_destaque?.trim() || "";
  const subtitulo = hero?.subtitulo?.trim() || TEXTO.subtitulo;
  const botao = hero?.botao_texto?.trim() || TEXTO.botao;
  const botaoUrl = hero?.botao_url?.trim() || TEXTO.botaoUrl;
  const mostraBotao = hero?.botao_principal_ativo !== false;
  const botao2 = hero?.botao_secundario_texto?.trim() || TEXTO.botao2;
  const botao2Url = hero?.botao_secundario_url?.trim() || TEXTO.botao2Url;
  const mostraBotao2 = hero?.botao_secundario_ativo !== false && Boolean(botao2);
  const cards = destaques.length > 0 ? destaques : DESTAQUES_FOTO;
  const intervaloMs = Math.min(30, Math.max(3, hero?.intervalo_carrossel || 5)) * 1000;

  const imagensValidas = useMemo(
    () => (heroImagens || []).filter((img) => imagemUsavel(img.imagem)),
    [heroImagens],
  );
  const [indice, setIndice] = useState(0);
  const [geracao, setGeracao] = useState(0);
  const [falhas, setFalhas] = useState<Set<number>>(new Set());
  const [sobre, setSobre] = useState(false);
  const [pausado, setPausado] = useState(false);
  const [reduzMovimento, setReduzMovimento] = useState(false);
  const toque = useRef<{ x: number; y: number } | null>(null);

  const slides = useMemo<Slide[]>(() => {
    const enviadas = imagensValidas
      .filter((img) => !falhas.has(img.id))
      .map((img) => ({
        id: img.id,
        titulo: img.titulo,
        descricao: img.titulo || "Tela do sistema",
        link: img.link,
        imagem: img.imagem,
        tipo: "imagem" as const,
      }));
    return enviadas.length > 0 ? enviadas : SLIDES_PADRAO;
  }, [imagensValidas, falhas]);

  const atual = slides[indice] ?? slides[0];

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const aplicar = () => setReduzMovimento(media.matches);
    aplicar();
    media.addEventListener("change", aplicar);
    return () => media.removeEventListener("change", aplicar);
  }, []);

  useEffect(() => {
    setIndice(0);
  }, [slides.length]);

  useEffect(() => {
    if (slides.length <= 1 || sobre || pausado || reduzMovimento) return;
    const timer = setInterval(() => {
      setIndice((i) => (i + 1) % slides.length);
    }, intervaloMs);
    return () => clearInterval(timer);
  }, [slides.length, sobre, pausado, reduzMovimento, intervaloMs, geracao]);

  const ir = (delta: number) => {
    if (slides.length <= 1) return;
    setIndice((i) => (i + delta + slides.length) % slides.length);
    setGeracao((valor) => valor + 1);
  };

  const escolher = (proximo: number) => {
    setIndice(proximo);
    setGeracao((valor) => valor + 1);
  };

  const aoToque = (evento: React.TouchEvent) => {
    const ponto = evento.changedTouches[0];
    if (!ponto || !toque.current) return;
    const dx = ponto.clientX - toque.current.x;
    const dy = ponto.clientY - toque.current.y;
    toque.current = null;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy)) ir(dx < 0 ? 1 : -1);
  };

  const tela = atual?.tipo === "clinica" ? <TelaClinica /> : atual?.tipo === "crm" ? <TelaCrm /> : null;

  const falhaImagem = (evento: React.SyntheticEvent<HTMLImageElement>, id: number) => {
    const img = evento.currentTarget;
    if (img.dataset.reserva === "1") {
      setFalhas((prev) => new Set(prev).add(id));
      return;
    }
    if (img.src.includes(".webp")) {
      img.dataset.reserva = "1";
      img.src = img.src.replace(/\.webp(\?.*)?$/, ".png$1");
      return;
    }
    setFalhas((prev) => new Set(prev).add(id));
  };

  const classeTela = `h-full w-full object-contain object-center ${reduzMovimento ? "" : "[animation:lwk-fade_0.45s_ease]"}`;

  return (
    <section className="relative flex min-h-0 flex-1 flex-col text-white" aria-label="Banner principal">
      {slides[0]?.imagem?.startsWith("/") && <link rel="preload" as="image" href={slides[0].imagem} fetchPriority="high" />}
      <div className="relative flex min-h-0 w-full flex-1 flex-col px-4 pb-3 pt-1 sm:px-6 lg:px-8">
        <div className="grid min-h-0 flex-1 items-center gap-6 lg:grid-cols-[minmax(36rem,1fr)_minmax(0,1.05fr)] lg:gap-6">
          <div className="relative z-10 max-w-2xl lg:pl-4">
            <span className="inline-flex items-center gap-2 rounded-full border border-sky-200/40 bg-sky-400/10 px-3 py-1 text-sm text-sky-100">
              <Code2 className="h-4 w-4" aria-hidden />
              {selo}
            </span>
            <h1 className="mt-4 max-w-xl text-[clamp(2.15rem,3.5vw,3.45rem)] font-extrabold leading-[1.05] tracking-tight">
              <span className="block">{titulo}</span>
              {destaque ? <span className="mt-1 block text-[#3ecbff]">{destaque}</span> : null}
            </h1>
            <p className="mt-4 max-w-lg text-[clamp(0.95rem,1.2vw,1.125rem)] leading-relaxed text-slate-200">
              {subtitulo}
            </p>
            <div className="mt-5 flex flex-row flex-wrap items-center gap-3 sm:flex-nowrap sm:gap-4">
              {mostraBotao && (
                <a
                  href={botaoUrl}
                  className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full bg-[#2f6bff] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-950/40 transition hover:bg-[#3b78ff] sm:text-base"
                >
                  <IconeDoBotao texto={botao} />
                  {botao}
                </a>
              )}
              {mostraBotao2 && (
                <a
                  href={botao2Url}
                  className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-white/40 bg-[#0c2758]/80 px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#14336e] sm:text-base"
                >
                  <IconeDoBotao texto={botao2} />
                  {botao2}
                </a>
              )}
            </div>
          </div>

          <div
            className="relative flex h-full min-h-[240px] w-full flex-col items-center justify-center outline-none focus-visible:ring-2 focus-visible:ring-white/70"
            role="region"
            aria-roledescription="carrossel"
            aria-label="Demonstração dos sistemas"
            tabIndex={0}
            onKeyDown={(evento) => {
              if (evento.key === "ArrowLeft") {
                evento.preventDefault();
                ir(-1);
              } else if (evento.key === "ArrowRight") {
                evento.preventDefault();
                ir(1);
              }
            }}
            onMouseEnter={() => setSobre(true)}
            onMouseLeave={() => setSobre(false)}
          >
            <p className="sr-only" aria-live="polite">
              {atual ? `${atual.titulo}. ${atual.descricao} Imagem ${indice + 1} de ${slides.length}.` : ""}
            </p>
            <button
              type="button"
              onClick={() => ir(-1)}
              className="absolute left-0 top-[42%] z-10 flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-[#12315f]/90 text-white shadow-lg hover:bg-[#1a4180] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              aria-label="Imagem anterior"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={() => ir(1)}
              className="absolute right-0 top-[42%] z-10 flex h-11 w-11 translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-[#12315f]/90 text-white shadow-lg hover:bg-[#1a4180] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              aria-label="Próxima imagem"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            {atual?.inteiro && atual.imagem ? (
              <a href={atual.link || "#solucoes"} className="relative block h-full min-h-[240px]" aria-label={atual.titulo || "Abrir o sistema"}>
                <Image
                  src={atual.imagem}
                  alt={atual.titulo || "Notebook com o CRM Vendas"}
                  fill
                  priority
                  sizes="(min-width: 1024px) 54vw, 100vw"
                  className="object-contain object-center"
                />
              </a>
            ) : (
              <div
                className="relative flex w-full flex-col items-center"
                style={{ width: "min(100%, calc((100dvh - 15rem) * 1.16))" }}
                onTouchStart={(evento) => {
                  const ponto = evento.changedTouches[0];
                  if (ponto) toque.current = { x: ponto.clientX, y: ponto.clientY };
                }}
                onTouchEnd={aoToque}
              >
                <div className="relative w-full rounded-t-[1.15rem] bg-[#1b2230] p-[0.55rem] pb-0 shadow-[0_30px_50px_rgba(0,0,0,0.45)]">
                  <div className="relative aspect-[3/2] overflow-hidden rounded-t-[0.45rem] bg-[#0b1220]">
                    {atual?.imagem ? (
                      atual.link ? (
                        <a href={atual.link} className="absolute inset-0" aria-label={`Abrir ${atual.titulo}`}>
                          <img key={atual.id} src={atual.imagem} alt={atual.descricao || atual.titulo} draggable={false} fetchPriority={indice === 0 ? "high" : "auto"} loading={indice === 0 ? "eager" : "lazy"} className={classeTela} onError={(evento) => falhaImagem(evento, atual.id)} />
                        </a>
                      ) : (
                        <img key={atual.id} src={atual.imagem} alt={atual.descricao || atual.titulo} draggable={false} fetchPriority={indice === 0 ? "high" : "auto"} loading={indice === 0 ? "eager" : "lazy"} className={`absolute inset-0 ${classeTela}`} onError={(evento) => falhaImagem(evento, atual.id)} />
                      )
                    ) : (
                      <a href={atual?.link || "#solucoes"} className="absolute inset-0 block" aria-label={atual?.titulo || "Abrir o sistema"}>
                        {tela}
                      </a>
                    )}
                  </div>
                  {atual?.titulo && (
                    atual.link ? (
                      <a href={atual.link} className="absolute bottom-0 left-1/2 z-10 inline-flex max-w-[92%] -translate-x-1/2 translate-y-1/2 items-center gap-2 truncate rounded-full bg-[#0b3b8f] px-4 py-1.5 text-sm font-semibold shadow-lg hover:bg-[#0d47a8]" aria-label={`Abrir ${atual.titulo}`}>
                        {atual.tipo === "clinica" || atual.titulo.toLowerCase().includes("clínica") ? <UserRound className="h-4 w-4 shrink-0" aria-hidden /> : <Users className="h-4 w-4 shrink-0" aria-hidden />}
                        {atual.titulo}
                      </a>
                    ) : (
                      <span className="pointer-events-none absolute bottom-0 left-1/2 z-10 inline-flex max-w-[92%] -translate-x-1/2 translate-y-1/2 items-center gap-2 truncate rounded-full bg-[#0b3b8f] px-4 py-1.5 text-sm font-semibold shadow-lg">
                        {atual.tipo === "clinica" || atual.titulo.toLowerCase().includes("clínica") ? <UserRound className="h-4 w-4 shrink-0" aria-hidden /> : <Users className="h-4 w-4 shrink-0" aria-hidden />}
                        {atual.titulo}
                      </span>
                    )
                  )}
                </div>
                <div className="relative -mx-[3.5%] h-4 w-[107%] rounded-b-[1.1rem] bg-gradient-to-b from-[#d5dce6] via-[#b7c0cc] to-[#8b95a3] shadow-[0_18px_24px_rgba(0,0,0,0.35)]">
                  <span className="absolute left-1/2 top-0 h-1.5 w-20 -translate-x-1/2 rounded-b-md bg-[#5e6876]" />
                </div>
              </div>
            )}
            {slides.length > 1 && (
              <div className="mt-3 flex items-center justify-center gap-2">
                {slides.map((slide, i) => (
                  <button
                    key={slide.id}
                    type="button"
                    aria-current={i === indice ? "true" : undefined}
                    aria-label={`Mostrar ${slide.titulo}`}
                    onClick={() => escolher(i)}
                    className={`h-2.5 w-2.5 rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white ${i === indice ? "bg-white" : "bg-white/35"}`}
                  />
                ))}
                <button
                  type="button"
                  aria-pressed={pausado}
                  aria-label={pausado ? "Continuar a troca automática" : "Pausar a troca automática"}
                  onClick={() => setPausado((v) => !v)}
                  className="ml-2 inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/30 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                >
                  {pausado ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="mt-3 grid w-full shrink-0 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map((card) => {
            const href = card.link || LINK_CARTAO[card.titulo] || "#solucoes";
            const Icone = ICONE_CARTAO[card.titulo as keyof typeof ICONE_CARTAO] || IconeCodigo;
            const linhas = QUEBRA_TITULO[card.titulo];
            return (
              <a
                key={card.id}
                href={href}
                className="flex items-center gap-3 rounded-2xl border border-cyan-300/50 bg-[#071833]/70 px-4 py-3.5 shadow-[0_0_0_1px_rgba(34,211,238,0.08)] transition hover:-translate-y-0.5 hover:border-cyan-200"
              >
                <Icone />
                <span>
                  <h2 className="text-[1.02rem] font-semibold leading-tight">
                    {linhas ? (
                      <>
                        {linhas[0]}
                        <br />
                        {linhas[1]}
                      </>
                    ) : (
                      card.titulo
                    )}
                  </h2>
                  <p className="mt-1 text-sm leading-snug text-slate-300">{card.descricao}</p>
                </span>
              </a>
            );
          })}
        </div>
      </div>
    </section>
  );
}
