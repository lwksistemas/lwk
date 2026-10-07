"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatApiErrorBody } from "@/lib/api-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { dividirValorProtocolo } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
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
  profissional_id: number | null;
  profissionais: Opcao[];
  locais: Opcao[];
  procedimentos: ProcedimentoOpcao[];
  produtos: ProdutoOpcao[];
}

interface ProtocoloPersonalizadoModalProps {
  patientId: number;
  onClose: () => void;
}

const CAMPO = "w-full border border-gray-300 dark:border-neutral-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-neutral-900";

export function ProtocoloPersonalizadoModal({ patientId, onClose }: ProtocoloPersonalizadoModalProps) {
  const toast = useToast();
  const [opcoes, setOpcoes] = useState<OpcoesProtocolo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [procedimentoId, setProcedimentoId] = useState("");
  const [escolhidos, setEscolhidos] = useState<ProcedimentoOpcao[]>([]);
  const [produtoId, setProdutoId] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [produtos, setProdutos] = useState<Array<{ produto_id: number; nome: string; quantidade: string }>>([]);
  const [descontoTipo, setDescontoTipo] = useState<DescontoTipo>("percentual");
  const [descontoValor, setDescontoValor] = useState("0");
  const [sessoes, setSessoes] = useState("4");
  const [intervalo, setIntervalo] = useState("15");
  const [unidade, setUnidade] = useState("dias");
  const [tempo, setTempo] = useState("40");
  const [forma, setForma] = useState<"POR_CONSULTA" | "TOTAL">("POR_CONSULTA");
  const [professionalId, setProfessionalId] = useState("");
  const [localId, setLocalId] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [nome, setNome] = useState("");

  useEffect(() => {
    let ativo = true;
    ClinicaBelezaAPI.get<OpcoesProtocolo>(
      `/protocolos/personalizados/opcoes/?patient=${patientId}`,
    )
      .then((data) => {
        if (!ativo) return;
        setOpcoes(data);
        if (data.profissional_id) setProfessionalId(String(data.profissional_id));
        if (data.locais.length === 1) setLocalId(String(data.locais[0].id));
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
  const qtdSessoes = Math.max(1, Number(sessoes) || 1);
  const partes = useMemo(
    () => dividirValorProtocolo(conta.liquido, qtdSessoes, forma),
    [conta.liquido, qtdSessoes, forma],
  );

  const adicionarProcedimento = () => {
    const item = opcoes?.procedimentos.find((p) => String(p.id) === procedimentoId);
    if (!item || escolhidos.some((p) => p.id === item.id)) return;
    setEscolhidos((lista) => [...lista, item]);
    setProcedimentoId("");
  };

  const adicionarProduto = () => {
    const item = opcoes?.produtos.find((p) => String(p.id) === produtoId);
    if (!item || produtos.some((p) => p.produto_id === item.id)) return;
    setProdutos((lista) => [...lista, { produto_id: item.id, nome: item.nome, quantidade }]);
    setProdutoId("");
    setQuantidade("1");
  };

  const salvar = async () => {
    setErro("");
    setSalvando(true);
    try {
      const resultado = await ClinicaBelezaAPI.post<{
        agendamentos: Array<{ ajustado: boolean }>;
      }>("/protocolos/personalizados/", {
        patient: patientId,
        professional: Number(professionalId),
        local_atendimento: Number(localId),
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
        forma_cobranca: forma,
        data_inicio: dataInicio,
        nome,
      });
      const ajustados = resultado.agendamentos.filter((item) => item.ajustado).length;
      const aviso = ajustados
        ? ` ${ajustados} sessão(ões) foram para o próximo horário livre.`
        : "";
      toast.success(`Protocolo criado com ${resultado.agendamentos.length} sessões na agenda.${aviso}`);
      onClose();
    } catch (err) {
      setErro(formatApiErrorBody(err) || "Não foi possível criar o protocolo.");
    } finally {
      setSalvando(false);
    }
  };

  const profissionalFixa = Boolean(opcoes?.profissional_id);

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
          <div>
            <h3 id="protocolo-personalizado-titulo" className="text-lg font-semibold text-gray-900 dark:text-white">
              Protocolo personalizado
            </h3>
            <p className="text-sm text-gray-500 mt-0.5">
              Monte o tratamento, o desconto e as sessões desta cliente.
            </p>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg text-gray-500" aria-label="Fechar">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-4">
          {carregando ? (
            <p className="text-sm text-gray-500">Carregando procedimentos...</p>
          ) : (
            <>
              <div className="flex flex-wrap gap-2">
                <select value={procedimentoId} onChange={(e) => setProcedimentoId(e.target.value)} className={`${CAMPO} max-w-md`}>
                  <option value="">Adicionar procedimento</option>
                  {opcoes?.procedimentos.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome} — {formatCurrency(item.preco)}
                    </option>
                  ))}
                </select>
                <button type="button" onClick={adicionarProcedimento} className="px-3 py-2 text-sm rounded-lg border">
                  Incluir
                </button>
              </div>
              {escolhidos.map((item) => (
                <div key={item.id} className="flex items-center justify-between gap-3 text-sm">
                  <span>{item.nome}</span>
                  <span className="flex items-center gap-3">
                    {formatCurrency(item.preco)}
                    <button type="button" className="text-red-600" onClick={() => setEscolhidos((lista) => lista.filter((p) => p.id !== item.id))}>
                      Remover
                    </button>
                  </span>
                </div>
              ))}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <label className="text-sm">
                  Desconto
                  <select value={descontoTipo} onChange={(e) => setDescontoTipo(e.target.value as DescontoTipo)} className={`${CAMPO} mt-1`}>
                    <option value="percentual">Porcentagem</option>
                    <option value="fixo">Valor fixo (R$)</option>
                  </select>
                </label>
                <label className="text-sm">
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
                <label className="text-sm">Sessões
                  <input value={sessoes} onChange={(e) => setSessoes(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                </label>
                <label className="text-sm">Intervalo
                  <input value={intervalo} onChange={(e) => setIntervalo(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                </label>
                <label className="text-sm">Unidade
                  <select value={unidade} onChange={(e) => setUnidade(e.target.value)} className={`${CAMPO} mt-1`}>
                    <option value="dias">Dias</option>
                    <option value="semanas">Semanas</option>
                    <option value="meses">Meses</option>
                  </select>
                </label>
                <label className="text-sm">Minutos de cada atendimento
                  <input value={tempo} onChange={(e) => setTempo(e.target.value)} className={`${CAMPO} mt-1`} inputMode="numeric" />
                </label>
              </div>

              <label className="text-sm block">Pagamento
                <select value={forma} onChange={(e) => setForma(e.target.value as "POR_CONSULTA" | "TOTAL")} className={`${CAMPO} mt-1`}>
                  <option value="POR_CONSULTA">Dividir pelas sessões</option>
                  <option value="TOTAL">Pagar tudo na primeira sessão</option>
                </select>
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Primeira sessão {formatCurrency(partes[0] || 0)}
                {forma === "POR_CONSULTA" ? ` · cada sessão ${formatCurrency(partes[0] || 0)}` : " · as seguintes ficam sem cobrança"}
              </p>

              <div className="flex flex-wrap gap-2">
                <select value={produtoId} onChange={(e) => setProdutoId(e.target.value)} className={`${CAMPO} max-w-xs`}>
                  <option value="">Produto por sessão</option>
                  {opcoes?.produtos.map((item) => (
                    <option key={item.id} value={item.id}>{item.nome}</option>
                  ))}
                </select>
                <input value={quantidade} onChange={(e) => setQuantidade(e.target.value)} className={`${CAMPO} max-w-[6rem]`} inputMode="decimal" />
                <button type="button" onClick={adicionarProduto} className="px-3 py-2 text-sm rounded-lg border">Incluir produto</button>
              </div>
              {produtos.map((item) => (
                <div key={item.produto_id} className="flex justify-between text-sm">
                  <span>{item.nome} · {item.quantidade} por sessão</span>
                  <button type="button" className="text-red-600" onClick={() => setProdutos((lista) => lista.filter((p) => p.produto_id !== item.produto_id))}>Remover</button>
                </div>
              ))}
              <p className="text-xs text-gray-500">O estoque baixa quando a sessão é finalizada.</p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label className="text-sm">Profissional
                  <select
                    value={professionalId}
                    onChange={(e) => setProfessionalId(e.target.value)}
                    disabled={profissionalFixa}
                    className={`${CAMPO} mt-1`}
                  >
                    <option value="">Selecione</option>
                    {opcoes?.profissionais.map((item) => (
                      <option key={item.id} value={item.id}>{item.nome}</option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">Local
                  <select value={localId} onChange={(e) => setLocalId(e.target.value)} className={`${CAMPO} mt-1`}>
                    <option value="">Selecione</option>
                    {opcoes?.locais.map((item) => (
                      <option key={item.id} value={item.id}>{item.nome}</option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">Primeira sessão
                  <input type="datetime-local" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} className={`${CAMPO} mt-1`} />
                </label>
                <label className="text-sm">Nome do tratamento
                  <input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Protocolo personalizado" className={`${CAMPO} mt-1`} />
                </label>
              </div>
              <p className="text-xs text-gray-500">
                Se o horário estiver ocupado, a sessão vai para o próximo horário livre da profissional. A secretaria pode mudar depois.
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
            disabled={salvando || carregando || escolhidos.length === 0 || !professionalId || !localId || !dataInicio}
            className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            {salvando ? "Criando..." : "Criar sessões na agenda"}
          </button>
        </div>
      </div>
    </div>
  );
}
