import { describe, expect, it } from 'vitest';
import {
  emitenteFieldsFromApi,
  emitentePayloadFromForm,
  resumoEmitenteLoja,
} from './crm-emitente-loja';

describe('crm-emitente-loja', () => {
  it('payload vazio quando nao personalizado', () => {
    expect(
      emitentePayloadFromForm({
        emitente_personalizado: false,
        emitente_nome: 'X',
        emitente_endereco: '',
        emitente_cpf_cnpj: '',
        emitente_responsavel: '',
        emitente_email: '',
      }),
    ).toEqual({
      emitente_nome: '',
      emitente_endereco: '',
      emitente_cpf_cnpj: '',
      emitente_responsavel: '',
      emitente_email: '',
    });
  });

  it('detecta personalizado pela api', () => {
    const f = emitenteFieldsFromApi({ emitente_nome: 'Parceiro LTDA' });
    expect(f.emitente_personalizado).toBe(true);
    expect(f.emitente_nome).toBe('Parceiro LTDA');
  });

  it('resumo padrao da loja', () => {
    const txt = resumoEmitenteLoja(
      { id: 1, nome: 'Felix', slug: 'felix', cpf_cnpj: '41.449.198/0001-72' },
      {
        emitente_personalizado: false,
        emitente_nome: '',
        emitente_endereco: '',
        emitente_cpf_cnpj: '',
        emitente_responsavel: '',
        emitente_email: '',
      },
    );
    expect(txt).toContain('Felix');
    expect(txt).toContain('padrão da loja');
  });
});
