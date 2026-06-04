# Design Document — Relatório de Comissões

## Overview

Relatório de Comissões para o módulo Clínica da Beleza. O sistema fornece um endpoint backend que calcula comissões por profissional a partir dos pagamentos com status PAID, e uma interface frontend com filtros, tabela, totais e exportação (CSV/PDF). A arquitetura usa service layer no backend e páginas Next.js dentro do ClinicaBelezaShell no frontend.

## Architecture

O relatório de comissões segue a arquitetura existente do projeto:

- **Backend**: Nova view `RelatorioComissoesView` (APIView) + service layer `comissao_relatorio_service.py` na app `clinica_beleza`
- **Frontend**: Páginas Next.js 14 sob `/loja/[slug]/relatorios/` usando o `ClinicaBelezaShell` via layout compartilhado
- **Isolamento**: `LojaIsolationManager` garante dados exclusivos por tenant
- **Permissões**: `CLINICA_FINANCEIRO` (administrador, recepção, caixa)

```
┌────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)                                 │
│  /loja/[slug]/relatorios/         → Hub de relatórios  │
│  /loja/[slug]/relatorios/comissoes → Relatório         │
│                                                        │
│  Layout: ClinicaBelezaShell (sidebar + topbar)         │
└────────────────────┬───────────────────────────────────┘
                     │ GET /api/clinica-beleza/relatorios/comissoes/
                     │     ?data_inicio=&data_fim=&professional_id=
                     ▼
┌────────────────────────────────────────────────────────┐
│  Backend (Django 5 + DRF)                              │
│  views_relatorios.py → RelatorioComissoesView          │
│  comissao_relatorio_service.py → calcular_comissoes()  │
│                                                        │
│  Payment.objects (LojaIsolationManager)                │
│  → filter(status='PAID', payment_date__date__range)    │
│  → annotate / aggregate por profissional               │
└────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend

#### 1. `comissao_relatorio_service.py`

Service layer responsável pelo cálculo de comissões. Recebe parâmetros de filtro e retorna dados agregados.

```python
from decimal import Decimal
from datetime import date
from typing import Optional
from django.db.models import Sum, Count, F, Value
from django.db.models.functions import Coalesce

from .models import Payment, Professional


def calcular_comissoes(
    *,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    professional_id: Optional[int] = None,
) -> dict:
    """
    Calcula comissões dos profissionais com base nos pagamentos PAID no período.

    Retorna:
        {
            "profissionais": [
                {
                    "professional_id": int,
                    "nome": str,
                    "total_atendimentos": int,
                    "valor_total": Decimal,
                    "comissao_percentual": int,
                    "comissao_total": Decimal,
                }
            ],
            "totais": {
                "total_atendimentos": int,
                "valor_total": Decimal,
                "comissao_total": Decimal,
            }
        }
    """
    qs = Payment.objects.filter(status='PAID')

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    # Agrupar por profissional
    dados = (
        qs
        .values(
            'appointment__professional_id',
            'appointment__professional__nome',
        )
        .annotate(
            total_atendimentos=Count('id'),
            valor_total=Coalesce(Sum('amount'), Value(Decimal('0'))),
            comissao_total=Coalesce(Sum('comissao_valor'), Value(Decimal('0'))),
        )
        .order_by('appointment__professional__nome')
    )

    profissionais = []
    total_atend = 0
    total_valor = Decimal('0')
    total_comissao = Decimal('0')

    for row in dados:
        # Calcular percentual médio de comissão
        valor = row['valor_total'] or Decimal('0')
        comissao = row['comissao_total'] or Decimal('0')
        pct = int((comissao / valor * 100).quantize(Decimal('1'))) if valor > 0 else 0

        profissionais.append({
            'professional_id': row['appointment__professional_id'],
            'nome': row['appointment__professional__nome'],
            'total_atendimentos': row['total_atendimentos'],
            'valor_total': valor,
            'comissao_percentual': pct,
            'comissao_total': comissao,
        })
        total_atend += row['total_atendimentos']
        total_valor += valor
        total_comissao += comissao

    return {
        'profissionais': profissionais,
        'totais': {
            'total_atendimentos': total_atend,
            'valor_total': total_valor,
            'comissao_total': total_comissao,
        },
    }
