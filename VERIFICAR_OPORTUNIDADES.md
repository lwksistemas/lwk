# Como Verificar Oportunidades no Banco

## 1. Verificar Total de Oportunidades
```bash
heroku run "python backend/manage.py shell -c \"from crm_vendas.models import Oportunidade; print(f'Total: {Oportunidade.objects.count()}')\"" --app lwksistemas
```

## 2. Listar Últimas 5 Oportunidades Criadas
```bash
heroku run "python backend/manage.py shell -c \"from crm_vendas.models import Oportunidade; for o in Oportunidade.objects.order_by('-created_at')[:5]: print(f'{o.id} - {o.titulo} - {o.etapa} - {o.created_at}')\"" --app lwksistemas
```

## 3. Verificar Oportunidades de uma Loja Específica
```bash
heroku run "python backend/manage.py shell -c \"from crm_vendas.models import Oportunidade; from stores.models import Loja; loja = Loja.objects.get(cnpj='41449198000172'); from django_tenants.utils import schema_context; from django.db import connection; connection.set_tenant(loja); print(f'Oportunidades da loja {loja.nome}: {Oportunidade.objects.count()}'); for o in Oportunidade.objects.all()[:10]: print(f'  {o.id} - {o.titulo} - {o.etapa}')\"" --app lwksistemas
```

## 4. Verificar Logs em Tempo Real
```bash
heroku logs --tail --app lwksistemas | grep -i "oportunidade"
```

## O Que Fazer Se Não Aparecer

1. **Abra o Console do Navegador** (F12)
2. **Vá para a aba Network**
3. **Crie uma nova oportunidade**
4. **Procure pela requisição POST** para `/crm-vendas/oportunidades/`
5. **Verifique:**
   - Status Code (deve ser 201)
   - Response (deve retornar os dados da oportunidade criada)
   - Se houver erro, copie a mensagem

## Possíveis Causas

1. **Cache do Navegador** - Limpar cache
2. **Erro no Backend** - Verificar logs
3. **Problema de Permissão** - Verificar se usuário tem permissão
4. **Filtro de Vendedor** - Se for vendedor, só vê suas próprias oportunidades
