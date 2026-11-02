'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ImageUploadMedia as ImageUpload } from '@/components/ImageUploadMedia';
import { Modal } from '@/components/ui/Modal';
import { urlWhatsapp } from '@/lib/whatsapp-site';

interface ItemMenu {
  id?: number;
  grupo: 'solucoes' | 'segmentos';
  rotulo: string;
  url: string;
  ordem?: number;
  ativo?: boolean;
}

interface Pagina {
  id?: number;
  slug: string;
  titulo: string;
  resumo: string;
  corpo: string;
  itens: string;
  mensagem_whatsapp: string;
  imagem?: string;
  ativo?: boolean;
}

interface Pedido {
  id: number;
  nome: string;
  empresa: string;
  whatsapp: string;
  produto: string;
  mensagem: string;
  origem: string;
  created_at: string;
}

const NOME_ORIGEM: Record<string, string> = {
  contato: 'Contato',
  demonstracao: 'Demonstração',
  orcamento: 'Orçamento',
};

const NOME_PRODUTO: Record<string, string> = {
  'crm-vendas': 'CRM Vendas',
  'clinicas-estetica': 'Gestão para Clínicas de Estética',
  personalizados: 'Sistemas personalizados',
  outros: 'Outro segmento',
};

function nomeDe(mapa: Record<string, string>, valor: string) {
  return mapa[valor] || valor || '—';
}

function dataPedido(valor: string) {
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return '';
  return data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function lista<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  const pagina = data as { results?: T[] };
  return pagina?.results ?? [];
}

const BLOCOS_HOME = [
  'home-solucoes',
  'home-crm',
  'home-clinica',
  'home-personalizados',
  'home-beneficios',
  'home-planos',
  'home-contato',
] as const;

const NOME_BLOCO: Record<string, string> = {
  'home-solucoes': 'Nossas soluções',
  'home-crm': 'Cartão do CRM',
  'home-clinica': 'Cartão da clínica',
  'home-personalizados': 'Desenvolvimento de sistemas personalizados',
  'home-beneficios': 'Benefícios e diferenciais',
  'home-planos': 'Planos e proposta',
  'home-contato': 'Contato e demonstração',
};

function partes(linha: string) {
  return linha.split('|').map((parte) => parte.trim());
}

function EditorPagina({
  editando,
  setEditando,
  onSave,
}: {
  editando: Pagina;
  setEditando: (pagina: Pagina | null) => void;
  onSave: () => void;
}) {
  const trocaFoto = editando.slug === 'home-crm' || editando.slug === 'home-clinica';
  const daHome = editando.slug.startsWith('home-');
  const cartoes = editando.itens.split('\n').map((linha) => linha.trim()).filter(Boolean).map(partes);
  const atualizarCartao = (indice: number, campo: number, valor: string) => {
    const proximos = cartoes.map((item) => [...item]);
    while (proximos.length <= indice) proximos.push(['', '']);
    proximos[indice][campo] = valor;
    setEditando({ ...editando, itens: proximos.map((item) => item.join('|')).join('\n') });
  };
  return (
    <div className="space-y-3 rounded-xl border p-4">
      <p className="text-sm font-medium text-slate-700">{NOME_BLOCO[editando.slug] || editando.titulo}</p>
      <div>
        <Label>Título que aparece na home</Label>
        <Input value={editando.titulo} onChange={(e) => setEditando({ ...editando, titulo: e.target.value })} />
      </div>
      {editando.slug !== 'home-beneficios' && (
        <div>
          <Label>Mensagem abaixo do título</Label>
          <textarea className="min-h-20 w-full rounded-md border px-3 py-2 text-sm" value={editando.resumo} onChange={(e) => setEditando({ ...editando, resumo: e.target.value })} />
        </div>
      )}
      {editando.slug === 'home-beneficios' && (
        <p className="text-sm text-slate-500">Os quatro cartões desta seção ficam na aba Benefícios.</p>
      )}
      {(editando.slug === 'home-crm' || editando.slug === 'home-clinica') && (
        <div>
          <Label>Tópicos, um por linha</Label>
          <textarea className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" value={editando.itens} onChange={(e) => setEditando({ ...editando, itens: e.target.value })} />
        </div>
      )}
      {editando.slug === 'home-personalizados' && cartoes.map((cartao, indice) => (
        <div key={indice} className="grid gap-2 md:grid-cols-2">
          <div>
            <Label>Cartão {indice + 1} — título</Label>
            <Input value={cartao[0] || ''} onChange={(e) => atualizarCartao(indice, 0, e.target.value)} />
          </div>
          <div>
            <Label>Cartão {indice + 1} — mensagem</Label>
            <Input value={cartao[1] || ''} onChange={(e) => atualizarCartao(indice, 1, e.target.value)} />
          </div>
        </div>
      ))}
      {editando.slug === 'home-planos' && cartoes.map((cartao, indice) => (
        <div key={indice} className="grid gap-2 md:grid-cols-2">
          <div>
            <Label>Plano {indice + 1} — título</Label>
            <Input value={cartao[0] || ''} onChange={(e) => atualizarCartao(indice, 0, e.target.value)} />
          </div>
          <div>
            <Label>Plano {indice + 1} — mensagem</Label>
            <Input value={cartao[1] || ''} onChange={(e) => atualizarCartao(indice, 1, e.target.value)} />
          </div>
        </div>
      ))}
      {!daHome && (
        <>
          <div>
            <Label>Texto</Label>
            <textarea className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" value={editando.corpo} onChange={(e) => setEditando({ ...editando, corpo: e.target.value })} />
          </div>
          <div>
            <Label>Destaques (um por linha)</Label>
            <textarea className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" value={editando.itens} onChange={(e) => setEditando({ ...editando, itens: e.target.value })} />
          </div>
        </>
      )}
      {trocaFoto && (
        <ImageUpload
          label="Foto do cartão"
          description="Esta foto aparece em Nossas soluções. Use uma captura sem nome de cliente. Se apagar, volta a foto atual do site."
          value={editando.imagem || ''}
          onChange={(url) => setEditando({ ...editando, imagem: url })}
          folder="fotos"
        />
      )}
      {!daHome && (
        <div>
          <Label>Mensagem do WhatsApp</Label>
          <Input value={editando.mensagem_whatsapp} onChange={(e) => setEditando({ ...editando, mensagem_whatsapp: e.target.value })} />
        </div>
      )}
      <div className="flex gap-2">
        <Button type="button" onClick={onSave}>Salvar página</Button>
        <Button type="button" variant="outline" onClick={() => setEditando(null)}>Fechar</Button>
      </div>
    </div>
  );
}

