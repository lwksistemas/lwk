"use client";

import { Suspense } from "react";
import { SalaoServicosPageContent } from "@/components/salao/servicos/SalaoServicosPageContent";

export default function ServicosSalaoPage() {
  return (
    <Suspense fallback={<p className="p-4 text-sm text-[#8a6e74]">Carregando…</p>}>
      <SalaoServicosPageContent />
    </Suspense>
  );
}
