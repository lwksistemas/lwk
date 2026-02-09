# ✅ Checklist de Deploy - Sistema de Monitoramento

## 📋 Pré-Deploy

### Backend

- [ ] **Variáveis de Ambiente Configuradas**
  ```bash
  # Email (obrigatório)
  EMAIL_HOST=smtp.gmail.com
  EMAIL_PORT=587
  EMAIL_USE_TLS=True
  EMAIL_HOST_USER=seu-email@gmail.com
  EMAIL_HOST_PASSWORD=sua-senha-app
  DEFAULT_FROM_EMAIL=Sistema <noreply@lwksistemas.com.br>
  
  # Notificações de Segurança
  SECURITY_NOTIFICATION_EMAILS=admin@lwksistemas.com.br,seguranca@lwksistemas.com.br
  SITE_URL=https://lwksistemas.com.br
  
  # Redis (produção)
  REDIS_URL=redis://localhost:6379/1
  
  # Django-Q
  DJANGO_Q_WORKERS=4
  ```

- [ ] **Migrations Executadas**
  ```bash
  python manage.py migrate
  ```

- [ ] **Schedules Configurados**
  ```bash
  python manage.py setup_security_schedules
  ```

- [ ] **Django-Q Iniciado**
  ```bash
  # Supervisor ou systemd
  python manage.py qcluster
  ```

- [ ] **Redis Instalado e Rodando**
  ```bash
  redis-cli ping
  # Deve retornar: PONG
  ```

- [ ] **Testes Executados**
  ```bash
  python manage.py check
  # Deve retornar: 0 issues
  ```

### Frontend

- [ ] **Build de Produção**
  ```bash
  npm run build
  # ou
  yarn build
  ```

- [ ] **Variáveis de Ambiente**
  ```bash
  NEXT_PUBLIC_API_URL=https://lwksistemas.com.br/api
  ```

- [ ] **Testes de Compilação**
  ```bash
  npm run type-check
  # Deve retornar: 0 errors
  ```

### Infraestrutura

- [ ] **Banco de Dados**
  - [ ] Backup realizado
  - [ ] Espaço em disco suficiente (>10GB)
  - [ ] Índices criados automaticamente pelas migrations

- [ ] **Servidor**
  - [ ] CPU: Mínimo 2 cores
  - [ ] RAM: Mínimo 4GB
  - [ ] Disco: Mínimo 20GB livre

- [ ] **Firewall**
  - [ ] Porta 6379 (Redis) acessível apenas internamente
  - [ ] Porta 80/443 (HTTP/HTTPS) aberta

## 🚀 Deploy

### 1. Backend

```bash
# 1. Atualizar código
git pull origin main

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar migrations
python manage.py migrate

# 5. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 6. Configurar schedules
python manage.py setup_security_schedules

# 7. Reiniciar serviços
sudo systemctl restart gunicorn
sudo systemctl restart django-q
sudo systemctl restart nginx
```

### 2. Frontend

```bash
# 1. Atualizar código
git pull origin main

# 2. Instalar dependências
npm install

# 3. Build de produção
npm run build

# 4. Reiniciar serviço
sudo systemctl restart next
# ou
pm2 restart next-app
```

### 3. Redis

```bash
# Verificar se está rodando
sudo systemctl status redis

# Se não estiver, iniciar
sudo systemctl start redis
sudo systemctl enable redis
```

## ✅ Pós-Deploy

### Validação Backend

- [ ] **API Acessível**
  ```bash
  curl https://lwksistemas.com.br/api/superadmin/violacoes-seguranca/
  # Deve retornar 401 (não autenticado) ou 200 (se autenticado)
  ```

- [ ] **Django-Q Rodando**
  ```bash
  # Verificar logs
  tail -f logs/django-q.log
  
  # Deve mostrar:
  # - Schedules configurados
  # - Tasks sendo executadas
  ```

- [ ] **Schedules Ativos**
  ```bash
  python manage.py shell
  >>> from django_q.models import Schedule
  >>> Schedule.objects.count()
  4  # Deve retornar 4
  ```

- [ ] **Detector Funcionando**
  ```bash
  python manage.py detect_security_violations
  # Deve executar sem erros
  ```

- [ ] **Cache Funcionando**
  ```bash
  python manage.py shell
  >>> from django.core.cache import cache
  >>> cache.set('test', 'value', 60)
  >>> cache.get('test')
  'value'  # Deve retornar o valor
  ```

- [ ] **Email Funcionando**
  ```bash
  python manage.py shell
  >>> from django.core.mail import send_mail
  >>> send_mail('Teste', 'Mensagem', 'noreply@lwksistemas.com.br', ['admin@lwksistemas.com.br'])
  1  # Deve retornar 1 (email enviado)
  ```

### Validação Frontend

- [ ] **Site Acessível**
  - Abrir: https://lwksistemas.com.br/superadmin/login
  - Deve carregar página de login

- [ ] **Login Funcionando**
  - Fazer login com credenciais de SuperAdmin
  - Deve redirecionar para dashboard

- [ ] **Dashboards Carregando**
  - [ ] Dashboard Principal
  - [ ] Dashboard de Alertas
  - [ ] Dashboard de Auditoria
  - [ ] Busca de Logs

