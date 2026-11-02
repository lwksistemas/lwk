export type EfeitoTexto = "typing" | "fade" | "reveal" | "scroll" | "slide" | "zoom" | "nenhuma";
export type TransicaoImagem = "fade" | "slide" | "zoom" | "nenhuma";
export type VelocidadeAnimacao = "lenta" | "normal" | "rapida";
export type DirecaoAnimacao = "horizontal" | "vertical";

export interface ItemAnimacao {
  efeito: EfeitoTexto;
  ativo: boolean;
  velocidade: VelocidadeAnimacao;
  duracao: number;
  atraso: number;
  repetir: boolean;
  direcao: DirecaoAnimacao;
}

export interface ItemImagem {
  transicao: TransicaoImagem;
  ativo: boolean;
  velocidade: VelocidadeAnimacao;
  duracao: number;
  atraso: number;
}

export interface DispositivoAnimacao {
  selo: ItemAnimacao;
  titulo: ItemAnimacao;
  destaque: ItemAnimacao;
  descricao: ItemAnimacao;
  botao: ItemAnimacao;
  botao2: ItemAnimacao;
  secoes: ItemAnimacao;
  imagens: ItemImagem;
}

export interface AnimacoesHome {
  igual_celular: boolean;
  computador: DispositivoAnimacao;
  celular: DispositivoAnimacao;
}

export const CHAVE_PREVER_ANIMACOES = "lwk-home-animacoes-prever";

export const EFEITOS_TEXTO: { id: EfeitoTexto; rotulo: string }[] = [
  { id: "nenhuma", rotulo: "Sem animação" },
  { id: "fade", rotulo: "Fade-in" },
  { id: "typing", rotulo: "Digitação" },
  { id: "reveal", rotulo: "Revelação do texto" },
  { id: "scroll", rotulo: "Ao rolar a página" },
  { id: "slide", rotulo: "Slide-in" },
  { id: "zoom", rotulo: "Zoom-in" },
];

export const TRANSICOES_IMAGEM: { id: TransicaoImagem; rotulo: string }[] = [
  { id: "fade", rotulo: "Fade" },
  { id: "slide", rotulo: "Slide" },
  { id: "zoom", rotulo: "Zoom" },
  { id: "nenhuma", rotulo: "Sem efeito" },
];

export const CHAVES_ELEMENTO = ["selo", "titulo", "destaque", "descricao", "botao", "botao2", "secoes"] as const;
export type ChaveElemento = (typeof CHAVES_ELEMENTO)[number];

export const NOME_ELEMENTO: Record<ChaveElemento, string> = {
  selo: "Etiqueta",
  titulo: "Título principal",
  destaque: "Segunda linha azul",
  descricao: "Texto de apresentação",
  botao: "Botão principal",
  botao2: "Segundo botão",
  secoes: "Seções abaixo do banner",
};

const EFEITOS = new Set(EFEITOS_TEXTO.map((item) => item.id));
const TRANSICOES = new Set(TRANSICOES_IMAGEM.map((item) => item.id));

function numero(valor: unknown, minimo: number, maximo: number, padrao: number) {
  const n = Number(valor);
  if (!Number.isFinite(n)) return padrao;
  return Math.min(maximo, Math.max(minimo, Math.round(n)));
}

export function itemAnimacaoPadrao(): ItemAnimacao {
  return {
    efeito: "nenhuma",
    ativo: false,
    velocidade: "normal",
    duracao: 700,
    atraso: 0,
    repetir: false,
    direcao: "horizontal",
  };
}

export function itemImagemPadrao(): ItemImagem {
  return {
    transicao: "fade",
    ativo: true,
    velocidade: "normal",
    duracao: 450,
    atraso: 0,
  };
}

function dispositivoPadrao(): DispositivoAnimacao {
  return {
    selo: itemAnimacaoPadrao(),
    titulo: itemAnimacaoPadrao(),
    destaque: itemAnimacaoPadrao(),
    descricao: itemAnimacaoPadrao(),
    botao: itemAnimacaoPadrao(),
    botao2: itemAnimacaoPadrao(),
    secoes: itemAnimacaoPadrao(),
    imagens: itemImagemPadrao(),
  };
}

function lerItem(bruto: unknown): ItemAnimacao {
  const item = bruto && typeof bruto === "object" ? (bruto as Partial<ItemAnimacao>) : {};
  const efeito = EFEITOS.has(item.efeito as EfeitoTexto) ? (item.efeito as EfeitoTexto) : "nenhuma";
  return {
    efeito,
    ativo: Boolean(item.ativo) && efeito !== "nenhuma",
    velocidade: item.velocidade === "lenta" || item.velocidade === "rapida" ? item.velocidade : "normal",
    duracao: numero(item.duracao, 200, 3000, 700),
    atraso: numero(item.atraso, 0, 3000, 0),
    repetir: Boolean(item.repetir),
    direcao: item.direcao === "vertical" ? "vertical" : "horizontal",
  };
}

