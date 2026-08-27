import { describe, expect, it } from "vitest";
import {
  filtrarClientesWhatsapp,
  labelStatusWhatsapp,
  labelTipoWhatsapp,
  type WhatsappCliente,
} from "./whatsapp-painel-utils";

const cliente = (over: Partial<WhatsappCliente>): WhatsappCliente => ({
  id: 1,
  tipo: "lwk_loja",
  loja_id: 6,
  nome: "Harmonis",
  slug: "clinicaharmonis",
  documento: "37302743000126",
  ativo: true,
  quota_numeros: 1,
  chaves: [],
  numeros: [{ instance_name: "lwk_loja_6", telefone: "5516999999999", status: "connected" }],
  ...over,
});

describe("filtrarClientesWhatsapp", () => {
  it("filtra por nome da loja", () => {
    const list = [cliente({}), cliente({ nome: "Nova Imagem", slug: "novaimagem", loja_id: 2 })];
    expect(filtrarClientesWhatsapp(list, "harmonis")).toHaveLength(1);
  });

  it("filtra por telefone conectado", () => {
    const list = [cliente({})];
    expect(filtrarClientesWhatsapp(list, "5516999")).toHaveLength(1);
    expect(filtrarClientesWhatsapp(list, "888777")).toHaveLength(0);
  });
});

describe("labels WhatsApp", () => {
  it("traduz status e tipo", () => {
    expect(labelStatusWhatsapp("connected")).toBe("Conectado");
    expect(labelStatusWhatsapp("qr_pending")).toBe("Aguardando QR");
    expect(labelTipoWhatsapp("parceiro")).toBe("Parceiro API");
  });
});
