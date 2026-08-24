import { describe, expect, it } from 'vitest';
import { formatApiErrorBody } from './api-errors';
import { getCrmApiErrorDetail } from './crm-utils';

describe('formatApiErrorBody', () => {
  it('mostra non_field_errors sem prefixo técnico', () => {
    expect(
      formatApiErrorBody({
        non_field_errors: ['Já existe um lead cadastrado com este CPF/CNPJ nesta loja.'],
      }),
    ).toBe('Já existe um lead cadastrado com este CPF/CNPJ nesta loja.');
  });

  it('mostra duplicata de cpf_cnpj sem prefixo do campo', () => {
    expect(
      formatApiErrorBody({
        cpf_cnpj: ['Já existe um lead cadastrado com este CPF/CNPJ nesta loja.'],
      }),
    ).toBe('Já existe um lead cadastrado com este CPF/CNPJ nesta loja.');
  });

  it('mantém prefixo em erros de campo genéricos', () => {
    expect(formatApiErrorBody({ email: ['Insira um endereço de e-mail válido.'] })).toBe(
      'email: Insira um endereço de e-mail válido.',
    );
  });
});

describe('getCrmApiErrorDetail', () => {
  it('extrai duplicata de lead em non_field_errors (produção Felix)', () => {
    expect(
      getCrmApiErrorDetail(
        {
          response: {
            status: 400,
            data: {
              non_field_errors: ['Já existe um lead cadastrado com este CPF/CNPJ nesta loja.'],
            },
          },
        },
        'Erro ao salvar lead.',
      ),
    ).toBe('Já existe um lead cadastrado com este CPF/CNPJ nesta loja.');
  });

  it('usa fallback quando a API não devolve corpo', () => {
    expect(getCrmApiErrorDetail({ response: { status: 500 } }, 'Erro ao salvar lead.')).toBe(
      'Erro ao salvar lead.',
    );
  });
});
