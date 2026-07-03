export interface LoginConfigData {
  logo: string;
  login_background: string;
  login_logo: string;
  cor_primaria: string;
  cor_secundaria: string;
}

export interface LoginColorPreset {
  nome: string;
  primaria: string;
  secundaria: string;
}

export interface LoginConfigPageContentProps {
  slug: string;
  apiPath: string;
  backHref: string;
  accentColor: string;
  defaultPrimary: string;
  defaultSecondary: string;
  colorPresets: LoginColorPreset[];
  backgroundDescription?: string;
  title?: string;
}

export interface LoginConfigFormState {
  logo: string;
  loginBackground: string;
  loginLogo: string;
  corPrimaria: string;
  corSecundaria: string;
}
