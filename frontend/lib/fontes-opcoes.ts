export const FONTES_HOME = [
  { id: "inter", rotulo: "Inter" },
  { id: "poppins", rotulo: "Poppins" },
  { id: "montserrat", rotulo: "Montserrat" },
  { id: "nunito", rotulo: "Nunito" },
  { id: "dm", rotulo: "DM Sans" },
  { id: "outfit", rotulo: "Outfit" },
] as const;

export const TAMANHOS_HOME = [
  { id: "pequeno", rotulo: "Pequena", px: "14px" },
  { id: "normal", rotulo: "Normal", px: "16px" },
  { id: "grande", rotulo: "Grande", px: "18px" },
  { id: "maior", rotulo: "Muito grande", px: "20px" },
] as const;

export function tamanhoHomePx(id?: string) {
  return TAMANHOS_HOME.find((item) => item.id === id)?.px ?? "16px";
}

export function fonteHomeValida(id?: string) {
  return FONTES_HOME.some((item) => item.id === id) ? id! : "inter";
}
