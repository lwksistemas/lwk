import { cloudinaryLojaLogin } from "@/lib/cloudinary-folders";
import { ImageUpload } from "@/components/ImageUpload";

interface LoginConfigImagesSectionProps {
  lojaDoc: string;
  lojaDocReady: boolean;
  lojaDocLoading: boolean;
  logo: string;
  loginBackground: string;
  loginLogo: string;
  backgroundDescription: string;
  onLogoChange: (value: string) => void;
  onLoginBackgroundChange: (value: string) => void;
  onLoginLogoChange: (value: string) => void;
}

export function LoginConfigImagesSection({
  lojaDoc,
  lojaDocReady,
  lojaDocLoading,
  logo,
  loginBackground,
  loginLogo,
  backgroundDescription,
  onLogoChange,
  onLoginBackgroundChange,
  onLoginLogoChange,
}: LoginConfigImagesSectionProps) {
  const folder = cloudinaryLojaLogin(lojaDoc);
  const disabled = lojaDocLoading || !lojaDocReady;

  return (
    <>
      <ImageUpload
        label="Logo da clínica (principal)"
        description="Usado no sistema (PNG com fundo transparente recomendado)"
        value={logo}
        onChange={onLogoChange}
        maxSize={2}
        aspectRatio="16:9"
        folder={folder}
        disabled={disabled}
      />
      <ImageUpload
        label="Imagem de fundo da tela de login"
        description={backgroundDescription}
        value={loginBackground}
        onChange={onLoginBackgroundChange}
        maxSize={5}
        aspectRatio="16:9"
        folder={folder}
        disabled={disabled}
      />
      <ImageUpload
        label="Logo da tela de login"
        description="Opcional — se vazio, usa o logo principal"
        value={loginLogo}
        onChange={onLoginLogoChange}
        maxSize={2}
        aspectRatio="1:1"
        folder={folder}
        disabled={disabled}
      />
    </>
  );
}
