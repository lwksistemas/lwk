/** Rótulo curto do plano, como "Ultrasis Laudos - Mensal", não é descrição da proposta. */
export function descricaoUtilNaProposta(texto: string): boolean {
  const limpo = texto.replace(/\s+/g, ' ').trim();
  if (!limpo) return false;
  if (limpo.length >= 60) return true;
  return /[.:;]/.test(limpo);
}

/** Coloca no conteúdo da proposta a descrição dos serviços escolhidos na oportunidade. */
export function conteudoComDescricoes(
  atual: string,
  itens: Array<{ produto_servico_descricao?: string | null }>,
): string {
  const base = (atual || '').trim();
  const faltam: string[] = [];
  const rotulos = new Set<string>();
  const vistos = new Set<string>();
  for (const item of itens) {
    const texto = (item.produto_servico_descricao || '').replace(/\s+/g, ' ').trim();
    if (!texto || vistos.has(texto)) continue;
    vistos.add(texto);
    if (!descricaoUtilNaProposta(texto)) {
      rotulos.add(texto);
      continue;
    }
    if (base.includes(texto)) continue;
    faltam.push(texto);
  }
  const paragrafos = base ? base.split(/\n{2,}/) : [];
  const limpa = paragrafos
    .filter((paragrafo) => !rotulos.has(paragrafo.replace(/\s+/g, ' ').trim()))
    .join('\n\n')
    .trim();
  if (faltam.length === 0) return limpa;
  const bloco = faltam.join('\n\n');
  return limpa ? `${limpa}\n\n${bloco}` : bloco;
}
