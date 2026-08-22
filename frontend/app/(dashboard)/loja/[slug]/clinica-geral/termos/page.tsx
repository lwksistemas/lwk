'use client';

export default function ClinicaGeralTermosPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 p-8">
      <h1 className="text-xl font-semibold text-slate-800">Termos de uso</h1>
      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-6 text-sm leading-6 text-slate-600">
        <p>
          O LWK Sistemas é um sistema de gestão para consultórios. Os dados de pacientes e consultas
          pertencem à loja contratante e devem ser tratados conforme a LGPD.
        </p>
        <p>
          O acesso é pessoal. Não compartilhe senha. Use o menu do usuário para alterar a senha e
          abrir chamado de suporte quando necessário.
        </p>
        <p>
          O uso do sistema implica concordância com a política de privacidade disponível em{' '}
          <a href="https://lwksistemas.com.br" className="text-teal-700 hover:underline">
            lwksistemas.com.br
          </a>
          .
        </p>
      </div>
    </div>
  );
}
