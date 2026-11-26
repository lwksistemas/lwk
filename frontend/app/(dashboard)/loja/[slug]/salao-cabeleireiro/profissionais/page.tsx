"use client";

import { Suspense } from "react";
import { SalaoProfissionaisPageContent } from "@/components/salao/profissionais/SalaoProfissionaisPageContent";

export default function ProfissionaisSalaoPage() {
  return (
    <Suspense fallback={<p className="p-4 text-sm text-[#8a6e74]">Carregando…</p>}>
      <SalaoProfissionaisPageContent />
    </Suspense>
  );
}
