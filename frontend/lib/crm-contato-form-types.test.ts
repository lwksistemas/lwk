import { describe, expect, it } from 'vitest';
import { aplicarDadosEmpresaNoContato, EMPTY_CONTATO_FORM } from './crm-contato-form-types';

describe('aplicarDadosEmpresaNoContato', () => {
  it('copia telefone e e-mail da empresa', () => {
    const atual = aplicarDadosEmpresaNoContato(
      { ...EMPTY_CONTATO_FORM, nome: 'ANA', conta: '4' },
      { telefone: '(16) 3333-4444', email: 'financeiro@empresa.com' },
    );
    expect(atual?.telefone).toBe('(16) 3333-4444');
    expect(atual?.email).toBe('financeiro@empresa.com');
    expect(atual?.nome).toBe('ANA');
  });

  it('não apaga o que já foi digitado quando a empresa não tem o campo', () => {
    const atual = aplicarDadosEmpresaNoContato(
      { ...EMPTY_CONTATO_FORM, telefone: '(11) 99999-0000', email: 'eu@mail.com' },
      { telefone: '', email: 'empresa@mail.com' },
    );
    expect(atual?.telefone).toBe('(11) 99999-0000');
    expect(atual?.email).toBe('empresa@mail.com');
  });

  it('sem telefone e sem e-mail não altera o formulário', () => {
    expect(aplicarDadosEmpresaNoContato(EMPTY_CONTATO_FORM, { telefone: '  ', email: '' })).toBeNull();
  });
});
