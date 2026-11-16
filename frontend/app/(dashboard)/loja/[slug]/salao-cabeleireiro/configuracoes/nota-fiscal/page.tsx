"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { SalaoNFSeConfigProvider } from "@/contexts/SalaoNFSeConfigContext";
import SalaoNFSeForm from "@/components/salao/SalaoNFSeForm";

export default function NotaFiscalSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/salao-cabeleireiro/configuracoes`;

  return (
    <SalaoNFSeConfigProvider>
      <div className="space-y-4">
        <Link href={base} className="inline-flex items-center gap-2 text-sm text-[#8a6e74]">
          <ArrowLeft size={16} /> Voltar às configurações
        </Link>
        <SalaoNFSeForm configBackHref={base} />
      </div>
    </SalaoNFSeConfigProvider>
  );
}
