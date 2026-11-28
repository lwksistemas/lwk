"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Award,
  CalendarCheck,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  ClipboardList,
  Loader2,
  Lock,
  MapPin,
  MessageCircle,
  Phone,
  Search,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  User,
} from "lucide-react";
import {
  agendamentoOnlinePublicoApi as api,
  mensagemErroAgendamentoOnline,
  type PublicoCategoria,
  type PublicoCriarResultado,
  type PublicoInfo,
  type PublicoProcedimento,
  type PublicoProfissional,
} from "@/lib/clinica-beleza-api/agendamento-online";
import {
  formatarDuracao,
  formatarPrecoBRL,
  mascaraCelular,
  telefoneParaWhatsApp,
} from "@/lib/agendamento-online-format";
import { Calendario, parseYmd } from "./Calendario";

type Step = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;

const ROTULOS_PASSOS = [
  { titulo: "Categoria", desc: "Escolha a categoria", icon: Sparkles },
  { titulo: "Procedimento", desc: "Escolha o procedimento", icon: ClipboardList },
  { titulo: "Profissional", desc: "Selecione o profissional", icon: Stethoscope },
  { titulo: "Data e hora", desc: "Escolha a data e o horário", icon: CalendarDays },
  { titulo: "Seus dados", desc: "Informe seus dados", icon: User },
  { titulo: "Confirmação", desc: "Confirme o agendamento", icon: CheckCircle2 },
] as const;

const BENEFICIOS = [
  { icon: ShieldCheck, texto: "Agendamento rápido e seguro" },
  { icon: Lock, texto: "Seus dados protegidos (LGPD)" },
  { icon: Award, texto: "Atendimento com profissionais qualificados" },
] as const;

const HEX = /^#[0-9a-fA-F]{6}$/;

function corValida(c: string | undefined, fallback: string) {
  return c && HEX.test(c) ? c : fallback;
}