```

#### 2. `views_relatorios.py`

View APIView com permissões financeiras que recebe os query params e delega ao service.

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date, datetime

from .permissions import CLINICA_FINANCEIRO
from .comissao_relatorio_service import calcular_comissoes


class RelatorioComissoesView(APIView):
    """GET /clinica-beleza/relatorios/comissoes/"""
    permission_classes = CLINICA_FINANCEIRO

    def get(self, request):
        data_inicio = self._parse_date(request.query_params.get('data_inicio'))
        data_fim = self._parse_date(request.query_params.get('data_fim'))
        professional_id = request.query_params.get('professional_id')

        if professional_id:
            try:
                professional_id = int(professional_id)
            except (ValueError, TypeError):
                professional_id = None

        resultado = calcular_comissoes(
            data_inicio=data_inicio,
            data_fim=data_fim,
            professional_id=professional_id,
        )

        # Serializar Decimal para float no response
        return Response({
            'profissionais': [
                {
                    **p,
                    'valor_total': float(p['valor_total']),
                    'comissao_total': float(p['comissao_total']),
                }
                for p in resultado['profissionais']
            ],
            'totais': {
                'total_atendimentos': resultado['totais']['total_atendimentos'],
                'valor_total': float(resultado['totais']['valor_total']),
                'comissao_total': float(resultado['totais']['comissao_total']),
            },
        })

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
```

#### 3. URL Registration (em `urls.py`)

```python
# Adicionar ao urlpatterns de clinica_beleza/urls.py:
path('relatorios/comissoes/', RelatorioComissoesView.as_view(), name='relatorio-comissoes'),
```

### Frontend

#### 4. Layout para Relatórios com ClinicaBelezaShell

Novo arquivo `frontend/app/(dashboard)/loja/[slug]/relatorios/layout.tsx` que envolve as páginas de relatórios no `ClinicaBelezaShell`:

```typescript
'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { ClinicaBelezaShell } from '@/components/clinica-beleza/ClinicaBelezaShell';
import type { LojaInfo } from '@/types/dashboard';

export default function RelatoriosLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, handleLogout, isLoja, ready } = useLojaAuth(slug);
  const [loja, setLoja] = useState<LojaInfo | null>(null);

  const loadLoja = useCallback(async () => {
    try {
      const res = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLoja(res.data as LojaInfo);
      if (typeof window !== 'undefined' && res.data?.id) {
        sessionStorage.setItem('current_loja_id', String(res.data.id));
        if (res.data.slug) sessionStorage.setItem('loja_slug', res.data.slug);
      }
    } catch { setLoja(null); }
  }, [slug]);

  useEffect(() => { if (ready && isLoja) loadLoja(); }, [ready, isLoja, loadLoja]);
  useEffect(() => { if (ready && !isLoja) window.location.href = loginPath; }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja || !loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  return (
    <ClinicaBelezaShell loja={loja} onLogout={handleLogout}>
      {children}
    </ClinicaBelezaShell>
  );
}
```

#### 5. Hub de Relatórios (`/relatorios/page.tsx`)

Reescrita da página existente como um hub simples com cards para cada relatório:

```typescript
'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { BarChart3 } from 'lucide-react';

const RELATORIOS = [
  {
    titulo: 'Comissões dos Profissionais',
    descricao: 'Visualize as comissões por profissional com filtros de período.',
    href: 'comissoes',
    icon: BarChart3,
  },
];

export default function RelatoriosHubPage() {
  const params = useParams();
  const slug = params.slug as string;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Relatórios</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {RELATORIOS.map((rel) => (
          <Link
            key={rel.href}
            href={`/loja/${slug}/relatorios/${rel.href}`}
            className="block p-6 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
          >
            <rel.icon className="w-8 h-8 text-[#8B3D52] mb-3" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{rel.titulo}</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{rel.descricao}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

#### 6. Página de Relatório de Comissões (`/relatorios/comissoes/page.tsx`)

Página interativa com filtros, tabela de dados e exportações:

```typescript
'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';

