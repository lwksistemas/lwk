import { describe, expect, it } from 'vitest';
import {
  formatCrmBrl,
  formatCrmBrlCompact,
  formatOportunidadeVinculoLabel,
  gerarTituloOportunidade,
  gerarTituloProposta,
  normalizeListResponse,
  rotuloExibicaoOportunidade,
  subtituloExibicaoOportunidade,
  subtituloModalOportunidade,
} from './crm-utils';

describe('gerarTituloOportunidade', () => {
  it('usa nome do lead', () => {
    expect(gerarTituloOportunidade({ nome: 'Maria Silva' })).toBe('Maria Silva');
  });

  it('concatena empresa quando diferente do nome', () => {
    expect(gerarTituloOportunidade({ nome: 'Maria', empresa: 'Acme Ltda' })).toBe('Maria — Acme Ltda');
  });

  it('ignora empresa igual ao nome', () => {
    expect(gerarTituloOportunidade({ nome: 'Acme', empresa: 'acme' })).toBe('Acme');
  });

  it('fallback sem nome', () => {
    expect(gerarTituloOportunidade({ nome: '' })).toBe('Oportunidade');
  });
});

describe('gerarTituloProposta', () => {
  it('CPF usa nome do lead', () => {
    expect(gerarTituloProposta({ nome: 'João', cpf_cnpj: '123.456.789-00' })).toBe('João');
  });

  it('CNPJ prioriza razão social', () => {
    expect(
      gerarTituloProposta({
        nome: 'João',
        cpf_cnpj: '12.345.678/0001-90',
        conta_info: { razao_social: 'Empresa XYZ Ltda' },
      }),
    ).toBe('Empresa XYZ Ltda');
  });
});

describe('formatOportunidadeVinculoLabel', () => {
  it('prioriza nome do cliente em vez do titulo da prestadora', () => {
    const label = formatOportunidadeVinculoLabel({
      titulo: 'Felix Representações',
      lead_nome: 'Maria Silva',
      valor: '1500',
      empresa_prestadora_nome: 'Felix Representações',
    });
    expect(label.startsWith('Maria Silva — R$')).toBe(true);
    expect(label).not.toContain('Felix Representações');
  });

  it('mostra empresa do cliente (conta), não some ao carregar prestadora', () => {
    const label = formatOportunidadeVinculoLabel({
      titulo: 'Felix Representações',
      lead_nome: 'CAROLINE ALETÉIA VIEIRA DO AMARAL',
      valor: '1142',
      conta_nome: 'ULTRASIS INFORMATICA LTDA',
      empresa_prestadora_nome: 'Felix Representações',
    });
    expect(label).toContain('CAROLINE ALETÉIA VIEIRA DO AMARAL · ULTRASIS INFORMATICA LTDA');
    expect(label).toContain('R$');
    expect(label).not.toContain('Felix Representações');
  });
});

describe('rotuloExibicaoOportunidade', () => {
  it('prioriza lead_nome', () => {
    expect(rotuloExibicaoOportunidade({ titulo: 'T', lead_nome: 'Ana' })).toBe('Ana');
  });

  it('usa titulo quando diferente da prestadora', () => {
    expect(
      rotuloExibicaoOportunidade({
        titulo: 'Projeto X',
        empresa_prestadora_nome: 'Prestadora Y',
      }),
    ).toBe('Projeto X');
  });
});

describe('subtituloExibicaoOportunidade', () => {
  it('mostra prestadora no card quando lead é o título', () => {
    expect(
      subtituloExibicaoOportunidade({
        titulo: 'ULTRASIS INFORMATICA LTDA',
        lead_nome: 'JOANA ROSA',
        empresa_prestadora_nome: 'ULTRASIS INFORMATICA LTDA',
      }),
    ).toBe('ULTRASIS INFORMATICA LTDA');
  });

  it('não repete lead no subtítulo do card', () => {
    expect(
      subtituloExibicaoOportunidade({
        titulo: 'João',
        lead_nome: 'João',
      }),
    ).toBe('');
  });
});

describe('subtituloModalOportunidade', () => {
  it('não repete prestadora no cabeçalho do modal (fica só no select)', () => {
    expect(
      subtituloModalOportunidade({
        titulo: 'ULTRASIS INFORMATICA LTDA',
        lead_nome: 'JOANA ROSA',
        conta_nome: 'ULTRASIS INFORMATICA LTDA',
        empresa_prestadora_nome: 'ULTRASIS INFORMATICA LTDA',
      }),
    ).toBe('');
  });

  it('mostra empresa do cliente quando diferente da prestadora', () => {
    expect(
      subtituloModalOportunidade({
        titulo: 'Felix Representações',
        lead_nome: 'CAROLINE',
        conta_nome: 'ULTRASIS INFORMATICA LTDA',
        empresa_prestadora_nome: 'Felix Representações',
      }),
    ).toBe('ULTRASIS INFORMATICA LTDA');
  });
});

describe('normalizeListResponse', () => {
  it('aceita array direto', () => {
    expect(normalizeListResponse([{ id: 1 }])).toEqual([{ id: 1 }]);
  });

  it('extrai results paginado', () => {
    expect(normalizeListResponse({ results: [{ id: 2 }] })).toEqual([{ id: 2 }]);
  });

  it('null/undefined retorna vazio', () => {
    expect(normalizeListResponse(null)).toEqual([]);
    expect(normalizeListResponse(undefined)).toEqual([]);
  });
});

describe('formatCrmBrl', () => {
  it('formata número em BRL', () => {
    expect(formatCrmBrl(1234.5)).toContain('1.234');
  });

  it('string vazia retorna vazio', () => {
    expect(formatCrmBrl('')).toBe('');
  });
});

describe('formatCrmBrlCompact', () => {
  it('compacta milhões', () => {
    expect(formatCrmBrlCompact(2_500_000)).toBe('R$ 2.5M');
  });

  it('compacta milhares', () => {
    expect(formatCrmBrlCompact(3500)).toBe('R$ 3.5K');
  });
});
