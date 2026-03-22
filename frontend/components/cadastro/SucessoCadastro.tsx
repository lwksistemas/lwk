import Link from 'next/link';

interface SucessoCadastroProps {
  loja: any;
  email: string;
}

export function SucessoCadastro({ loja, email }: SucessoCadastroProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center">
        <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6 animate-bounce">
          <span className="text-5xl text-green-600">✓</span>
        </div>
        
        <h2 className="text-3xl font-bold text-gray-800 mb-2">
          Cadastro realizado com sucesso!
        </h2>
        <p className="text-xl text-purple-600 font-semibold mb-6">{loja.nome}</p>
        
        {/* Informação sobre boleto */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-900 font-medium mb-2">
            📧 Boleto enviado para o email
          </p>
          <p className="text-sm text-blue-800">
            A senha de acesso será enviada automaticamente para <strong>{email}</strong> após a confirmação do pagamento.
          </p>
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
              ? `${window.location.origin}${loja.login_page_url}` 
              : loja.login_page_url}
          </p>
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
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
        >
          Voltar para Home
        </Link>
      </div>
    </div>
  );
}
