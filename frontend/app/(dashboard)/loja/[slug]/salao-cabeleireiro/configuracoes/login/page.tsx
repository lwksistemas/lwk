"use client";

import { useParams } from "next/navigation";
import { LoginConfigPageContent } from "@/components/shared/login-config/LoginConfigPageContent";
import type { LoginColorPreset } from "@/components/shared/login-config/login-config-page-types";

const CORES: LoginColorPreset[] = [
  { nome: "Rosa", primaria: "#7A3044", secundaria: "#5c2434" },
  { nome: "Roxo", primaria: "#4c1d78", secundaria: "#3b1460" },
  { nome: "Verde", primaria: "#3d5244", secundaria: "#2c3b32" },
  { nome: "Burgundy", primaria: "#8B3D52", secundaria: "#6B2F40" },
  { nome: "Azul", primaria: "#3B82F6", secundaria: "#2563EB" },
];

export default function LoginSalaoPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/salao-cabeleireiro/configuracoes`;
  return (
    <LoginConfigPageContent
      slug={slug}
      apiPath="/salao-cabeleireiro/identidade/"
      backHref={base}
      accentColor="#7A3044"
      defaultPrimary="#7A3044"
      defaultSecondary="#4c1d78"
      colorPresets={CORES}
      backgroundDescription="Opcional. Se ficar vazio, a tela de login usa a imagem padrão do salão."
      title="Configurar tela de login"
    />
  );
}
