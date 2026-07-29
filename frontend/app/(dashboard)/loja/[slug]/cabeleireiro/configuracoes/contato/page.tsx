"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { SalaoPageHeader } from "@/components/cabeleireiro/SalaoPageHeader";
import { SALAO_PRIMARY } from "@/components/cabeleireiro/salao-nav";
import { ContatoReciboSettings } from "@/components/loja/ContatoReciboSettings";

export default function SalaoContatoReciboPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/cabeleireiro/configuracoes`;

  return (
    <div>
      <SalaoPageHeader
        title="Contato no recibo"
        subtitle="Telefone e e-mail do salão no recibo de pagamento"
      />
      <div className="p-4 md:p-6 space-y-4">
        <Link
          href={base}
          className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:underline"
        >
          <ArrowLeft size={16} />
          Voltar às configurações
        </Link>
        <ContatoReciboSettings
          apiPrefix="/cabeleireiro"
          accentColor={SALAO_PRIMARY}
          entidadeLabel="salão"
        />
      </div>
    </div>
  );
}
