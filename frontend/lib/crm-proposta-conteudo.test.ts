import { describe, expect, it } from 'vitest';

import { conteudoComDescricoes } from './crm-proposta-conteudo';

describe('conteudoComDescricoes', () => {
  it('coloca a descrição do serviço no conteúdo', () => {
    const texto = 'ANADEM GREEN 2026. Medicina. Pessoa física. Especialidades: ACUPUNTURA.';
    expect(conteudoComDescricoes('', [{ produto_servico_descricao: texto }])).toBe(texto);
  });

  it('não repete a descrição que já está no conteúdo', () => {
    const texto = 'ANADEM GREEN 2026. Medicina.';
    expect(conteudoComDescricoes(texto, [{ produto_servico_descricao: texto }])).toBe(texto);
  });
});
