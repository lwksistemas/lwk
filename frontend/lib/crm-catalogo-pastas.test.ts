import { describe, expect, it } from 'vitest';
import { pastaTemFilhos, pastasDoNivel, type PastaCatalogo } from './crm-catalogo-pastas';

const pastas: PastaCatalogo[] = [
  { id: 1, nome: 'PROTEÇÃO JURÍDICA', cor: '#3B82F6', pai: null, ordem: 1, total: 589, direto: 0 },
  { id: 2, nome: 'MEDICINA', cor: '#0F766E', pai: 1, ordem: 1, total: 400, direto: 400 },
  { id: 3, nome: 'ODONTOLOGIA', cor: '#0369A1', pai: 1, ordem: 2, total: 189, direto: 189 },
];

describe('pastas do catálogo', () => {
  it('abre a raiz sem esperar os itens', () => {
    expect(pastasDoNivel(pastas, null).map((pasta) => pasta.nome)).toEqual(['PROTEÇÃO JURÍDICA']);
  });

  it('entra na pasta pelas subpastas já carregadas', () => {
    expect(pastasDoNivel(pastas, 1).map((pasta) => pasta.total)).toEqual([400, 189]);
    expect(pastaTemFilhos(pastas, 1)).toBe(true);
    expect(pastaTemFilhos(pastas, 2)).toBe(false);
  });
});
