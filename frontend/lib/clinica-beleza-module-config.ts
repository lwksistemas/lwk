import type { ComponentProps } from "react";
import type { ProcedimentosPageContent } from "@/components/clinica-beleza/ProcedimentosPageContent";
import type { ProtocolosPageContent } from "@/components/clinica-beleza/ProtocolosPageContent";

type RelatedLink = { label: string; href: string };

type ProcedimentosConfig = Pick<
  ComponentProps<typeof ProcedimentosPageContent>,
  "title" | "subtitle" | "defaultCategoria" | "relatedLinks"
>;

type ProtocolosConfig = Pick<
  ComponentProps<typeof ProtocolosPageContent>,
  "title" | "subtitle" | "defaultCategoria" | "relatedLinks"
>;

function links(slug: string, extra: RelatedLink[] = []): RelatedLink[] {
  return extra;
}

export const CLINICA_MODULO_PROCEDIMENTOS: Record<"estetica" | "soroterapia", (slug: string) => ProcedimentosConfig> = {
  estetica: (slug) => ({
    title: "Estética — Procedimentos",
    subtitle: "Tratamentos estéticos oferecidos",
    defaultCategoria: "estetica",
    relatedLinks: links(slug, [
      { label: "Profissionais", href: `/loja/${slug}/clinica-beleza/profissionais` },
      { label: "Agenda", href: `/loja/${slug}/agenda` },
    ]),
  }),
  soroterapia: (slug) => ({
    title: "Soroterapia — Procedimentos",
    subtitle: "Soros e protocolos de soroterapia",
    defaultCategoria: "soroterapia",
    relatedLinks: links(slug, [{ label: "Agenda", href: `/loja/${slug}/agenda` }]),
  }),
};

export const CLINICA_MODULO_PROTOCOLOS: Record<"estetica" | "soroterapia", (slug: string) => ProtocolosConfig> = {
  estetica: (slug) => ({
    title: "Estética — Protocolos",
    subtitle: "Roteiros de tratamentos estéticos",
    defaultCategoria: "estetica",
    relatedLinks: links(slug, [
      { label: "Protocolos (geral)", href: `/loja/${slug}/clinica-beleza/protocolos` },
      { label: "Profissionais", href: `/loja/${slug}/clinica-beleza/profissionais` },
      { label: "Agenda", href: `/loja/${slug}/agenda` },
    ]),
  }),
  soroterapia: (slug) => ({
    title: "Soroterapia — Protocolos",
    subtitle: "Protocolos de soroterapia",
    defaultCategoria: "soroterapia",
    relatedLinks: links(slug, [
      { label: "Protocolos (geral)", href: `/loja/${slug}/clinica-beleza/protocolos` },
      { label: "Agenda", href: `/loja/${slug}/agenda` },
    ]),
  }),
};
