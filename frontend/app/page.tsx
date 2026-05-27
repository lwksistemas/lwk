import Header from "./components/Header";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Modules from "./components/Modules";
import WhyUs from "./components/WhyUs";
import DashboardPreview from "./components/DashboardPreview";
import PwaRedirect from "./components/PwaRedirect";
import WhatsAppButton from "@/components/WhatsAppButton";
import { getHomepage } from "@/lib/api";
import type { HomepageData } from "@/types/homepage";

const DEFAULTS: HomepageData = {
  hero: {
    titulo: "Controle total da sua empresa em um único sistema",
    subtitulo: "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.",
    botao_texto: "Testar Gratuitamente",
  },
  hero_imagens: [],
  funcionalidades: [],
  modulos: [],
  whyus: [],
  empresa: null,
};

export default async function HomePage() {
  let data: HomepageData;

  try {
    data = await getHomepage();
  } catch {
    data = DEFAULTS;
  }

  const hero = data.hero ?? DEFAULTS.hero;
  const heroImagens = data.hero_imagens ?? [];
  const funcionalidades = data.funcionalidades ?? [];
  const modulos = data.modulos ?? [];
  const whyus = data.whyus ?? [];
  const empresa = data.empresa ?? null;

  return (
    <PwaRedirect>
      <main className="w-screen min-w-screen max-w-none overflow-x-hidden bg-gradient-to-b from-slate-50 to-white dark:from-gray-900 dark:to-gray-950">
        <Header />
        <Hero hero={hero} heroImagens={heroImagens} />
        <Features funcionalidades={funcionalidades} />
        <DashboardPreview />
        <WhyUs whyus={whyus} />
        <Modules modulos={modulos} />
        <footer className="w-full bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex flex-col gap-6 md:gap-4">
              {/* Dados da empresa */}
              <div className="flex flex-col items-center gap-1 text-center md:items-start md:text-left">
                <p className="text-sm font-semibold text-white">
                  {empresa?.nome_empresa || 'LWK Sistemas'}
                </p>
                {empresa?.cnpj && (
                  <p className="text-xs text-blue-200">
                    CNPJ: {empresa.cnpj}
                  </p>
                )}
                {empresa?.endereco && (
                  <p className="text-xs text-blue-200">
                    {empresa.endereco}
                  </p>
                )}
              </div>

              <div className="flex flex-col md:flex-row justify-between items-center gap-4 border-t border-blue-700 pt-4">
                <p className="text-center text-sm md:text-left">
                  © 2026 {empresa?.nome_empresa || 'LWK Sistemas'} — Todos os direitos reservados
                </p>
                <div className="flex gap-4">
                  <a
                    href="/superadmin/login"
                    className="text-white hover:text-blue-200 transition-colors font-medium text-sm"
                  >
                    Login Admin
                  </a>
                  <span className="text-blue-300">|</span>
                  <a
                    href="/suporte/login"
                    className="text-white hover:text-blue-200 transition-colors font-medium text-sm"
                  >
                    Login Suporte
                  </a>
                </div>
              </div>
            </div>
          </div>
        </footer>
        <WhatsAppButton />
      </main>
    </PwaRedirect>
  );
}
