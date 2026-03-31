# 🧪 INSTRUÇÕES DE TESTE - REFATORAÇÃO
**Data:** 31 de Março de 2026  
**Versão:** 1.0  
**Status:** Pronto para Testes

---

## 🎯 OBJETIVO

Testar todas as mudanças da refatoração para garantir que:
1. Nenhuma funcionalidade foi quebrada
2. Novos componentes funcionam corretamente
3. Performance não foi afetada
4. Compatibilidade está mantida

---

## 📋 CHECKLIST DE TESTES

### Fase 1: API Client Consolidado ✅

#### Teste 1: API Client Funciona
```bash
# Iniciar frontend
cd frontend
npm run dev
```

**Passos:**
1. Abrir aplicação no navegador
2. Fazer login em qualquer loja
3. Navegar por diferentes páginas
4. Verificar que dados carregam normalmente

**Resultado Esperado:**
- ✅ Todas as páginas carregam
- ✅ Dados aparecem corretamente
- ✅ Sem erros no console

---

#### Teste 2: Alias clinicaApiClient Funciona
```typescript
// Verificar que código antigo ainda funciona
import { clinicaApiClient } from '@/lib/api-client';
// Deve funcionar normalmente
```

**Resultado Esperado:**
- ✅ Import funciona
- ✅ Deprecation warning aparece no console (desenvolvimento)
- ✅ Funcionalidade mantida

---

### Fase 2: Modais Migrados 🔄

#### Teste 3: ModalClientes (Cabeleireiro)
```bash
# Acessar dashboard do cabeleireiro
http://localhost:3000/loja/[slug-cabeleireiro]/dashboard
```

**Passos:**
1. Clicar em "Gerenciar Clientes"
2. Verificar que modal abre
3. Clicar em "+ Novo Cliente"
4. Preencher formulário
5. Salvar
6. Verificar que cliente aparece na lista
7. Editar cliente
8. Excluir cliente

**Resultado Esperado:**
- ✅ Modal abre corretamente
- ✅ Lista de clientes carrega
- ✅ Formulário funciona
- ✅ Validações funcionam (campos obrigatórios)
- ✅ Salvar funciona
- ✅ Editar funciona
- ✅ Excluir funciona
- ✅ Loading states aparecem
- ✅ Mensagens de erro aparecem quando necessário

---

#### Teste 4: ModalClientes (Clínica)
```bash
# Acessar dashboard da clínica
http://localhost:3000/loja/[slug-clinica]/dashboard
```

**Passos:** (mesmos do Teste 3)

**Resultado Esperado:** (mesmos do Teste 3)

**Campos Adicionais a Testar:**
- ✅ Campo Estado (select) funciona
- ✅ Campo Endereço funciona
- ✅ Campo Cidade funciona

---

### Fase 2: Management Commands 🔄

#### Teste 5: check_schemas
```bash
cd backend

# Teste básico
python manage.py check_schemas

# Teste com verbose
python manage.py check_schemas --verbose

# Teste com check-leads
python manage.py check_schemas --check-leads

# Teste com limit
python manage.py check_schemas --limit 10

# Teste help
python manage.py check_schemas --help
```

**Resultado Esperado:**
- ✅ Comando executa sem erros
- ✅ Lista schemas corretamente
- ✅ Verbose mostra detalhes
- ✅ Check-leads funciona
- ✅ Limit funciona
- ✅ Help mostra informações corretas
- ✅ Output está formatado e colorido

---

#### Teste 6: cleanup_orfaos
```bash
cd backend

# Teste dry-run (seguro)
python manage.py cleanup_orfaos --dry-run

# Teste apenas schemas
python manage.py cleanup_orfaos --schemas --dry-run

# Teste apenas lojas
python manage.py cleanup_orfaos --lojas --dry-run

# Teste apenas usuários
python manage.py cleanup_orfaos --usuarios --dry-run

# Teste help
python manage.py cleanup_orfaos --help
```

**Resultado Esperado:**
- ✅ Dry-run não faz alterações
- ✅ Mostra o que seria removido
- ✅ Opções seletivas funcionam
- ✅ Help mostra informações corretas
- ✅ Output está formatado e colorido

**⚠️ ATENÇÃO:** NÃO executar sem --dry-run em produção sem backup!

---

## 🔍 TESTES DE REGRESSÃO

### Teste 7: Funcionalidades Existentes

**Áreas a Testar:**
1. Login/Logout
2. Dashboard
3. Agendamentos
4. Financeiro
5. Relatórios
6. Configurações

**Para Cada Área:**
- [ ] Página carrega
- [ ] Dados aparecem
- [ ] Ações funcionam (criar, editar, excluir)
- [ ] Sem erros no console
- [ ] Performance normal

---

## 📊 TESTES DE PERFORMANCE

### Teste 8: Tempo de Carregamento

**Antes da Refatoração:**
```
Tempo de carregamento médio: [anotar]
```

**Depois da Refatoração:**
```
Tempo de carregamento médio: [anotar]
```

**Resultado Esperado:**
- ✅ Tempo igual ou melhor
- ✅ Sem degradação de performance

---

### Teste 9: Tamanho do Bundle

```bash
cd frontend
npm run build

# Verificar tamanho
ls -lh .next/static/chunks/
```

**Resultado Esperado:**
- ✅ Tamanho similar ou menor
- ✅ Sem aumento significativo

---

## 🐛 TESTES DE ERRO

### Teste 10: Tratamento de Erros

