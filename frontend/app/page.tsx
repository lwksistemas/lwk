import Header from "./components/Header";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Modules from "./components/Modules";
import WhyUs from "./components/WhyUs";
import DashboardPreview from "./components/DashboardPreview";
import PwaRedirect from "./components/PwaRedirect";
import { getHomepage } from "@/lib/api";
import type { HomepageData } from "@/types/homepage";

const DEFAULTS: HomepageData = {
  hero: {
    titulo: "Controle total da sua empresa em um único sistema",
    subtitulo: "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.",
    botao_texto: "Testar Gratuitamente",
  },
  funcionalidades: [],
  modulos: [],
};

export default async function HomePage() {
  let data: HomepageData;

  try {
    data = await getHomepage();
  } catch {
    data = DEFAULTS;
  }

  const hero = data.hero ?? DEFAULTS.hero;
  const funcionalidades = data.funcionalidades ?? [];
  const modulos = data.modulos ?? [];

  return (
    <PwaRedirect>
      <main className="w-screen min-w-screen max-w-none overflow-x-hidden bg-gradient-to-b from-slate-50 to-white">
        <Header />
        <Hero hero={hero} />
        <Features funcionalidades={funcionalidades} />
        <DashboardPreview />
        <WhyUs />
        <Modules modulos={modulos} />
        <footer className="w-full bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <p className="text-center md:text-left">
                © 2026 LWKS Sistemas - Todos os direitos reservados
              </p>
              <div className="flex gap-4">
                <a
                  href="/superadmin/login"
                  className="text-white hover:text-blue-200 transition-colors font-medium"
                >
                  Login Admin
                </a>
                <span className="text-blue-300">|</span>
                <a
                  href="/suporte/login"
                  className="text-white hover:text-blue-200 transition-colors font-medium"
                >
                  Login Suporte
                </a>
              </div>
            </div>
          </div>
        </footer>
      </main>
    </PwaRedirect>
  );
}
