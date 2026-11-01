import Link from "next/link";
import { urlWhatsapp } from "@/lib/whatsapp-site";

interface EmpresaFooterData {
  nome_empresa?: string | null;
  cnpj?: string | null;
  endereco?: string | null;
  telefone_whatsapp?: string | null;
  mensagem_whatsapp?: string | null;
  email_contato?: string | null;
}

export default function Footer({ empresa }: { empresa?: EmpresaFooterData | null }) {
  const nomeEmpresa = empresa?.nome_empresa || "LWK Sistemas";
  const whatsapp = urlWhatsapp(empresa?.telefone_whatsapp, empresa?.mensagem_whatsapp);

  return (
    <footer id="contato" className="w-full bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col gap-6 md:gap-4">
          <div className="flex flex-col items-center gap-1 text-center md:items-start md:text-left">
            <p className="text-sm font-semibold text-white">{nomeEmpresa}</p>
            {empresa?.cnpj && <p className="text-xs text-blue-200">CNPJ: {empresa.cnpj}</p>}
            {empresa?.endereco && <p className="text-xs text-blue-200">{empresa.endereco}</p>}
            {empresa?.email_contato && <p className="text-xs text-blue-200">{empresa.email_contato}</p>}
            {empresa?.telefone_whatsapp && <p className="text-xs text-blue-200">WhatsApp: {empresa.telefone_whatsapp}</p>}
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center gap-4 border-t border-blue-700 pt-4">
            <p className="text-center text-sm md:text-left">
              © 2026 {nomeEmpresa} — Todos os direitos reservados
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link href="/privacidade" className="text-white hover:text-blue-200 transition-colors font-medium text-sm">
                Política de Privacidade
              </Link>
              <span className="text-blue-300">|</span>
              <Link href="/contato" className="text-white hover:text-blue-200 transition-colors font-medium text-sm">
                Contato
              </Link>
              {whatsapp && (
                <>
                  <span className="text-blue-300">|</span>
                  <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="text-white hover:text-blue-200 transition-colors font-medium text-sm">
                    WhatsApp
                  </a>
                </>
              )}
              <span className="text-blue-300">|</span>
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

