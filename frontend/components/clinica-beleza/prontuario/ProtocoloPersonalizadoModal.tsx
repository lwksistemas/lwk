"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { useToast } from "@/components/ui/Toast";
import { aplicarDescontoProtocolo, type DescontoTipo } from "./protocolo-personalizado-utils";

interface Opcao {
  id: number;
  nome: string;
}

interface ProcedimentoOpcao extends Opcao {
  preco: string;
}

interface ProdutoOpcao extends Opcao {
  unidade_medida: string;
}

interface OpcoesProtocolo {
  locais: Opcao[];
  procedimentos: ProcedimentoOpcao[];
  produtos: ProdutoOpcao[];
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

export function ProtocoloPersonalizadoModal({ patientId, onClose }: ProtocoloPersonalizadoModalProps) {
  const toast = useToast();
  const [opcoes, setOpcoes] = useState<OpcoesProtocolo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [procedimentoId, setProcedimentoId] = useState("");
  const [escolhidos, setEscolhidos] = useState<ProcedimentoOpcao[]>([]);
  const [buscaProduto, setBuscaProduto] = useState("");
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

  useEffect(() => {
    let ativo = true;
    ClinicaBelezaAPI.get<OpcoesProtocolo>(
      `/protocolos/personalizados/opcoes/?patient=${patientId}`,
    )
      .then((data) => {
        if (ativo) setOpcoes(data);
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

  const bruto = escolhidos.reduce((soma, item) => soma + Number(item.preco), 0);
  const conta = aplicarDescontoProtocolo(bruto, descontoTipo, Number(descontoValor || 0));

  const sugestoes = useMemo(() => {
    const termo = buscaProduto.trim().toLowerCase();
    if (!termo) return [];
    return (opcoes?.produtos ?? [])
      .filter((item) => item.nome.toLowerCase().includes(termo))
      .filter((item) => !produtos.some((escolhido) => escolhido.produto_id === item.id))
      .slice(0, 8);
  }, [buscaProduto, opcoes, produtos]);

  const adicionarProcedimento = () => {
    const item = opcoes?.procedimentos.find((p) => String(p.id) === procedimentoId);
    if (!item || escolhidos.some((p) => p.id === item.id)) return;
    setEscolhidos((lista) => [...lista, item]);
    setProcedimentoId("");
  };

  const adicionarProduto = (item: ProdutoOpcao) => {
    const qtd = quantidade.replace(",", ".").trim();
    const numero = Number(qtd);
    if (!qtd || !Number.isFinite(numero) || numero <= 0) {
      setErroProduto("Informe uma quantidade maior que zero.");
      return;
    }
    if (produtos.some((escolhido) => escolhido.produto_id === item.id)) {
      setErroProduto("Este produto já está na lista.");
      return;
    }
    setProdutos((lista) => [
      ...lista,
      { produto_id: item.id, nome: item.nome, quantidade: qtd, unidade: item.unidade_medida },
    ]);
    setBuscaProduto("");
    setQuantidade("1");
    setErroProduto("");
  };

  const salvar = async () => {
    setErro("");
    setSalvando(true);
    try {
      await ClinicaBelezaAPI.post("/protocolos/personalizados/", {
        patient: patientId,
        procedimentos: escolhidos.map((item) => item.id),
        produtos: produtos.map((item) => ({
          produto_id: item.produto_id,
          quantidade: item.quantidade,
        })),
        desconto_tipo: descontoTipo,
        desconto_valor: descontoValor || "0",
        sessoes: Number(sessoes),
        intervalo_quantidade: Number(intervalo),
        intervalo_unidade: unidade,
        tempo_minutos: Number(tempo),
        nome,
      });
      toast.success("Protocolo salvo. A secretaria agenda e escolhe a profissional.");
      onClose();
    } catch (err) {
      setErro(formatApiErrorBody(err) || "Não foi possível criar o protocolo.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-3 sm:p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full min-w-0 max-w-3xl max-h-[min(90vh,100%)] flex flex-col overflow-hidden"
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
              <div className="flex flex-wrap gap-2 min-w-0">
                <select
                  value={procedimentoId}
                  onChange={(e) => setProcedimentoId(e.target.value)}
                  className={`${CAMPO} max-w-md flex-1`}
                >
                  <option value="">Adicionar procedimento</option>
                  {opcoes?.procedimentos.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome} — {formatCurrency(item.preco)}
                    </option>
                  ))}
                </select>
                <button type="button" onClick={adicionarProcedimento} className="px-3 py-2 text-sm rounded-lg border shrink-0">
                  Incluir
                </button>
              </div>
              {escolhidos.map((item) => (
                <div key={item.id} className="flex items-start justify-between gap-3 text-sm min-w-0">
                  <span className="min-w-0 break-words">{item.nome}</span>
                  <span className="flex items-center gap-3 shrink-0">
                    {formatCurrency(item.preco)}
                    <button type="button" className="text-red-600" onClick={() => setEscolhidos((lista) => lista.filter((p) => p.id !== item.id))}>
                      Remover
                    </button>
                  </span>
                </div>
              ))}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <label className="text-sm min-w-0">
                  Desconto
                  <select value={descontoTipo} onChange={(e) => setDescontoTipo(e.target.value as DescontoTipo)} className={`${CAMPO} mt-1`}>
                    <option value="percentual">Porcentagem</option>
                    <option value="fixo">Valor fixo (R$)</option>
                  </select>
                </label>
                <label className="text-sm min-w-0">
                  {descontoTipo === "percentual" ? "Porcentagem" : "Valor (R$)"}
                  <input value={descontoValor} onChange={(e) => setDescontoValor(e.target.value)} className={`${CAMPO} mt-1`} inputMode="decimal" />
                </label>
                <div className="text-sm rounded-lg border border-gray-200 dark:border-neutral-700 px-3 py-2">
                  <p>Soma {formatCurrency(bruto)}</p>
                  <p>Desconto {formatCurrency(conta.desconto)}</p>
                  <p className="font-semibold">Total {formatCurrency(conta.liquido)}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <label className="text-sm min-w-0">Sessões
                  <input value={sessoes} onChange={(e) => setSessoes(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                </label>
                <label className="text-sm min-w-0">Intervalo
                  <input value={intervalo} onChange={(e) => setIntervalo(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                </label>
                <label className="text-sm min-w-0">Unidade
                  <select value={unidade} onChange={(e) => setUnidade(e.target.value)} className={`${CAMPO} mt-1`}>
                    <option value="dias">Dias</option>
                    <option value="semanas">Semanas</option>
                    <option value="meses">Meses</option>
                  </select>
                </label>
                <label className="text-sm min-w-0">Minutos de cada atendimento
                  <input value={tempo} onChange={(e) => setTempo(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                </label>
              </div>

              <div className="min-w-0 space-y-2">
                <p className="text-sm text-gray-700 dark:text-gray-200">Produto por sessão</p>
                <div className="flex gap-2 min-w-0">
                  <input
                    value={buscaProduto}
                    onChange={(e) => {
                      setBuscaProduto(e.target.value);
                      setErroProduto("");
                    }}
                    placeholder="Buscar produto pelo nome"
                    className={CAMPO}
                  />
                  <input
                    value={quantidade}
                    onChange={(e) => setQuantidade(e.target.value)}
                    aria-label="Quantidade por sessão"
                    className="w-20 shrink-0 border border-gray-300 dark:border-neutral-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-neutral-900"
                    inputMode="decimal"
                  />
                </div>
                {sugestoes.length > 0 ? (
                  <ul className="border border-gray-200 dark:border-neutral-600 rounded-lg max-h-40 overflow-y-auto">
                    {sugestoes.map((item) => (
                      <li key={item.id}>
                        <button
                          type="button"
                          onClick={() => adicionarProduto(item)}
                          className="w-full text-left px-3 py-2 text-sm break-words hover:bg-gray-50 dark:hover:bg-neutral-700"
                        >
                          {item.nome}
                          {item.unidade_medida ? ` · ${item.unidade_medida}` : ""}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
                {buscaProduto.trim() && sugestoes.length === 0 ? (
                  <p className="text-sm text-gray-500">Nenhum produto com esse nome.</p>
                ) : null}
                {erroProduto ? <p className="text-sm text-red-600">{erroProduto}</p> : null}
              </div>
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
                Busque o produto e clique no nome para incluir, com a quantidade ao lado. O estoque baixa quando a sessão é finalizada.
              </p>

              <label className="text-sm block min-w-0">Nome do tratamento
                <input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Protocolo personalizado" className={`${CAMPO} mt-1`} />
              </label>
              <p className="text-xs text-gray-500">
                Na agenda, a secretaria escolhe o tipo Protocolo, a profissional, o local e a primeira sessão. Depois de Cliente presente, o recebimento escolhe o valor total com desconto ou o parcelamento por sessão.
              </p>
            </>
          )}
          {erro ? <p className="text-sm text-red-600">{erro}</p> : null}
        </div>

        <div className="shrink-0 flex justify-end gap-2 px-5 py-3 border-t border-gray-200 dark:border-neutral-700">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm border rounded-lg">Cancelar</button>
          <button
            type="button"
            onClick={() => void salvar()}
            disabled={salvando || carregando || escolhidos.length === 0}
            className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            {salvando ? "Salvando..." : "Salvar protocolo"}
          </button>
        </div>
      </div>
    </div>
  );
}
