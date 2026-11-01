import { DM_Sans, Inter, Montserrat, Nunito, Outfit, Poppins } from "next/font/google";
import { fonteHomeValida } from "./fontes-opcoes";

const comum = { subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" } as const;

const fontes = {
  inter: Inter(comum),
  poppins: Poppins(comum),
  montserrat: Montserrat(comum),
  nunito: Nunito(comum),
  dm: DM_Sans(comum),
  outfit: Outfit(comum),
};

export function classeFonteHome(id?: string) {
  const chave = fonteHomeValida(id) as keyof typeof fontes;
  return fontes[chave].className;
}
