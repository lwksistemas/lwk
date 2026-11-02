'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TextoAnimado } from '@/app/components/AnimacaoHome';
import {
  CHAVES_ELEMENTO,
  EFEITOS_TEXTO,
  NOME_ELEMENTO,
  TRANSICOES_IMAGEM,
  type AnimacoesHome,
  type ChaveElemento,
  type DirecaoAnimacao,
  type DispositivoAnimacao,
  type EfeitoTexto,
  type ItemAnimacao,
  type ItemImagem,
  type TransicaoImagem,
  type VelocidadeAnimacao,
  animacoesPadrao,
  duracaoDaVelocidade,
  normalizarAnimacoes,
} from '@/lib/animacoes-home';
import type { HeroData } from './types';

const campo = 'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm';

function atualizarDispositivo(
  atual: AnimacoesHome,
  lado: 'computador' | 'celular',
  mudar: (bloco: DispositivoAnimacao) => DispositivoAnimacao,
) {
  return { ...atual, [lado]: mudar(atual[lado]) };
}

export function AnimacoesTab({
  heroForm,
  setHeroForm,
  onSave,
  saving,
}: {
  heroForm: HeroData;
  setHeroForm: React.Dispatch<React.SetStateAction<HeroData>>;
  onSave: () => void;
  saving: boolean;
}) {
  const animacoes = normalizarAnimacoes(heroForm.animacoes);
  const [lado, setLado] = useState<'computador' | 'celular'>('computador');
  const [reprise, setReprise] = useState(0);
  const ladoEfetivo = animacoes.igual_celular ? 'computador' : lado;
  const dispositivo = animacoes[ladoEfetivo];

  const gravar = (proxima: AnimacoesHome) => setHeroForm((atual) => ({ ...atual, animacoes: proxima }));

  const mudarItem = (chave: ChaveElemento, parcial: Partial<ItemAnimacao>) => {
    gravar(atualizarDispositivo(animacoes, ladoEfetivo, (bloco) => ({
      ...bloco,
      [chave]: { ...bloco[chave], ...parcial },
    })));
  };

  const mudarImagem = (parcial: Partial<ItemImagem>) => {
    gravar(atualizarDispositivo(animacoes, ladoEfetivo, (bloco) => ({
      ...bloco,
      imagens: { ...bloco.imagens, ...parcial },
    })));
  };

  const escolherEfeito = (chave: ChaveElemento, efeito: EfeitoTexto) => {
    mudarItem(chave, { efeito, ativo: efeito !== 'nenhuma' });
  };

  const escolherVelocidade = (chave: ChaveElemento, velocidade: VelocidadeAnimacao) => {
    mudarItem(chave, { velocidade, duracao: duracaoDaVelocidade(velocidade) });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Animações da homepage</CardTitle>
          <CardDescription>
            O visual atual permanece até você escolher um efeito e salvar. O intervalo das telas e os nomes dos botões continuam na aba Banner.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={animacoes.igual_celular}
              onChange={(e) => gravar({ ...animacoes, igual_celular: e.target.checked, celular: e.target.checked ? animacoes.computador : animacoes.celular })}
            />
            No celular, usar as mesmas animações do computador
          </label>
          {!animacoes.igual_celular && (
            <div className="flex gap-2">
              <Button type="button" variant={lado === 'computador' ? 'default' : 'outline'} onClick={() => setLado('computador')}>Computador</Button>
              <Button type="button" variant={lado === 'celular' ? 'default' : 'outline'} onClick={() => setLado('celular')}>Celular</Button>
            </div>
          )}

          <div key={reprise} className="rounded-xl bg-[#071833] p-5 text-white">
            <TextoAnimado item={dispositivo.selo} className="inline-flex rounded-full border border-sky-200/40 px-3 py-1 text-sm text-sky-100">
              {heroForm.selo || 'Software House'}
            </TextoAnimado>
            <div className="mt-3 text-3xl font-extrabold leading-tight">
              <TextoAnimado texto={heroForm.titulo || 'Soluções de software'} item={dispositivo.titulo} className="block" />
              <TextoAnimado texto={heroForm.titulo_destaque || 'para sua empresa.'} item={dispositivo.destaque} className="mt-1 block text-[#3ecbff]" />
            </div>
            <TextoAnimado texto={heroForm.subtitulo || 'Texto de apresentação da homepage.'} item={dispositivo.descricao} className="mt-3 block max-w-xl text-sm text-slate-200" />
            <div className="mt-4 flex flex-wrap gap-3">
              <TextoAnimado item={dispositivo.botao} className="inline-flex">
                <span className="rounded-full bg-[#2f6bff] px-4 py-2 text-sm font-semibold">{heroForm.botao_texto || 'Botão principal'}</span>
              </TextoAnimado>
              <TextoAnimado item={dispositivo.botao2} className="inline-flex">
                <span className="rounded-full border border-white/40 px-4 py-2 text-sm font-semibold">{heroForm.botao_secundario_texto || 'Segundo botão'}</span>
              </TextoAnimado>
            </div>
            <Button type="button" variant="outline" className="mt-4" onClick={() => setReprise((valor) => valor + 1)}>Ver de novo</Button>
          </div>

          {CHAVES_ELEMENTO.map((chave) => (
            <Elemento
              key={chave}
              nome={NOME_ELEMENTO[chave]}
              item={dispositivo[chave]}
              onEfeito={(efeito) => escolherEfeito(chave, efeito)}
              onItem={(parcial) => mudarItem(chave, parcial)}
              onVelocidade={(velocidade) => escolherVelocidade(chave, velocidade)}
            />
          ))}

          <div className="space-y-3 rounded-xl border p-4">
            <p className="font-medium">Imagens do notebook</p>
            <p className="text-sm text-slate-500">
              A troca continua a cada {heroForm.intervalo_carrossel || 5} segundos, configurados na aba Banner. Aqui só muda o efeito da passagem.
            </p>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={dispositivo.imagens.ativo && dispositivo.imagens.transicao !== 'nenhuma'}
                onChange={(e) => mudarImagem({ ativo: e.target.checked, transicao: e.target.checked && dispositivo.imagens.transicao === 'nenhuma' ? 'fade' : dispositivo.imagens.transicao })}
              />
              Ativar transição
            </label>
            <div className="grid gap-3 md:grid-cols-4">
              <div>
                <Label>Efeito</Label>
                <select className={campo} value={dispositivo.imagens.transicao} onChange={(e) => {
                  const transicao = e.target.value as TransicaoImagem;
                  mudarImagem({ transicao, ativo: transicao !== 'nenhuma' });
                }}>
                  {TRANSICOES_IMAGEM.map((opcao) => <option key={opcao.id} value={opcao.id}>{opcao.rotulo}</option>)}
                </select>
              </div>
              <div>
                <Label>Velocidade</Label>
                <select className={campo} value={dispositivo.imagens.velocidade} onChange={(e) => {
                  const velocidade = e.target.value as VelocidadeAnimacao;
                  mudarImagem({ velocidade, duracao: duracaoDaVelocidade(velocidade, true) });
                }}>
                  <option value="lenta">Lenta</option>
                  <option value="normal">Normal</option>
                  <option value="rapida">Rápida</option>
                </select>
              </div>
              <div>
                <Label>Duração (ms)</Label>
                <Input type="number" min={200} max={3000} value={dispositivo.imagens.duracao} onChange={(e) => mudarImagem({ duracao: Number(e.target.value) })} />
              </div>
              <div>
                <Label>Atraso (ms)</Label>
                <Input type="number" min={0} max={3000} value={dispositivo.imagens.atraso} onChange={(e) => mudarImagem({ atraso: Number(e.target.value) })} />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={dispositivo.imagens.celular} onChange={(e) => mudarImagem({ celular: e.target.checked })} />
              No celular
            </label>
          </div>
          {Array.isArray(heroForm.animacoes_historico) && heroForm.animacoes_historico.length > 0 && (
            <div className="space-y-2 rounded-xl border p-4">
              <p className="font-medium">Versões anteriores</p>
              <p className="text-sm text-slate-500">Escolher uma versão só preenche o formulário. Salvar e publicar grava no site.</p>
              {heroForm.animacoes_historico.map((versao) => (
                <div key={versao.salvo_em} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span>{new Date(versao.salvo_em).toLocaleString('pt-BR')}</span>
                  <Button type="button" variant="outline" onClick={() => gravar(normalizarAnimacoes(versao.animacoes))}>Usar esta versão</Button>
                </div>
              ))}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={onSave} disabled={saving}>{saving ? 'Publicando...' : 'Salvar e publicar'}</Button>
            <Button type="button" variant="outline" onClick={() => gravar(animacoesPadrao())}>Restaurar padrão</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Elemento({
  nome,
  item,
  onEfeito,
  onItem,
  onVelocidade,
}: {
  nome: string;
  item: ItemAnimacao;
  onEfeito: (efeito: EfeitoTexto) => void;
  onItem: (parcial: Partial<ItemAnimacao>) => void;
  onVelocidade: (velocidade: VelocidadeAnimacao) => void;
}) {
  return (
    <div className="space-y-3 rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium">{nome}</p>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={item.ativo} onChange={(e) => onItem({ ativo: e.target.checked, efeito: e.target.checked && item.efeito === 'nenhuma' ? 'fade' : item.efeito })} />
          Ativa
        </label>
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <div>
          <Label>Efeito</Label>
          <select className={campo} value={item.efeito} onChange={(e) => onEfeito(e.target.value as EfeitoTexto)}>
            {EFEITOS_TEXTO.map((opcao) => <option key={opcao.id} value={opcao.id}>{opcao.rotulo}</option>)}
          </select>
        </div>
        <div>
          <Label>Velocidade</Label>
          <select className={campo} value={item.velocidade} onChange={(e) => onVelocidade(e.target.value as VelocidadeAnimacao)}>
            <option value="lenta">Lenta</option>
            <option value="normal">Normal</option>
            <option value="rapida">Rápida</option>
          </select>
        </div>
        <div>
          <Label>Duração (ms)</Label>
          <Input type="number" min={200} max={3000} value={item.duracao} onChange={(e) => onItem({ duracao: Number(e.target.value) })} />
        </div>
        <div>
          <Label>Atraso (ms)</Label>
          <Input type="number" min={0} max={3000} value={item.atraso} onChange={(e) => onItem({ atraso: Number(e.target.value) })} />
        </div>
      </div>
      <div className="flex flex-wrap gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={item.repetir} disabled={item.efeito === 'nenhuma'} onChange={(e) => onItem({ repetir: e.target.checked })} />
          Repetir
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={item.celular} onChange={(e) => onItem({ celular: e.target.checked })} />
          No celular
        </label>
        {item.efeito === 'slide' && (
          <label className="flex items-center gap-2">
            Direção
            <select className={campo} value={item.direcao} onChange={(e) => onItem({ direcao: e.target.value as DirecaoAnimacao })}>
              <option value="horizontal">Lateral</option>
              <option value="vertical">Vertical</option>
            </select>
          </label>
        )}
      </div>
      {(nome === 'Botão principal' || nome === 'Segundo botão' || nome.startsWith('Cards')) && item.efeito === 'typing' && (
        <p className="text-sm text-slate-500">Nesse bloco, a digitação revela o elemento inteiro.</p>
      )}
    </div>
  );
}
