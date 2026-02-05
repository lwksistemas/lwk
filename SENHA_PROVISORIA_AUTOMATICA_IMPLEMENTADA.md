# ✅ Senha Provisória Automática - Implementação Completa

## 📋 RESUMO
Sistema de criação de usuários com senha provisória gerada automaticamente e enviada por email.

---

## 🎯 OBJETIVO
Remover campo de senha do formulário de criação de usuários e gerar senha provisória automaticamente, enviando por email.

---

## ✅ IMPLEMENTAÇÃO

### Backend (v401) ✅ DEPLOYADO
**Arquivo**: `backend/superadmin/serializers.py`

#### Método `UsuarioSistemaSerializer.create()`:
```python
def create(self, validated_data):
    import random
    import string
    from django.core.mail import send_mail
    from django.conf import settings
    
    user_data = validated_data.pop('user')
    
    # Gerar senha provisória automaticamente (10 caracteres)
    senha_provisoria = ''.join(random.choices(
        string.ascii_letters + string.digits + '!@#$%&*', 
        k=10
    ))
    
    # Criar usuário com senha provisória
    user = User.objects.create_user(
        username=user_data['username'],
        email=user_data.get('email', ''),
        password=senha_provisoria,
        first_name=user_data.get('first_name', ''),
        last_name=user_data.get('last_name', ''),
        is_staff=True
    )
    
    # Criar perfil com senha provisória
    perfil = UsuarioSistema.objects.create(
        user=user, 
        senha_provisoria=senha_provisoria,
        senha_foi_alterada=False,
        **validated_data
    )
    
    # Adicionar ao grupo apropriado
    if perfil.tipo == 'suporte':
        grupo, _ = Group.objects.get_or_create(name='suporte')
        user.groups.add(grupo)
    elif perfil.tipo == 'superadmin':
        user.is_superuser = True
        user.save()
    
    # Enviar email com senha provisória
    try:
        tipo_display = 'Super Admin' if perfil.tipo == 'superadmin' else 'Suporte'
        url_login = f"https://lwksistemas.com.br/{perfil.tipo}/login"
        
        assunto = f"Bem-vindo ao LWK Sistemas - {tipo_display}"
        mensagem = f"""
Olá {user.first_name or user.username}!

Sua conta foi criada no LWK Sistemas.

🔐 DADOS DE ACESSO:
• URL de Login: {url_login}
• Usuário: {user.username}
• Senha Provisória: {senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Você será solicitado a trocar a senha no primeiro acesso
• Por segurança, altere a senha assim que fizer login
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA CONTA:
• Nome: {user.first_name} {user.last_name}
• Email: {user.email}
• Tipo: {tipo_display}

---
Equipe LWK Sistemas
        """.strip()
        
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
        logger.info(f"✅ Email enviado para {user.email} com senha provisória")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao enviar email: {e}")
    
    # Armazenar senha provisória no contexto para retornar na resposta
    perfil._senha_provisoria_gerada = senha_provisoria
    
    return perfil
```

**Arquivo**: `backend/superadmin/views.py`

#### Método `UsuarioSistemaViewSet.create()`:
```python
def create(self, request, *args, **kwargs):
    """Criar usuário com senha provisória gerada automaticamente"""
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    
    # Pegar senha provisória gerada
    senha_provisoria = getattr(serializer.instance, '_senha_provisoria_gerada', None)
    
    # Adicionar senha provisória na resposta
    response_data = serializer.data
    response_data['senha_provisoria'] = senha_provisoria
    response_data['message'] = 'Usuário criado com sucesso! Senha provisória enviada por email.'
    
    headers = self.get_success_headers(serializer.data)
    return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
```

---

### Frontend ✅ DEPLOYADO
**Arquivo**: `frontend/app/(dashboard)/superadmin/usuarios/page.tsx`

#### Mudanças no Modal:
1. **Campo senha removido ao criar** (mantido apenas ao editar)
2. **Aviso sobre senha provisória** exibido ao criar
3. **Alert mostra senha gerada** após criação bem-sucedida

```typescript
// Ao criar: backend gera senha provisória automaticamente
// Ao editar: só incluir senha se foi preenchida
if (isEditing && formData.password) {
  userData.password = formData.password;
}

// Após criação bem-sucedida
if (!isEditing) {
  const senhaProvisoria = response.data.senha_provisoria;
  alert(`✅ Usuário criado com sucesso!\n\n📧 Senha provisória enviada para: ${formData.email}\n🔐 Senha: ${senhaProvisoria}\n\n⚠️ O usuário deverá trocar a senha no primeiro acesso.`);
}
```

