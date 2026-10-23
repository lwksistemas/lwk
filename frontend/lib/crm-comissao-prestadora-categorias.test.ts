import { describe, expect, it } from 'vitest';

import { categoriasParaComissao, idsNaCategoria } from './crm-comissao-prestadora-categorias';

const arvore = [
  { id: 1, nome: 'PROTEÇÃO JURÍDICA', pai: null, ordem: 1 },
  { id: 2, nome: 'MEDICINA', pai: 1, ordem: 1 },
  { id: 3, nome: 'TABELA GREEN', pai: 2, ordem: 1 },
  { id: 4, nome: 'GRUPO 2', pai: 3, ordem: 2 },
  { id: 5, nome: 'BOLETO BANCÁRIO', pai: 4, ordem: 1 },
  { id: 6, nome: 'OUTRA', pai: null, ordem: 2 },
];

describe('categoriasParaComissao', () => {
  it('mostra a categoria e esconde as subpastas que receberam os serviços', () => {
    expect(
      categoriasParaComissao(arvore, [{ categoria: 5 }, { categoria: 5 }]).map((item) => item.nome),
    ).toEqual(['PROTEÇÃO JURÍDICA']);
  });

  it('mantém duas categorias quando os serviços estão em raízes diferentes', () => {
    expect(
      categoriasParaComissao(arvore, [{ categoria: 5 }, { categoria: 6 }]).map((item) => item.nome),
    ).toEqual(['PROTEÇÃO JURÍDICA', 'OUTRA']);
  });
});

describe('idsNaCategoria', () => {
  it('inclui a categoria e as subpastas para listar os serviços', () => {
    expect([...idsNaCategoria(arvore, 1)].sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 5]);
  });
});