interface ProfissionalComissao {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  valor_total: number;
  comissao_percentual: number;
  comissao_total: number;
}

interface RelatorioData {
  profissionais: ProfissionalComissao[];
  totais: {
    total_atendimentos: number;
    valor_total: number;
    comissao_total: number;
  };
}

export default function RelatorioComissoesPage() {
  const params = useParams();
  const slug = params.slug as string;

  // Filtros com padrão = mês atual
  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split('T')[0]);
  const [professionalId, setProfessionalId] = useState<string>('');

  const [data, setData] = useState<RelatorioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [professionals, setProfessionals] = useState<{id: number; nome: string}[]>([]);

  // Carregar lista de profissionais para filtro
  useEffect(() => {
    apiClient.get('/clinica-beleza/professionals/')
      .then(res => setProfessionals(res.data.results || res.data))
      .catch(() => {});
  }, []);

  const buscar = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { data_inicio: dataInicio, data_fim: dataFim };
      if (professionalId) params.professional_id = professionalId;
      const res = await apiClient.get('/clinica-beleza/relatorios/comissoes/', { params });
      setData(res.data);
    } catch { setData(null); }
    finally { setLoading(false); }
  }, [dataInicio, dataFim, professionalId]);

  useEffect(() => { buscar(); }, [buscar]);

  const exportarCSV = () => { /* lógica de exportação CSV */ };
  const exportarPDF = () => { window.print(); };

  return (/* JSX com filtros, tabela, totais, botões de exportação */);
}
```

## Interfaces

### API Response — `GET /api/clinica-beleza/relatorios/comissoes/`

**Query Parameters:**

| Parâmetro        | Tipo   | Obrigatório | Descrição                              |
|------------------|--------|-------------|----------------------------------------|
| `data_inicio`    | string | Não         | Data no formato `YYYY-MM-DD`           |
| `data_fim`       | string | Não         | Data no formato `YYYY-MM-DD`           |
| `professional_id`| int    | Não         | ID do profissional para filtrar        |

**Response (200 OK):**

```json
{
  "profissionais": [
    {
      "professional_id": 1,
      "nome": "Dr. João Silva",
      "total_atendimentos": 15,
      "valor_total": 4500.00,
      "comissao_percentual": 30,
      "comissao_total": 1350.00
    }
  ],
  "totais": {
    "total_atendimentos": 15,
    "valor_total": 4500.00,
    "comissao_total": 1350.00
  }
}
```

**Response (200 OK — sem dados):**

```json
{
  "profissionais": [],
  "totais": {
    "total_atendimentos": 0,
    "valor_total": 0.0,
    "comissao_total": 0.0
  }
}
```

### Interface TypeScript (Frontend)

```typescript
interface ProfissionalComissao {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  valor_total: number;
  comissao_percentual: number;
  comissao_total: number;
}

interface RelatorioComissoesResponse {
  profissionais: ProfissionalComissao[];
  totais: {
    total_atendimentos: number;
    valor_total: number;
    comissao_total: number;
  };
}
```

## Data Models

Não há novos models. O relatório utiliza os models existentes:

- **Payment** — fonte principal dos dados (campos: `amount`, `status`, `payment_date`, `comissao_percentual`, `comissao_valor`, FK `appointment`)
- **Appointment** — acesso ao `professional` e `procedure` via FK
- **Professional** — nome do profissional para exibição
- **ProfessionalCommission** — regras de comissão (já utilizadas no cálculo do `comissao_valor` no Payment.save())

### Fluxo de Dados

```
Payment (status=PAID, payment_date in range)
  → appointment → professional (nome)
  → amount (valor pago)
  → comissao_valor (já calculado no save() do Payment)
  → Agrupamento por professional_id
  → Soma: count, sum(amount), sum(comissao_valor)
