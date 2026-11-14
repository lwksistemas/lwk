"use client";

import { useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { mensagemErro } from "@/components/clinica-beleza/pdv/pdv-tipos";

const CAMPO = "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm";

export function CupomFiscalConfigForm({ cor }: { cor: string }) {
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [cscInformado, setCscInformado] = useState(false);
  const [certificado, setCertificado] = useState(false);
  const [form, setForm] = useState({
    habilitada: false,
    regime: "simples",
    id_csc: "",
    csc: "",
    inscricao_estadual: "",
    serie: "1",
    ambiente_homologacao: true,
    ncm_padrao: "",
    codigo_municipio: "",
    aliquota_icms: "18.00",
  });

  useEffect(() => {
    let vivo = true;
    ClinicaBelezaAPI.nfce
      .config()
      .then((config) => {
        if (!vivo) return;
        setCscInformado(config.csc_informado);
        setCertificado(config.certificado_a1);
        setForm({
          habilitada: config.habilitada,
          regime: config.regime || "simples",
          id_csc: config.id_csc || "",
          csc: "",
          inscricao_estadual: config.inscricao_estadual || "",
          serie: String(config.serie || 1),
          ambiente_homologacao: config.ambiente_homologacao,
          ncm_padrao: config.ncm_padrao || "",
          codigo_municipio: config.codigo_municipio || "",
          aliquota_icms: config.aliquota_icms || "18.00",
        });
      })
      .catch((falha) => {
        if (vivo) setErro(mensagemErro(falha, "Não foi possível carregar o cupom fiscal."));
      })
      .finally(() => {
        if (vivo) setCarregando(false);
      });
    return () => {
      vivo = false;
    };
  }, []);

  const salvar = async () => {
    setSalvando(true);
    setErro("");
    setAviso("");
    try {
      const salva = await ClinicaBelezaAPI.nfce.salvar({
        habilitada: form.habilitada,
        regime: form.regime,
        id_csc: form.id_csc,
        csc: form.csc,
        inscricao_estadual: form.inscricao_estadual,
        serie: Number(form.serie || 1),
        ambiente_homologacao: form.ambiente_homologacao,
        ncm_padrao: form.ncm_padrao,
        codigo_municipio: form.codigo_municipio,
        aliquota_icms: form.aliquota_icms,
      });
      setCscInformado(salva.csc_informado);
      setCertificado(salva.certificado_a1);
      setForm((atual) => ({ ...atual, habilitada: salva.habilitada, csc: "" }));
      setAviso(salva.habilitada ? "Cupom fiscal ligado para as vendas de produto." : "Cupom fiscal desligado. O recibo continua igual.");
    } catch (falha) {
      setErro(mensagemErro(falha, "Não foi possível salvar o cupom fiscal."));
    } finally {
      setSalvando(false);
    }
  };

  if (carregando) return <p className="text-sm text-gray-500">Carregando...</p>;

  return (
    <div className="max-w-xl space-y-4 rounded-xl border border-gray-200 bg-white p-6">
      <p className="text-sm text-gray-600">
        O recibo de pagamento continua. O cupom fiscal sai na venda de produtos do caixa, depois que a SEFAZ autorizar.
        A clínica habilita a NFC-e na SEFAZ-SP e informa aqui o regime, o CSC e a inscrição estadual.
      </p>
      <label className="flex items-start gap-2 text-sm text-gray-800">
        <input
          type="checkbox"
          className="mt-1"
          checked={form.habilitada}
          onChange={(e) => setForm({ ...form, habilitada: e.target.checked })}
        />
        <span>Emitir cupom fiscal nas vendas de produto</span>
      </label>
      <label className="block text-sm">
        Regime
        <select className={`${CAMPO} mt-1`} value={form.regime} onChange={(e) => setForm({ ...form, regime: e.target.value })}>
          <option value="simples">Simples Nacional</option>
          <option value="normal">Regime normal</option>
        </select>
      </label>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          ID do CSC
          <input className={`${CAMPO} mt-1`} value={form.id_csc} onChange={(e) => setForm({ ...form, id_csc: e.target.value })} />
        </label>
        <label className="block text-sm">
          CSC
          <input
            className={`${CAMPO} mt-1`}
            type="password"
            autoComplete="new-password"
            placeholder={cscInformado ? "Já informado. Preencha só para trocar." : ""}
            value={form.csc}
            onChange={(e) => setForm({ ...form, csc: e.target.value })}
          />
        </label>
      </div>
      <label className="block text-sm">
        Inscrição estadual
        <input className={`${CAMPO} mt-1`} value={form.inscricao_estadual} onChange={(e) => setForm({ ...form, inscricao_estadual: e.target.value })} />
      </label>
      <label className="block text-sm">
        Ambiente
        <select
          className={`${CAMPO} mt-1`}
          value={form.ambiente_homologacao ? "teste" : "producao"}
          onChange={(e) => setForm({ ...form, ambiente_homologacao: e.target.value === "teste" })}
        >
          <option value="teste">Homologação, sem valor fiscal</option>
          <option value="producao">Produção, com valor fiscal</option>
        </select>
      </label>
      <label className="block text-sm">
        NCM padrão
        <input
          className={`${CAMPO} mt-1`}
          inputMode="numeric"
          placeholder="Opcional. Oito dígitos, se o produto não tiver o seu."
          value={form.ncm_padrao}
          onChange={(e) => setForm({ ...form, ncm_padrao: e.target.value })}
        />
      </label>
      <label className="block text-sm">
        Código IBGE do município
        <input
          className={`${CAMPO} mt-1`}
          inputMode="numeric"
          placeholder="Opcional. A emissão tenta achar pela cidade da clínica."
          value={form.codigo_municipio}
          onChange={(e) => setForm({ ...form, codigo_municipio: e.target.value })}
        />
      </label>
      {form.regime === "normal" && (
        <label className="block text-sm">
          Alíquota de ICMS (%)
          <input className={`${CAMPO} mt-1`} value={form.aliquota_icms} onChange={(e) => setForm({ ...form, aliquota_icms: e.target.value })} />
        </label>
      )}
      <p className="text-sm text-gray-600">
        {certificado
          ? "O cupom usa o certificado A1 já enviado em Nota Fiscal."
          : "Ainda falta o certificado A1 em Nota Fiscal. Sem ele a SEFAZ não autoriza o cupom."}
      </p>
      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {aviso && <p className="text-sm text-emerald-700">{aviso}</p>}
      <button
        type="button"
        disabled={salvando}
        onClick={() => void salvar()}
        className="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        style={{ backgroundColor: cor }}
      >
        {salvando ? "Salvando..." : "Salvar"}
      </button>
    </div>
  );
}
