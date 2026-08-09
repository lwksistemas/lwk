/** Opções de emissão NFS-e — mesmo padrão em CRM, Clínica e Cabeleireiro. */

export type ProvedorNf = "asaas" | "issnet" | "nacional" | "manual";

export type EmissaoOpcao = "asaas" | "issnet_nacional" | "nacional_adn";

export type EmissaoOpcaoInfo = {
  key: EmissaoOpcao;
  numero: number;
  titulo: string;
  descricao: string;
  badge?: string;
};

export const NFSE_EMISSAO_OPCOES: EmissaoOpcaoInfo[] = [
  {
    key: "asaas",
    numero: 1,
    titulo: "Asaas (conta da sua loja)",
    descricao:
      "Emissão de NFS-e pela conta Asaas da loja. A API Key fica em Configurações → Asaas (banco).",
  },
  {
    key: "issnet_nacional",
    numero: 2,
    titulo: "ISSNet — Padrão Nacional (DPS / RTC)",
    descricao:
      "Layout NFS-e via webservice Nacional da ISSNet (Ribeirão Preto). Padrão vigente desde a Reforma Tributária.",
    badge: "Padrão atual",
  },
  {
    key: "nacional_adn",
    numero: 4,
    titulo: "API Nacional NFS-e (Direto)",
    descricao:
      "Emissão direta na API Nacional (ADN/SEFIN), sem intermediário. Para municípios com emissão direta liberada.",
  },
];

export function resolverEmissaoOpcao(
  provedor: ProvedorNf | string | undefined,
  _usarNacional?: boolean,
): EmissaoOpcao {
  if (provedor === "asaas") return "asaas";
  if (provedor === "nacional") return "nacional_adn";
  // issnet (e legado ABRASF/manual) → Padrão Nacional
  if (provedor === "issnet") return "issnet_nacional";
  return "asaas";
}

export function aplicarEmissaoOpcao(opcao: EmissaoOpcao): {
  provedor_nf: ProvedorNf;
  issnet_usar_padrao_nacional: boolean;
} {
  switch (opcao) {
    case "asaas":
      return { provedor_nf: "asaas", issnet_usar_padrao_nacional: false };
    case "issnet_nacional":
      return { provedor_nf: "issnet", issnet_usar_padrao_nacional: true };
    case "nacional_adn":
      return { provedor_nf: "nacional", issnet_usar_padrao_nacional: false };
  }
}
