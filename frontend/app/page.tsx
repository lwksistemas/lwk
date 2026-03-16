import Header from "./components/Header";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Modules from "./components/Modules";
import WhyUs from "./components/WhyUs";
import DashboardPreview from "./components/DashboardPreview";
import CtaSection from "./components/CtaSection";
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
      <main className="w-screen min-w-screen max-w-none overflow-x-hidden">
        <Header />
        <Hero hero={hero} />
        <Features funcionalidades={funcionalidades} />
        <DashboardPreview />
        <WhyUs />
        <Modules modulos={modulos} />
        <CtaSection />
        <footer className="w-full bg-blue-900 text-white text-center p-6">
          © 2026 LWKS Sistemas - Todos os direitos reservados
        </footer>
      </main>
    </PwaRedirect>
  );
}
