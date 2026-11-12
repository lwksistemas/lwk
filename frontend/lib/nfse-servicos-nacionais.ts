/**Serviços da lista nacional usados na NFS-e. O texto é o que a nota imprime em Serviço prestado. */

export type ServicoNacionalOpcao = {
  id: string
  lc116: string
  tribNac: string
  nbs: string
  descricao: string
}

export const SERVICOS_NACIONAIS: ServicoNacionalOpcao[] = [
  {
    id: '010101',
    lc116: '01.01',
    tribNac: '01.01.01',
    nbs: '1.1502.10.00',
    descricao: 'Análise e desenvolvimento de sistemas.',
  },
  {
    id: '010201',
    lc116: '01.02',
    tribNac: '01.02.01',
    nbs: '1.1502.10.00',
    descricao: 'Programação.',
  },
  {
    id: '010301',
    lc116: '01.03',
    tribNac: '01.03.01',
    nbs: '1.1506.10.00',
    descricao: 'Processamento, armazenamento ou hospedagem de dados, textos, imagens, vídeos, páginas eletrônicas, aplicativos e sistemas de informação.',
  },
  {
    id: '010401',
    lc116: '01.04',
    tribNac: '01.04.01',
    nbs: '1.1502.10.00',
    descricao: 'Elaboração de programas de computadores, inclusive de jogos eletrônicos.',
  },
  {
    id: '010501',
    lc116: '01.05',
    tribNac: '01.05.01',
    nbs: '1.1103.21.00',
    descricao: 'Licenciamento ou cessão de direito de uso de programas de computação.',
  },
  {
    id: '010601',
    lc116: '01.06',
    tribNac: '01.06.01',
    nbs: '1.1501.10.00',
    descricao: 'Assessoria e consultoria em informática.',
  },
  {
    id: '010701',
    lc116: '01.07',
    tribNac: '01.07.01',
    nbs: '1.1501.30.00',
    descricao: 'Suporte técnico em informática, inclusive instalação, configuração e manutenção de programas de computação e bancos de dados.',
  },
  {
    id: '010801',
    lc116: '01.08',
    tribNac: '01.08.01',
    nbs: '1.1502.30.00',
    descricao: 'Planejamento, confecção, manutenção e atualização de páginas eletrônicas.',
  },
  {
    id: '010901',
    lc116: '01.09',
    tribNac: '01.09.01',
    nbs: '1.1703.10.00',
    descricao: 'Disponibilização, sem cessão definitiva, de conteúdos de áudio, vídeo, imagem e texto por meio da internet.',
  },
  {
    id: '140101',
    lc116: '14.01',
    tribNac: '14.01.01',
    nbs: '',
    descricao: 'Manutenção e conservação de máquinas, aparelhos e equipamentos.',
  },
  {
    id: '170601',
    lc116: '17.06',
    tribNac: '17.06.01',
    nbs: '',
    descricao: 'Propaganda e publicidade, inclusive promoção de vendas.',
  },
]

export function digitosCodigo(valor: string): string {
  return (valor || '').replace(/\D/g, '')
}

export function servicoPeloCodigoNacional(codigo: string): ServicoNacionalOpcao | undefined {
  const digits = digitosCodigo(codigo).slice(0, 6)
  return SERVICOS_NACIONAIS.find((item) => item.id === digits)
}
