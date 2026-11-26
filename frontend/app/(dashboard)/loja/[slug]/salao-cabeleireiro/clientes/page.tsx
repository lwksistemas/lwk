"use client";

import { Suspense } from "react";
import { SalaoClientesPageContent } from "@/components/salao/clientes/SalaoClientesPageContent";

export default function ClientesSalaoPage() {
  return (
    <Suspense fallback={<p className="p-4 text-sm text-[#8a6e74]">Carregando…</p>}>
      <SalaoClientesPageContent />
    </Suspense>
  );
}
