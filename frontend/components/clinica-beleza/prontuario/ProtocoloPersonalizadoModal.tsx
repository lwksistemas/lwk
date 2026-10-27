"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { useToast } from "@/components/ui/Toast";
import { precoDaPromocao } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import type { DescontoTipo } from "./protocolo-personalizado-utils";

interface Opcao {
  id: number;
  nome: string;
}

interface ProcedimentoOpcao extends Opcao {
  preco: string;
  categoria: string;
  categoria_nome: string;
}

interface ProdutoOpcao extends Opcao {
  unidade_medida: string;
  categoria: string;
  categoria_nome: string;
}

interface CategoriaOpcao {
  slug: string;
  nome: string;
}

interface OpcoesProtocolo {
  locais: Opcao[];
  procedimentos: ProcedimentoOpcao[];
  produtos: ProdutoOpcao[];
}

interface ProcedimentoEscolhido extends ProcedimentoOpcao {
  desconto_tipo: DescontoTipo;
  desconto_valor: string;
}

interface ProtocoloSalvo {
  id: number;
  nome: string;
  sessoes: number;
  intervalo_quantidade: number;
  intervalo_unidade: string;
  tempo_minutos: number;
  desconto_escopo?: "total" | "individual";
  desconto_tipo: DescontoTipo;
  desconto_valor: string;
  valor_total: string;
  na_agenda: number;
  pode_editar: boolean;
  pode_excluir: boolean;
  procedimentos: ProcedimentoEscolhido[];
  produtos: ProdutoEscolhido[];
}

interface ProdutoEscolhido {
  produto_id: number;
  nome: string;
  quantidade: string;
  unidade: string;
}

interface ProtocoloPersonalizadoModalProps {
  patientId: number;
  onClose: () => void;
}

const CAMPO = "w-full min-w-0 border border-gray-300 dark:border-neutral-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-neutral-900";
const SECAO = "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-700 pb-2";

function categoriasDe(itens: Array<{ categoria: string; categoria_nome: string }>): CategoriaOpcao[] {
  const mapa = new Map<string, string>();
  for (const item of itens) {
    if (!mapa.has(item.categoria)) mapa.set(item.categoria, item.categoria_nome || item.categoria);
  }
  return [...mapa.entries()]
    .map(([slug, nome]) => ({ slug, nome }))
    .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
}

