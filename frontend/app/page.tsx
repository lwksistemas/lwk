import Header from "./components/Header";
import Hero from "./components/Hero";
import VitrineHome from "./components/VitrineHome";
import Footer from "./components/Footer";
import PwaRedirect from "./components/PwaRedirect";
import { getHomepage } from "@/lib/api";
import { urlWhatsapp } from "@/lib/whatsapp-site";
import type { HomepageData } from "@/types/homepage";
import type { Metadata } from "next";

/** ISR: revalida a homepage a cada 60s para refletir edições do superadmin. */
export const revalidate = 60;

export const metadata: Metadata = {
  title: "LWK Sistemas | CRM, Gestão para Clínicas e Software Personalizado",
  description:
    "Sistemas para clínicas de estética, CRM de vendas e software sob medida. Peça uma demonstração.",
};

const DEFAULTS: HomepageData = {
  hero: {
    titulo: "Soluções de software para o seu negócio.",
    subtitulo:
      "Desenvolvemos sistemas e soluções personalizadas para clínicas de estética, CRM de vendas e diversos outros segmentos, com tecnologia, segurança e suporte especializado.",
    selo: "Software House",
    botao_texto: "Conheça nossas soluções",
    botao_url: "#solucoes",
    botao_principal_ativo: true,
    botao_secundario_texto: "Solicite uma demonstração",
    botao_secundario_url: "/demonstracao",
    botao_secundario_ativo: true,
  },
  hero_imagens: [],
  funcionalidades: [],
  modulos: [],
  whyus: [],
  empresa: null,
  menu: { solucoes: [], segmentos: [] },
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
  const empresa = data.empresa ?? null;
  const whatsapp = urlWhatsapp(empresa?.telefone_whatsapp, empresa?.mensagem_whatsapp);

  return (
    <PwaRedirect>
      <main id="inicio" className="w-full max-w-none scroll-smooth overflow-x-hidden bg-white dark:bg-gray-950">
        <Header
          solucoes={(data.menu?.solucoes ?? []).map((item) => ({ label: item.rotulo, href: item.url }))}
          segmentos={(data.menu?.segmentos ?? []).map((item) => ({ label: item.rotulo, href: item.url }))}
          whatsappUrl={whatsapp}
        />
        <div className="flex flex-col bg-[#031433] lg:h-[calc(100dvh-5.5rem)] lg:overflow-hidden" style={{ backgroundImage: "radial-gradient(820px 460px at 72% 38%, rgba(70,160,255,0.45), transparent 60%), radial-gradient(380px 280px at 18% 78%, rgba(20,90,180,0.35), transparent 70%), linear-gradient(180deg, #04183f 0%, #0a3478 46%, #0c3f8c 68%, #071833 100%)" }}>
          <Hero hero={hero} heroImagens={heroImagens} destaques={funcionalidades} />
        </div>
        <VitrineHome telefone={empresa?.telefone_whatsapp} email={empresa?.email_contato} />
        <Footer empresa={empresa} />
      </main>
    </PwaRedirect>
  );
}
