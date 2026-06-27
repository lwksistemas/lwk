"use client";

/**
 * Integração Memed — prescrição digital (Receituário e Exames).
 *
 * Fluxo:
 * 1. Busca o token do prescritor no backend (api-key/secret-key ficam no servidor).
 * 2. Injeta o script da Memed com data-token=<token>.
 * 3. Aguarda o módulo `plataforma.prescricao` iniciar e define o paciente.
 * 4. Abre o editor da Memed (medicamentos e exames ficam no mesmo editor).
 *
 * Carrega sob demanda (no primeiro clique) para não pesar a página.
 */

import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from "react";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { apenasDigitos } from "@/lib/format-br";
import { logger } from "@/lib/logger";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  interface Window {
    MdHub?: any;
    MdSinapsePrescricao?: any;
  }
}

export interface MemedPrescricaoHandle {
  /** Garante a Memed carregada, define o paciente e abre o editor de prescrição. */
  abrir: () => Promise<void>;
  /** Fecha o editor de prescrição da Memed (comando `hide`). */
  fechar: () => void;
}

interface DadosClinica {
  local_name?: string;
  address?: string;
  city?: string;
  state?: string;
  phone?: string;
}

interface MemedPrescricaoProps {
  consultaId: number;
  professionalId?: number | null;
  patientId: number;
  patientName: string;
  /** Chamado após registrar uma prescrição emitida (para atualizar o histórico). */
  onPrescricaoRegistrada?: () => void;
}

/**
 * Handler global do evento `prescricaoImpressa`. É registrado uma única vez no MdHub
 * (que dispara o evento) e delega para a instância atual do componente, que conhece a
 * consulta/paciente correntes. Evita registrar múltiplos listeners a cada clique.
 */
let prescricaoImpressaHandler: ((data: unknown) => void) | null = null;

