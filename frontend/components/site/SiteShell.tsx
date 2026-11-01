import type { HomepageData } from "@/types/homepage";
import Header from "@/app/components/Header";
import Footer from "@/app/components/Footer";
import { urlWhatsapp } from "@/lib/whatsapp-site";

export function SiteShell({
  data,
  children,
}: {
  data: HomepageData;
  children: React.ReactNode;
}) {
  const empresa = data.empresa;
  const whatsapp = urlWhatsapp(empresa?.telefone_whatsapp, empresa?.mensagem_whatsapp);

  return (
    <div className="min-h-screen bg-[#031433] text-white">
      <Header
        solucoes={(data.menu?.solucoes ?? []).map((item) => ({ label: item.rotulo, href: item.url }))}
        whatsappUrl={whatsapp}
        rotulos={data.hero?.rotulos_botoes}
      />
      {children}
      <Footer empresa={empresa} />
    </div>
  );
}
