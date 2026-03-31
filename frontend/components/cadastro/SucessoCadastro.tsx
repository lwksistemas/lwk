import Link from 'next/link';
import { CadastroFundo } from '@/components/cadastro/CadastroFundo';

interface SucessoCadastroProps {
  loja: any;
  email: string;
}

export function SucessoCadastro({ loja, email }: SucessoCadastroProps) {
  return (
    <div className="relative isolate flex min-h-[100dvh] min-h-screen items-center justify-center overflow-x-hidden px-3 py-8 sm:px-4 sm:py-10">
      <CadastroFundo />

      <div className="relative z-10 w-full max-w-2xl rounded-xl border border-slate-200/80 bg-white/95 p-6 text-center shadow-xl shadow-slate-900/10 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-900/90 sm:rounded-2xl sm:p-8 sm:shadow-2xl">
        <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6 animate-bounce">
          <span className="text-5xl text-green-600">✓</span>
        </div>
        
        <h2 className="mb-2 text-2xl font-bold text-gray-800 dark:text-slate-100 sm:text-3xl">
          Cadastro realizado com sucesso!
        </h2>
        <p className="mb-6 text-lg font-semibold text-indigo-700 dark:text-indigo-300 sm:text-xl">
          {loja.nome}
        </p>
        
        {/* Informação importante sobre senha */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 rounded-lg p-5 mb-6">
          <div className="flex items-start gap-3">
            <span className="text-3xl">🔐</span>
            <div className="text-left flex-1">
              <p className="text-base font-bold text-blue-900 mb-2">
                Importante: Senha de Acesso
              </p>
              <p className="text-sm text-blue-800 mb-2">
                A senha de acesso será <strong>gerada automaticamente</strong> e enviada para o email <strong className="text-purple-700">{email}</strong> após a confirmação do pagamento.
              </p>
              <p className="text-xs text-blue-700 bg-blue-100 rounded px-2 py-1 inline-block">
                💡 Verifique também a caixa de spam
              </p>
            </div>
          </div>
        </div>

        {/* Links de pagamento */}
        {(loja.boleto_url || loja.pix_qr_code) && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
            <p className="text-sm font-semibold text-purple-900 mb-3">
              Formas de pagamento disponíveis:
            </p>
            <div className="space-y-2">
              {loja.boleto_url && (
                <a
                  href={loja.boleto_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block px-4 py-2 bg-white border border-purple-300 rounded-md hover:bg-purple-100 transition text-purple-700 font-medium"
                >
                  🧾 Abrir Boleto
                </a>
              )}
              {loja.pix_qr_code && (
                <div className="block px-4 py-2 bg-white border border-purple-300 rounded-md text-purple-700">
                  📱 QR Code PIX disponível
                </div>
              )}
            </div>
          </div>
        )}

        {/* URL de acesso */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-gray-600 mb-2">URL de acesso ao sistema:</p>
          <p className="font-mono text-sm text-gray-800 break-all">
            {typeof window !== 'undefined' 
              ? `${window.location.origin}/${loja.atalho || `loja/${loja.slug}/login`}` 
              : `/${loja.atalho || `loja/${loja.slug}/login`}`}
          </p>
          {loja.atalho && (
            <p className="text-xs text-gray-500 mt-2">
              ✨ URL amigável: /{loja.atalho}
            </p>
          )}
        </div>

        {/* Próximos passos */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 text-left">
          <p className="text-sm font-semibold text-yellow-900 mb-2">📋 Próximos passos:</p>
          <ol className="text-sm text-yellow-800 space-y-1 list-decimal list-inside">
            <li>Realize o pagamento do boleto ou PIX</li>
            <li>Aguarde a confirmação do pagamento (1-3 dias úteis para boleto)</li>
            <li>Você receberá a senha por email automaticamente</li>
            <li>Acesse o sistema e comece a usar!</li>
          </ol>
        </div>
        
        <Link
          href="/"
          className="inline-block min-h-[48px] w-full rounded-lg bg-blue-600 px-6 py-3 text-base font-medium text-white transition hover:bg-blue-700 sm:w-auto"
        >
          Voltar para Home
        </Link>
      </div>
    </div>
  );
}
