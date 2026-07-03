"use client";

import Link from "next/link";
import { ArrowLeft, LogIn } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { useLojaCloudinaryDocument } from "@/lib/cloudinary-folders";
import { LoginConfigColorSection } from "./LoginConfigColorSection";
import { LoginConfigImagesSection } from "./LoginConfigImagesSection";
import type { LoginConfigPageContentProps } from "./login-config-page-types";
import { useLoginConfigPage } from "./useLoginConfigPage";

export function LoginConfigPageContent({
  slug,
  apiPath,
  backHref,
  accentColor,
  defaultPrimary,
  defaultSecondary,
  colorPresets,
  backgroundDescription = "Opcional — se vazio, usa a imagem padrão do tipo de loja",
  title = "Configurar tela de login",
}: LoginConfigPageContentProps) {
  const { documento: lojaDoc, ready: lojaDocReady, loading: lojaDocLoading } =
    useLojaCloudinaryDocument(slug);

  const { loading, saving, form, updateForm, applyColorPreset, saveConfig } = useLoginConfigPage(
    apiPath,
    defaultPrimary,
    defaultSecondary,
  );

  return (
    <ClinicaBelezaPageContent className="space-y-6">
      <Link
        href={backHref}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: accentColor }}>
            <LogIn size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h1>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Personalize logo, cores e identidade visual da tela de login.
        </p>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <div className="space-y-6">
            <LoginConfigImagesSection
              lojaDoc={lojaDoc}
              lojaDocReady={lojaDocReady}
              lojaDocLoading={lojaDocLoading}
              logo={form.logo}
              loginBackground={form.loginBackground}
              loginLogo={form.loginLogo}
              backgroundDescription={backgroundDescription}
              onLogoChange={(logo) => updateForm({ logo })}
              onLoginBackgroundChange={(loginBackground) => updateForm({ loginBackground })}
              onLoginLogoChange={(loginLogo) => updateForm({ loginLogo })}
            />

            <LoginConfigColorSection
              colorPresets={colorPresets}
              corPrimaria={form.corPrimaria}
              corSecundaria={form.corSecundaria}
              accentColor={accentColor}
              onApplyPreset={applyColorPreset}
              onCorPrimariaChange={(corPrimaria) => updateForm({ corPrimaria })}
              onCorSecundariaChange={(corSecundaria) => updateForm({ corSecundaria })}
            />

            <div className="flex flex-wrap items-center justify-end gap-3">
              <a
                href={`/loja/${slug}/login`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm hover:underline"
                style={{ color: accentColor }}
              >
                Ver tela de login →
              </a>
              <button
                type="button"
                onClick={() => void saveConfig()}
                disabled={saving}
                className="px-4 py-2 text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: accentColor }}
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        )}
      </div>
    </ClinicaBelezaPageContent>
  );
}
