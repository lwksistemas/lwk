"use client";

import dynamic from "next/dynamic";

const tabLoading = (label: string) => (
  <div className="text-center py-12 text-gray-500 text-sm">Carregando {label}...</div>
);

export const ConsultaHistoricoTabLazy = dynamic(
  () => import("../ConsultaHistoricoTab").then((m) => ({ default: m.ConsultaHistoricoTab })),
  { loading: () => tabLoading("histórico") },
);

export const ConsultaDocumentosTabLazy = dynamic(
  () => import("../ConsultaDocumentosTab").then((m) => ({ default: m.ConsultaDocumentosTab })),
  { loading: () => tabLoading("documentos") },
);

export const ConsultaFotosTabLazy = dynamic(
  () => import("../ConsultaFotosTab").then((m) => ({ default: m.ConsultaFotosTab })),
  { loading: () => tabLoading("fotos") },
);