/** Remove tags HTML simples (a posologia vem como HTML). */
function stripHtml(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

interface ItemPrescricao {
  nome?: string;
  posologia?: string;
  tipo?: string;
  receituario?: string;
}

function extrairUrlPdf(obj: unknown, profundidade = 0): string {
  if (profundidade > 6 || obj == null) return "";
  if (typeof obj === "string") {
    const s = obj.trim();
    if (/^https?:\/\//i.test(s)) return s;
    return "";
  }
  if (Array.isArray(obj)) {
    for (const item of obj) {
      const u = extrairUrlPdf(item, profundidade + 1);
      if (u) return u;
    }
    return "";
  }
  if (typeof obj === "object") {
    const o = obj as Record<string, unknown>;
    for (const key of ["url_pdf", "pdf_url", "link_pdf", "pdf", "url", "link", "secure_url"]) {
      const val = o[key];
      if (typeof val === "string" && /^https?:\/\//i.test(val.trim())) return val.trim();
    }
    for (const val of Object.values(o)) {
      const u = extrairUrlPdf(val, profundidade + 1);
      if (u) return u;
    }
  }
  return "";
}

/** Extrai (de forma defensiva) os dados úteis do payload do evento prescricaoImpressa. */
function parsePrescricao(data: unknown): { prescricaoId: string; itens: ItemPrescricao[]; resumo: string; pdfUrl: string } {
  const d = (data ?? {}) as Record<string, any>;
  const prescricao = (d.prescricao ?? d["prescrição"] ?? d) as Record<string, any>;
  const meds: any[] = Array.isArray(d.medicamentos)
    ? d.medicamentos
    : Array.isArray(prescricao?.medicamentos)
      ? prescricao.medicamentos
      : Array.isArray(prescricao?.itens)
        ? prescricao.itens
        : [];
  const prescricaoId = String(prescricao?.id ?? d.prescricao_id ?? d.id ?? "");

  const pdfUrl = extrairUrlPdf(d) || extrairUrlPdf(prescricao);

  const itens: ItemPrescricao[] = meds.map((m) => ({
    nome: m?.nome ?? m?.descricao ?? m?.titulo ?? "",
    posologia: m?.sanitized_posology ?? stripHtml(m?.posologia),
    tipo: m?.tipo ?? "",
    receituario: m?.receituario ?? "",
  }));

  const resumo = itens
    .map((it) => (it.posologia ? `- ${it.nome} — ${it.posologia}` : `- ${it.nome}`))
    .filter((line) => line.replace(/^- /, "").trim())
    .join("\n");

  return { prescricaoId, itens, resumo, pdfUrl };
}

const SCRIPT_ID = "memed-sinapse-prescricao";
const MODULO_PRESCRICAO = "plataforma.prescricao";
const READY_FLAG = "__memedPrescricaoPronta";
const TIMEOUT_MS = 20000;

/** Indica se o módulo de prescrição da Memed já terminou de inicializar. */
function moduloPronto(): boolean {
  return typeof window !== "undefined" && (window as any)[READY_FLAG] === true;
}

/**
 * Registra (uma única vez) o listener de `core:moduleInit` e marca um flag global
 * quando o módulo de prescrição fica pronto.
 *
 * Por que global e idempotente: o evento `core:moduleInit` dispara só uma vez por
 * carregamento do script. Se registrarmos um novo listener a cada clique, o evento
 * já terá disparado e nunca mais chega — causando timeout. Marcar o flag e fazer
 * polling sobre ele evita essa corrida.
 */
function registrarListenerPrescricao(): void {
  if (typeof window === "undefined") return;
  const sinapse = (window as any).MdSinapsePrescricao;
  if (!sinapse?.event?.add || (window as any).__memedListenerRegistrado) return;
  (window as any).__memedListenerRegistrado = true;
  sinapse.event.add("core:moduleInit", (module: any) => {
    if (module?.name === MODULO_PRESCRICAO) {
      (window as any)[READY_FLAG] = true;
      // Captura o evento de prescrição emitida (uma única vez por carregamento).
      const mdhub = (window as any).MdHub;
      if (mdhub?.event?.add && !(window as any).__memedPrescImpressaRegistrado) {
        (window as any).__memedPrescImpressaRegistrado = true;
        mdhub.event.add("prescricaoImpressa", (data: unknown) => {
          try {
            prescricaoImpressaHandler?.(data);
          } catch {
            // Não deixa um erro de callback quebrar a Memed.
          }
        });
      }
    }
  });
}

/** Converte data ISO (YYYY-MM-DD) para o formato dd/mm/aaaa esperado pela Memed. */
function toBrDate(value?: string | null): string {
  if (!value) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return "";
  const [, y, m, d] = match;
  return `${d}/${m}/${y}`;
}

const MemedPrescricao = forwardRef<MemedPrescricaoHandle, MemedPrescricaoProps>(
  ({ consultaId, professionalId, patientId, patientName, onPrescricaoRegistrada }, ref) => {
    const initPromiseRef = useRef<Promise<void> | null>(null);
    const readyRef = useRef(false);
    const clinicaRef = useRef<DadosClinica | null>(null);

    const carregarScript = useCallback((scriptUrl: string, token: string) => {
      return new Promise<void>((resolve, reject) => {
        const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
        if (existing) {
          // Script já presente: garante o token mais recente do prescritor e o listener.
          existing.setAttribute("data-token", token);
          registrarListenerPrescricao();
          resolve();
          return;
        }
        const script = document.createElement("script");
        script.id = SCRIPT_ID;
        script.type = "text/javascript";
        script.src = scriptUrl;
        script.setAttribute("data-token", token);
        script.async = true;
        script.onload = () => {
          registrarListenerPrescricao();
          resolve();
        };
        script.onerror = () => reject(new Error("Falha ao carregar o script da Memed."));
        document.body.appendChild(script);
      });
    }, []);

    const aguardarModulo = useCallback(() => {
      return new Promise<void>((resolve, reject) => {
        registrarListenerPrescricao();
        const inicio = Date.now();
        const verificar = () => {
          if (moduloPronto()) {
            resolve();
            return;
          }
          if (Date.now() - inicio > TIMEOUT_MS) {
            reject(new Error(
              "Tempo esgotado ao iniciar a Memed. Verifique a conexão e tente novamente.",
            ));
            return;
          }
          // O listener pode ainda não estar registrado se o script demorar a executar.
          registrarListenerPrescricao();
          setTimeout(verificar, 150);
        };
        verificar();
      });
    }, []);

    const garantirPronto = useCallback(() => {
      if (readyRef.current) return Promise.resolve();
      if (initPromiseRef.current) return initPromiseRef.current;

      const promise = (async () => {
        const path =
          professionalId != null
            ? `/memed/token/?professional=${professionalId}`
            : "/memed/token/";

        // Preload hint: adiciona <link rel="preload"> para o script da Memed
        // antes mesmo de ter o token (URL é estável por ambiente).
        const preloadScript = (url: string) => {
          if (document.querySelector(`link[href="${url}"]`)) return;
          const link = document.createElement("link");
          link.rel = "preload";
          link.as = "script";
          link.href = url;
          document.head.appendChild(link);
        };
        // URL conhecida (produção) — preload enquanto busca token
        preloadScript("https://memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js");

        const res = await clinicaBelezaFetch(path);
        const cfg = await res.json();
        if (!res.ok) {
          throw new Error(
            (typeof cfg?.error === "string" && cfg.error) ||
              "Não foi possível obter o token do prescritor na Memed.",
          );
        }
        if (!cfg?.token || !cfg?.script_url) {
          throw new Error("Configuração da Memed incompleta (token ou script ausente).");
        }
        clinicaRef.current = cfg.clinica ?? null;
        await carregarScript(cfg.script_url, cfg.token);
        await aguardarModulo();
        readyRef.current = true;
      })();

      initPromiseRef.current = promise;
      promise.catch(() => {
        // Permite nova tentativa após falha.
        initPromiseRef.current = null;
      });
      return promise;
    }, [professionalId, carregarScript, aguardarModulo]);

    // Pré-carrega a Memed ao abrir a consulta, para o primeiro clique ser instantâneo.
    // Retry automático: se falhar, tenta novamente após 3s (máx 2 tentativas).
    useEffect(() => {
      let tentativas = 0;
      const maxTentativas = 2;
      const tentarPrecarregar = () => {
        garantirPronto().catch((e) => {
          tentativas++;
          logger.warn(`Memed: pré-carregamento falhou (tentativa ${tentativas}/${maxTentativas}):`, e);
          if (tentativas < maxTentativas) {
            setTimeout(tentarPrecarregar, 3000);
          }
        });
      };
      tentarPrecarregar();
    }, [garantirPronto]);

    // Logout ao desmontar: limpa o localStorage da Memed. A doc exige isso
    // OBRIGATORIAMENTE quando vários prescritores usam o mesmo computador, para
    // evitar mistura de cadastros entre sessões. Doc: comandos-mdhub/logout.
    useEffect(() => {
      return () => {
        try {
          window.MdHub?.command?.send?.("plataforma.sdk", "logout");
        } catch {
          // Silencioso: o componente já está sendo desmontado.
        }
      };
    }, []);

    // Registra o handler da prescrição emitida com a consulta/paciente atuais.
    // Ao emitir uma receita na Memed, salva no histórico do paciente.
    useEffect(() => {
      prescricaoImpressaHandler = (data: unknown) => {
        const { prescricaoId, itens, resumo, pdfUrl } = parsePrescricao(data);
        if (!prescricaoId && !itens.length) {
          logger.warn("Memed: evento prescricaoImpressa sem dados utilizáveis.", data);
          return;
        }
        const payload = {
          prescricao_id: prescricaoId,
          resumo,
          itens,
          pdf_url: pdfUrl,
          professional: professionalId ?? null,
        };
        const salvar = () =>
          ClinicaBelezaAPI.memed.salvarPrescricao(consultaId, payload).then(() => {
            onPrescricaoRegistrada?.();
          });

        void salvar().catch((e) => logger.warn("Memed: falha ao registrar prescrição no histórico:", e));

        if (!pdfUrl && prescricaoId) {
          window.setTimeout(() => {
            void salvar().catch(() => {});
          }, 4000);
        }
      };
      return () => {
        prescricaoImpressaHandler = null;
      };
    }, [consultaId, professionalId, onPrescricaoRegistrada]);

    const definirPaciente = useCallback(async () => {
      let detalhe: Record<string, any> = {};
      try {
        detalhe = await ClinicaBelezaAPI.get(`/patients/${patientId}/`);
      } catch (e) {
        logger.warn("Memed: não foi possível carregar detalhes do paciente:", e);
      }
      // A Memed não permite editar manualmente os campos enviados via MdHub.
      // Por isso enviamos apenas os campos preenchidos — o prescritor completa o resto.
      // A Memed aceita o id externo como `idExterno` (SDK) e `external_id` (exemplos
      // oficiais do script). Enviamos os dois para garantir o vínculo do paciente.
      const paciente: Record<string, unknown> = {
        idExterno: String(patientId),
        external_id: String(patientId),
        nome: detalhe?.nome || patientName,
      };
      const cpf = apenasDigitos(detalhe?.cpf);
      if (cpf) paciente.cpf = cpf;
      const telefone = apenasDigitos(detalhe?.telefone);
      if (telefone) paciente.telefone = telefone;
      if (detalhe?.email) paciente.email = detalhe.email;
      if (detalhe?.endereco) paciente.endereco = detalhe.endereco;
      if (detalhe?.cidade) paciente.cidade = detalhe.cidade;
      const dataNascimento = toBrDate(detalhe?.data_nascimento);
      if (dataNascimento) paciente.data_nascimento = dataNascimento;

      await window.MdHub.command.send("plataforma.prescricao", "setPaciente", paciente);
    }, [patientId, patientName]);

    // Preenche o local de atendimento (clínica) no receituário via setWorkplace.
    // Opcional: se não houver dados da clínica, não envia nada.
    const definirClinica = useCallback(async () => {
      const clinica = clinicaRef.current;
      if (!clinica || !clinica.local_name) return;
      const workplace: Record<string, unknown> = { local_name: clinica.local_name };
      if (clinica.address) workplace.address = clinica.address;
      if (clinica.city) workplace.city = clinica.city;
      if (clinica.state) workplace.state = clinica.state;
      if (clinica.phone) workplace.phone = String(clinica.phone);
      try {
        await window.MdHub.command.send("plataforma.prescricao", "setWorkplace", workplace);
      } catch (e) {
        logger.warn("Memed: não foi possível definir o local de atendimento:", e);
      }
    }, []);

    const abrir = useCallback(async () => {
      await garantirPronto();
      if (!window.MdHub) {
        throw new Error("Memed não disponível.");
      }
      await definirPaciente();
      await definirClinica();
      // Método canônico do quickstart da Memed para exibir o módulo de prescrição.
      window.MdHub.module.show("plataforma.prescricao");
    }, [garantirPronto, definirPaciente, definirClinica]);

    const fechar = useCallback(() => {
      try {
        window.MdHub?.module?.hide?.("plataforma.prescricao");
      } catch (e) {
        logger.warn("Memed: falha ao fechar o módulo de prescrição:", e);
      }
    }, []);

    useImperativeHandle(ref, () => ({ abrir, fechar }), [abrir, fechar]);

    return null;
  },
);

MemedPrescricao.displayName = "MemedPrescricao";

export default MemedPrescricao;