export function ConteudoSiteTab() {
  const [menu, setMenu] = useState<ItemMenu[]>([]);
  const [paginas, setPaginas] = useState<Pagina[]>([]);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [editando, setEditando] = useState<Pagina | null>(null);
  const [pedidoAberto, setPedidoAberto] = useState<Pedido | null>(null);
  const [aviso, setAviso] = useState('');

  const carregar = useCallback(async () => {
    const [menuRes, paginasRes, pedidosRes] = await Promise.all([
      apiClient.get('/superadmin/homepage/menu/'),
      apiClient.get('/superadmin/homepage/paginas/'),
      apiClient.get('/superadmin/homepage/solicitacoes/'),
    ]);
    setMenu(lista<ItemMenu>(menuRes.data));
    setPaginas(lista<Pagina>(paginasRes.data));
    setPedidos(lista<Pedido>(pedidosRes.data));
  }, []);

  useEffect(() => {
    carregar().catch(() => setAviso('Não foi possível carregar o menu e as páginas.'));
  }, [carregar]);

  async function salvarMenu(item: ItemMenu) {
    if (item.id) await apiClient.patch(`/superadmin/homepage/menu/${item.id}/`, item);
    else await apiClient.post('/superadmin/homepage/menu/', { ...item, ativo: true, ordem: menu.length + 1 });
    setAviso('Menu salvo.');
    carregar();
  }

  async function salvarPagina() {
    if (!editando?.id) return;
    await apiClient.patch(`/superadmin/homepage/paginas/${editando.id}/`, editando);
    setAviso('Página salva.');
    setEditando(null);
    carregar();
  }

  return (
    <div className="space-y-6">
      {aviso && <p className="rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-800">{aviso}</p>}
      <Card>
        <CardHeader>
          <CardTitle>Menu Soluções e Segmentos</CardTitle>
          <CardDescription>O menu Soluções usa o grupo Soluções. Segmentos no topo é um link único para /segmentos; os itens do grupo Segmentos não aparecem na home.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {menu.map((item) => (
            <div key={item.id} className="grid gap-2 md:grid-cols-[140px_1fr_1fr_auto]">
              <Input value={item.grupo === 'solucoes' ? 'Soluções' : 'Segmentos'} readOnly />
              <Input value={item.rotulo} onChange={(e) => setMenu((listaAtual) => listaAtual.map((atual) => atual.id === item.id ? { ...atual, rotulo: e.target.value } : atual))} />
              <Input value={item.url} onChange={(e) => setMenu((listaAtual) => listaAtual.map((atual) => atual.id === item.id ? { ...atual, url: e.target.value } : atual))} />
              <Button type="button" variant="outline" onClick={() => salvarMenu(item)}>Salvar</Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Textos da página inicial</CardTitle>
          <CardDescription>
            Cada item é uma faixa da home. Em Desenvolvimento de sistemas personalizados, o título é a frase grande e Mensagem abaixo do título é o parágrafo. Os três cartões ficam logo em seguida.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {paginas.filter((pagina) => pagina.slug.startsWith('home-')).length === 0 && (
            <p className="text-sm text-slate-500">Os blocos da home aparecem aqui depois da atualização do sistema.</p>
          )}
          {BLOCOS_HOME.map((slug) => paginas.find((pagina) => pagina.slug === slug)).filter((pagina): pagina is Pagina => Boolean(pagina)).map((pagina) => (
            <button key={pagina.id} type="button" className="block w-full rounded-lg border px-4 py-3 text-left hover:bg-slate-50" onClick={() => setEditando(pagina)}>
              <span className="font-medium">{NOME_BLOCO[pagina.slug]}</span>
              <span className="mt-1 block text-sm text-slate-500">{pagina.titulo}</span>
            </button>
          ))}
          {editando?.slug.startsWith('home-') && (
            <EditorPagina editando={editando} setEditando={setEditando} onSave={salvarPagina} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Páginas dos produtos</CardTitle>
          <CardDescription>Texto das páginas de CRM, clínica, personalizados, planos, contato e demonstração. Não é o texto da home.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {paginas.filter((pagina) => !pagina.slug.startsWith('home-')).map((pagina) => (
            <button key={pagina.id} type="button" className="block w-full rounded-lg border px-4 py-3 text-left hover:bg-slate-50" onClick={() => setEditando(pagina)}>
              <span className="font-medium">{pagina.titulo}</span>
              <span className="ml-2 text-sm text-slate-500">/{pagina.slug}</span>
            </button>
          ))}
          {editando && !editando.slug.startsWith('home-') && (
            <EditorPagina editando={editando} setEditando={setEditando} onSave={salvarPagina} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pedidos do site</CardTitle>
          <CardDescription>Cada pedido fica em uma linha. A mensagem abre no botão Ver mensagem.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {pedidos.length === 0 && <p className="text-sm text-slate-500">Nenhum pedido ainda.</p>}
          {pedidos.map((pedido) => (
            <div key={pedido.id} className="flex flex-col gap-3 rounded-lg border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="font-medium text-slate-900">{pedido.nome}</p>
                <p className="text-sm text-slate-600">
                  {nomeDe(NOME_PRODUTO, pedido.produto)} · {nomeDe(NOME_ORIGEM, pedido.origem)}
                  {pedido.empresa ? ` · ${pedido.empresa}` : ''}
                </p>
                <p className="text-sm text-slate-500">{pedido.whatsapp} · {dataPedido(pedido.created_at)}</p>
              </div>
              <Button type="button" variant="outline" className="shrink-0" onClick={() => setPedidoAberto(pedido)}>
                Ver mensagem
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Modal isOpen={!!pedidoAberto} onClose={() => setPedidoAberto(null)} maxWidth="2xl">
        {pedidoAberto && (
          <div className="space-y-4 p-6">
            <h3 className="text-lg font-semibold text-slate-900">Mensagem de {pedidoAberto.nome}</h3>
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Empresa</dt>
                <dd>{pedidoAberto.empresa || '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">WhatsApp</dt>
                <dd>{pedidoAberto.whatsapp}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Produto</dt>
                <dd>{nomeDe(NOME_PRODUTO, pedidoAberto.produto)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Origem</dt>
                <dd>{nomeDe(NOME_ORIGEM, pedidoAberto.origem)} · {dataPedido(pedidoAberto.created_at)}</dd>
              </div>
            </dl>
            <div className="max-h-[50vh] overflow-y-auto whitespace-pre-wrap break-words rounded-lg border bg-slate-50 p-4 text-sm leading-relaxed text-slate-800">
              {pedidoAberto.mensagem}
            </div>
            <div className="flex flex-wrap gap-2">
              {urlWhatsapp(pedidoAberto.whatsapp, 'Olá! Recebi seu pedido pelo site da LWK Sistemas.') && (
                <Button asChild>
                  <a
                    href={urlWhatsapp(pedidoAberto.whatsapp, 'Olá! Recebi seu pedido pelo site da LWK Sistemas.')!}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Responder no WhatsApp
                  </a>
                </Button>
              )}
              <Button type="button" variant="outline" onClick={() => setPedidoAberto(null)}>Fechar</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
