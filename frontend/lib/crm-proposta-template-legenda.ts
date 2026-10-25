/** Separa o texto do template da proposta entre a primeira folha e as seguintes. */

export const MARCA_SEGUNDA_FOLHA = '[[folha:2]]';

export const TIPOS_LETRA = [
  { id: 'padrao', nome: 'Padrão', familia: 'ui-sans-serif, system-ui, sans-serif' },
  { id: 'times', nome: 'Times', familia: 'Times, "Times New Roman", serif' },
  { id: 'helvetica', nome: 'Helvetica', familia: 'Helvetica, Arial, sans-serif' },
  { id: 'courier', nome: 'Courier', familia: '"Courier New", Courier, monospace' },
] as const;

export const TAMANHOS_LETRA = [8, 9, 10, 11, 12, 14] as const;

export interface LetraDoTemplate {
  tipo: string;
  tamanho: number;
}

export const LETRA_PADRAO: LetraDoTemplate = { tipo: 'padrao', tamanho: 9 };

export interface FolhasDoTemplate {
  primeiraPagina: string;
  proximasPaginas: string;
}

function letraValida(letra: LetraDoTemplate): LetraDoTemplate {
  const tipo = TIPOS_LETRA.some((item) => item.id === letra.tipo) ? letra.tipo : LETRA_PADRAO.tipo;
  const tamanho = TAMANHOS_LETRA.some((item) => item === letra.tamanho) ? letra.tamanho : LETRA_PADRAO.tamanho;
  return { tipo, tamanho };
}

export function lerLetraDoTemplate(conteudo: string): LetraDoTemplate {
  const marca = (conteudo || '').match(/\[\[letra:([a-z]+)\|(\d+)\]\]/);
  if (!marca) return { ...LETRA_PADRAO };
  return letraValida({ tipo: marca[1], tamanho: Number(marca[2]) });
}

export function semMarcaDeLetra(conteudo: string): string {
  return (conteudo || '')
    .replace(/\[\[letra:[a-z]+\|\d+\]\]\n*/g, '')
    .replace(/^\n+/, '');
}

function tituloDeBloco(bloco: string): string {
  const bruto = bloco.trim();
  if (bruto.startsWith('# ')) return bruto.slice(2).trim();
  if (!bruto || bruto.length > 60 || bruto.split(/\s+/).length > 8) return '';
  if (/[.:;•]/.test(bruto)) return '';
  return bruto;
}

function ehDadosPagamento(titulo: string): boolean {
  const texto = titulo
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/#/g, '')
    .toLowerCase();
  return texto.includes('dados') && texto.includes('pagamento');
}

function blocosDoTexto(conteudo: string): string[] {
  const blocos: string[] = [];
  for (const linha of conteudo.replace(/\r\n/g, '\n').split('\n')) {
    const texto = linha.trim();
    if (texto) {
      blocos.push(texto);
    } else if (blocos.length > 0 && blocos[blocos.length - 1] !== '') {
      blocos.push('');
    }
  }
  while (blocos.length > 0 && blocos[blocos.length - 1] === '') blocos.pop();
  return blocos;
}

export function juntarFolhasDoTemplate(
  primeiraPagina: string,
  proximasPaginas: string,
  letra: LetraDoTemplate = LETRA_PADRAO,
): string {
  const primeira = primeiraPagina.replace(/\r\n/g, '\n').trim();
  const proximas = proximasPaginas.replace(/\r\n/g, '\n').trim();
  let corpo = '';
  if (primeira && proximas) corpo = `${primeira}\n\n${MARCA_SEGUNDA_FOLHA}\n\n${proximas}`;
  else if (primeira) corpo = `${primeira}\n\n${MARCA_SEGUNDA_FOLHA}`;
  else if (proximas) corpo = `${MARCA_SEGUNDA_FOLHA}\n\n${proximas}`;
  if (!corpo) return '';
  const escolhida = letraValida(letra);
  if (escolhida.tipo === LETRA_PADRAO.tipo && escolhida.tamanho === LETRA_PADRAO.tamanho) return corpo;
  return `[[letra:${escolhida.tipo}|${escolhida.tamanho}]]\n\n${corpo}`;
}

export function textoVisivelDoTemplate(conteudo: string): string {
  return semMarcaDeLetra(conteudo)
    .replaceAll(MARCA_SEGUNDA_FOLHA, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function separarFolhasDoTemplate(conteudo: string): FolhasDoTemplate {
  const texto = semMarcaDeLetra(conteudo).replace(/\r\n/g, '\n');
  const indice = texto.indexOf(MARCA_SEGUNDA_FOLHA);
  if (indice >= 0) {
    return {
      primeiraPagina: texto.slice(0, indice).trim(),
      proximasPaginas: texto.slice(indice + MARCA_SEGUNDA_FOLHA.length).trim(),
    };
  }

  const intro: string[] = [];
  const secoes: { titulo: string; paragrafos: string[] }[] = [];
  let atual: { titulo: string; paragrafos: string[] } | null = null;
  let segurandoPagamento = false;

  for (const bloco of blocosDoTexto(texto)) {
    if (bloco === '') {
      if (segurandoPagamento) {
        segurandoPagamento = false;
        atual = null;
        continue;
      }
      (atual ? atual.paragrafos : intro).push(bloco);
      continue;
    }
    if (segurandoPagamento && atual) {
      atual.paragrafos.push(bloco);
      continue;
    }
    const titulo = tituloDeBloco(bloco);
    if (titulo) {
      atual = { titulo, paragrafos: [] };
      secoes.push(atual);
      segurandoPagamento = ehDadosPagamento(titulo);
      continue;
    }
    if (atual) atual.paragrafos.push(bloco);
    else intro.push(bloco);
  }

  const primeira: string[] = [];
  const restantes: string[] = [...intro];
  let usouPagamento = false;
  for (const secao of secoes) {
    if (!usouPagamento && ehDadosPagamento(secao.titulo)) {
      usouPagamento = true;
      primeira.push(secao.titulo, ...secao.paragrafos.filter(Boolean));
      continue;
    }
    restantes.push(secao.titulo, ...secao.paragrafos);
  }

  return {
    primeiraPagina: primeira.join('\n').trim(),
    proximasPaginas: restantes.join('\n').replace(/\n{3,}/g, '\n\n').trim(),
  };
}
