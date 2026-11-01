import type { HomepageData } from "@/types/homepage";
import Header from "@/app/components/Header";
import Footer from "@/app/components/Footer";
import WhatsAppButton from "@/components/WhatsAppButton";
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
    <div className="min-h-screen bg-white text-slate-900">
      <Header
        solucoes={(data.menu?.solucoes ?? []).map((item) => ({ label: item.rotulo, href: item.url }))}
        segmentos={(data.menu?.segmentos ?? []).map((item) => ({ label: item.rotulo, href: item.url }))}
        whatsappUrl={whatsapp}
      />
      {children}
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
    </div>
  );
}
