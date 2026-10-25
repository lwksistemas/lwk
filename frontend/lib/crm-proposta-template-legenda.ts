/** Separa o texto do template da proposta entre a primeira folha e as seguintes. */

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

export function separarFolhasDoTemplate(conteudo: string): FolhasDoTemplate {
  const intro: string[] = [];
  const secoes: { titulo: string; paragrafos: string[] }[] = [];
  let atual: { titulo: string; paragrafos: string[] } | null = null;

  for (const bloco of blocosDoTexto(conteudo)) {
    if (bloco === '') {
      (atual ? atual.paragrafos : intro).push(bloco);
      continue;
    }
    const titulo = tituloDeBloco(bloco);
    if (titulo) {
      atual = { titulo, paragrafos: [] };
      secoes.push(atual);
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