**Cenários a Testar:**
1. API offline
2. Dados inválidos
3. Permissões negadas
4. Timeout
5. Erro 500

**Para Cada Cenário:**
- [ ] Mensagem de erro aparece
- [ ] Aplicação não quebra
- [ ] Usuário pode tentar novamente
- [ ] Log de erro é gerado

---

## 🔐 TESTES DE SEGURANÇA

### Teste 11: Isolamento de Dados

**Cenários:**
1. Usuário da Loja A não vê dados da Loja B
2. Usuário sem permissão não acessa recursos
3. Tokens expirados são tratados

**Resultado Esperado:**
- ✅ Isolamento mantido
- ✅ Permissões respeitadas
- ✅ Segurança não comprometida

---

## 📱 TESTES DE RESPONSIVIDADE

### Teste 12: Dispositivos Móveis

**Dispositivos a Testar:**
- [ ] iPhone (Safari)
- [ ] Android (Chrome)
- [ ] Tablet
- [ ] Desktop

**Para Cada Dispositivo:**
- [ ] Layout responsivo
- [ ] Modais funcionam
- [ ] Formulários funcionam
- [ ] Navegação funciona

---

## 🌐 TESTES DE NAVEGADORES

### Teste 13: Compatibilidade

**Navegadores a Testar:**
- [ ] Chrome (última versão)
- [ ] Firefox (última versão)
- [ ] Safari (última versão)
- [ ] Edge (última versão)

**Para Cada Navegador:**
- [ ] Aplicação carrega
- [ ] Funcionalidades funcionam
- [ ] Sem erros no console

---

## 📝 RELATÓRIO DE TESTES

### Template de Relatório

```markdown
# Relatório de Testes - Refatoração
**Data:** [data]
**Testador:** [nome]
**Ambiente:** [desenvolvimento/staging/produção]

## Resumo
- Total de Testes: [número]
- Testes Passados: [número]
- Testes Falhados: [número]
- Taxa de Sucesso: [porcentagem]

## Testes Detalhados

### Teste 1: API Client
- Status: ✅ Passou / ❌ Falhou
- Observações: [observações]

### Teste 2: ModalClientes (Cabeleireiro)
- Status: ✅ Passou / ❌ Falhou
- Observações: [observações]

[... continuar para todos os testes]

## Problemas Encontrados
1. [Descrição do problema]
   - Severidade: Alta/Média/Baixa
   - Passos para reproduzir: [passos]
   - Solução proposta: [solução]

## Recomendações
- [Recomendação 1]
- [Recomendação 2]

## Conclusão
[Conclusão geral dos testes]
```

---

## 🚨 PROBLEMAS COMUNS E SOLUÇÕES

### Problema 1: Modal Não Abre
**Sintoma:** Clicar no botão não abre o modal

**Solução:**
```typescript
// Verificar import
import { GenericCrudModal } from '@/components/shared/GenericCrudModal';

// Verificar props
<GenericCrudModal
  title="Clientes"
  endpoint="/cabeleireiro/clientes/"
  fields={clienteFields}
  loja={loja}
  onClose={handleClose}
/>
```

---

### Problema 2: Dados Não Carregam
**Sintoma:** Lista vazia mesmo com dados no banco

**Solução:**
```typescript
// Verificar endpoint
endpoint="/cabeleireiro/clientes/" // Correto
endpoint="cabeleireiro/clientes/" // Errado (falta /)

// Verificar console
console.log('Response:', response);
```

---

### Problema 3: Command Não Encontrado
**Sintoma:** `python manage.py <command>` não funciona

**Solução:**
```bash
# Verificar estrutura
ls -la backend/management/commands/

# Verificar __init__.py
cat backend/management/commands/__init__.py

# Verificar nome do arquivo
# Deve ser: backend/management/commands/<categoria>/<nome>.py
```

---

## ✅ CRITÉRIOS DE ACEITAÇÃO

### Para Aprovar a Refatoração

**Obrigatório:**
- [ ] Todos os testes críticos passam
- [ ] Nenhuma funcionalidade quebrada
- [ ] Performance mantida ou melhorada
- [ ] Sem erros no console
- [ ] Compatibilidade mantida

**Desejável:**
- [ ] Testes de regressão passam
- [ ] Testes de performance passam
- [ ] Testes de segurança passam
- [ ] Testes de responsividade passam
- [ ] Testes de navegadores passam

---

## 📅 CRONOGRAMA DE TESTES

### Fase 1: Testes Básicos (1 dia)
- Testes 1-6 (API Client e Modais)
- Testes 7 (Regressão básica)

### Fase 2: Testes Avançados (1 dia)
- Testes 8-9 (Performance)
- Testes 10-11 (Erro e Segurança)

### Fase 3: Testes Finais (1 dia)
- Testes 12-13 (Responsividade e Navegadores)
- Relatório final

---

## 🎯 CONCLUSÃO

Após completar todos os testes:

**Se Todos Passarem:** ✅
- Aprovar refatoração
- Deploy em staging
- Monitorar por 1 semana
- Deploy em produção

**Se Alguns Falharem:** ⚠️
- Documentar problemas
- Corrigir issues
- Re-testar
- Repetir processo

**Se Muitos Falharem:** ❌
- Reverter mudanças
- Analisar problemas
- Replanejar refatoração
- Tentar novamente

---

**Documento criado por:** Kiro AI  
**Data:** 31 de Março de 2026  
**Versão:** 1.0  
**Status:** Pronto para Uso
