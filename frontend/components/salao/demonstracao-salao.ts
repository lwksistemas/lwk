import type { AgendamentoSalao, BloqueioSalao, JornadaDia, ProfissionalSalao, ResumoSalao } from "@/lib/salao-api";

const STATUS = {
  SCHEDULED: "Aguardando",
  CONFIRMED: "Confirmado",
  IN_PROGRESS: "Em atendimento",
  COMPLETED: "Concluído",
} as const;

const SERVICOS = [
  { id: 1, nome: "Corte", minutos: 45 },
  { id: 2, nome: "Escova", minutos: 40 },
  { id: 3, nome: "Coloração", minutos: 90 },
  { id: 4, nome: "Hidratação", minutos: 50 },
  { id: 5, nome: "Manicure", minutos: 40 },
  { id: 6, nome: "Penteado", minutos: 60 },
];

export function profissionaisDemonstracao(): ProfissionalSalao[] {
  return [
    { id: 1, nome: "Marina Costa", telefone: "", especialidade: "Coloração", comissao_tipo: "percentual", comissao_percentual: "40.00", comissao_fixa: "0.00", comissoes: [] },
    { id: 2, nome: "Paulo Henrique", telefone: "", especialidade: "Corte", comissao_tipo: "percentual", comissao_percentual: "35.00", comissao_fixa: "0.00", comissoes: [] },
    { id: 3, nome: "Lúcia Ferreira", telefone: "", especialidade: "Manicure", comissao_tipo: "percentual", comissao_percentual: "30.00", comissao_fixa: "0.00", comissoes: [] },
  ];
}

export function jornadasDemonstracao(): Record<number, JornadaDia[]> {
  const semana = [0, 1, 2, 3, 4, 5].map((dia) => ({
    dia_semana: dia,
    ativo: true,
    hora_entrada: "09:00",
    hora_saida: "19:00",
    intervalo_inicio: "12:00",
    intervalo_fim: "13:00",
  }));
  const domingo = {
    dia_semana: 6,
    ativo: true,
    hora_entrada: "10:00",
    hora_saida: "16:00",
    intervalo_inicio: "12:00",
    intervalo_fim: "13:00",
  };
  return { 1: [...semana, domingo], 2: [...semana, domingo], 3: [...semana, domingo] };
}

export function bloqueiosDemonstracao(hoje = new Date()): BloqueioSalao[] {
  const quarta = dataDaSemana(hoje, 2);
  const iso = dataIso(quarta);
  return [{
    id: 1,
    titulo: "Folga da tarde",
    tipo: "folga",
    data_inicio: iso,
    data_fim: iso,
    horario_inicio: "14:00",
    horario_fim: "19:00",
    profissional: 2,
    profissional_nome: "Paulo Henrique",
  }];
}

export function agendaDemonstracao(hoje = new Date()): AgendamentoSalao[] {
  const inicio = inicioDaSemana(hoje);
  const hojeOffset = (hoje.getDay() + 6) % 7;
  const clientes = ["Ana Beatriz", "Camila Souza", "Juliana Alves", "Fernanda Lima", "Patrícia Nunes", "Renata Dias", "Carla Mendes", "Beatriz Rocha", "Mariana Teixeira", "Aline Costa", "Helena Vieira", "Sônia Prado"];
  const grade: [number, number, number, number, number, string][] = [
    [hojeOffset, 9, 0, 1, 1, "COMPLETED"],
    [hojeOffset, 10, 0, 2, 2, "COMPLETED"],
    [hojeOffset, 11, 0, 3, 5, "IN_PROGRESS"],
    [hojeOffset, 14, 0, 1, 3, "CONFIRMED"],
    [hojeOffset, 15, 30, 2, 4, "SCHEDULED"],
    [hojeOffset, 17, 0, 3, 6, "SCHEDULED"],
  ];
  for (let dia = 0; dia < 7; dia += 1) {
    if (dia === hojeOffset) continue;
    grade.push([dia, 9, 30, 1, 3, "SCHEDULED"]);
    grade.push([dia, 11, 0, 2, 1, "CONFIRMED"]);
    grade.push([dia, 15, 0, 3, 5, "SCHEDULED"]);
    if (dia !== 2) grade.push([dia, 16, 30, 2, 2, "SCHEDULED"]);
  }
  return grade.map((item, indice) => {
    const [dia, hora, minuto, profissional, servicoId, status] = item;
    const servico = SERVICOS[servicoId - 1];
    const pessoa = profissionaisDemonstracao()[profissional - 1];
    const quando = new Date(inicio);
    quando.setDate(inicio.getDate() + dia);
    const comeco = instante(quando, hora, minuto);
    const fimData = new Date(quando);
    fimData.setHours(hora, minuto + servico.minutos, 0, 0);
    return {
      id: 9000 + indice,
      inicio: comeco,
      fim: instante(fimData, fimData.getHours(), fimData.getMinutes()),
      duracao_minutos: servico.minutos,
      status,
      status_label: STATUS[status as keyof typeof STATUS],
      cliente: indice + 1,
      cliente_nome: clientes[indice % clientes.length],
      profissional,
      profissional_nome: pessoa.nome,
      servico: servico.id,
      servico_nome: servico.nome,
      preco: "0.00",
      observacoes: "",
    };
  });
}

