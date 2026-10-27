'use client';

import { useState } from 'react';
import { entrarComRosto, type AlvoRosto } from '@/lib/rosto-login';
import type { LoginResponse } from '@/lib/auth';

type Props = AlvoRosto & {
  cor: string;
  disabled?: boolean;
  onSucesso: (sessao: LoginResponse) => void | Promise<void>;
  onErro: (mensagem: string) => void;
};

export default function BotaoRosto({
  userType,
  slug,
  username,
  cor,
  disabled,
  onSucesso,
  onErro,
}: Props) {
  const [ocupado, setOcupado] = useState(false);

  const usarRosto = async () => {
    setOcupado(true);
    onErro('');
    try {
      const sessao = await entrarComRosto({ userType, slug, username });
      await onSucesso(sessao);
    } catch (erro) {
      onErro(erro instanceof Error ? erro.message : 'Não foi possível usar o desbloqueio facial.');
    } finally {
      setOcupado(false);
    }
  };

  return (
    <button
      type="button"
      onClick={usarRosto}
      disabled={disabled || ocupado}
      className="w-full py-3 px-4 min-h-[48px] font-semibold rounded-md border bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      style={{ color: cor, borderColor: cor }}
    >
      {ocupado ? 'Confirmando...' : 'Facial'}
    </button>
  );
}
