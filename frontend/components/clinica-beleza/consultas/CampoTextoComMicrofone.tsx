"use client";

import { Mic } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { juntarTextoFalado } from "@/lib/ditado-texto";

type Reconhecimento = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((evento: EventoFala) => void) | null;
  onerror: ((evento: { error: string }) => void) | null;
  onend: (() => void) | null;
};

type EventoFala = {
  results: ArrayLike<{ isFinal: boolean; 0?: { transcript: string } }>;
};

const PARAR_OUTROS = "lwk-ditado-parar";

function fabricaReconhecimento(): (new () => Reconhecimento) | null {
  if (typeof window === "undefined") return null;
  const navegador = window as Window & {
    SpeechRecognition?: new () => Reconhecimento;
    webkitSpeechRecognition?: new () => Reconhecimento;
  };
  return navegador.SpeechRecognition || navegador.webkitSpeechRecognition || null;
}

export function CampoTextoComMicrofone({
  id,
  label,
  value,
  onChange,
  rows = 2,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (texto: string) => void;
  rows?: number;
}) {
  const [ouvindo, setOuvindo] = useState(false);
  const [suporta, setSuporta] = useState(true);
  const [revisando, setRevisando] = useState(false);
  const [aviso, setAviso] = useState("");
  const reconhecimento = useRef<Reconhecimento | null>(null);
  const base = useRef(value);
  const valorAtual = useRef(value);
  const aoMudar = useRef(onChange);
  const querOuvir = useRef(false);

  useEffect(() => {
    valorAtual.current = value;
  }, [value]);

  useEffect(() => {
    aoMudar.current = onChange;
  }, [onChange]);

  useEffect(() => {
    setSuporta(Boolean(fabricaReconhecimento()));
  }, []);

  function parar() {
    querOuvir.current = false;
    setOuvindo(false);
    try {
      reconhecimento.current?.stop();
    } catch {
      /* já estava parado */
    }
  }

  async function revisar() {
    const atual = valorAtual.current.trim();
    if (!atual || revisando) return;
    parar();
    setRevisando(true);
    setAviso("");
    try {
      const resposta = await ClinicaBelezaAPI.consultas.revisarTexto(atual, label);
      const texto = (resposta.texto || "").trim();
      if (!texto) {
        window.alert("A revisão voltou vazia. Tente de novo.");
        return;
      }
      valorAtual.current = texto;
      aoMudar.current(texto);
      setAviso("Texto revisado. Confira se o sentido continua o mesmo antes de salvar.");
    } catch (erro) {
      const mensagem =
        erro && typeof erro === "object" && "error" in erro && typeof erro.error === "string"
          ? erro.error
          : "Não foi possível revisar o texto agora.";
      window.alert(mensagem);
    } finally {
      setRevisando(false);
    }
  }

  function iniciar() {
    window.dispatchEvent(new CustomEvent(PARAR_OUTROS, { detail: id }));
    const Fabrica = fabricaReconhecimento();
    if (!Fabrica) {
      setSuporta(false);
      return;
    }
    const rec = reconhecimento.current ?? new Fabrica();
    reconhecimento.current = rec;
    rec.lang = "pt-BR";
    rec.continuous = true;
    rec.interimResults = true;
    base.current = valorAtual.current;
    querOuvir.current = true;
    setOuvindo(true);

    rec.onresult = (evento) => {
      let finais = "";
      let parcial = "";
      for (let i = 0; i < evento.results.length; i += 1) {
        const trecho = evento.results[i][0]?.transcript ?? "";
        if (evento.results[i].isFinal) finais += `${trecho} `;
        else parcial += trecho;
      }
      const texto = juntarTextoFalado(base.current, finais, parcial);
      valorAtual.current = texto;
      aoMudar.current(texto);
    };
    rec.onerror = (evento) => {
      if (evento.error === "not-allowed" || evento.error === "service-not-allowed") {
        querOuvir.current = false;
        setOuvindo(false);
        window.alert("Permita o microfone neste site para a fala virar texto.");
      }
    };
    rec.onend = () => {
      if (!querOuvir.current) {
        setOuvindo(false);
        return;
      }
      base.current = valorAtual.current;
      window.setTimeout(() => {
        if (!querOuvir.current) return;
        try {
          rec.start();
        } catch {
          /* o navegador ainda está encerrando a sessão anterior */
        }
      }, 200);
    };
    try {
      rec.start();
    } catch {
      querOuvir.current = false;
      setOuvindo(false);
    }
  }

  useEffect(() => {
    const aoPararOutro = (evento: Event) => {
      const outro = (evento as CustomEvent<string>).detail;
      if (outro !== id) parar();
    };
    window.addEventListener(PARAR_OUTROS, aoPararOutro);
    return () => {
      window.removeEventListener(PARAR_OUTROS, aoPararOutro);
      parar();
    };
  }, [id]);

  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-1">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor={id}>
          {label}
        </label>
        <div className="flex items-center gap-2 shrink-0">
        {value.trim() && !ouvindo ? (
          <button
            type="button"
            onClick={() => void revisar()}
            disabled={revisando}
            className="text-xs font-medium px-2.5 py-1 rounded-md border border-gray-300 dark:border-neutral-600 text-gray-800 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50"
          >
            {revisando ? "Revisando…" : "Revisar/corrigir"}
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => (ouvindo ? parar() : iniciar())}
          disabled={!suporta}
          aria-pressed={ouvindo}
          aria-label={ouvindo ? `Parar de gravar ${label}` : `Falar em ${label}`}
          title={
            suporta
              ? ouvindo
                ? "Parar de gravar"
                : "Falar neste campo"
              : "Este navegador não transforma fala em texto. Use o Chrome."
          }
          className={`inline-flex items-center justify-center h-8 w-8 rounded-full border ${
            ouvindo
              ? "bg-red-600 border-red-600 text-white animate-pulse"
              : "border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-700"
          } disabled:opacity-40`}
        >
          <Mic size={16} />
        </button>
        </div>
      </div>
      <textarea
        id={id}
        rows={rows}
        value={value}
        onChange={(e) => {
          setAviso("");
          onChange(e.target.value);
        }}
        className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600 text-sm"
      />
      {ouvindo ? (
        <p className="text-xs text-red-600 mt-1">Ouvindo. Fale que o texto entra neste campo.</p>
      ) : null}
      {aviso ? <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{aviso}</p> : null}
    </div>
  );
}