- [ ] **Notificações Funcionando**
  - [ ] Badge aparece no header
  - [ ] Dropdown abre ao clicar
  - [ ] Toast aparece para violações críticas
  - [ ] Notificações nativas funcionam (se permitidas)

### Testes End-to-End

- [ ] **Fluxo Completo de Violação**
  1. Criar violação de teste (via detector manual)
  2. Verificar que aparece no dashboard
  3. Verificar que email foi enviado
  4. Verificar que notificação aparece no frontend
  5. Resolver violação
  6. Verificar que status foi atualizado

- [ ] **Fluxo de Busca de Logs**
  1. Acessar busca de logs
  2. Aplicar filtros
  3. Ver detalhes de log
  4. Ver contexto temporal
  5. Exportar CSV
  6. Verificar arquivo baixado

- [ ] **Fluxo de Auditoria**
  1. Acessar dashboard de auditoria
  2. Selecionar período
  3. Verificar gráficos carregam
  4. Verificar rankings aparecem
  5. Verificar cache funciona (segunda carga mais rápida)

### Performance

- [ ] **Tempo de Resposta**
  - [ ] Dashboard principal: < 2s
  - [ ] Dashboard de alertas: < 2s
  - [ ] Dashboard de auditoria (cache HIT): < 500ms
  - [ ] Busca de logs: < 3s

- [ ] **Cache**
  - [ ] Primeira requisição: ~800ms
  - [ ] Segunda requisição (cache HIT): ~50ms
  - [ ] TTL de 5 minutos funcionando

- [ ] **Banco de Dados**
  - [ ] Queries < 100ms (com índices)
  - [ ] Sem N+1 queries
  - [ ] Conexões não esgotadas

### Monitoramento

- [ ] **Logs**
  ```bash
  # Backend
  tail -f logs/django.log
  
  # Django-Q
  tail -f logs/django-q.log
  
  # Nginx
  tail -f /var/log/nginx/access.log
  tail -f /var/log/nginx/error.log
  ```

- [ ] **Métricas**
  - [ ] CPU < 70%
  - [ ] RAM < 80%
  - [ ] Disco < 80%
  - [ ] Redis memória < 1GB

- [ ] **Alertas**
  - [ ] Email de teste recebido
  - [ ] Notificações frontend funcionando
  - [ ] Logs sendo registrados

## 🔒 Segurança

- [ ] **HTTPS Configurado**
  - [ ] Certificado SSL válido
  - [ ] Redirecionamento HTTP → HTTPS
  - [ ] HSTS habilitado

- [ ] **Firewall**
  - [ ] Apenas portas necessárias abertas
  - [ ] Redis acessível apenas internamente
  - [ ] SSH com chave pública

- [ ] **Permissões**
  - [ ] Arquivos com permissões corretas (644)
  - [ ] Diretórios com permissões corretas (755)
  - [ ] Logs com permissões corretas (666)

- [ ] **Secrets**
  - [ ] Variáveis de ambiente não commitadas
  - [ ] SECRET_KEY único e seguro
  - [ ] Senhas de banco fortes

## 📊 Monitoramento Contínuo

### Diário

- [ ] Verificar logs de erro
- [ ] Verificar violações críticas
- [ ] Verificar uso de recursos (CPU, RAM, Disco)

### Semanal

- [ ] Revisar estatísticas de auditoria
- [ ] Verificar taxa de sucesso de emails
- [ ] Verificar taxa de cache HIT
- [ ] Revisar logs de Django-Q

### Mensal

- [ ] Executar limpeza de logs antigos
- [ ] Verificar espaço em disco
- [ ] Revisar configurações de segurança
- [ ] Atualizar dependências

## 🆘 Rollback

Se algo der errado:

```bash
# 1. Reverter código
git revert HEAD
# ou
git checkout <commit-anterior>

# 2. Reverter migrations (se necessário)
python manage.py migrate superadmin <migration-anterior>

# 3. Reiniciar serviços
sudo systemctl restart gunicorn
sudo systemctl restart django-q
sudo systemctl restart nginx

# 4. Limpar cache
python manage.py clear_stats_cache
redis-cli FLUSHDB

# 5. Verificar logs
tail -f logs/django.log
```

## 📞 Contatos de Emergência

- **Desenvolvedor**: dev@lwksistemas.com.br
- **Infraestrutura**: infra@lwksistemas.com.br
- **Suporte**: suporte@lwksistemas.com.br

## 📝 Documentação

- [Documentação da API](DOCUMENTACAO_API_MONITORAMENTO.md)
- [Guia de Uso](GUIA_USO_SUPERADMIN.md)
- [Documentação Técnica](CONCLUSAO_FINAL_MONITORAMENTO_v513.md)

## ✅ Aprovação Final

- [ ] **Desenvolvedor**: _______________
- [ ] **QA**: _______________
- [ ] **DevOps**: _______________
- [ ] **Product Owner**: _______________

**Data do Deploy**: _______________  
**Versão**: v513  
**Ambiente**: Produção

---

**Notas**:
- Manter este checklist atualizado
- Documentar problemas encontrados
- Atualizar procedimentos conforme necessário
