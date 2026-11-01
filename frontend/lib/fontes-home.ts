import { DM_Sans, Inter, Montserrat, Nunito, Outfit, Poppins } from "next/font/google";
import { fonteHomeValida } from "./fontes-opcoes";

const inter = Inter({ subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" });
const poppins = Poppins({ subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" });
const montserrat = Montserrat({ subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" });
const nunito = Nunito({ subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" });
const dm = DM_Sans({ subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" });
const outfit = Outfit({ subsets: ["latin"], weight: ["400", "600", "700", "800"], display: "swap" });

const fontes = { inter, poppins, montserrat, nunito, dm, outfit };

export function classeFonteHome(id?: string) {
  const chave = fonteHomeValida(id) as keyof typeof fontes;
  return fontes[chave].className;
}
