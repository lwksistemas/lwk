import Header from "./components/Header";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Modules from "./components/Modules";
import WhyUs from "./components/WhyUs";
import DashboardPreview from "./components/DashboardPreview";
import Footer from "./components/Footer";
import PwaRedirect from "./components/PwaRedirect";
import WhatsAppButton from "@/components/WhatsAppButton";
import { getHomepage } from "@/lib/api";
import type { HomepageData } from "@/types/homepage";

/** ISR: revalida a homepage a cada 5 minutos (reduz Function Invocations no Vercel). */
export const revalidate = 300;

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
        <Footer empresa={empresa} />
        <WhatsAppButton
          empresa={
            empresa?.telefone_whatsapp
              ? {
                  telefone_whatsapp: empresa.telefone_whatsapp,
                  mensagem_whatsapp: empresa.mensagem_whatsapp || "",
                }
              : null
          }
        />
      </main>
    </PwaRedirect>
  );
}
