import { describe, expect, it } from 'vitest';
import { calcularDuracaoAgendamento, tempoConsultaBaseMinutos } from './clinica-beleza-duracao';
import {
  cpfCnpjValido,
  formatTelefone,
  mensagemCpfCnpjInvalido,
  telefoneInternacionalBr,
} from './format-br';

describe('telefone e documento', () => {
  it('mascara o celular e grava com 55', () => {
    expect(formatTelefone('16999621823')).toBe('(16) 99962-1823');
    expect(telefoneInternacionalBr('(16) 99962-1823')).toBe('5516999621823');
    expect(formatTelefone('550422761222')).toBe('(42) 2761-222');
    expect(formatTelefone('554792561525')).toBe('(47) 9256-1525');
    expect(telefoneInternacionalBr('')).toBe('');
  });

  it('aceita um CPF conhecido e recusa sequência repetida', () => {
    expect(cpfCnpjValido('390.533.447-05')).toBe(true);
    expect(mensagemCpfCnpjInvalido('111.111.111-11')).toContain('inválido');
    expect(mensagemCpfCnpjInvalido('')).toContain('Informe');
  });
});

describe('duração do atendimento', () => {
  it('usa o tempo do profissional e não fica abaixo da soma dos procedimentos', () => {
    expect(tempoConsultaBaseMinutos({ tempo_consulta_minutos: 40 }, { tempo_consulta_minutos: 20 })).toBe(40);
    expect(tempoConsultaBaseMinutos(null, null)).toBe(30);
    expect(calcularDuracaoAgendamento(90, { tempo_consulta_minutos: 40 })).toBe(90);
    expect(calcularDuracaoAgendamento(0, { tempo_consulta_minutos: 40 })).toBe(40);
  });
});
