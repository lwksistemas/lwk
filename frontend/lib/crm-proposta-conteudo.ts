/** Coloca no conteúdo da proposta a descrição dos serviços escolhidos na oportunidade. */

export function conteudoComDescricoes(
  atual: string,
  itens: Array<{ produto_servico_descricao?: string | null }>,
): string {
  const base = (atual || '').trim();
  const faltam: string[] = [];
  const vistos = new Set<string>();
  for (const item of itens) {
    const texto = (item.produto_servico_descricao || '').replace(/\s+/g, ' ').trim();
    if (!texto || vistos.has(texto) || base.includes(texto)) continue;
    vistos.add(texto);
    faltam.push(texto);
  }
  if (faltam.length === 0) return atual || '';
  const bloco = faltam.join('\n\n');
  return base ? `${base}\n\n${bloco}` : bloco;
}
