/**
 * Dentro da imagem, tira as rotas do outro app antes do next build.
 * O repositório não é alterado. LWK_FRONTEND_APP=all não apaga nada.
 */
import fs from "node:fs";
import path from "node:path";

const app = (process.env.LWK_FRONTEND_APP || "all").trim();

const TIRAR_DO_CRM = [
  "app/(dashboard)/loja/[slug]/clinica-beleza",
  "app/(dashboard)/loja/[slug]/clinica",
  "app/(dashboard)/loja/[slug]/cabeleireiro",
  "app/(dashboard)/loja/[slug]/hotel",
  "app/(dashboard)/loja/[slug]/agenda",
  "app/(dashboard)/loja/[slug]/relatorios",
  "app/(dashboard)/loja/[slug]/dashboard",
  "app/(dashboard)/superadmin",
  "app/confirmar-agendamento",
  "app/enviar-foto",
  "app/assinar-consentimento",
  "app/assinar-recibo",
  "app/teleconsulta",
  "app/assinar-reserva",
];

const TIRAR_DA_CLINICA = [
  "app/(dashboard)/loja/[slug]/crm-vendas",
  "app/(dashboard)/loja/[slug]/clinica",
  "app/(dashboard)/loja/[slug]/cabeleireiro",
  "app/(dashboard)/loja/[slug]/hotel",
  "app/(dashboard)/superadmin",
  "app/relatorio-comissao",
  "app/assinar-reserva",
];

const alvos =
  app === "crm-vendas" ? TIRAR_DO_CRM : app === "clinica-beleza" ? TIRAR_DA_CLINICA : [];

if (alvos.length === 0) {
  console.log(`recortar-rotas: app=${app || "all"} — site completo`);
  process.exit(0);
}

const raiz = process.cwd();
for (const rel of alvos) {
  const dir = path.join(raiz, rel);
  if (!fs.existsSync(dir)) continue;
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(`recortar-rotas: removido ${rel}`);
}
console.log(`recortar-rotas: build só de ${app}`);
