'use client';

import { useState } from 'react';
import { CheckCircle, Download } from 'lucide-react';

export interface ParteAssinatura {
  papel?: string;
  nome?: string;
  data?: string;
  hora?: string;
}

export interface ConfirmacaoAssinatura {
  ja_assinado?: boolean;
  tipo_documento_display?: string;
  nome_cliente?: string;
  data?: string;
  hora?: string;
  mensagem?: string;
  assinado_pelas_duas_partes?: boolean;
  assinaturas?: ParteAssinatura[];
  pode_baixar_pdf?: boolean;
  logo_loja?: string;
  logo_prestadora?: string;
  nome_loja?: string;
  nome_prestadora?: string;
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

function LogoMarca({ src, alt }: { src?: string; alt: string }) {
  const [visivel, setVisivel] = useState(Boolean(src));
  if (!src || !visivel) return null;
  return (
    <img
      src={src}
      alt={alt}
      className="mx-auto h-12 w-auto max-w-[200px] object-contain sm:h-16 sm:max-w-[240px]"
      onError={() => setVisivel(false)}
    />
  );
}

function quandoAssinou(parte: ParteAssinatura): string {
  return [parte.data, parte.hora].filter(Boolean).join(' às ');
}

export default function DocumentoJaAssinado({
  dados,
  onBaixarPdf,
}: {
  dados: ConfirmacaoAssinatura;
  onBaixarPdf?: () => Promise<void> | void;
}) {
  const [baixando, setBaixando] = useState(false);
  const [erroPdf, setErroPdf] = useState('');
  const titulo = dados.tipo_documento_display
    ? `${dados.tipo_documento_display} assinad${dados.tipo_documento_display.toLowerCase() === 'proposta' ? 'a' : 'o'}`
    : 'Documento assinado';
  const duasPartes = Boolean(dados.assinado_pelas_duas_partes && dados.assinaturas?.length);
  const podeBaixar = Boolean(dados.pode_baixar_pdf && onBaixarPdf);

  const baixar = async () => {
    if (!onBaixarPdf || baixando) return;
    setBaixando(true);
    setErroPdf('');
    try {
      await onBaixarPdf();
    } catch {
      setErroPdf('Não foi possível baixar o PDF. Tente novamente.');
    } finally {
      setBaixando(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 dark:from-slate-950 dark:to-slate-900 flex flex-col p-4 sm:p-8">
      <div className="m-auto bg-white dark:bg-slate-800 rounded-2xl shadow-xl px-5 py-6 sm:px-8 sm:py-8 max-w-md sm:max-w-lg w-full text-center">
        <LogoMarca src={dados.logo_loja} alt={dados.nome_loja || 'Logo da empresa'} />
        <div className={`flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 bg-green-100 dark:bg-green-900/40 rounded-full mx-auto ${dados.logo_loja ? 'mt-4' : ''} mb-4`}>
          <CheckCircle className="w-7 h-7 sm:w-8 sm:h-8 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-2">{titulo}</h2>
        <p className="text-gray-700 dark:text-slate-200 text-base sm:text-lg leading-snug">{mensagemConfirmacao(dados)}</p>
        {duasPartes && (
          <ul className="mt-4 space-y-2 text-left">
            {dados.assinaturas?.map((parte) => (
              <li
                key={`${parte.papel}-${parte.nome}`}
                className="rounded-xl bg-gray-50 dark:bg-slate-900/60 px-3 py-3 sm:px-4"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400">
                  {parte.papel}
                </p>
                <p className="text-base font-semibold text-gray-900 dark:text-white break-words">{parte.nome}</p>
                {quandoAssinou(parte) && (
                  <p className="text-sm text-gray-600 dark:text-slate-300">{quandoAssinou(parte)}</p>
                )}
              </li>
            ))}
          </ul>
        )}
        {podeBaixar && (
          <button
            type="button"
            onClick={() => void baixar()}
            disabled={baixando}
            className="mt-5 flex w-full min-h-12 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-base font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            <Download className="h-5 w-5 shrink-0" />
            <span>{baixando ? 'Baixando...' : 'Baixar PDF assinado'}</span>
          </button>
        )}
        {erroPdf && <p className="mt-3 text-sm text-red-600">{erroPdf}</p>}
        {dados.logo_prestadora && (
          <div className="mt-6 border-t border-gray-100 pt-5 dark:border-slate-700">
            <LogoMarca src={dados.logo_prestadora} alt={dados.nome_prestadora || 'Logo da prestadora'} />
          </div>
        )}
      </div>
    </div>
  );
}