function lerImagem(bruto: unknown): ItemImagem {
  const item = bruto && typeof bruto === "object" ? (bruto as Partial<ItemImagem>) : {};
  const transicao = TRANSICOES.has(item.transicao as TransicaoImagem) ? (item.transicao as TransicaoImagem) : "fade";
  return {
    transicao,
    ativo: item.ativo !== false && transicao !== "nenhuma",
    velocidade: item.velocidade === "lenta" || item.velocidade === "rapida" ? item.velocidade : "normal",
    duracao: numero(item.duracao, 200, 3000, 450),
    atraso: numero(item.atraso, 0, 3000, 0),
  };
}

function lerDispositivo(bruto: unknown): DispositivoAnimacao {
  const bloco = bruto && typeof bruto === "object" ? (bruto as Partial<DispositivoAnimacao>) : {};
  return {
    selo: lerItem(bloco.selo),
    titulo: lerItem(bloco.titulo),
    destaque: lerItem(bloco.destaque),
    descricao: lerItem(bloco.descricao),
    botao: lerItem(bloco.botao),
    botao2: lerItem(bloco.botao2),
    secoes: lerItem(bloco.secoes),
    imagens: lerImagem(bloco.imagens),
  };
}

export function animacoesPadrao(): AnimacoesHome {
  const computador = dispositivoPadrao();
  return {
    igual_celular: true,
    computador,
    celular: dispositivoPadrao(),
  };
}

export function normalizarAnimacoes(bruto: unknown): AnimacoesHome {
  if (!bruto || typeof bruto !== "object" || !("computador" in (bruto as object))) {
    return animacoesPadrao();
  }
  const origem = bruto as Partial<AnimacoesHome>;
  const computador = lerDispositivo(origem.computador);
  const igual = origem.igual_celular !== false;
  return {
    igual_celular: igual,
    computador,
    celular: igual ? lerDispositivo(origem.computador) : lerDispositivo(origem.celular),
  };
}

export function duracaoDaVelocidade(velocidade: VelocidadeAnimacao, imagem = false) {
  if (imagem) return velocidade === "lenta" ? 900 : velocidade === "rapida" ? 250 : 450;
  return velocidade === "lenta" ? 1200 : velocidade === "rapida" ? 400 : 700;
}

export function estiloEfeito(item: ItemAnimacao, reduzido: boolean): Record<string, string> {
  if (reduzido || !item.ativo || item.efeito === "nenhuma" || item.efeito === "typing" || item.efeito === "scroll") {
    return {};
  }
  const nome =
    item.efeito === "slide"
      ? item.direcao === "vertical"
        ? "lwk-slide-up"
        : "lwk-slide-in"
      : item.efeito === "zoom"
        ? "lwk-zoom-in"
        : item.efeito === "reveal"
          ? "lwk-reveal"
          : "lwk-fade-in";
  const vezes = item.repetir ? "infinite" : "1";
  return { animation: `${nome} ${item.duracao}ms ease ${item.atraso}ms ${vezes} both` };
}

export function estiloEntrada(item: ItemAnimacao, visivel: boolean, reduzido: boolean): Record<string, string> {
  const neutro = { opacity: "1", transform: "none", clipPath: "none" };
  if (reduzido || !item.ativo || item.efeito === "nenhuma") return neutro;
  const transition = `opacity ${item.duracao}ms ease ${item.atraso}ms, transform ${item.duracao}ms ease ${item.atraso}ms, clip-path ${item.duracao}ms ease ${item.atraso}ms`;
  if (visivel) return { ...neutro, transition };
  if (item.efeito === "zoom") return { transition, opacity: "0", transform: "scale(0.96)" };
  if (item.efeito === "slide" && item.direcao === "vertical") return { transition, opacity: "0", transform: "translate3d(0, 1rem, 0)" };
  if (item.efeito === "slide") return { transition, opacity: "0", transform: "translate3d(1.25rem, 0, 0)" };
  if (item.efeito === "scroll") return { transition, opacity: "0", transform: "translate3d(0, 1rem, 0)" };
  if (item.efeito === "reveal" || item.efeito === "typing") return { transition, clipPath: "inset(0 100% 0 0)" };
  return { transition, opacity: "0" };
}

export function estiloTransicaoImagem(item: ItemImagem, reduzido: boolean): Record<string, string> {
  if (reduzido || !item.ativo || item.transicao === "nenhuma") return {};
  const nome = item.transicao === "slide" ? "lwk-img-slide" : item.transicao === "zoom" ? "lwk-img-zoom" : "lwk-fade";
  return { animation: `${nome} ${item.duracao}ms ease ${item.atraso}ms both` };
}
