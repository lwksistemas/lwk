/** Formatação de status dos logs do superadmin. */

export type TipoResultadoLog = "sucesso" | "recusado" | "erro";

export interface LogStatusCampos {
  sucesso: boolean;
  erro?: string | null;
  acao?: string | null;
  acao_display?: string | null;
  recurso?: string | null;
  mensagem_status?: string | null;
  tipo_resultado?: TipoResultadoLog | null;
  metodo_http?: string | null;
  url?: string | null;
  navegador?: string | null;
  sistema_operacional?: string | null;
  user_agent?: string | null;
}

const RECURSO_LABEL: Record<string, string> = {
  Agenda: "agenda",
  Appointment: "agendamento",
  Patient: "paciente",
  Professional: "profissional",
  Consulta: "consulta",
  "Registrar-erro-frontend": "relato do navegador",
};

export function textoErroLegivel(raw?: string | null): string {
  const texto = (raw || "").trim();
  if (!texto) return "";
  if (texto.startsWith("HTTP ")) return "A requisição falhou no servidor.";

  const parsed = parseEstrutura(texto);
  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    const conflito = mensagemConflitoAgenda(parsed as Record<string, unknown>);
    if (conflito) return conflito;
    const extraido = mensagemDoDict(parsed as Record<string, unknown>);
    if (extraido) return extraido;
  }

  const conflito = mensagemConflitoTexto(texto);
  if (conflito) return conflito;

  const detalhe = texto.match(/string='([^']+)'/);
  if (detalhe?.[1]) return detalhe[1].trim();

  return encurtar(texto);
}

export function tipoResultadoLog(log: LogStatusCampos): TipoResultadoLog {
  if (log.tipo_resultado === "sucesso" || log.tipo_resultado === "recusado" || log.tipo_resultado === "erro") {
    return log.tipo_resultado;
  }
  if (log.sucesso) return "sucesso";
  const texto = textoErroLegivel(log.erro).toLowerCase();
  if (/traceback|internal server|erro ao salvar|erro interno/.test(texto)) return "erro";
  if (texto) return "recusado";
  return "erro";
}

export function mensagemStatusLog(log: LogStatusCampos): string {
  if (log.mensagem_status?.trim()) return log.mensagem_status.trim();
  if (log.sucesso) {
    const acao = (log.acao_display || log.acao || "Ação").trim();
    const recurso = rotuloRecurso(log.recurso);
    return recurso ? `${acao} em ${recurso} concluído.` : `${acao} concluído.`;
  }
  return textoErroLegivel(log.erro) || "A ação não foi concluída.";
}

export function tituloStatusLog(tipo: TipoResultadoLog): string {
  if (tipo === "sucesso") return "Concluído";
  if (tipo === "recusado") return "Não concluído";
  return "Falhou";
}

export function classeStatusLog(tipo: TipoResultadoLog): string {
  if (tipo === "sucesso") {
    return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
  }
  if (tipo === "recusado") {
    return "bg-amber-100 dark:bg-amber-900 text-amber-900 dark:text-amber-200";
  }
  return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
}

export function rotuloHttpLog(log: LogStatusCampos): string {
  const metodo = (log.metodo_http || "").trim().toUpperCase();
  const url = (log.url || "").trim();
  if (metodo && url) return `${metodo} ${url}`;
  if (url) return url;
  if (metodo) return metodo;
  return "URL não registrada";
}

export function rotuloNavegadorLog(log: LogStatusCampos): string {
  const partes = [log.navegador, log.sistema_operacional].filter(
    (p) => p && p !== "Desconhecido" && p !== "Outro",
  );
  if (partes.length) return partes.join(" · ");
  if (log.navegador && log.navegador !== "Desconhecido") return log.navegador;
  return "Não informado";
}

function rotuloRecurso(recurso?: string | null): string {
  const nome = (recurso || "").trim();
  if (!nome) return "";
  return RECURSO_LABEL[nome] || nome.replace(/-/g, " ").toLowerCase();
}

function mensagemConflitoAgenda(dados: Record<string, unknown>): string {
  if (dados.conflict !== true) return "";
  const server = dados.server && typeof dados.server === "object"
    ? (dados.server as Record<string, unknown>)
    : {};
  const cancelado = dados.resolution_hint === "server_cancelled" || server.status === "CANCELLED";
  const base = cancelado
    ? "Este agendamento está cancelado no servidor. A edição não foi salva."
    : "Este agendamento foi alterado em outro dispositivo. A edição não foi salva.";
  const permanece = rotuloVersaoServidor(server.title, server.start);
  return permanece ? `${base} Versão que permanece: ${permanece}.` : base;
}

function mensagemConflitoTexto(texto: string): string {
  if (!/['"]conflict['"]\s*:\s*(?:True|true)\b/.test(texto)) return "";
  const titulo = campoTexto(texto, "title");
  const inicio = campoTexto(texto, "start");
  const cancelado = texto.includes("server_cancelled") || /['"]status['"]\s*:\s*['"]CANCELLED['"]/.test(texto);
  const base = cancelado
    ? "Este agendamento está cancelado no servidor. A edição não foi salva."
    : "Este agendamento foi alterado em outro dispositivo. A edição não foi salva.";
  const permanece = rotuloVersaoServidor(titulo, inicio);
  return permanece ? `${base} Versão que permanece: ${permanece}.` : base;
}

function rotuloVersaoServidor(titulo: unknown, inicio: unknown): string {
  const nome = String(titulo || "").trim();
  const quando = formatarInicio(inicio);
  return [nome, quando].filter(Boolean).join(" · ");
}

function campoTexto(texto: string, campo: string): string {
  const achado = texto.match(new RegExp(`['"]${campo}['"]\\s*:\\s*'([^']*)'|['"]${campo}['"]\\s*:\\s*"([^"]*)"`));
  if (!achado) return "";
  return (achado[1] ?? achado[2] ?? "").trim();
}

function formatarInicio(valor: unknown): string {
  const texto = String(valor || "").trim();
  const achado = texto.match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
  if (!achado) return "";
  const [, ano, mes, dia, hora, minuto] = achado;
  return `${dia}/${mes}/${ano} ${hora}:${minuto}`;
}

function parseEstrutura(texto: string): unknown {
  try {
    return JSON.parse(texto);
  } catch {
    const aspas = texto.replace(/'/g, '"');
    try {
      return JSON.parse(aspas);
    } catch {
      return null;
    }
  }
}

function mensagemDoDict(dados: Record<string, unknown>): string {
  for (const chave of ["error", "detail", "message", "erro"]) {
    const valor = dados[chave];
    if (Array.isArray(valor) && valor.length) return String(valor[0]).trim();
    if (valor) return String(valor).trim();
  }
  const partes: string[] = [];
  for (const [chave, valor] of Object.entries(dados)) {
    if (Array.isArray(valor) && valor.length) partes.push(`${chave}: ${valor[0]}`);
    else if (valor !== null && valor !== "") partes.push(`${chave}: ${valor}`);
  }
  return encurtar(partes.join("; "));
}

function encurtar(texto: string, limite = 280): string {
  const limpo = texto.replace(/\s+/g, " ").trim();
  if (limpo.length <= limite) return limpo;
  return `${limpo.slice(0, limite - 1).trim()}…`;
}
