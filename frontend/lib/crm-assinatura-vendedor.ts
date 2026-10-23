function chaveNome(nome: string): string {
  return nome.trim().toLocaleLowerCase('pt-BR');
}

/** Grafia do cadastro quando o nome da oportunidade só difere em maiúsculas. */
export function nomeCanonicoAssinatura(
  vendedores: Array<{ nome?: string | null }>,
  atual: string,
): string {
  const escolhido = atual.trim();
  if (!escolhido) return '';
  const chave = chaveNome(escolhido);
  for (const vendedor of vendedores) {
    const nome = (vendedor.nome || '').trim();
    if (nome && chaveNome(nome) === chave) return nome;
  }
  return escolhido;
}

/** Nomes de vendedores cadastrados para a assinatura da proposta, com o valor atual incluso. */
export function nomesParaAssinatura(
  vendedores: Array<{ nome?: string | null }>,
  atual: string,
): string[] {
  const porChave = new Map<string, string>();
  for (const vendedor of vendedores) {
    const nome = (vendedor.nome || '').trim();
    if (!nome) continue;
    const chave = chaveNome(nome);
    if (!porChave.has(chave)) porChave.set(chave, nome);
  }
  const escolhido = atual.trim();
  if (escolhido) {
    const chave = chaveNome(escolhido);
    if (!porChave.has(chave)) porChave.set(chave, escolhido);
  }
  return [...porChave.values()].sort((a, b) => a.localeCompare(b, 'pt-BR'));
}
