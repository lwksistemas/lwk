export interface PastaCatalogo {
  id: number;
  nome: string;
  cor: string;
  pai: number | null;
  ordem: number;
  total: number;
  direto: number;
}

export function pastasDoNivel(pastas: PastaCatalogo[], paiId: number | null): PastaCatalogo[] {
  return pastas
    .filter((pasta) => (paiId == null ? pasta.pai == null : pasta.pai === paiId))
    .sort((a, b) => a.ordem - b.ordem || a.nome.localeCompare(b.nome, 'pt-BR'));
}

export function pastaTemFilhos(pastas: PastaCatalogo[], id: number): boolean {
  return pastas.some((pasta) => pasta.pai === id);
}
