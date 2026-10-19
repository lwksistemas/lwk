/**
 * Login por rosto do aparelho (Face ID ou desbloqueio facial).
 * O navegador confirma o rosto. O servidor não recebe foto nem biometria.
 */

import apiClient from './api-client';
import { authService, type LoginResponse } from './auth';

export type AlvoRosto = {
  userType: 'superadmin' | 'suporte' | 'loja';
  slug?: string;
  username: string;
};

function chaveAtivado(alvo: AlvoRosto) {
  return `rosto_ativado_${alvo.userType}_${alvo.slug || 'sistema'}_${alvo.username.trim().toLowerCase()}`;
}

function corpo(alvo: AlvoRosto) {
  return {
    username: alvo.username.trim(),
    user_type: alvo.userType,
    ...(alvo.userType === 'loja' ? { loja_slug: alvo.slug || '' } : {}),
  };
}

function deBase64Url(valor: string): Uint8Array {
  const falta = valor.length % 4 === 0 ? '' : '='.repeat(4 - (valor.length % 4));
  const base64 = valor.replace(/-/g, '+').replace(/_/g, '/') + falta;
  const binario = atob(base64);
  const saida = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i += 1) saida[i] = binario.charCodeAt(i);
  return saida;
}

function paraBase64Url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binario = '';
  bytes.forEach((byte) => {
    binario += String.fromCharCode(byte);
  });
  return btoa(binario).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

type OpcoesJson = {
  challenge: string;
  user?: { id: string; name: string; displayName: string };
  excludeCredentials?: { id: string; type: string }[];
  allowCredentials?: { id: string; type: string }[];
  [chave: string]: unknown;
};

function opcoesDeCriacao(json: OpcoesJson): PublicKeyCredentialCreationOptions {
  const user = json.user;
  if (!user) throw new Error('Não foi possível ativar o rosto neste aparelho.');
  return {
    ...(json as unknown as PublicKeyCredentialCreationOptions),
    challenge: deBase64Url(json.challenge) as BufferSource,
    user: {
      ...user,
      id: deBase64Url(user.id) as BufferSource,
    },
    excludeCredentials: (json.excludeCredentials || []).map((item) => ({
      ...item,
      id: deBase64Url(item.id) as BufferSource,
    })),
  } as PublicKeyCredentialCreationOptions;
}

function opcoesDeEntrada(json: OpcoesJson): PublicKeyCredentialRequestOptions {
  return {
    ...(json as unknown as PublicKeyCredentialRequestOptions),
    challenge: deBase64Url(json.challenge) as BufferSource,
    allowCredentials: (json.allowCredentials || []).map((item) => ({
      ...item,
      id: deBase64Url(item.id) as BufferSource,
    })),
  } as PublicKeyCredentialRequestOptions;
}

function credencialDeRegistro(credencial: PublicKeyCredential) {
  const resposta = credencial.response as AuthenticatorAttestationResponse;
  return {
    id: credencial.id,
    rawId: paraBase64Url(credencial.rawId),
    type: credencial.type,
    response: {
      clientDataJSON: paraBase64Url(resposta.clientDataJSON),
      attestationObject: paraBase64Url(resposta.attestationObject),
    },
  };
}

function credencialDeEntrada(credencial: PublicKeyCredential) {
  const resposta = credencial.response as AuthenticatorAssertionResponse;
  return {
    id: credencial.id,
    rawId: paraBase64Url(credencial.rawId),
    type: credencial.type,
    response: {
      clientDataJSON: paraBase64Url(resposta.clientDataJSON),
      authenticatorData: paraBase64Url(resposta.authenticatorData),
      signature: paraBase64Url(resposta.signature),
      userHandle: resposta.userHandle ? paraBase64Url(resposta.userHandle) : null,
    },
  };
}

export async function aparelhoTemRosto(): Promise<boolean> {
  if (typeof window === 'undefined' || !window.PublicKeyCredential?.isUserVerifyingPlatformAuthenticatorAvailable) {
    return false;
  }
  try {
    return await window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
  } catch {
    return false;
  }
}

function mensagemDoNavegador(erro: unknown): string {
  const resposta = erro && typeof erro === 'object' && 'response' in erro
    ? (erro as { response?: { data?: { error?: unknown } } }).response?.data
    : null;
  if (typeof resposta?.error === 'string') return resposta.error;
  const nome = erro && typeof erro === 'object' && 'name' in erro ? String((erro as { name: string }).name) : '';
  if (nome === 'NotAllowedError') {
    return 'O rosto não foi confirmado. Entre com a senha uma vez para ativar neste aparelho.';
  }
  if (erro instanceof Error && erro.message) return erro.message;
  return 'Não foi possível usar o rosto neste aparelho.';
}

export async function registrarRosto(alvo: AlvoRosto): Promise<void> {
  const opcoes = await apiClient.post('/auth/rosto/registrar/opcoes/', {
    user_type: alvo.userType,
    ...(alvo.userType === 'loja' ? { loja_slug: alvo.slug || '' } : {}),
  });
  const criada = await navigator.credentials.create({
    publicKey: opcoesDeCriacao(opcoes.data.publicKey),
  });
  if (!criada) throw new Error('O rosto não foi confirmado.');
  await apiClient.post('/auth/rosto/registrar/', {
    user_type: alvo.userType,
    ...(alvo.userType === 'loja' ? { loja_slug: alvo.slug || '' } : {}),
    credential: credencialDeRegistro(criada as PublicKeyCredential),
  });
  localStorage.setItem(chaveAtivado(alvo), '1');
}

export async function perguntarAtivarRosto(alvo: AlvoRosto): Promise<void> {
  if (!(await aparelhoTemRosto())) return;
  if (!alvo.username.trim()) return;
  const chave = chaveAtivado(alvo);
  if (localStorage.getItem(chave) === '1') return;
  if (sessionStorage.getItem(`${chave}_adiado`) === '1') return;
  const aceita = window.confirm(
    'Ativar o rosto neste aparelho?\n\nO Face ID ou o desbloqueio facial passa a liberar o login.',
  );
  if (!aceita) {
    sessionStorage.setItem(`${chave}_adiado`, '1');
    return;
  }
  try {
    await registrarRosto(alvo);
  } catch {
    /* A senha já entrou. O rosto pode ser ativado na próxima vez. */
  }
}

export async function entrarComRosto(alvo: AlvoRosto): Promise<LoginResponse> {
  if (!alvo.username.trim()) {
    throw new Error('Digite o usuário para usar o rosto.');
  }
  if (!(await aparelhoTemRosto())) {
    throw new Error('Este aparelho não oferece Face ID ou desbloqueio facial.');
  }
  try {
    const opcoes = await apiClient.post('/auth/rosto/entrar/opcoes/', corpo(alvo));
    const afirmacao = await navigator.credentials.get({
      publicKey: opcoesDeEntrada(opcoes.data.publicKey),
    });
    if (!afirmacao) throw new Error('O rosto não foi confirmado.');
    const sessao = await authService.loginRosto(alvo, credencialDeEntrada(afirmacao as PublicKeyCredential));
    localStorage.setItem(chaveAtivado(alvo), '1');
    return sessao;
  } catch (erro) {
    throw new Error(mensagemDoNavegador(erro));
  }
}
