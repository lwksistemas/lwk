"use client";

import { useEffect, useMemo, useState } from "react";
import { Wallet } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import {
  ProcedimentoCategoriaChips,
  useProcedimentoCategoriaFiltro,
} from "@/components/clinica-beleza/consultas/procedimentos-consulta/procedimento-categoria-filtro";
import { procedureSelectLabel } from "@/lib/clinica-beleza-categories";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type {
  PrazoPagamentoOpcao,
  PrazoPagamentoPolitica,
  ProcedimentoAnteriorItem,
} from "@/lib/clinica-beleza-api/client-entities";
import { formatApiErrorBody } from "@/lib/api-errors";
import { useToast } from "@/components/ui/Toast";

interface FinanceiroPacienteCardProps {
  patientId: number;
  open: boolean;
  onClose: () => void;
}

const fieldClass =
  "w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 px-3 py-2 text-sm";

const FORMAS = [
  { id: "PIX", label: "PIX" },
  { id: "CASH", label: "Dinheiro" },
  { id: "CREDIT_CARD", label: "Cartão de crédito" },
  { id: "DEBIT_CARD", label: "Cartão de débito" },
  { id: "TRANSFER", label: "Transferência" },
];

function moeda(valor: string | number): string {
  const numero = typeof valor === "number" ? valor : Number(valor);
  if (!Number.isFinite(numero)) return "R$ 0,00";
  return numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function dataBr(iso: string): string {
  const [ano, mes, dia] = (iso || "").slice(0, 10).split("-");
  if (!ano || !mes || !dia) return iso;
  return `${dia}/${mes}/${ano}`;
}

type CatalogoProcedimento = {
  id: number;
  nome: string;
  categoria: string;
  preco: string;
};

function textoBusca(valor: string): string {
  return valor
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function hojeIso(): string {
  const agora = new Date();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  const dia = String(agora.getDate()).padStart(2, "0");
  return `${agora.getFullYear()}-${mes}-${dia}`;
}

function regraAtual(politica: PrazoPagamentoPolitica | null): string {
  if (!politica?.tem_prazo_pagamento) return "Sem prazo. A recepção não recebe esta cliente a prazo.";
  if (politica.prazo_pagamento_modo === "DIAS_APOS" && politica.prazo_pagamento_dias) {
    return `${politica.prazo_pagamento_dias} dias após o lançamento`;
  }
  if (politica.prazo_pagamento_modo === "DIA_FIXO" && politica.prazo_pagamento_dia_mes) {
    return `Dia ${politica.prazo_pagamento_dia_mes} do mês`;
  }
  if (politica.prazo_pagamento_modo === "SEMANAL") {
    return "Semanal, 7 dias após o lançamento";
  }
  return "Sem prazo.";
}

export function FinanceiroPacienteCard({ patientId, open, onClose }: FinanceiroPacienteCardProps) {
  const toast = useToast();
  const [carregando, setCarregando] = useState(true);
  const [politica, setPolitica] = useState<PrazoPagamentoPolitica | null>(null);
  const [opcoes, setOpcoes] = useState<PrazoPagamentoOpcao[]>([]);
  const [procedimentos, setProcedimentos] = useState<ProcedimentoAnteriorItem[]>([]);
  const [catalogo, setCatalogo] = useState<CatalogoProcedimento[]>([]);
  const [buscaProc, setBuscaProc] = useState("");
  const [procedimentoId, setProcedimentoId] = useState<number | "">("");
  const [criandoPrazo, setCriandoPrazo] = useState(false);
  const [nomePrazo, setNomePrazo] = useState("");
  const [modoPrazo, setModoPrazo] = useState<"DIAS_APOS" | "DIA_FIXO" | "SEMANAL">("DIAS_APOS");
  const [numeroPrazo, setNumeroPrazo] = useState("");
  const [dataProc, setDataProc] = useState("");
  const [nomeProc, setNomeProc] = useState("");
  const [valorProc, setValorProc] = useState("");
  const [pagoProc, setPagoProc] = useState("");
  const [dataPagamento, setDataPagamento] = useState("");
  const [receberId, setReceberId] = useState<number | null>(null);
  const [valorReceber, setValorReceber] = useState("");
  const [dataReceber, setDataReceber] = useState(hojeIso());
  const [formaReceber, setFormaReceber] = useState("PIX");
  const [ocupado, setOcupado] = useState(false);

  const carregar = () => {
    setCarregando(true);
    Promise.all([
      ClinicaBelezaAPI.patients.prazoPagamento.get(patientId),
      ClinicaBelezaAPI.patients.prazoPagamento.opcoes(),
      ClinicaBelezaAPI.patients.procedimentosAnteriores.list(patientId),
      ClinicaBelezaAPI.procedures.list({ active: true, all: 1 }),
    ])
      .then(([prazo, lista, lancamentos, procs]) => {
        setPolitica(prazo);
        setOpcoes(Array.isArray(lista) ? lista : []);
        setProcedimentos(Array.isArray(lancamentos) ? lancamentos : []);
        setCatalogo(
          (Array.isArray(procs) ? procs : [])
            .map((item) => {
              const proc = item as { id?: number; nome?: string; categoria?: string; preco?: string | number };
              return {
                id: Number(proc.id),
                nome: String(proc.nome || "").trim(),
                categoria: String(proc.categoria || ""),
                preco: String(proc.preco ?? ""),
              };
            })
            .filter((item) => item.id && item.nome)
            .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")),
        );
      })
      .catch((e) => {
        toast.error(formatApiErrorBody(e) || "Não foi possível carregar o financeiro da cliente.");
      })
      .finally(() => setCarregando(false));
  };

  useEffect(() => {
    if (!open) return;
    carregar();
    // carregar identidade estável o bastante para abrir o painel
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, patientId]);

  const { categoriaAtiva, setCategoriaAtiva, categoriasDisponiveis, filtrados } =
    useProcedimentoCategoriaFiltro(catalogo);
  const procedimentosBusca = useMemo(() => {
    const termo = textoBusca(buscaProc);
    if (!termo) return filtrados;
    return filtrados.filter((item) => textoBusca(item.nome).includes(termo));
  }, [filtrados, buscaProc]);

  const escolherProcedimento = (id: number | "") => {
    setProcedimentoId(id);
    const escolhido = catalogo.find((item) => item.id === id);
    if (!escolhido) {
      setNomeProc("");
      return;
    }
    setNomeProc(escolhido.nome);
    if (escolhido.preco) setValorProc(escolhido.preco.replace(".", ","));
  };

  if (!open) return null;

  const erro = (e: unknown, fallback: string) => {
    toast.error(formatApiErrorBody(e) || fallback);
  };

  const aplicarOpcao = async (prazoOpcaoId: number | null) => {
    setOcupado(true);
    try {
      const salvo = await ClinicaBelezaAPI.patients.prazoPagamento.save(patientId, {
        prazo_opcao_id: prazoOpcaoId,
      });
      setPolitica(salvo);
      toast.success(prazoOpcaoId ? "Prazo desta cliente atualizado." : "Esta cliente ficou sem prazo.");
    } catch (e) {
      erro(e, "Não foi possível salvar o prazo.");
    } finally {
      setOcupado(false);
    }
  };

  const criarPrazo = async () => {
    setOcupado(true);
    try {
      const criado = await ClinicaBelezaAPI.patients.prazoPagamento.criarOpcao({
        nome: nomePrazo.trim(),
        modo: modoPrazo,
        dias: modoPrazo === "DIAS_APOS" ? Number(numeroPrazo) : null,
        dia_mes: modoPrazo === "DIA_FIXO" ? Number(numeroPrazo) : null,
      });
      const salvo = await ClinicaBelezaAPI.patients.prazoPagamento.save(patientId, {
        prazo_opcao_id: criado.id,
      });
      setPolitica(salvo);
      setOpcoes((lista) => [...lista.filter((item) => item.id !== criado.id), criado].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")));
      setCriandoPrazo(false);
      setNomePrazo("");
      setNumeroPrazo("");
      toast.success("Prazo criado e aplicado nesta cliente.");
    } catch (e) {
      erro(e, "Não foi possível criar o prazo.");
    } finally {
      setOcupado(false);
    }
  };

  const excluirPrazo = async (id: number) => {
    setOcupado(true);
    try {
      await ClinicaBelezaAPI.patients.prazoPagamento.excluirOpcao(id);
      setOpcoes((lista) => lista.filter((item) => item.id !== id));
      if (politica?.prazo_opcao_id === id) {
        const atual = await ClinicaBelezaAPI.patients.prazoPagamento.get(patientId);
        setPolitica(atual);
      }
      toast.success("Prazo excluído.");
    } catch (e) {
      erro(e, "Não foi possível excluir o prazo.");
    } finally {
      setOcupado(false);
    }
  };

  const lancarProcedimento = async () => {
    setOcupado(true);
    try {
      const criado = await ClinicaBelezaAPI.patients.procedimentosAnteriores.criar(patientId, {
        data_procedimento: dataProc,
        nome: nomeProc.trim(),
        valor: valorProc.replace(",", "."),
        valor_pago: (pagoProc || "0").replace(",", "."),
        data_pagamento: dataPagamento,
      });
      setProcedimentos((lista) => [criado, ...lista.filter((item) => item.id !== criado.id)]);
      setDataProc("");
      setNomeProc("");
      setValorProc("");
      setPagoProc("");
      setDataPagamento("");
      setBuscaProc("");
      setProcedimentoId("");
      toast.success("Procedimento lançado.");
    } catch (e) {
      erro(e, "Não foi possível lançar o procedimento.");
    } finally {
      setOcupado(false);
    }
  };

  const excluirProcedimento = async (id: number) => {
    setOcupado(true);
    try {
      await ClinicaBelezaAPI.patients.procedimentosAnteriores.excluir(patientId, id);
      setProcedimentos((lista) => lista.filter((item) => item.id !== id));
      toast.success("Lançamento excluído.");
    } catch (e) {
      erro(e, "Não foi possível excluir o lançamento.");
    } finally {
      setOcupado(false);
    }
  };

  const receber = async (id: number) => {
    setOcupado(true);
    try {
      const atualizado = await ClinicaBelezaAPI.patients.procedimentosAnteriores.receber(patientId, id, {
        valor: valorReceber.replace(",", "."),
        data: dataReceber,
        payment_method: formaReceber,
      });
      setProcedimentos((lista) => lista.map((item) => (item.id === id ? atualizado : item)));
      setReceberId(null);
      setValorReceber("");
      toast.success("Recebimento lançado.");
    } catch (e) {
      erro(e, "Não foi possível lançar o recebimento.");
    } finally {
      setOcupado(false);
    }
  };

  const valorSelecionado = politica?.prazo_opcao_id ? String(politica.prazo_opcao_id) : "";

  return (
    <ClinicaBelezaPanel className="p-4 sm:p-5 space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Wallet size={18} style={{ color: "var(--cb-primary, #8B3D52)" }} />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Financeiro</h3>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Duas opções: o prazo da venda a prazo e o procedimento feito antes do sistema.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-sm text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
        >
          Fechar
        </button>
      </div>

      {carregando ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">Carregando…</p>
      ) : (
        <>
          <section className="space-y-3">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">1. Venda a prazo</h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">{regraAtual(politica)}</p>
            <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
              <select
                value={valorSelecionado}
                disabled={ocupado}
                onChange={(e) => {
                  const valor = e.target.value;
                  void aplicarOpcao(valor ? Number(valor) : null);
                }}
                className={`${fieldClass} sm:max-w-md`}
              >
                <option value="">Sem prazo (não recebe a prazo)</option>
                {opcoes.map((opcao) => (
                  <option key={opcao.id} value={opcao.id}>
                    {opcao.nome} — {opcao.regra}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => setCriandoPrazo((v) => !v)}
                className="px-3 py-2 rounded-lg text-sm font-medium border border-gray-300 dark:border-neutral-600"
              >
                Criar prazo
              </button>
              {politica?.prazo_opcao_id ? (
                <button
                  type="button"
                  disabled={ocupado}
                  onClick={() => void excluirPrazo(politica.prazo_opcao_id as number)}
                  className="px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-300 disabled:opacity-50"
                >
                  Excluir este prazo
                </button>
              ) : null}
            </div>

            {criandoPrazo && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl rounded-lg border border-gray-200 dark:border-neutral-700 p-3">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium mb-1">Nome do prazo</label>
                  <input
                    value={nomePrazo}
                    onChange={(e) => setNomePrazo(e.target.value)}
                    placeholder="ex.: Dia 10"
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">Regra</label>
                  <select
                    value={modoPrazo}
                    onChange={(e) => setModoPrazo(e.target.value as "DIAS_APOS" | "DIA_FIXO" | "SEMANAL")}
                    className={fieldClass}
                  >
                    <option value="DIAS_APOS">Dias após o lançamento</option>
                    <option value="DIA_FIXO">Dia fixo do mês</option>
                    <option value="SEMANAL">Semanal</option>
                  </select>
                </div>
                {modoPrazo === "SEMANAL" ? (
                  <p className="text-sm text-gray-600 dark:text-gray-300 self-end pb-2">
                    Vence 7 dias depois do lançamento.
                  </p>
                ) : (
                <div>
                  <label className="block text-xs font-medium mb-1">
                    {modoPrazo === "DIAS_APOS" ? "Quantidade de dias" : "Dia do mês (1 a 28)"}
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={modoPrazo === "DIAS_APOS" ? 365 : 28}
                    value={numeroPrazo}
                    onChange={(e) => setNumeroPrazo(e.target.value)}
                    className={fieldClass}
                  />
                </div>
                )}
                <div className="sm:col-span-2">
                  <button
                    type="button"
                    disabled={ocupado}
                    onClick={() => void criarPrazo()}
                    className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
                    style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
                  >
                    Criar e usar nesta cliente
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className="space-y-3">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              2. Procedimento feito antes do sistema
            </h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Escolha a categoria e o procedimento já cadastrado. O valor entra com o preço do cadastro e pode ser ajustado.
              Informe o que já foi pago e a data desse pagamento. Se sobrar diferença, ela vence na data do prazo configurado acima.
              Este lançamento não entra na agenda nem na comissão.
            </p>
            <ProcedimentoCategoriaChips
              categoriasDisponiveis={categoriasDisponiveis}
              categoriaAtiva={categoriaAtiva}
              onChange={(slug) => {
                setCategoriaAtiva(slug);
                escolherProcedimento("");
              }}
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Data do procedimento</label>
                <input type="date" value={dataProc} onChange={(e) => setDataProc(e.target.value)} className={fieldClass} />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Buscar</label>
                <input
                  value={buscaProc}
                  onChange={(e) => setBuscaProc(e.target.value)}
                  placeholder="Nome do procedimento"
                  className={fieldClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Procedimento</label>
                <select
                  value={procedimentoId}
                  onChange={(e) => escolherProcedimento(e.target.value ? Number(e.target.value) : "")}
                  className={fieldClass}
                >
                  <option value="">
                    {procedimentosBusca.length === 0 ? "Nenhum procedimento nesta busca" : "Selecione"}
                  </option>
                  {procedimentosBusca.map((item) => (
                    <option key={item.id} value={item.id}>
                      {procedureSelectLabel(item.nome, item.categoria, { includeCategorySuffix: !categoriaAtiva })}
                      {item.preco ? ` · ${moeda(item.preco)}` : ""}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Valor do procedimento</label>
                <input
                  inputMode="decimal"
                  value={valorProc}
                  onChange={(e) => setValorProc(e.target.value)}
                  placeholder="0,00"
                  className={fieldClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Valor pago</label>
                <input
                  inputMode="decimal"
                  value={pagoProc}
                  onChange={(e) => setPagoProc(e.target.value)}
                  placeholder="0,00"
                  className={fieldClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Data do pagamento</label>
                <input
                  type="date"
                  value={dataPagamento}
                  onChange={(e) => setDataPagamento(e.target.value)}
                  className={fieldClass}
                />
              </div>
            </div>
            <button
              type="button"
              disabled={ocupado}
              onClick={() => void lancarProcedimento()}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              Lançar procedimento
            </button>

            <div className="space-y-2">
              {procedimentos.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Nenhum procedimento anterior lançado.</p>
              ) : (
                procedimentos.map((item) => (
                  <div key={item.id} className="rounded-lg border border-gray-200 dark:border-neutral-700 p-3 space-y-2">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.nome}</p>
                        <p className="text-xs text-gray-500">{dataBr(item.data_procedimento)}</p>
                      </div>
                      <p className="text-sm">
                        Valor {moeda(item.valor)}
                        {" · "}
                        Pago {moeda(item.valor_pago)}
                        {item.data_pagamento ? ` em ${dataBr(item.data_pagamento)}` : ""}
                        {" · "}
                        <span className="font-semibold">
                          {item.quitado
                            ? "Quitado"
                            : `Diferença ${moeda(item.saldo)}${item.data_vencimento ? ` · vence ${dataBr(item.data_vencimento)}` : ""}`}
                        </span>
                      </p>
                    </div>
                    {item.recebimentos.length > 0 && (
                      <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-0.5">
                        {item.recebimentos.map((recebimento) => (
                          <li key={recebimento.id}>
                            {dataBr(recebimento.data)} · {recebimento.payment_method_label} · {moeda(recebimento.valor)}
                          </li>
                        ))}
                      </ul>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {!item.quitado && (
                        <button
                          type="button"
                          onClick={() => {
                            setReceberId(item.id);
                            setValorReceber(String(item.saldo));
                            setDataReceber(hojeIso());
                          }}
                          className="px-3 py-1.5 rounded-lg text-sm font-medium text-white"
                          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
                        >
                          Receber
                        </button>
                      )}
                      <button
                        type="button"
                        disabled={ocupado}
                        onClick={() => void excluirProcedimento(item.id)}
                        className="px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-300 disabled:opacity-50"
                      >
                        Excluir
                      </button>
                    </div>
                    {receberId === item.id && (
                      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 pt-1">
                        <input
                          inputMode="decimal"
                          value={valorReceber}
                          onChange={(e) => setValorReceber(e.target.value)}
                          className={fieldClass}
                          aria-label="Valor recebido"
                        />
                        <input
                          type="date"
                          value={dataReceber}
                          onChange={(e) => setDataReceber(e.target.value)}
                          className={fieldClass}
                          aria-label="Data do recebimento"
                        />
                        <select
                          value={formaReceber}
                          onChange={(e) => setFormaReceber(e.target.value)}
                          className={fieldClass}
                          aria-label="Forma de pagamento"
                        >
                          {FORMAS.map((forma) => (
                            <option key={forma.id} value={forma.id}>{forma.label}</option>
                          ))}
                        </select>
                        <button
                          type="button"
                          disabled={ocupado}
                          onClick={() => void receber(item.id)}
                          className="px-3 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
                          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
                        >
                          Confirmar
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </section>
        </>
      )}
    </ClinicaBelezaPanel>
  );
}
