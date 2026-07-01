'use client';

import { useCallback, useState } from 'react';
import { consultaCep } from '@/lib/consulta-cep';
import { consultaCnpj } from '@/lib/consulta-cnpj';
import { toUpperCase } from '@/lib/format-br';
import { useToast } from '@/components/ui/Toast';

export interface CrmEnderecoFields {
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
}

export interface CrmCnpjFields extends CrmEnderecoFields {
  nome: string;
  empresa: string;
  cpf_cnpj: string;
}

type ApplyPatch<T> = (updater: (prev: T) => T) => void;

/** Busca CEP/CNPJ com toast — compartilhado entre formulários de Lead. */
export function useCrmCepCnpjLookup<T extends CrmCnpjFields>(
  onFormChange: ApplyPatch<T>,
  options?: { upperCaseEndereco?: boolean },
) {
  const toast = useToast();
  const upperCaseEndereco = options?.upperCaseEndereco ?? false;
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

  const handleBuscarCnpj = useCallback(
    async (cpfCnpj: string) => {
      const cnpj = cpfCnpj.replace(/\D/g, '');
      if (cnpj.length !== 14) {
        toast.warning('Informe um CNPJ válido com 14 dígitos para buscar.');
        return;
      }
      setBuscarCnpjLoading(true);
      try {
        const data = await consultaCnpj(cpfCnpj);
        if (data) {
          onFormChange((f) => ({
            ...f,
            nome: data.razao_social || f.nome,
            empresa: data.nome_fantasia || f.empresa,
            cep: data.cep || f.cep,
            logradouro: data.logradouro || f.logradouro,
            numero: data.numero || f.numero,
            complemento: data.complemento || f.complemento,
            bairro: data.bairro || f.bairro,
            cidade: data.municipio || f.cidade,
            uf: data.uf || f.uf,
          }));
        } else {
          toast.warning('CNPJ não encontrado ou serviço indisponível.');
        }
      } catch {
        toast.error('Erro ao consultar CNPJ. Tente novamente.');
      } finally {
        setBuscarCnpjLoading(false);
      }
    },
    [onFormChange, toast],
  );

  const handleBuscarCep = useCallback(
    async (cep: string) => {
      const digits = cep.replace(/\D/g, '');
      if (digits.length !== 8) {
        toast.warning('Informe um CEP válido com 8 dígitos.');
        return;
      }
      setBuscarCepLoading(true);
      try {
        const endereco = await consultaCep(cep);
        if (endereco) {
          onFormChange((f) => ({
            ...f,
            logradouro: upperCaseEndereco ? toUpperCase(endereco.logradouro) : endereco.logradouro,
            bairro: upperCaseEndereco ? toUpperCase(endereco.bairro) : endereco.bairro,
            cidade: upperCaseEndereco ? toUpperCase(endereco.cidade) : endereco.cidade,
            uf: upperCaseEndereco ? endereco.uf.toUpperCase() : endereco.uf,
          }));
        } else {
          toast.error('Erro ao consultar CEP. Verifique sua conexão ou tente novamente em instantes.');
        }
      } finally {
        setBuscarCepLoading(false);
      }
    },
    [onFormChange, toast, upperCaseEndereco],
  );

  return { handleBuscarCnpj, handleBuscarCep, buscarCepLoading, buscarCnpjLoading };
}
