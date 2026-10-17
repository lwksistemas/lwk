import { describe, expect, it } from 'vitest';
import {
  propostaConfirmCopy,
  propostaOcultaColunaAssinatura,
  rotuloOportunidadePropostaLista,
  rotuloPrestadorPropostaLista,
  rotuloTituloPropostaLista,
} from './crm-propostas-helpers';

describe('rótulos da lista de propostas', () => {
  it('título é o contato e oportunidade é a empresa no CNPJ', () => {
    const linha = {
      lead_nome: 'ANA CLAUDIA',
      titulo: 'MARCHESINI SERVICOS MEDICOS LTDA',
      conta_nome: 'MARCHESINI SERVICOS MEDICOS LTDA',
      prestador_nome: 'ULTRASIS INFORMATICA LTDA',
    };
    expect(rotuloTituloPropostaLista(linha)).toBe('ANA CLAUDIA');
    expect(rotuloOportunidadePropostaLista(linha)).toBe('MARCHESINI SERVICOS MEDICOS LTDA');
    expect(rotuloPrestadorPropostaLista(linha)).toBe('ULTRASIS INFORMATICA LTDA');
  });

  it('CPF mostra pessoa física na oportunidade', () => {
    expect(rotuloOportunidadePropostaLista({ conta_nome: 'PESSOA FISICA' })).toBe('PESSOA FISICA');
    expect(rotuloTituloPropostaLista({ lead_nome: 'ALLAN FERNANDES COSTA', titulo: 'ALLAN FERNANDES COSTA' })).toBe(
      'ALLAN FERNANDES COSTA',
    );
  });
});

describe('crm-propostas-helpers', () => {
  it('propostaOcultaColunaAssinatura em cancelada, pedido ou assinatura concluída', () => {
    expect(propostaOcultaColunaAssinatura({ status: 'cancelada' })).toBe(true);
    expect(propostaOcultaColunaAssinatura({ status: 'pedido' })).toBe(true);
    expect(
      propostaOcultaColunaAssinatura({ status: 'enviada', status_assinatura: 'concluido' }),
    ).toBe(true);
    expect(
      propostaOcultaColunaAssinatura({ status: 'enviada', status_assinatura: 'aguardando_cliente' }),
    ).toBe(false);
  });

  it('propostaConfirmCopy retorna textos de confirmação', () => {
    const assinada = propostaConfirmCopy({
      type: 'marcar_assinado',
      id: 1,
      titulo: 'Proposta A',
    });
    expect(assinada?.confirmLabel).toBe('Marcar assinada');
    expect(assinada?.message).toContain('Proposta A');

    const pedido = propostaConfirmCopy({
      type: 'confirmar_pedido',
      id: 2,
      titulo: 'Proposta B',
    });
    expect(pedido?.confirmLabel).toBe('Confirmar pedido');
    expect(propostaConfirmCopy(null)).toBeNull();
  });
});
