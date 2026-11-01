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
    <footer id="contato" className="w-full border-t border-white/10 bg-[#031433] text-white">
      <div className="w-full px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-semibold text-white">{nomeEmpresa}</p>
            {empresa?.cnpj && <p className="text-sm text-slate-300">CNPJ: {empresa.cnpj}</p>}
            {empresa?.endereco && <p className="text-sm text-slate-300">{empresa.endereco}</p>}
            {empresa?.email_contato && <p className="text-sm text-slate-300">{empresa.email_contato}</p>}
            {empresa?.telefone_whatsapp && <p className="text-sm text-slate-300">WhatsApp: {empresa.telefone_whatsapp}</p>}
          </div>

          <div className="flex flex-col gap-4 border-t border-white/10 pt-4 md:flex-row md:items-center md:justify-between">
            <p className="text-sm text-slate-300">
              © 2026 {nomeEmpresa} — Todos os direitos reservados
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link href="/privacidade" className="text-sm font-medium text-white hover:text-sky-200">
                Política de Privacidade
              </Link>
              <span className="text-white/30">|</span>
              <Link href="/contato" className="text-sm font-medium text-white hover:text-sky-200">
                Contato
              </Link>
              {whatsapp && (
                <>
                  <span className="text-white/30">|</span>
                  <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-white hover:text-sky-200">
                    WhatsApp
                  </a>
                </>
              )}
              <span className="text-white/30">|</span>
              <Link
                href="/superadmin/login"
                className="text-sm font-medium text-white hover:text-sky-200"
              >
                Login Admin
              </Link>
              <span className="text-white/30">|</span>
              <Link
                href="/suporte/login"
                className="text-sm font-medium text-white hover:text-sky-200"
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

