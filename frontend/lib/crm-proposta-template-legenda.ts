/** Separa o texto do template da proposta entre a primeira folha e as seguintes. */

export const MARCA_SEGUNDA_FOLHA = '[[folha:2]]';

export interface FolhasDoTemplate {
  primeiraPagina: string;
  proximasPaginas: string;
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

export function juntarFolhasDoTemplate(primeiraPagina: string, proximasPaginas: string): string {
  const primeira = primeiraPagina.replace(/\r\n/g, '\n').trim();
  const proximas = proximasPaginas.replace(/\r\n/g, '\n').trim();
  if (primeira && proximas) return `${primeira}\n\n${MARCA_SEGUNDA_FOLHA}\n\n${proximas}`;
  if (primeira) return `${primeira}\n\n${MARCA_SEGUNDA_FOLHA}`;
  if (proximas) return `${MARCA_SEGUNDA_FOLHA}\n\n${proximas}`;
  return '';
}

export function textoVisivelDoTemplate(conteudo: string): string {
  return (conteudo || '')
    .replaceAll(MARCA_SEGUNDA_FOLHA, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function separarFolhasDoTemplate(conteudo: string): FolhasDoTemplate {
  const texto = (conteudo || '').replace(/\r\n/g, '\n');
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

  for (const bloco of blocosDoTexto(conteudo)) {
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
