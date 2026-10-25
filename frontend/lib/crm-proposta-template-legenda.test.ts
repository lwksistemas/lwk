import { describe, expect, it } from 'vitest';
import { separarFolhasDoTemplate } from './crm-proposta-template-legenda';

describe('legenda das folhas do template da proposta', () => {
  it('manda o bloco de pagamento para a primeira folha e o resto para as seguintes', () => {
    const folhas = separarFolhasDoTemplate([
      'Vantagens de ser um cliente Anadem',
      'Assistência jurídica especializada.',
      '',
      'Dados para pagamento',
      'Banco: 001',
      'Agência: 1234',
      '',
      'Cobertura',
      'Retroativa de 5 anos.',
    ].join('\n'));

    expect(folhas.primeiraPagina).toBe('Dados para pagamento\nBanco: 001\nAgência: 1234');
    expect(folhas.proximasPaginas).toContain('Vantagens de ser um cliente Anadem');
    expect(folhas.proximasPaginas).toContain('Cobertura');
    expect(folhas.proximasPaginas).not.toContain('Banco: 001');
  });

  it('deixa a primeira folha vazia quando não há o título de pagamento', () => {
    const folhas = separarFolhasDoTemplate('Vantagens\nTexto da cobertura.');
    expect(folhas.primeiraPagina).toBe('');
    expect(folhas.proximasPaginas).toContain('Texto da cobertura.');
  });
});
