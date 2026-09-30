"use client";

import { Suspense } from "react";
import { ProcedimentosRealizadosPage } from "@/components/clinica-beleza/procedimentos-realizados/ProcedimentosRealizadosPage";

export default function ProcedimentosRealizadosRoute() {
  return (
    <Suspense fallback={<div className="text-center py-16 text-gray-500">Carregando...</div>}>
      <ProcedimentosRealizadosPage />
    </Suspense>
  );
}
