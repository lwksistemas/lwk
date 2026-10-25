import { describe, expect, it } from 'vitest';
import {
  juntarFolhasDoTemplate,
  separarFolhasDoTemplate,
  textoVisivelDoTemplate,
} from './crm-proposta-template-legenda';

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

  it('mantém a linha do banco na primeira folha até a linha em branco', () => {
    const folhas = separarFolhasDoTemplate([
      'Dados para pagamento',
      'Banco, agência, conta, CNPJ e PIX da Anadem',
      '',
      'Vantagens',
      'Texto da cobertura.',
    ].join('\n'));

    expect(folhas.primeiraPagina).toBe(
      'Dados para pagamento\nBanco, agência, conta, CNPJ e PIX da Anadem',
    );
    expect(folhas.proximasPaginas).toBe('Vantagens\nTexto da cobertura.');
  });

  it('grava e reabre as duas folhas do jeito que foram escritas', () => {
    const primeira = 'Dados para pagamento\nBanco, agência, conta, CNPJ e PIX da Anadem\n\nUma linha a mais.';
    const proximas = 'Vantagens de ser um cliente Anadem\n\nCobertura nacional.';
    const gravado = juntarFolhasDoTemplate(primeira, proximas);
    const folhas = separarFolhasDoTemplate(gravado);

    expect(folhas.primeiraPagina).toBe(primeira);
    expect(folhas.proximasPaginas).toBe(proximas);
    expect(textoVisivelDoTemplate(gravado)).not.toContain('[[folha:2]]');
    expect(textoVisivelDoTemplate(gravado)).toContain('Cobertura nacional.');
  });

  it('deixa a primeira folha vazia quando não há o título de pagamento', () => {
    const folhas = separarFolhasDoTemplate('Vantagens\nTexto da cobertura.');
    expect(folhas.primeiraPagina).toBe('');
    expect(folhas.proximasPaginas).toContain('Texto da cobertura.');
  });
});
