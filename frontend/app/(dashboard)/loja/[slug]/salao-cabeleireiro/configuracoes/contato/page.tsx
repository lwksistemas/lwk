"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { ContatoReciboSettings } from "@/components/loja/ContatoReciboSettings";

export default function ContatoSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  return (
    <div>
      <Link href={`/loja/${slug}/salao-cabeleireiro/configuracoes`} className="mb-4 inline-flex items-center gap-2 text-sm text-[#8a6e74]">
        <ArrowLeft size={16} /> Voltar às configurações
      </Link>
      <ContatoReciboSettings apiPrefix="/salao-cabeleireiro" accentColor="#7A3044" entidadeLabel="salão" publicoLabel="cliente" />
    </div>
  );
}
