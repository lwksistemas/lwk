import Link from "next/link";

interface EmpresaFooterData {
  nome_empresa?: string | null;
  cnpj?: string | null;
  endereco?: string | null;
}

export default function Footer({ empresa }: { empresa?: EmpresaFooterData | null }) {
  const nomeEmpresa = empresa?.nome_empresa || "LWK Sistemas";

  return (
    <footer className="w-full bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col gap-6 md:gap-4">
          <div className="flex flex-col items-center gap-1 text-center md:items-start md:text-left">
            <p className="text-sm font-semibold text-white">{nomeEmpresa}</p>
            {empresa?.cnpj && <p className="text-xs text-blue-200">CNPJ: {empresa.cnpj}</p>}
            {empresa?.endereco && <p className="text-xs text-blue-200">{empresa.endereco}</p>}
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center gap-4 border-t border-blue-700 pt-4">
            <p className="text-center text-sm md:text-left">
              © 2026 {nomeEmpresa} — Todos os direitos reservados
            </p>
            <div className="flex gap-4">
              <Link
                href="/superadmin/login"
                className="text-white hover:text-blue-200 transition-colors font-medium text-sm"
              >
                Login Admin
              </Link>
              <span className="text-blue-300">|</span>
              <Link
                href="/suporte/login"
                className="text-white hover:text-blue-200 transition-colors font-medium text-sm"
              >
                Login Suporte
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

