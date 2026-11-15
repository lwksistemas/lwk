"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function NotaFiscalSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  return (
    <div>
      <Link href={`/loja/${slug}/salao-cabeleireiro/configuracoes`} className="mb-4 inline-flex items-center gap-2 text-sm text-[#8a6e74]">
        <ArrowLeft size={16} /> Voltar às configurações
      </Link>
      <h1 className="text-2xl font-semibold">Nota fiscal (NFS-e)</h1>
      <p className="mt-2 max-w-2xl text-sm text-[#8a6e74]">
        O salão terá provedor, certificado e dados fiscais próprios, como na clínica. A emissão continua desligada: esta tela não envia nota.
      </p>
      <ul className="mt-4 max-w-xl space-y-2 rounded-3xl border border-[#f0e4e6] bg-white p-4 text-sm">
        <li>Provedor de nota fiscal</li>
        <li>Certificado digital</li>
        <li>Emissão automática desligada</li>
      </ul>
    </div>
  );
}
