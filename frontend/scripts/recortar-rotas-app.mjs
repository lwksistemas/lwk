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

const ARQUIVOS_DE_ROTA = new Set([
  "page.tsx",
  "page.ts",
  "page.jsx",
  "page.js",
  "layout.tsx",
  "layout.ts",
  "loading.tsx",
  "error.tsx",
  "not-found.tsx",
  "template.tsx",
  "default.tsx",
  "route.ts",
  "route.tsx",
]);

function tirarRotas(dir) {
  if (!fs.existsSync(dir)) return;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const alvo = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      tirarRotas(alvo);
      continue;
    }
    if (!ARQUIVOS_DE_ROTA.has(ent.name)) continue;
    fs.rmSync(alvo);
    console.log(`recortar-rotas: removido ${path.relative(raiz, alvo)}`);
  }
}

const raiz = process.cwd();
for (const rel of alvos) tirarRotas(path.join(raiz, rel));
console.log(`recortar-rotas: build só de ${app}`);