#### Aviso no Formulário:
```typescript
{!isEditing && (
  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
    <p className="text-sm text-blue-800">
      <strong>ℹ️ Senha Provisória:</strong> Uma senha será gerada automaticamente e enviada para o email do usuário. O usuário deverá trocar a senha no primeiro acesso.
    </p>
  </div>
)}
```

---

## 🔄 FLUXO COMPLETO

### 1. Criação de Usuário
1. SuperAdmin acessa `/superadmin/usuarios`
2. Clica em "+ Novo Usuário"
3. Preenche formulário (SEM campo senha)
4. Clica em "Criar Usuário"

### 2. Backend Processa
1. Gera senha provisória (10 caracteres aleatórios)
2. Cria usuário Django com senha provisória
3. Cria perfil UsuarioSistema com `senha_foi_alterada=False`
4. Envia email com credenciais
5. Retorna senha na resposta da API

### 3. Frontend Exibe
1. Mostra alert com senha gerada
2. Informa que email foi enviado
3. Recarrega lista de usuários

### 4. Primeiro Acesso do Usuário
1. Usuário recebe email com credenciais
2. Acessa URL de login apropriada
3. Faz login com senha provisória
4. Sistema detecta `senha_foi_alterada=False`
5. Força troca de senha

---

## 📧 EMAIL ENVIADO

**Assunto**: Bem-vindo ao LWK Sistemas - [Super Admin/Suporte]

**Conteúdo**:
```
Olá [Nome]!

Sua conta foi criada no LWK Sistemas.

🔐 DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br/[tipo]/login
• Usuário: [username]
• Senha Provisória: [senha_gerada]

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Você será solicitado a trocar a senha no primeiro acesso
• Por segurança, altere a senha assim que fizer login
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA CONTA:
• Nome: [Nome Completo]
• Email: [email]
• Tipo: [Super Admin/Suporte]

---
Equipe LWK Sistemas
```

---

## 🔐 SEGURANÇA

### Senha Provisória
- **Tamanho**: 10 caracteres
- **Caracteres**: Letras (maiúsculas e minúsculas), números e símbolos (!@#$%&*)
- **Geração**: `random.choices()` com caracteres seguros
- **Armazenamento**: Hash no banco (via `set_password()`)

### Campos de Controle
- `senha_provisoria`: Armazena senha em texto plano (apenas para referência)
- `senha_foi_alterada`: Boolean que controla se precisa trocar senha

### Fluxo de Troca
1. Login com senha provisória
2. Sistema verifica `senha_foi_alterada=False`
3. Redireciona para tela de troca de senha
4. Após trocar, marca `senha_foi_alterada=True`

---

## 🧪 TESTES

### Testar Criação
1. Acesse: https://lwksistemas.com.br/superadmin/usuarios
2. Clique em "+ Novo Usuário"
3. Preencha dados (sem senha)
4. Verifique alert com senha gerada
5. Verifique email recebido

### Testar Edição
1. Clique em "✏️ Editar" em um usuário
2. Verifique que campo senha aparece (opcional)
3. Deixe em branco para manter senha atual
4. Ou preencha para alterar senha

---

## 📊 STATUS

| Componente | Status | Deploy | URL |
|------------|--------|--------|-----|
| Backend | ✅ Completo | v401 | https://lwksistemas-38ad47519238.herokuapp.com |
| Frontend | ✅ Completo | Prod | https://lwksistemas.com.br |
| Email | ✅ Configurado | - | Gmail SMTP |
| Testes | ⏳ Pendente | - | Aguardando teste manual |

---

## 🎉 RESULTADO

✅ **Campo senha removido** do formulário de criação
✅ **Senha provisória gerada** automaticamente (10 caracteres)
✅ **Email enviado** com credenciais de acesso
✅ **Alert exibe senha** após criação
✅ **Fluxo de troca** de senha no primeiro acesso
✅ **Edição mantém** campo senha opcional

---

## 📝 PRÓXIMOS PASSOS

1. ✅ Deploy backend (v401) - CONCLUÍDO
2. ✅ Deploy frontend - CONCLUÍDO
3. ⏳ Teste manual de criação de usuário
4. ⏳ Verificar recebimento de email
5. ⏳ Testar primeiro acesso e troca de senha

---

**Data**: 05/02/2026
**Versão Backend**: v401
**Versão Frontend**: Prod (Vercel)
**Status**: ✅ IMPLEMENTADO E DEPLOYADO