export function resumoDemonstracao(hoje = new Date()): ResumoSalao {
  const agenda = agendaDemonstracao(hoje);
  const inicio = inicioDaSemana(hoje);
  const hojeIso = dataIso(hoje);
  const doDia = agenda.filter((item) => item.inicio.slice(0, 10) === hojeIso);
  const serie = Array.from({ length: diasNoMes(hoje) }, (_, indice) => {
    const dia = indice + 1;
    const valor = dia > hoje.getDate() ? 0 : 180 + ((dia * 47) % 320);
    return { dia, valor };
  });
  return {
    painel: "operacao",
    pode_trocar: false,
    hoje: {
      agendamentos: doDia.length,
      em_andamento: doDia.filter((item) => item.status === "IN_PROGRESS").length,
      concluidos: doDia.filter((item) => item.status === "COMPLETED").length,
      faturamento: dinheiro(430),
      ocupacao: 68,
    },
    mes: {
      receita: dinheiro(14050),
      novos_clientes: 12,
      ticket: dinheiro(95),
      clientes_ativos: 86,
    },
    semana: Array.from({ length: 7 }, (_, offset) => {
      const dia = new Date(inicio);
      dia.setDate(inicio.getDate() + offset);
      const iso = dataIso(dia);
      return {
        data: iso,
        rotulo: dia.toLocaleDateString("pt-BR", { weekday: "short" }),
        total: agenda.filter((item) => item.inicio.slice(0, 10) === iso).length,
      };
    }),
    serie_mes: serie,
    servicos: [
      { nome: "Coloração", quantidade: 24, receita: dinheiro(5280) },
      { nome: "Corte", quantidade: 41, receita: dinheiro(3280) },
      { nome: "Escova", quantidade: 36, receita: dinheiro(2520) },
      { nome: "Hidratação", quantidade: 19, receita: dinheiro(1710) },
      { nome: "Manicure", quantidade: 28, receita: dinheiro(1260) },
    ],
    comissoes: [
      { nome: "Marina Costa", quantidade: 18, comissao: dinheiro(1280) },
      { nome: "Paulo Henrique", quantidade: 22, comissao: dinheiro(980) },
      { nome: "Lúcia Ferreira", quantidade: 15, comissao: dinheiro(640) },
    ],
    aniversariantes: [
      { nome: "Helena Vieira", dia: `03/${dois(hoje.getMonth() + 1)}` },
      { nome: "Aline Costa", dia: `15/${dois(hoje.getMonth() + 1)}` },
      { nome: "Sônia Prado", dia: `22/${dois(hoje.getMonth() + 1)}` },
      { nome: "Beatriz Rocha", dia: `28/${dois(hoje.getMonth() + 1)}` },
    ],
    agenda_hoje: doDia.map((item) => ({
      id: item.id,
      hora: item.inicio.slice(11, 16),
      cliente: item.cliente_nome,
      servico: item.servico_nome,
      profissional: item.profissional_nome,
      status: item.status,
      status_label: item.status_label,
    })),
  };
}

function inicioDaSemana(data: Date) {
  const copia = new Date(data);
  copia.setHours(0, 0, 0, 0);
  copia.setDate(copia.getDate() - ((copia.getDay() + 6) % 7));
  return copia;
}

function dataDaSemana(hoje: Date, offset: number) {
  const inicio = inicioDaSemana(hoje);
  inicio.setDate(inicio.getDate() + offset);
  return inicio;
}

function dataIso(data: Date) {
  return `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
}

function instante(data: Date, hora: number, minuto: number) {
  return `${dataIso(data)}T${dois(hora)}:${dois(minuto)}:00`;
}

function diasNoMes(data: Date) {
  return new Date(data.getFullYear(), data.getMonth() + 1, 0).getDate();
}

function dois(valor: number) {
  return String(valor).padStart(2, "0");
}

function dinheiro(valor: number) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
