import { describe, expect, it } from 'vitest';
import { calcIMC, calcSC, coletarCirurgias, coletarDiagnosticos, emptyFicha, fichaParaSoap, filtrarAbasAtendimento, formatTimer, isAnexoImagem, mergeFicha, resumoAbaFicha, toggleItem, ABAS_ATENDIMENTO } from '@/lib/clinica-geral-atendimento';

describe('clinica-geral-atendimento', () => {
  it('calcula IMC, SC e o cronômetro', () => {
    expect(calcIMC('70', '170')).toBe('24.2');
    expect(calcSC('70', '170')).toBe('1.82');
    expect(formatTimer(5)).toBe('00:05');
    expect(formatTimer(125)).toBe('02:05');
  });

  it('alterna tags e monta SOAP a partir da ficha', () => {
    const lista = toggleItem([], 'Depressão');
    expect(lista).toHaveLength(1);
    expect(toggleItem(lista, 'Depressão')).toEqual([]);
    const ficha = mergeFicha({
      ...emptyFicha(),
      queixas: [{ nome: 'Cefaléia', duracao: 'Até 24h' }],
      historia_doenca: 'Dor há 1 dia',
      diagnostico: 'Cefaleia tensional',
      tratamentos: [{ nome: 'Dipirona' }],
    });
    const soap = fichaParaSoap(ficha);
    expect(soap.subjetivo).toContain('Cefaléia');
    expect(soap.avaliacao).toBe('Cefaleia tensional');
    expect(soap.plano).toContain('Dipirona');
  });

  it('monta o DIAG do resumo clínico com diagnóstico atual e antigo', () => {
    const rows = coletarDiagnosticos(
      [
        {
          id: 1,
          consulta: 10,
          paciente: 3,
          especialidade: '',
          subjetivo: '',
          objetivo: '',
          avaliacao: '',
          plano: '',
          ficha: {
            ...emptyFicha(),
            diagnostico: 'N18 - Insuficiência renal crônica',
            antecedentes_clinicos: [{ nome: 'Depressão' }],
            antecedentes_cirurgicos: [{ nome: 'Apendicectomia' }],
          },
        },
      ],
      [{ id: 10, data: '2026-08-23', hora: '18:25' } as never],
    );
    expect(rows.map((r) => r.texto)).toEqual([
      'N18 - Insuficiência renal crônica',
      'Depressão (Diagnóstico antigo)',
    ]);
    expect(coletarCirurgias([
      { ficha: { ...emptyFicha(), antecedentes_cirurgicos: [{ nome: 'Apendicectomia' }] } } as never,
    ])).toEqual(['Apendicectomia']);
  });

  it('resume a aba HMA e reconhece foto em anexo', () => {
    expect(resumoAbaFicha('HMA', mergeFicha({ queixas: [{ nome: 'Cefaléia', duracao: 'Até 24h' }], historia_doenca: 'Dor há 1 dia' }))).toEqual([
      'Cefaléia — Até 24h',
      'Dor há 1 dia',
    ]);
    expect(isAnexoImagem('raio-x.jpg')).toBe(true);
    expect(isAnexoImagem('laudo.pdf')).toBe(false);
  });

  it('esconde abas ocultas do atendimento e nunca deixa a lista vazia', () => {
    const visiveis = filtrarAbasAtendimento(['EM', 'Lx']);
    expect(visiveis.some((a) => a.id === 'EM')).toBe(false);
    expect(visiveis.some((a) => a.id === 'HMA')).toBe(true);
    expect(filtrarAbasAtendimento(ABAS_ATENDIMENTO.map((a) => a.id)).length).toBe(ABAS_ATENDIMENTO.length);
  });
});
