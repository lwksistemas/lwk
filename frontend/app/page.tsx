import Header from "./components/Header";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Modules from "./components/Modules";
import PwaRedirect from "./components/PwaRedirect";
import { getHomepage } from "@/lib/api";
import type { HomepageData } from "@/types/homepage";

const DEFAULTS: HomepageData = {
  hero: {
    titulo: "LWK SISTEMAS",
    subtitulo: "Gestão de Lojas",
    botao_texto: "Testar grátis",
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
      <main>
        <Header />
        <Hero hero={hero} />
        <Features funcionalidades={funcionalidades} />
        <Modules modulos={modulos} />
        <footer className="bg-gray-900 text-white text-center p-6">
          © 2026 LWKS Sistemas - Todos os direitos reservados
        </footer>
      </main>
    </PwaRedirect>
  );
}