function iniciais(nome: string) {
  return nome
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

function dataExtenso(ymdStr: string) {
  if (!ymdStr) return "";
  const d = parseYmd(ymdStr);
  return d.toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
}

const primaryBg: CSSProperties = { backgroundColor: "var(--ao-primary)" };
const primaryText: CSSProperties = { color: "var(--ao-primary)" };
const softBg: CSSProperties = { backgroundColor: "color-mix(in srgb, var(--ao-primary) 10%, white)" };

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-3xl border border-pink-100 bg-white p-4 shadow-sm sm:p-5 ${className}`}>{children}</div>;
}

function BotaoPrimario({
  children,
  onClick,
  disabled,
  loading,
  className = "",
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-full px-6 text-base font-semibold text-white shadow-md transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      style={primaryBg}
    >
      {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
      {children}
    </button>
  );
}

function Carregando({ texto = "Carregando…" }: { texto?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500" role="status">
      <Loader2 className="h-5 w-5 animate-spin" style={primaryText} /> {texto}
    </div>
  );
}

function Aviso({ children, onRetry }: { children: ReactNode; onRetry?: () => void }) {
  return (
    <div className="flex items-start gap-2 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        {children}
        {onRetry ? (
          <button type="button" onClick={onRetry} className="ml-2 font-semibold underline">
            Tentar novamente
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function AgendamentoOnlineWizard({ slug }: { slug: string }) {
  const [info, setInfo] = useState<PublicoInfo | null>(null);
  const [infoErro, setInfoErro] = useState("");
  const [step, setStep] = useState<Step>(0);

  // Dados carregados
  const [categorias, setCategorias] = useState<PublicoCategoria[]>([]);
  const [procs, setProcs] = useState<{ chave: string; itens: PublicoProcedimento[] } | null>(null);
  const [profs, setProfs] = useState<{ procId: number; itens: PublicoProfissional[] } | null>(null);
  const [dias, setDias] = useState<{ chave: string; itens: string[] } | null>(null);
  const [slots, setSlots] = useState<{ chave: string; itens: string[] } | null>(null);
  const [erroPasso, setErroPasso] = useState("");

  // Seleções (preservadas ao voltar)
  const [categoria, setCategoria] = useState<PublicoCategoria | null>(null);
  const [procedimento, setProcedimento] = useState<PublicoProcedimento | null>(null);
  const [profissional, setProfissional] = useState<PublicoProfissional | null>(null);
  const [dia, setDia] = useState("");
  const [hora, setHora] = useState("");
  const [busca, setBusca] = useState("");

  const [nome, setNome] = useState("");
  const [telefone, setTelefone] = useState("");
  const [email, setEmail] = useState("");
  const [nascimento, setNascimento] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [aceite, setAceite] = useState(false);
  const [errosForm, setErrosForm] = useState<Record<string, string>>({});

  const [enviando, setEnviando] = useState(false);
  const [erroEnvio, setErroEnvio] = useState("");
  const [resultado, setResultado] = useState<PublicoCriarResultado | null>(null);

  const topoRef = useRef<HTMLDivElement>(null);

  const temCategorias = categorias.length > 0;

  /* ----------------------------- Carregamentos ----------------------------- */

  useEffect(() => {
    let vivo = true;
    (async () => {
      try {
        const data = await api.info(slug);
        if (!vivo) return;
        setInfo(data);
        if (data.disponivel) {
          try {
            const cats = await api.categorias(slug);
            if (vivo) setCategorias(cats);
          } catch {
            /* sem categorias: vai direto para procedimentos */
          }
        }
      } catch (err) {
        if (!vivo) return;
        setInfoErro(mensagemErroAgendamentoOnline(err, "Não foi possível carregar a página de agendamento."));
      }
    })();
    return () => {
      vivo = false;
    };
  }, [slug]);

  const chaveProcs = categoria?.slug ?? "";

  const carregarProcs = useCallback(async () => {
    setErroPasso("");
    setProcs(null);
    try {
      const itens = await api.procedimentos(slug, chaveProcs || undefined);
      setProcs({ chave: chaveProcs, itens });
    } catch (err) {
      setErroPasso(mensagemErroAgendamentoOnline(err, "Não foi possível carregar os procedimentos."));
    }
  }, [slug, chaveProcs]);

  useEffect(() => {
    if (step === 2 && (!procs || procs.chave !== chaveProcs)) void carregarProcs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, chaveProcs]);

  const carregarProfs = useCallback(async () => {
    if (!procedimento) return;
    setErroPasso("");
    setProfs(null);
    try {
      const itens = await api.profissionais(slug, procedimento.id);
      setProfs({ procId: procedimento.id, itens });
    } catch (err) {
      setErroPasso(mensagemErroAgendamentoOnline(err, "Não foi possível carregar os profissionais."));
    }
  }, [slug, procedimento]);

  useEffect(() => {
    if (step === 3 && procedimento && (!profs || profs.procId !== procedimento.id)) void carregarProfs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, procedimento?.id]);

  const chaveDias = profissional && procedimento ? `${profissional.id}:${procedimento.id}` : "";

  const carregarDias = useCallback(async () => {
    if (!profissional || !procedimento) return;
    setErroPasso("");
    setDias(null);
    try {
      const r = await api.dias(slug, profissional.id, procedimento.id);
      setDias({ chave: chaveDias, itens: r.dias });
    } catch (err) {
      setErroPasso(mensagemErroAgendamentoOnline(err, "Não foi possível carregar as datas."));
    }
  }, [slug, profissional, procedimento, chaveDias]);

  useEffect(() => {
    if (step === 4 && chaveDias && (!dias || dias.chave !== chaveDias)) void carregarDias();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, chaveDias]);

  const carregarSlots = useCallback(
    async (diaSel: string) => {
      if (!profissional || !procedimento || !diaSel) return;
      setSlots(null);
      setErroPasso("");
      try {
        const r = await api.slots(slug, profissional.id, procedimento.id, diaSel);
        setSlots({ chave: `${chaveDias}:${diaSel}`, itens: r.slots });
      } catch (err) {
        setErroPasso(mensagemErroAgendamentoOnline(err, "Não foi possível carregar os horários."));
      }
    },
    [slug, profissional, procedimento, chaveDias],
  );

  // Ao voltar ao passo 4 com dia já escolhido, garante os horários carregados.
  useEffect(() => {
    if (step === 4 && dia && (!slots || slots.chave !== `${chaveDias}:${dia}`)) void carregarSlots(dia);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, dia, chaveDias]);

  /* ------------------------------- Navegação ------------------------------- */

  const irPara = useCallback((s: Step) => {
    setErroPasso("");
    setStep(s);
    requestAnimationFrame(() => topoRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }, []);

  const voltar = () => {
    if (step === 2 && !temCategorias) return irPara(0);
    if (step > 0 && step < 7) irPara((step - 1) as Step);
  };

  const escolherCategoria = (c: PublicoCategoria | null) => {
    if ((c?.slug ?? "") !== (categoria?.slug ?? "")) {
      setProcedimento(null);
      setProfissional(null);
      setDia("");
      setHora("");
    }
    setCategoria(c);
    setBusca("");
    irPara(2);
  };

  const escolherProcedimento = (p: PublicoProcedimento) => {
    if (p.id !== procedimento?.id) {
      setProfissional(null);
      setDia("");
      setHora("");
    }
    setProcedimento(p);
    irPara(3);
  };

  const escolherProfissional = (p: PublicoProfissional) => {
    if (p.id !== profissional?.id) {
      setDia("");
      setHora("");
    }
    setProfissional(p);
    irPara(4);
  };

  const escolherDia = (d: string) => {
    setDia(d);
    setHora("");
  };

  const validarForm = () => {
    const e: Record<string, string> = {};
    if (nome.trim().split(/\s+/).filter(Boolean).length < 2) e.nome = "Informe nome e sobrenome.";
    const digitos = telefone.replace(/\D/g, "");
    if (digitos.length < 10) e.telefone = "Informe um celular válido com DDD.";
    if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) e.email = "E-mail inválido.";
    if (!aceite) e.aceite = "Aceite os termos para continuar.";
    setErrosForm(e);
    return Object.keys(e).length === 0;
  };

  const confirmar = async () => {
    if (!procedimento || !profissional || !dia || !hora) return;
    setEnviando(true);
    setErroEnvio("");
    try {
      const r = await api.criar(slug, {
        nome: nome.trim(),
        telefone: telefone.replace(/\D/g, ""),
        email: email.trim() || undefined,
        data_nascimento: nascimento || undefined,
        observacoes: observacoes.trim() || undefined,
        professional: profissional.id,
        procedure: procedimento.id,
        date_ymd: dia,
        time: hora,
      });
      setResultado(r);
      irPara(7);
    } catch (err) {
      setErroEnvio(mensagemErroAgendamentoOnline(err, "Não foi possível concluir o agendamento."));
      // O horário pode ter sido ocupado: recarrega para o cliente escolher outro.
      setSlots(null);
      setDias(null);
    } finally {
      setEnviando(false);
    }
  };

  const reiniciar = () => {
    setCategoria(null);
    setProcedimento(null);
    setProfissional(null);
    setDia("");
    setHora("");
    setBusca("");
    setAceite(false);
    setObservacoes("");
    setResultado(null);
    setErroEnvio("");
    setDias(null);
    setSlots(null);
    irPara(0);
  };

  /* -------------------------------- Derivados ------------------------------- */

  const primaria = corValida(info?.cor_primaria, "#EC4899");
  const secundaria = corValida(info?.cor_secundaria, "#DB2777");

  const rootStyle = {
    "--ao-primary": primaria,
    "--ao-secondary": secundaria,
  } as CSSProperties;

  const procsFiltrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    const itens = procs?.itens ?? [];
    return q ? itens.filter((p) => p.nome.toLowerCase().includes(q) || p.descricao?.toLowerCase().includes(q)) : itens;
  }, [procs, busca]);

  const whatsappNumero = telefoneParaWhatsApp(info?.whatsapp || info?.telefone);
  const whatsappHref = whatsappNumero
    ? `https://wa.me/${whatsappNumero}?text=${encodeURIComponent(`Olá! Gostaria de agendar um horário em ${info?.nome ?? "sua clínica"}.`)}`
    : "";

  /* --------------------------------- Estados -------------------------------- */

  if (!info && !infoErro) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-pink-50/50">
        <Carregando texto="Carregando agendamento…" />
      </div>
    );
  }

  if (infoErro || !info?.disponivel) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-pink-50/50 p-4" style={rootStyle}>
        <Card className="w-full max-w-md text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full" style={softBg}>
            <CalendarDays className="h-7 w-7" style={primaryText} />
          </div>
          <h1 className="text-lg font-semibold text-gray-900">Agendamento indisponível</h1>
          <p className="mt-2 text-sm text-gray-600">
            {infoErro || info?.error || "O agendamento online está temporariamente indisponível."}
          </p>
          {info?.telefone ? (
            <a
              href={`https://wa.me/${telefoneParaWhatsApp(info.telefone)}`}
              className="mt-4 inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold text-white"
              style={primaryBg}
            >
              <Phone className="h-4 w-4" /> Falar com a clínica
            </a>
          ) : null}
        </Card>
      </div>
    );
  }

  const nomeClinica = info.nome || "Clínica";

  /* --------------------------------- Layout --------------------------------- */

  const naBoas = step === 0;

  return (
    <div
      className={`relative min-h-[100dvh] text-gray-900 ${
        naBoas
          ? "overflow-x-hidden bg-[radial-gradient(120%_80%_at_10%_-10%,#fce7f3_0%,#fff5f8_35%,#ffffff_70%)]"
          : "bg-gradient-to-b from-pink-50 via-white to-white"
      }`}
      style={rootStyle}
    >
      {naBoas ? <FundoOndas /> : null}
      <div ref={topoRef} />
      {!naBoas ? (
        <header className="sticky top-0 z-20 border-b border-pink-100 bg-white/90 backdrop-blur">
          <div className="mx-auto flex h-14 w-full max-w-6xl items-center gap-3 px-4 sm:px-6">
            {step > 0 && step < 7 ? (
              <button
                type="button"
                onClick={voltar}
                aria-label="Voltar"
                className="rounded-full p-2 text-gray-700 hover:bg-gray-100"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
            ) : (
              <LogoClinica info={info} size={32} />
            )}
            <p className="min-w-0 flex-1 truncate text-sm font-semibold">{nomeClinica}</p>
            {step > 0 && step < 7 ? (
              <span className="shrink-0 text-xs font-medium text-gray-500">Passo {step} de 6</span>
            ) : null}
          </div>
          {step > 0 && step < 7 ? (
            <div className="h-1 w-full bg-pink-100" aria-hidden>
              <div className="h-full transition-all" style={{ ...primaryBg, width: `${(step / 6) * 100}%` }} />
            </div>
          ) : null}
        </header>
      ) : null}

      <main className="relative z-[1] mx-auto w-full max-w-6xl px-4 pb-28 pt-4 sm:px-6 sm:pt-6">
        {step === 0 && (
          <Boas
            info={info}
            nome={nomeClinica}
            onIniciar={() => irPara(temCategorias ? 1 : 2)}
            whatsappHref={whatsappHref}
          />
        )}

        {step === 1 && (
          <Secao titulo="Escolha uma categoria" desc="Que tipo de atendimento você procura?">
            <div className="grid gap-3 sm:grid-cols-2">
              {categorias.map((c) => {
                const ativo = categoria?.slug === c.slug;
                return (
                  <button
                    key={c.slug}
                    type="button"
                    onClick={() => escolherCategoria(c)}
                    className={`group flex items-center gap-3 rounded-3xl border bg-white p-4 text-left shadow-sm transition hover:shadow-md ${
                      ativo ? "border-2" : "border-pink-100"
                    }`}
                    style={ativo ? { borderColor: "var(--ao-primary)" } : undefined}
                  >
                    <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl" style={softBg}>
                      <Sparkles className="h-6 w-6" style={primaryText} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-semibold">{c.nome}</span>
                      <span className="text-xs text-gray-500">
                        {c.quantidade} {c.quantidade === 1 ? "procedimento" : "procedimentos"}
                      </span>
                    </span>
                    <ChevronRight className="h-5 w-5 text-gray-400 group-hover:translate-x-0.5" />
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              onClick={() => escolherCategoria(null)}
              className="mt-4 w-full rounded-full border border-pink-200 bg-white py-3 text-sm font-semibold"
              style={primaryText}
            >
              Ver todos os procedimentos
            </button>
          </Secao>
        )}

        {step === 2 && (
          <Secao
            titulo="Escolha o procedimento"
            desc={categoria ? `Categoria: ${categoria.nome}` : "Todos os procedimentos disponíveis"}
          >
            <div className="relative mb-4">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar procedimento…"
                aria-label="Buscar procedimento"
                className="w-full rounded-full border border-pink-100 bg-white py-3 pl-10 pr-4 text-sm shadow-sm outline-none focus:ring-2 focus:ring-pink-200"
              />
            </div>
            {erroPasso ? (
              <Aviso onRetry={carregarProcs}>{erroPasso}</Aviso>
            ) : !procs ? (
              <Carregando />
            ) : procsFiltrados.length === 0 ? (
              <p className="py-10 text-center text-sm text-gray-500">Nenhum procedimento encontrado.</p>
            ) : (
              <ul className="space-y-3">
                {procsFiltrados.map((p) => {
                  const ativo = procedimento?.id === p.id;
                  return (
                    <li key={p.id}>
                      <button
                        type="button"
                        onClick={() => escolherProcedimento(p)}
                        className={`w-full rounded-3xl border bg-white p-4 text-left shadow-sm transition hover:shadow-md ${
                          ativo ? "border-2" : "border-pink-100"
                        }`}
                        style={ativo ? { borderColor: "var(--ao-primary)" } : undefined}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="font-semibold">{p.nome}</p>
                            {p.descricao ? <p className="mt-0.5 line-clamp-2 text-xs text-gray-500">{p.descricao}</p> : null}
                            <p className="mt-2 inline-flex items-center gap-1 text-xs text-gray-600">
                              <Clock className="h-3.5 w-3.5" /> {formatarDuracao(p.duracao_minutos)}
                            </p>
                          </div>
                          <p className="shrink-0 text-sm font-bold" style={primaryText}>
                            {p.exibir_valor && p.preco ? formatarPrecoBRL(p.preco) : p.preco_rotulo || "Sob consulta"}
                          </p>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </Secao>
        )}

        {step === 3 && (
          <Secao titulo="Escolha o profissional" desc={procedimento?.nome}>
            {erroPasso ? (
              <Aviso onRetry={carregarProfs}>{erroPasso}</Aviso>
            ) : !profs ? (
              <Carregando />
            ) : profs.itens.length === 0 ? (
              <p className="py-10 text-center text-sm text-gray-500">
                Nenhum profissional disponível para este procedimento no momento.
              </p>
            ) : (
              <ul className="grid gap-3 sm:grid-cols-2">
                {profs.itens.map((p) => {
                  const ativo = profissional?.id === p.id;
                  return (
                    <li key={p.id}>
                      <button
                        type="button"
                        onClick={() => escolherProfissional(p)}
                        className={`flex w-full items-center gap-4 rounded-3xl border bg-white p-4 text-left shadow-sm transition hover:shadow-md ${
                          ativo ? "border-2" : "border-pink-100"
                        }`}
                        style={ativo ? { borderColor: "var(--ao-primary)" } : undefined}
                      >
                        <Avatar nome={p.nome} url={p.foto_url} size={64} />
                        <span className="min-w-0">
                          <span className="block font-semibold">{p.nome}</span>
                          {p.especialidade ? <span className="block text-xs text-gray-500">{p.especialidade}</span> : null}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </Secao>
        )}

        {step === 4 && (
          <Secao titulo="Escolha data e horário" desc={`${procedimento?.nome ?? ""} · ${profissional?.nome ?? ""}`}>
            {erroPasso && !dias ? (
              <Aviso onRetry={carregarDias}>{erroPasso}</Aviso>
            ) : !dias ? (
              <Carregando />
            ) : dias.itens.length === 0 ? (
              <p className="py-10 text-center text-sm text-gray-500">
                Não há horários livres para este profissional no período. Tente outro profissional.
              </p>
            ) : (
              <div className="space-y-4">
                <Calendario diasDisponiveis={dias.itens} selecionado={dia} onSelect={escolherDia} />
                {dia ? (
                  <Card>
                    <p className="mb-3 text-sm font-semibold capitalize">{dataExtenso(dia)}</p>
                    {erroPasso ? (
                      <Aviso onRetry={() => carregarSlots(dia)}>{erroPasso}</Aviso>
                    ) : !slots || slots.chave !== `${chaveDias}:${dia}` ? (
                      <Carregando texto="Buscando horários…" />
                    ) : slots.itens.length === 0 ? (
                      <p className="text-sm text-gray-500">Sem horários livres neste dia. Escolha outra data.</p>
                    ) : (
                      <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                        {slots.itens.map((h) => {
                          const ativo = hora === h;
                          return (
                            <button
                              key={h}
                              type="button"
                              aria-pressed={ativo}
                              onClick={() => setHora(h)}
                              className={`rounded-full border py-2.5 text-sm font-semibold transition ${
                                ativo ? "text-white shadow" : "border-pink-200 bg-white text-gray-800 hover:bg-pink-50"
                              }`}
                              style={ativo ? primaryBg : undefined}
                            >
                              {h}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </Card>
                ) : (
                  <p className="text-center text-sm text-gray-500">Selecione um dia destacado no calendário.</p>
                )}
                <BarraInferior>
                  <BotaoPrimario disabled={!dia || !hora} onClick={() => irPara(5)}>
                    Continuar
                  </BotaoPrimario>
                </BarraInferior>
              </div>
            )}
          </Secao>
        )}

        {step === 5 && (
          <Secao titulo="Seus dados" desc="Usaremos para confirmar seu agendamento.">
            <form
              noValidate
              onSubmit={(e) => {
                e.preventDefault();
                if (validarForm()) irPara(6);
              }}
              className="space-y-4"
            >
              <Card className="space-y-4">
                <Campo label="Nome completo *" erro={errosForm.nome}>
                  <input
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    autoComplete="name"
                    className={inputCls}
                    placeholder="Maria Silva"
                  />
                </Campo>
                <Campo label="Celular (WhatsApp) *" erro={errosForm.telefone}>
                  <input
                    value={telefone}
                    onChange={(e) => setTelefone(mascaraCelular(e.target.value))}
                    inputMode="tel"
                    autoComplete="tel"
                    className={inputCls}
                    placeholder="(11) 99999-8888"
                  />
                </Campo>
                <Campo label="E-mail (opcional)" erro={errosForm.email}>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    className={inputCls}
                    placeholder="voce@email.com"
                  />
                </Campo>
                <Campo label="Data de nascimento (opcional)">
                  <input
                    type="date"
                    value={nascimento}
                    max={new Date().toISOString().slice(0, 10)}
                    onChange={(e) => setNascimento(e.target.value)}
                    autoComplete="bday"
                    className={inputCls}
                  />
                </Campo>
                <Campo label="Observações (opcional)">
                  <textarea
                    rows={3}
                    value={observacoes}
                    onChange={(e) => setObservacoes(e.target.value)}
                    className={inputCls}
                    placeholder="Alguma informação que devemos saber?"
                  />
                </Campo>
              </Card>

              <Card>
                <label className="flex cursor-pointer items-start gap-3 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={aceite}
                    onChange={(e) => setAceite(e.target.checked)}
                    className="mt-0.5 h-4 w-4"
                    style={{ accentColor: "var(--ao-primary)" }}
                  />
                  <span>
                    Autorizo o uso dos meus dados para fins de agendamento e contato pela clínica.
                  </span>
                </label>
                {errosForm.aceite ? <p className="mt-1 text-xs text-red-600">{errosForm.aceite}</p> : null}
                {info.politica_privacidade ? (
                  <details className="mt-3 text-xs text-gray-600">
                    <summary className="cursor-pointer font-medium" style={primaryText}>
                      Política de privacidade
                    </summary>
                    <p className="mt-2 whitespace-pre-line">{info.politica_privacidade}</p>
                  </details>
                ) : null}
              </Card>

              <BarraInferior>
                <BotaoPrimario type="submit">Revisar agendamento</BotaoPrimario>
              </BarraInferior>
            </form>
          </Secao>
        )}

        {step === 6 && (
          <Secao titulo="Revise e confirme" desc="Confira se está tudo certo antes de finalizar.">
            <Card className="space-y-4">
              <Linha icon={Sparkles} rotulo="Procedimento" valor={procedimento?.nome} extra={formatarDuracao(procedimento?.duracao_minutos ?? 0)} />
              <Linha icon={Stethoscope} rotulo="Profissional" valor={profissional?.nome} extra={profissional?.especialidade} />
              <Linha icon={CalendarCheck} rotulo="Data e horário" valor={`${dataExtenso(dia)} às ${hora}`} capitalize />
              {procedimento?.exibir_valor && procedimento.preco ? (
                <Linha icon={ClipboardList} rotulo="Valor" valor={formatarPrecoBRL(procedimento.preco)} />
              ) : null}
              <hr className="border-pink-100" />
              <Linha icon={User} rotulo="Paciente" valor={nome} extra={[telefone, email].filter(Boolean).join(" · ")} />
              {info.endereco ? <Linha icon={MapPin} rotulo="Local" valor={info.endereco} /> : null}
            </Card>
            {info.modo_confirmacao === "secretaria" ? (
              <p className="mt-3 rounded-2xl bg-amber-50 p-3 text-xs text-amber-800">
                Seu pedido será analisado pela clínica. Você receberá a confirmação em breve.
              </p>
            ) : null}
            {erroEnvio ? (
              <div className="mt-3 space-y-2">
                <Aviso>{erroEnvio}</Aviso>
                <button
                  type="button"
                  onClick={() => {
                    setHora("");
                    setErroEnvio("");
                    irPara(4);
                  }}
                  className="w-full rounded-full border border-pink-200 bg-white py-3 text-sm font-semibold"
                  style={primaryText}
                >
                  Escolher outro horário
                </button>
              </div>
            ) : null}
            <BarraInferior>
              <BotaoPrimario onClick={confirmar} loading={enviando}>
                Confirmar agendamento
              </BotaoPrimario>
            </BarraInferior>
          </Secao>
        )}

        {step === 7 && resultado && (
          <div className="py-6 text-center">
            <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full text-white shadow-lg" style={primaryBg}>
              <Check className="h-10 w-10" strokeWidth={3} />
            </div>
            <h1 className="mt-5 text-2xl font-bold">
              {resultado.pendente_aprovacao ? "Solicitação enviada!" : "Agendamento confirmado!"}
            </h1>
            <p className="mx-auto mt-2 max-w-md text-sm text-gray-600">{resultado.mensagem}</p>
            <Card className="mx-auto mt-6 max-w-md space-y-3 text-left">
              <Linha icon={Sparkles} rotulo="Procedimento" valor={resultado.procedure_nome || procedimento?.nome} />
              <Linha icon={Stethoscope} rotulo="Profissional" valor={resultado.professional_nome || profissional?.nome} />
              <Linha icon={CalendarCheck} rotulo="Data e horário" valor={`${dataExtenso(dia)} às ${hora}`} capitalize />
              <p className="pt-1 text-xs text-gray-500">Protocolo nº {resultado.numero}</p>
            </Card>
            <div className="mx-auto mt-6 flex max-w-md flex-col gap-3">
              <BotaoPrimario onClick={reiniciar}>Fazer novo agendamento</BotaoPrimario>
              {whatsappHref ? (
                <a
                  href={whatsappHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-pink-200 bg-white px-6 text-sm font-semibold"
                  style={primaryText}
                >
                  <MessageCircle className="h-5 w-5" /> Falar com a clínica
                </a>
              ) : null}
            </div>
          </div>
        )}
      </main>

      {info.botao_whatsapp_ativo && whatsappHref ? (
        <a
          href={whatsappHref}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Falar pelo WhatsApp"
          className="fixed bottom-5 right-4 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-lg transition hover:scale-105"
          style={{ marginBottom: "env(safe-area-inset-bottom)" }}
        >
          <MessageCircle className="h-7 w-7" />
        </a>
      ) : null}
    </div>
  );
}

/* ------------------------------ Sub-componentes ----------------------------- */

const inputCls =
  "w-full rounded-2xl border border-pink-100 bg-white px-4 py-3 text-base outline-none focus:border-pink-300 focus:ring-2 focus:ring-pink-100";

function Secao({ titulo, desc, children }: { titulo: string; desc?: string; children: ReactNode }) {
  return (
    <section>
      <h1 className="text-xl font-bold sm:text-2xl">{titulo}</h1>
      {desc ? <p className="mb-4 mt-1 text-sm text-gray-500">{desc}</p> : <div className="mb-4" />}
      {children}
    </section>
  );
}

function Campo({ label, erro, children }: { label: string; erro?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-gray-700">{label}</span>
      {children}
      {erro ? <span className="mt-1 block text-xs text-red-600">{erro}</span> : null}
    </label>
  );
}

function Linha({
  icon: Icon,
  rotulo,
  valor,
  extra,
  capitalize,
}: {
  icon: typeof User;
  rotulo: string;
  valor?: string;
  extra?: string;
  capitalize?: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full" style={softBg}>
        <Icon className="h-4 w-4" style={primaryText} />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-gray-500">{rotulo}</p>
        <p className={`text-sm font-semibold ${capitalize ? "first-letter:uppercase" : ""}`}>{valor || "—"}</p>
        {extra && extra !== "—" ? <p className="text-xs text-gray-500">{extra}</p> : null}
      </div>
    </div>
  );
}

function BarraInferior({ children }: { children: ReactNode }) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-10 border-t border-pink-100 bg-white/95 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur">
      <div className="mx-auto max-w-6xl pr-16 sm:px-2">{children}</div>
    </div>
  );
}

function FundoOndas() {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 h-[420px] overflow-hidden" aria-hidden>
      <svg className="absolute -top-16 left-0 h-[360px] w-[140%] opacity-40" viewBox="0 0 1440 320" preserveAspectRatio="none">
        <path
          fill="var(--ao-primary)"
          fillOpacity="0.12"
          d="M0,96L80,112C160,128,320,160,480,154.7C640,149,800,107,960,101.3C1120,96,1280,128,1360,144L1440,160L1440,0L1360,0C1280,0,1120,0,960,0C800,0,640,0,480,0C320,0,160,0,80,0L0,0Z"
        />
      </svg>
      <svg className="absolute top-10 left-[-10%] h-[300px] w-[130%] opacity-50" viewBox="0 0 1440 320" preserveAspectRatio="none">
        <path
          fill="var(--ao-secondary)"
          fillOpacity="0.1"
          d="M0,192L60,170.7C120,149,240,107,360,112C480,117,600,171,720,186.7C840,203,960,181,1080,154.7C1200,128,1320,96,1380,80L1440,64L1440,0L1380,0C1320,0,1200,0,1080,0C960,0,840,0,720,0C600,0,480,0,360,0C240,0,120,0,60,0L0,0Z"
        />
      </svg>
    </div>
  );
}

function Avatar({ nome, url, size }: { nome: string; url?: string; size: number }) {
  if (url) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={url} alt={nome} width={size} height={size} className="shrink-0 rounded-full object-cover" style={{ width: size, height: size }} />;
  }
  return (
    <span
      className="flex shrink-0 items-center justify-center rounded-full font-bold text-white"
      style={{ ...primaryBg, width: size, height: size, fontSize: size / 3 }}
      aria-hidden
    >
      {iniciais(nome)}
    </span>
  );
}

function LogoClinica({ info, size }: { info: PublicoInfo; size: number }) {
  if (info.logo_url) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={info.logo_url} alt="" width={size} height={size} className="rounded-full object-cover" style={{ width: size, height: size }} />;
  }
  return <Avatar nome={info.nome || "C"} size={size} />;
}

function Boas({
  info,
  nome,
  onIniciar,
  whatsappHref,
}: {
  info: PublicoInfo;
  nome: string;
  onIniciar: () => void;
  whatsappHref: string;
}) {
  const apresentacao =
    info.texto_apresentacao?.trim() || "Agende seu atendimento de forma prática, rápida e segura.";

  return (
    <div className="space-y-6 pb-8 sm:space-y-8">
      <section className="overflow-hidden rounded-[1.75rem] border border-pink-100/80 bg-white/70 shadow-sm backdrop-blur-sm sm:rounded-[2rem]">
        <div className="grid md:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
          <div className="relative min-h-[220px] overflow-hidden bg-pink-100 sm:min-h-[280px] md:min-h-[320px]">
            {info.banner_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={info.banner_url} alt="" className="absolute inset-0 h-full w-full object-cover" />
            ) : (
              <div
                className="absolute inset-0"
                style={{
                  background: `linear-gradient(145deg, color-mix(in srgb, var(--ao-primary) 55%, white), color-mix(in srgb, var(--ao-secondary) 75%, #fce7f3))`,
                }}
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-white/40 md:to-white/70" />
          </div>

          <div className="flex flex-col justify-center gap-4 px-5 py-7 text-center sm:px-8 sm:py-10 md:text-left">
            <div className="flex flex-col items-center gap-3 md:flex-row md:items-center">
              <div className="rounded-full bg-white p-1.5 shadow-md ring-1 ring-pink-100">
                <LogoClinica info={info} size={64} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold tracking-wide text-gray-700 sm:text-base">{nome}</p>
              </div>
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl" style={primaryText}>
                Agendamento Online
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-gray-600 sm:text-base">{apresentacao}</p>
            </div>
          </div>
        </div>
      </section>

      <Card className="!p-5 sm:!p-7">
        <h2 className="mb-5 text-center text-xl font-bold sm:mb-7 sm:text-2xl">Como agendar?</h2>
        <ol className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 lg:gap-2">
          {ROTULOS_PASSOS.map((p, i) => {
            const Icon = p.icon;
            return (
              <li key={p.titulo} className="relative flex flex-col items-center text-center">
                {i < ROTULOS_PASSOS.length - 1 ? (
                  <ChevronRight
                    className="pointer-events-none absolute -right-2 top-6 hidden h-5 w-5 text-pink-300 lg:block"
                    aria-hidden
                  />
                ) : null}
                <span
                  className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl text-white shadow-sm"
                  style={primaryBg}
                >
                  <Icon className="h-6 w-6" />
                </span>
                <span className="text-[11px] font-semibold uppercase tracking-wide text-pink-500">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="mt-1 text-sm font-medium leading-snug text-gray-800">{p.desc}</span>
              </li>
            );
          })}
        </ol>

        <div className="mx-auto mt-8 flex max-w-xl flex-col gap-3">
          <BotaoPrimario onClick={onIniciar} className="!rounded-2xl">
            <CalendarCheck className="h-5 w-5" /> Iniciar Agendamento
            <ChevronRight className="h-5 w-5" />
          </BotaoPrimario>
          {whatsappHref ? (
            <a
              href={whatsappHref}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl border border-pink-200 bg-white px-6 text-base font-semibold transition hover:bg-pink-50"
              style={primaryText}
            >
              <MessageCircle className="h-5 w-5" /> Falar com a Secretária no WhatsApp
            </a>
          ) : null}
        </div>
      </Card>

      <ul className="grid gap-4 sm:grid-cols-3">
        {BENEFICIOS.map((b) => {
          const Icon = b.icon;
          return (
            <li key={b.texto} className="flex items-center gap-3 rounded-2xl bg-white/80 px-4 py-3 text-sm font-medium text-gray-700 shadow-sm ring-1 ring-pink-100">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full" style={softBg}>
                <Icon className="h-5 w-5" style={primaryText} />
              </span>
              {b.texto}
            </li>
          );
        })}
      </ul>

      {info.endereco || info.telefone ? (
        <div className="space-y-1 text-center text-xs text-gray-500">
          {info.endereco ? (
            <p className="inline-flex items-center justify-center gap-1">
              <MapPin className="h-3.5 w-3.5" /> {info.endereco}
            </p>
          ) : null}
          {info.telefone ? (
            <p className="inline-flex items-center justify-center gap-1">
              <Phone className="h-3.5 w-3.5" /> {info.telefone}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
