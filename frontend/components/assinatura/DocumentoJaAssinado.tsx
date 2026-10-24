'use client';

import { CheckCircle } from 'lucide-react';

export interface ConfirmacaoAssinatura {
  ja_assinado?: boolean;
  tipo_documento_display?: string;
  nome_cliente?: string;
  data?: string;
  hora?: string;
  mensagem?: string;
}

export function mensagemConfirmacao(dados: ConfirmacaoAssinatura): string {
  if (dados.mensagem?.trim()) return dados.mensagem.trim();
  const rotulo = dados.tipo_documento_display || 'Documento';
  const nome = (dados.nome_cliente || '').trim();
  const quando = [dados.data, dados.hora].filter(Boolean).join(' às ');
  const particípio = rotulo.toLowerCase() === 'proposta' ? 'assinada' : 'assinado';
  let texto = `${rotulo} ${particípio} digitalmente`;
  if (nome) texto += ` por ${nome}`;
  if (quando) texto += ` em ${quando}`;
  return `${texto}.`;
}

export default function DocumentoJaAssinado({ dados }: { dados: ConfirmacaoAssinatura }) {
  const titulo = dados.tipo_documento_display
    ? `${dados.tipo_documento_display} assinad${dados.tipo_documento_display.toLowerCase() === 'proposta' ? 'a' : 'o'}`
    : 'Documento assinado';

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <div className="flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/40 rounded-full mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">{titulo}</h2>
        <p className="text-gray-700 dark:text-slate-200 text-lg">{mensagemConfirmacao(dados)}</p>
      </div>
    </div>
  );
}