export function ProtocoloPersonalizadoModal({ patientId, onClose }: ProtocoloPersonalizadoModalProps) {
  const toast = useToast();
  const [opcoes, setOpcoes] = useState<OpcoesProtocolo | null>(null);
  const [salvos, setSalvos] = useState<ProtocoloSalvo[]>([]);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);
  const [erro, setErro] = useState("");
  const [categoriaProcedimento, setCategoriaProcedimento] = useState("");
  const [procedimentoId, setProcedimentoId] = useState("");
  const [escolhidos, setEscolhidos] = useState<ProcedimentoEscolhido[]>([]);
  const [descontoEscopo, setDescontoEscopo] = useState<"total" | "individual">("total");
  const [categoriaProduto, setCategoriaProduto] = useState("");
  const [produtoId, setProdutoId] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [erroProduto, setErroProduto] = useState("");
  const [produtos, setProdutos] = useState<ProdutoEscolhido[]>([]);
  const [descontoTipo, setDescontoTipo] = useState<DescontoTipo>("percentual");
  const [descontoValor, setDescontoValor] = useState("0");
  const [sessoes, setSessoes] = useState("4");
  const [intervalo, setIntervalo] = useState("15");
  const [unidade, setUnidade] = useState("dias");
  const [tempo, setTempo] = useState("40");
  const [nome, setNome] = useState("");

  const carregarSalvos = async () => {
    const lista = await ClinicaBelezaAPI.get<ProtocoloSalvo[]>(
      `/protocolos/personalizados/?patient=${patientId}`,
    );
    setSalvos(Array.isArray(lista) ? lista : []);
  };

  useEffect(() => {
    let ativo = true;
    Promise.all([
      ClinicaBelezaAPI.get<OpcoesProtocolo>(
        `/protocolos/personalizados/opcoes/?patient=${patientId}`,
      ),
      ClinicaBelezaAPI.get<ProtocoloSalvo[]>(
        `/protocolos/personalizados/?patient=${patientId}`,
      ),
    ])
      .then(([opcoesData, lista]) => {
        if (!ativo) return;
        setOpcoes(opcoesData);
        setSalvos(Array.isArray(lista) ? lista : []);
      })
      .catch((err) => {
        if (ativo) setErro(formatApiErrorBody(err) || "Não foi possível carregar os procedimentos.");
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [patientId]);

  const limparFormulario = () => {
    setEditandoId(null);
    setEscolhidos([]);
    setProdutos([]);
    setDescontoEscopo("total");
    setDescontoTipo("percentual");
    setDescontoValor("0");
    setSessoes("4");
    setIntervalo("15");
    setUnidade("dias");
    setTempo("40");
    setNome("");
    setCategoriaProcedimento("");
    setProcedimentoId("");
    setCategoriaProduto("");
    setProdutoId("");
    setQuantidade("1");
    setErro("");
  };

  const editar = (item: ProtocoloSalvo) => {
    if (!item.pode_editar) {
      setErro("Este protocolo já está na agenda. Exclua o pacote para tirar as sessões que ainda não foram atendidas.");
      return;
    }
    setErro("");
    setEditandoId(item.id);
    setEscolhidos(item.procedimentos.map((procedimento) => ({
      ...procedimento,
      desconto_tipo: procedimento.desconto_tipo === "fixo" ? "fixo" : "percentual",
      desconto_valor: procedimento.desconto_valor || "0",
    })));
    setProdutos(item.produtos);
    setDescontoEscopo(item.desconto_escopo === "individual" ? "individual" : "total");
    setDescontoTipo(item.desconto_tipo === "fixo" ? "fixo" : "percentual");
    setDescontoValor(item.desconto_valor);
    setSessoes(String(item.sessoes));
    setIntervalo(String(item.intervalo_quantidade));
    setUnidade(item.intervalo_unidade || "dias");
    setTempo(String(item.tempo_minutos));
    setNome(item.nome === "Protocolo personalizado" ? "" : item.nome);
  };

  const excluir = async (item: ProtocoloSalvo) => {
    if (!item.pode_excluir) {
      setErro("Este protocolo já teve sessão com a cliente presente ou pagamento. Ele permanece no prontuário.");
      return;
    }
    const aviso = item.na_agenda > 0
      ? `Excluir "${item.nome}"? As ${item.na_agenda} sessões que ainda não foram atendidas saem da agenda.`
      : `Excluir "${item.nome}"?`;
    if (!window.confirm(aviso)) return;
    setErro("");
    setExcluindoId(item.id);
    try {
      await ClinicaBelezaAPI.delete(`/protocolos/personalizados/${item.id}/`);
      if (editandoId === item.id) limparFormulario();
      await carregarSalvos();
      toast.success("Protocolo excluído.");
    } catch (err) {
      setErro(formatApiErrorBody(err) || "Não foi possível excluir o protocolo.");
    } finally {
      setExcluindoId(null);
    }
  };

  const conta = precoDaPromocao(
    escolhidos.map((item) => ({
      preco: Number(item.preco) || 0,
      desconto_tipo: item.desconto_tipo,
      desconto_valor: Number(String(item.desconto_valor).replace(",", ".")) || 0,
    })),
    descontoEscopo,
    descontoTipo,
    Number(String(descontoValor).replace(",", ".")) || 0,
  );

  const procedimentosClinica = useMemo(
    () => (opcoes?.procedimentos ?? []).filter((item) => item.categoria !== "protocolo"),
    [opcoes],
  );
  const categoriasProcedimento = useMemo(
    () => categoriasDe(procedimentosClinica),
    [procedimentosClinica],
  );
  const procedimentosDaCategoria = useMemo(
    () =>
      procedimentosClinica.filter(
        (item) => item.categoria === categoriaProcedimento && !escolhidos.some((escolhido) => escolhido.id === item.id),
      ),
    [procedimentosClinica, categoriaProcedimento, escolhidos],
  );
  const categoriasProduto = useMemo(
    () => categoriasDe(opcoes?.produtos ?? []),
    [opcoes],
  );
  const produtosDaCategoria = useMemo(
    () =>
      (opcoes?.produtos ?? []).filter(
        (item) => item.categoria === categoriaProduto && !produtos.some((escolhido) => escolhido.produto_id === item.id),
      ),
    [opcoes, categoriaProduto, produtos],
  );

  const adicionarProcedimento = () => {
    if (!categoriaProcedimento) {
      setErro("Escolha a categoria do procedimento.");
      return;
    }
    const item = procedimentosDaCategoria.find((p) => String(p.id) === procedimentoId);
    if (!item) {
      setErro("Escolha o procedimento.");
      return;
    }
    if (escolhidos.some((p) => p.id === item.id)) {
      setErro("Este procedimento já está no protocolo.");
      return;
    }
    setErro("");
    setEscolhidos((lista) => [...lista, { ...item, desconto_tipo: "percentual", desconto_valor: "0" }]);
    setProcedimentoId("");
  };

  const adicionarProduto = () => {
    if (!categoriaProduto) {
      setErroProduto("Escolha a categoria do produto.");
      return;
    }
    const item = produtosDaCategoria.find((p) => String(p.id) === produtoId);
    if (!item) {
      setErroProduto("Escolha o produto.");
      return;
    }
    const qtd = quantidade.replace(",", ".").trim();
    const numero = Number(qtd);
    if (!qtd || !Number.isFinite(numero) || numero <= 0) {
      setErroProduto("Informe uma quantidade maior que zero.");
      return;
    }
    setProdutos((lista) => [
      ...lista,
      { produto_id: item.id, nome: item.nome, quantidade: qtd, unidade: item.unidade_medida },
    ]);
    setProdutoId("");
    setQuantidade("1");
    setErroProduto("");
  };

  const salvar = async () => {
    setErro("");
    setSalvando(true);
    const corpo = {
      procedimentos: escolhidos.map((item) => ({
        procedure: item.id,
        desconto_tipo: descontoEscopo === "individual" ? item.desconto_tipo : "",
        desconto_valor: descontoEscopo === "individual" ? item.desconto_valor || "0" : "0",
      })),
      produtos: produtos.map((item) => ({
        produto_id: item.produto_id,
        quantidade: item.quantidade,
      })),
      desconto_escopo: descontoEscopo,
      desconto_tipo: descontoTipo,
      desconto_valor: descontoValor || "0",
      sessoes: Number(sessoes),
      intervalo_quantidade: Number(intervalo),
      intervalo_unidade: unidade,
      tempo_minutos: Number(tempo),
      nome,
    };
    try {
      if (editandoId) {
        await ClinicaBelezaAPI.patch(`/protocolos/personalizados/${editandoId}/`, corpo);
        toast.success("Protocolo atualizado.");
      } else {
        await ClinicaBelezaAPI.post("/protocolos/personalizados/", { patient: patientId, ...corpo });
        toast.success("Protocolo salvo. A secretaria agenda e escolhe a profissional.");
      }
      limparFormulario();
      await carregarSalvos();
    } catch (err) {
      setErro(formatApiErrorBody(err) || "Não foi possível salvar o protocolo.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-3 sm:p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-[min(96vw,1280px)] max-h-[min(88vh,820px)] min-h-0 flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="protocolo-personalizado-titulo"
      >
        <div className="shrink-0 flex items-start justify-between gap-3 px-5 py-3.5 border-b border-gray-200 dark:border-neutral-700">
          <div className="min-w-0">
            <h3 id="protocolo-personalizado-titulo" className="text-lg font-semibold text-gray-900 dark:text-white">
              Protocolo personalizado
            </h3>
            <p className="text-sm text-gray-500 mt-0.5">
              Monte o tratamento e o desconto desta cliente. Qualquer profissional pode atender.
            </p>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg text-gray-500" aria-label="Fechar">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 min-h-0 min-w-0 overflow-y-auto overflow-x-hidden p-5 space-y-4">
          {carregando ? (
            <p className="text-sm text-gray-500">Carregando procedimentos...</p>
          ) : (
            <>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900 dark:text-white">Protocolos desta cliente</p>
                {salvos.length === 0 ? (
                  <p className="text-sm text-gray-500">Nenhum protocolo personalizado ainda.</p>
                ) : (
                  salvos.map((item) => (
                    <div
                      key={item.id}
                      className="flex flex-wrap items-start justify-between gap-2 rounded-lg border border-gray-200 dark:border-neutral-700 px-3 py-2"
                    >
                      <div className="min-w-0 text-sm">
                        <p className="font-medium break-words">{item.nome}</p>
                        <p className="text-gray-500">
                          {item.sessoes} sessões · {formatCurrency(item.valor_total)}
                          {" · "}
                          {item.na_agenda > 0 ? `${item.na_agenda} na agenda` : "Ainda não agendado"}
                        </p>
                        {!item.pode_editar ? (
                          <p className="text-xs text-gray-500">A edição fica bloqueada porque as sessões já estão na agenda.</p>
                        ) : null}
                        {!item.pode_excluir ? (
                          <p className="text-xs text-gray-500">Não pode ser excluído: já teve atendimento ou pagamento.</p>
                        ) : null}
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <button
                          type="button"
                          onClick={() => editar(item)}
                          disabled={!item.pode_editar}
                          title={item.pode_editar ? "Editar" : "Já está na agenda"}
                          className="px-3 py-1.5 text-sm rounded-lg border disabled:opacity-40"
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => void excluir(item)}
                          disabled={!item.pode_excluir || excluindoId === item.id}
                          title={item.pode_excluir ? "Excluir" : "Já teve atendimento ou pagamento"}
                          className="px-3 py-1.5 text-sm rounded-lg border text-red-600 disabled:opacity-40"
                        >
                          {excluindoId === item.id ? "Excluindo..." : "Excluir"}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 items-start">
              <div className="space-y-4 min-w-0">
              <div className="space-y-4 border-t border-gray-200 dark:border-neutral-700 pt-4">
                <p className={SECAO}>{editandoId ? "Editar protocolo" : "Dados do protocolo"}</p>
                <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_8rem] gap-3">
                  <label className="text-sm block min-w-0">
                    Nome do protocolo *
                    <input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Protocolo personalizado" className={`${CAMPO} mt-1`} />
                  </label>
                  <label className="text-sm block min-w-0">
                    Tempo estimado (min) *
                    <input value={tempo} onChange={(e) => setTempo(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                  </label>
                </div>
                <p className="text-xs text-gray-500">
                  Este é o protocolo desta cliente. Ele é diferente do protocolo global da clínica.
                </p>
              </div>
              <div className="space-y-4 border-t border-gray-200 dark:border-neutral-700 pt-4">
                <p className={SECAO}>Pacote comercial</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <label className="text-sm min-w-0">Sessões *
                    <input value={sessoes} onChange={(e) => setSessoes(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                  </label>
                  <label className="text-sm min-w-0">Intervalo entre sessões *
                    <input value={intervalo} onChange={(e) => setIntervalo(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                  </label>
                  <label className="text-sm min-w-0">Unidade *
                    <select value={unidade} onChange={(e) => setUnidade(e.target.value)} className={`${CAMPO} mt-1`}>
                      <option value="dias">Dias</option>
                      <option value="semanas">Semanas</option>
                      <option value="meses">Meses</option>
                    </select>
                  </label>
                </div>
                <p className="text-xs text-gray-500">
                  O intervalo é entre uma sessão e a outra. Na agenda, a secretaria escolhe o tipo Protocolo, a profissional, o local e a primeira sessão. Depois de Cliente presente, o recebimento escolhe o valor total com desconto ou o parcelamento por sessão.
                </p>
              </div>
              </div>
              <div className="space-y-4 min-w-0 border-t border-gray-200 dark:border-neutral-700 pt-4">
                <p className={SECAO}>Procedimentos da promoção</p>
                <p className="text-xs text-gray-500">
                  Inclua os procedimentos já cadastrados. O valor cobrado é a soma deles, com o desconto abaixo. O preço segue o convênio desta cliente.
                </p>
              <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,11rem)_minmax(0,1fr)_auto] gap-2 min-w-0">
                <select
                  value={categoriaProcedimento}
                  onChange={(e) => {
                    setCategoriaProcedimento(e.target.value);
                    setProcedimentoId("");
                    setErro("");
                  }}
                  className={CAMPO}
                  aria-label="Categoria do procedimento"
                >
                  <option value="">Categoria</option>
                  {categoriasProcedimento.map((item) => (
                    <option key={item.slug} value={item.slug}>{item.nome}</option>
                  ))}
                </select>
                <select
                  value={procedimentoId}
                  onChange={(e) => {
                    setProcedimentoId(e.target.value);
                    setErro("");
                  }}
                  disabled={!categoriaProcedimento}
                  className={CAMPO}
                  aria-label="Procedimento"
                >
                  <option value="">{categoriaProcedimento ? "Procedimento" : "Escolha a categoria"}</option>
                  {procedimentosDaCategoria.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome} — {formatCurrency(item.preco)}
                    </option>
                  ))}
                </select>
                <button type="button" onClick={adicionarProcedimento} className="px-3 py-2 text-sm rounded-lg border shrink-0">
                  Incluir
                </button>
              </div>
              {escolhidos.length > 0 ? (
                <div className="space-y-2">
                  <label className="text-sm block">
                    Desconto
                    <select
                      value={descontoEscopo}
                      onChange={(e) => setDescontoEscopo(e.target.value as "total" | "individual")}
                      className={`${CAMPO} mt-1`}
                    >
                      <option value="total">No total dos procedimentos</option>
                      <option value="individual">Em cada procedimento</option>
                    </select>
                  </label>
                  {escolhidos.map((item) => (
                    <div
                      key={item.id}
                      className={
                        descontoEscopo === "individual"
                          ? "grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_9rem_7rem_auto] gap-2 items-center"
                          : "flex items-center justify-between gap-3"
                      }
                    >
                      <span className="text-sm min-w-0 break-words">
                        {item.nome}
                        <span className="text-gray-500"> · {formatCurrency(item.preco)}</span>
                      </span>
                      {descontoEscopo === "individual" ? (
                        <>
                          <select
                            value={item.desconto_tipo}
                            aria-label={`Tipo de desconto de ${item.nome}`}
                            onChange={(e) =>
                              setEscolhidos((lista) =>
                                lista.map((atual) =>
                                  atual.id === item.id
                                    ? { ...atual, desconto_tipo: e.target.value as DescontoTipo }
                                    : atual,
                                ),
                              )
                            }
                            className={CAMPO}
                          >
                            <option value="percentual">Porcentagem</option>
                            <option value="fixo">Valor fixo (R$)</option>
                          </select>
                          <input
                            value={item.desconto_valor}
                            aria-label={`Desconto de ${item.nome}`}
                            onChange={(e) =>
                              setEscolhidos((lista) =>
                                lista.map((atual) =>
                                  atual.id === item.id ? { ...atual, desconto_valor: e.target.value } : atual,
                                ),
                              )
                            }
                            className={CAMPO}
                            inputMode="decimal"
                          />
                        </>
                      ) : null}
                      <button
                        type="button"
                        className="text-sm text-red-600"
                        onClick={() => setEscolhidos((lista) => lista.filter((p) => p.id !== item.id))}
                      >
                        Remover
                      </button>
                    </div>
                  ))}
                  <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_8rem_auto] gap-2 items-end">
                    {descontoEscopo === "total" ? (
                      <>
                        <label className="text-sm">
                          Tipo
                          <select value={descontoTipo} onChange={(e) => setDescontoTipo(e.target.value as DescontoTipo)} className={`${CAMPO} mt-1`}>
                            <option value="percentual">Porcentagem</option>
                            <option value="fixo">Valor fixo (R$)</option>
                          </select>
                        </label>
                        <label className="text-sm">
                          {descontoTipo === "percentual" ? "Porcentagem" : "Valor (R$)"}
                          <input value={descontoValor} onChange={(e) => setDescontoValor(e.target.value)} className={`${CAMPO} mt-1`} inputMode="decimal" />
                        </label>
                      </>
                    ) : (
                      <span className="hidden sm:block sm:col-span-2" />
                    )}
                    <div className="text-sm rounded-lg border border-gray-200 dark:border-neutral-700 px-3 py-2">
                      <p>Soma {formatCurrency(conta.bruto)}</p>
                      <p>Desconto {formatCurrency(conta.desconto)}</p>
                      <p className="font-semibold">Total {formatCurrency(conta.liquido)}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">Nenhum procedimento incluído.</p>
              )}
              <div className="min-w-0 space-y-2 border-t border-gray-200 dark:border-neutral-700 pt-4">
                <p className={SECAO}>Produtos por sessão</p>
                <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,11rem)_minmax(0,1fr)_5rem_auto] gap-2 min-w-0">
                  <select
                    value={categoriaProduto}
                    onChange={(e) => {
                      setCategoriaProduto(e.target.value);
                      setProdutoId("");
                      setErroProduto("");
                    }}
                    className={CAMPO}
                    aria-label="Categoria do produto"
                  >
                    <option value="">Categoria</option>
                    {categoriasProduto.map((item) => (
                      <option key={item.slug} value={item.slug}>{item.nome}</option>
                    ))}
                  </select>
                  <select
                    value={produtoId}
                    onChange={(e) => {
                      setProdutoId(e.target.value);
                      setErroProduto("");
                    }}
                    disabled={!categoriaProduto}
                    className={CAMPO}
                    aria-label="Produto"
                  >
                    <option value="">{categoriaProduto ? "Produto" : "Escolha a categoria"}</option>
                    {produtosDaCategoria.map((item) => (
                      <option key={item.id} value={item.id}>{item.nome}</option>
                    ))}
                  </select>
                  <input
                    value={quantidade}
                    onChange={(e) => setQuantidade(e.target.value)}
                    aria-label="Quantidade por sessão"
                    className={CAMPO}
                    inputMode="decimal"
                  />
                  <button type="button" onClick={adicionarProduto} className="px-3 py-2 text-sm rounded-lg border shrink-0">
                    Incluir
                  </button>
                </div>
                {erroProduto ? <p className="text-sm text-red-600">{erroProduto}</p> : null}
              {produtos.map((item) => (
                <div key={item.produto_id} className="flex items-start gap-2 text-sm min-w-0">
                  <span className="min-w-0 flex-1 break-words">{item.nome}</span>
                  <input
                    value={item.quantidade}
                    onChange={(e) =>
                      setProdutos((lista) =>
                        lista.map((atual) =>
                          atual.produto_id === item.produto_id
                            ? { ...atual, quantidade: e.target.value }
                            : atual,
                        ),
                      )
                    }
                    aria-label={`Quantidade de ${item.nome}`}
                    className="w-20 shrink-0 border border-gray-300 dark:border-neutral-600 rounded-lg px-2 py-1 text-sm bg-white dark:bg-neutral-900"
                    inputMode="decimal"
                  />
                  <span className="shrink-0 text-gray-500">{item.unidade || "por sessão"}</span>
                  <button
                    type="button"
                    className="shrink-0 text-red-600"
                    onClick={() => setProdutos((lista) => lista.filter((p) => p.produto_id !== item.produto_id))}
                  >
                    Remover
                  </button>
                </div>
              ))}
              <p className="text-xs text-gray-500">
                Escolha a categoria e depois o produto. A quantidade é por sessão. O estoque baixa quando a sessão é finalizada.
              </p>
              </div>
              </div>
              </div>
            </>
          )}
          {erro ? <p className="text-sm text-red-600">{erro}</p> : null}
        </div>

        <div className="shrink-0 flex justify-end gap-2 px-5 py-3 border-t border-gray-200 dark:border-neutral-700">
          {editandoId ? (
            <button type="button" onClick={limparFormulario} className="px-4 py-2 text-sm border rounded-lg">
              Novo protocolo
            </button>
          ) : null}
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm border rounded-lg">Cancelar</button>
          <button
            type="button"
            onClick={() => void salvar()}
            disabled={salvando || carregando || escolhidos.length === 0}
            className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            {salvando ? "Salvando..." : editandoId ? "Salvar alterações" : "Cadastrar protocolo"}
          </button>
        </div>
      </div>
    </div>
  );
}
