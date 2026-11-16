"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { CupomFiscalSalaoForm } from "@/components/salao/CupomFiscalSalaoForm";

export default function CupomFiscalSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  return (
    <div className="space-y-4">
      <Link href={`/loja/${slug}/salao-cabeleireiro/configuracoes`} className="inline-flex items-center gap-2 text-sm text-[#8a6e74]">
        <ArrowLeft size={16} /> Voltar às configurações
      </Link>
      <div>
        <h1 className="text-2xl font-semibold">Cupom fiscal</h1>
        <p className="mt-1 text-sm text-[#8a6e74]">NFC-e das vendas de produto deste salão.</p>
      </div>
      <CupomFiscalSalaoForm />
    </div>
  );
}
