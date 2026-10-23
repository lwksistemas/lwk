/** Nomes de vendedores cadastrados para a assinatura da proposta, com o valor atual incluso. */
export function nomesParaAssinatura(
  vendedores: Array<{ nome?: string | null }>,
  atual: string,
): string[] {
  const nomes = new Set<string>();
  for (const vendedor of vendedores) {
    const nome = (vendedor.nome || '').trim();
    if (nome) nomes.add(nome);
  }
  const escolhido = atual.trim();
  if (escolhido) nomes.add(escolhido);
  return [...nomes].sort((a, b) => a.localeCompare(b, 'pt-BR'));
}
