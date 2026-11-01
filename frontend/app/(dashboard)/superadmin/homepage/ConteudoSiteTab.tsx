'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ImageUploadMedia as ImageUpload } from '@/components/ImageUploadMedia';

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

function lista<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  const pagina = data as { results?: T[] };
  return pagina?.results ?? [];
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
  return (
    <div className="space-y-3 rounded-xl border p-4">
      <div>
        <Label>Título</Label>
        <Input value={editando.titulo} onChange={(e) => setEditando({ ...editando, titulo: e.target.value })} />
      </div>
      <div>
        <Label>Resumo</Label>
        <textarea className="min-h-16 w-full rounded-md border px-3 py-2 text-sm" value={editando.resumo} onChange={(e) => setEditando({ ...editando, resumo: e.target.value })} />
      </div>
      <div>
        <Label>Texto</Label>
        <textarea className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" value={editando.corpo} onChange={(e) => setEditando({ ...editando, corpo: e.target.value })} />
      </div>
      <div>
        <Label>Destaques (um por linha)</Label>
        <textarea className="min-h-24 w-full rounded-md border px-3 py-2 text-sm" value={editando.itens} onChange={(e) => setEditando({ ...editando, itens: e.target.value })} />
      </div>
      {trocaFoto && (
        <ImageUpload
          label="Foto do cartão"
          description="Esta foto aparece em Nossas soluções. Use uma captura sem nome de cliente. Se apagar, volta a foto atual do site."
          value={editando.imagem || ''}
          onChange={(url) => setEditando({ ...editando, imagem: url })}
          folder="fotos"
        />
      )}
      <div>
        <Label>Mensagem do WhatsApp</Label>
        <Input value={editando.mensagem_whatsapp} onChange={(e) => setEditando({ ...editando, mensagem_whatsapp: e.target.value })} />
      </div>
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
            Blocos home-*. Em home-crm e home-clinica dá para trocar a foto de Nossas soluções. Sem foto nova, permanece a atual.
            Em home-personalizados, cada destaque é Título|texto e o campo Texto é o botão no formato Rótulo|/caminho.
            Em home-planos, cada linha é Título|texto|/caminho|botão. O título da seção de benefícios é home-beneficios; os cartões ficam na aba Benefícios.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {paginas.filter((pagina) => pagina.slug.startsWith('home-')).length === 0 && (
            <p className="text-sm text-slate-500">Os blocos da home aparecem aqui depois da atualização do sistema.</p>
          )}
          {paginas.filter((pagina) => pagina.slug.startsWith('home-')).map((pagina) => (
            <button key={pagina.id} type="button" className="block w-full rounded-lg border px-4 py-3 text-left hover:bg-slate-50" onClick={() => setEditando(pagina)}>
              <span className="font-medium">{pagina.titulo}</span>
              <span className="ml-2 text-sm text-slate-500">/{pagina.slug}</span>
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
          <CardDescription>Formulários de contato e demonstração.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {pedidos.length === 0 && <p className="text-sm text-slate-500">Nenhum pedido ainda.</p>}
          {pedidos.map((pedido) => (
            <div key={pedido.id} className="rounded-lg border px-4 py-3 text-sm">
              <p className="font-medium">{pedido.nome} · {pedido.produto}</p>
              <p className="text-slate-600">{pedido.empresa} · {pedido.whatsapp} · {pedido.origem}</p>
              <p className="mt-1">{pedido.mensagem}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