```

## Error Handling

| Cenário | HTTP | Resposta |
|---------|------|----------|
| Usuário não autenticado | 401 | `{"detail": "Authentication credentials were not provided."}` |
| Sem permissão financeira | 403 | `{"detail": "Acesso permitido apenas para administrador, recepção ou caixa."}` |
| Parâmetro de data inválido | 200 | Ignora o parâmetro (trata como `None`) — não quebra a requisição |
| Nenhum dado no período | 200 | `{"profissionais": [], "totais": {...zeros...}}` |
| Erro interno no cálculo | 500 | `{"error": "Erro ao gerar relatório"}` |

### Frontend Error States

- **Erro de rede/API**: Exibe toast/mensagem "Erro ao carregar dados. Tente novamente."
- **Lista vazia**: Exibe mensagem informativa "Nenhum dado encontrado para o período selecionado."
- **Loading**: Skeleton/spinner enquanto aguarda resposta da API.

## Testing Strategy

- **Unit tests (backend)**: Testar `calcular_comissoes()` com cenários específicos (período sem dados, profissional único, múltiplos profissionais)
- **Property tests (backend)**: Validar propriedades universais do service (filtros, agregação, totais, isolamento)
- **Unit tests (frontend)**: Testar geração de CSV, formatação do nome do arquivo, componentes com dados mockados
- **Property tests (frontend)**: Validar que a função de exportação CSV mantém fidelidade com os dados de entrada
- **Integration tests**: Testar o endpoint completo com autenticação e permissões

## Correctness Properties

*Uma propriedade é uma característica ou comportamento que deve ser verdadeiro em todas as execuções válidas do sistema — essencialmente, uma declaração formal sobre o que o sistema deve fazer. Propriedades servem como ponte entre especificações legíveis e garantias de correção verificáveis por máquina.*

### Property 1: Correção dos filtros do serviço de comissões

*Para qualquer* conjunto de registros Payment e quaisquer parâmetros de filtro (data_inicio, data_fim, professional_id), o serviço `calcular_comissoes` SHALL incluir no resultado apenas pagamentos com status PAID, com `payment_date` dentro do intervalo [data_inicio, data_fim] e vinculados ao professional_id informado (quando fornecido).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Correção da agregação por profissional

*Para qualquer* conjunto de pagamentos PAID retornados pelo filtro, a contagem de atendimentos (`total_atendimentos`) de cada profissional SHALL ser igual ao número de pagamentos daquele profissional, o `valor_total` SHALL ser igual à soma dos `amount` desses pagamentos, e `comissao_total` SHALL ser igual à soma dos `comissao_valor`.

**Validates: Requirements 2.5**

### Property 3: Invariante dos totais gerais

*Para qualquer* resultado retornado pelo serviço, os valores em `totais` (total_atendimentos, valor_total, comissao_total) SHALL ser iguais à soma dos respectivos valores de todos os itens em `profissionais`.

**Validates: Requirements 2.6**

### Property 4: Fidelidade da exportação CSV

*Para qualquer* conjunto de dados de comissões exibidos na tabela, o CSV gerado SHALL conter exatamente uma linha para cada profissional com os mesmos valores, uma linha de cabeçalho com as colunas corretas, e uma linha final de totais cujos valores correspondem aos totais exibidos.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: Formato do nome do arquivo CSV

*Para quaisquer* datas data_inicio e data_fim selecionadas nos filtros, o nome do arquivo CSV SHALL seguir o formato `comissoes_{data_inicio}_{data_fim}.csv` onde as datas estão no formato YYYY-MM-DD.

**Validates: Requirements 4.4**

### Property 6: Isolamento multi-tenant

*Para qualquer* requisição autenticada ao endpoint de relatório de comissões, o serviço SHALL retornar exclusivamente pagamentos pertencentes ao tenant (loja) do usuário autenticado, independentemente da existência de pagamentos em outros tenants.

**Validates: Requirements 6.1**

### Property 7: Estado ativo da navegação para sub-rotas

*Para qualquer* pathname que comece com `/loja/{slug}/relatorios`, a função `isClinicaBelezaNavActive` SHALL retornar `true` para o item de navegação "Relatórios" (path: `relatorios`).

**Validates: Requirements 1.3**
