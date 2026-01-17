from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from pathlib import Path
from .models import (
    TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja,
    PagamentoLoja, UsuarioSistema
)
from .serializers import (
    TipoLojaSerializer, PlanoAssinaturaSerializer, LojaSerializer,
    FinanceiroLojaSerializer, PagamentoLojaSerializer, UsuarioSistemaSerializer,
    LojaCreateSerializer
)

class IsSuperAdmin(permissions.BasePermission):
    """Permissão apenas para super admins"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class TipoLojaViewSet(viewsets.ModelViewSet):
    queryset = TipoLoja.objects.all()
    serializer_class = TipoLojaSerializer
    permission_classes = [IsSuperAdmin]


class PlanoAssinaturaViewSet(viewsets.ModelViewSet):
    queryset = PlanoAssinatura.objects.all()
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de loja"""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.queryset.filter(tipos_loja__id=tipo_id, is_active=True)
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)


class LojaViewSet(viewsets.ModelViewSet):
    queryset = Loja.objects.all()
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LojaCreateSerializer
        return LojaSerializer
    
    def get_permissions(self):
        # Permitir acesso público ao endpoint info_publica
        if self.action == 'info_publica':
            return []
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar por slug se fornecido
        slug = self.request.query_params.get('slug')
        if slug:
            queryset = queryset.filter(slug=slug)
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def info_publica(self, request):
        """Retorna informações públicas da loja para página de login (sem autenticação)"""
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'slug é obrigatório'}, status=400)
        
        try:
            loja = Loja.objects.get(slug=slug, is_active=True)
            return Response({
                'nome': loja.nome,
                'slug': loja.slug,
                'tipo_loja_nome': loja.tipo_loja.nome,
                'cor_primaria': loja.cor_primaria,
                'cor_secundaria': loja.cor_secundaria,
                'logo': loja.logo,
                'login_page_url': loja.login_page_url,
            })
        except Loja.DoesNotExist:
            return Response({'error': 'Loja não encontrada'}, status=404)
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def verificar_senha_provisoria(self, request):
        """Verifica se o usuário logado precisa trocar a senha provisória (sem autenticação necessária)"""
        # Se não estiver autenticado, retornar False
        if not request.user or not request.user.is_authenticated:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não autenticado'
            })
        
        try:
            # Buscar loja do usuário logado
            loja = Loja.objects.get(owner=request.user)
            
            return Response({
                'precisa_trocar_senha': not loja.senha_foi_alterada and bool(loja.senha_provisoria),
                'loja_id': loja.id,
                'loja_nome': loja.nome,
                'loja_slug': loja.slug,
            })
        except Loja.DoesNotExist:
            return Response({
                'precisa_trocar_senha': False,
                'mensagem': 'Usuário não possui loja associada'
            })
    
    @action(detail=True, methods=['post'], permission_classes=[])
    def alterar_senha_primeiro_acesso(self, request, pk=None):
        """Permite ao proprietário alterar a senha no primeiro acesso (sem restrição de SuperAdmin)"""
        # Verificar se está autenticado
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'error': 'Autenticação necessária'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        loja = self.get_object()
        
        # Verificar se o usuário é o proprietário
        if request.user != loja.owner:
            return Response(
                {'error': 'Apenas o proprietário pode alterar a senha'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar se já alterou a senha
        if loja.senha_foi_alterada:
            return Response(
                {'error': 'A senha já foi alterada anteriormente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        nova_senha = request.data.get('nova_senha')
        confirmar_senha = request.data.get('confirmar_senha')
        
        if not nova_senha or not confirmar_senha:
            return Response(
                {'error': 'Nova senha e confirmação são obrigatórias'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nova_senha != confirmar_senha:
            return Response(
                {'error': 'As senhas não coincidem'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(nova_senha) < 6:
            return Response(
                {'error': 'A senha deve ter no mínimo 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Alterar senha do usuário
        user = loja.owner
        user.set_password(nova_senha)
        user.save()
        
        # Marcar que a senha foi alterada
        loja.senha_foi_alterada = True
        loja.save()
        
        return Response({
            'message': 'Senha alterada com sucesso!',
            'loja': loja.nome
        })
    
    def destroy(self, request, *args, **kwargs):
        """Exclusão completa da loja com limpeza de todos os dados"""
        loja = self.get_object()
        
        try:
            # Coletar informações antes da exclusão
            loja_nome = loja.nome
            loja_id = loja.id
            database_name = loja.database_name
            database_created = loja.database_created
            owner_username = loja.owner.username
            
            # Contar dados relacionados
            financeiro_exists = hasattr(loja, 'financeiro')
            pagamentos_count = loja.pagamentos.count() if hasattr(loja, 'pagamentos') else 0
            outras_lojas_owner = Loja.objects.filter(owner=loja.owner).exclude(id=loja.id).count()
            
            # 1. Remover banco de dados físico se existir
            banco_removido = False
            if database_created:
                db_path = settings.BASE_DIR / f'db_{database_name}.sqlite3'
                
                # Remover das configurações do Django
                if database_name in settings.DATABASES:
                    del settings.DATABASES[database_name]
                    print(f"✅ Configuração do banco removida: {database_name}")
                
                # Remover arquivo físico do banco
                if db_path.exists():
                    import os
                    os.remove(db_path)
                    banco_removido = True
                    print(f"✅ Arquivo do banco removido: {db_path}")
            
            # 2. Coletar dados do proprietário antes da possível exclusão
            owner = loja.owner
            usuario_sera_removido = outras_lojas_owner == 0
            
            # 3. Remover a loja (isso remove automaticamente em cascade):
            # - FinanceiroLoja (OneToOneField com CASCADE)
            # - PagamentoLoja (ForeignKey com CASCADE) 
            # - Relacionamentos ManyToMany
            loja.delete()
            print(f"✅ Loja removida: {loja_nome}")
            
            # 4. Remover usuário proprietário se não for usado por outras lojas
            usuario_removido = False
            if usuario_sera_removido:
                # Verificar se o usuário não é superuser ou staff importante
                if not owner.is_superuser and not owner.is_staff:
                    owner.delete()
                    usuario_removido = True
                    print(f"✅ Usuário proprietário removido: {owner_username}")
                else:
                    print(f"⚠️ Usuário {owner_username} mantido (superuser/staff)")
            
            # 5. Limpeza adicional de arquivos relacionados (se houver)
            # TODO: Remover uploads, logos, etc. se implementado no futuro
            
            return Response({
                'message': f'Loja "{loja_nome}" foi completamente removida do sistema',
                'detalhes': {
                    'loja_id': loja_id,
                    'loja_nome': loja_nome,
                    'loja_removida': True,
                    'banco_dados': {
                        'existia': database_created,
                        'nome': database_name,
                        'arquivo_removido': banco_removido,
                        'config_removida': database_created
                    },
                    'dados_financeiros': {
                        'financeiro_removido': financeiro_exists,
                        'pagamentos_removidos': pagamentos_count
                    },
                    'usuario_proprietario': {
                        'username': owner_username,
                        'removido': usuario_removido,
                        'motivo_nao_removido': 'Possui outras lojas' if not usuario_sera_removido else ('Superuser/Staff' if not usuario_removido and usuario_sera_removido else None)
                    },
                    'limpeza_completa': True
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Erro ao excluir loja: {error_details}")
            
            return Response(
                {
                    'error': f'Erro ao excluir loja: {str(e)}',
                    'detalhes': 'Alguns dados podem não ter sido removidos completamente',
                    'error_completo': error_details if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reenviar_senha(self, request, pk=None):
        """Reenviar senha provisória por email"""
        loja = self.get_object()
        
        if not loja.senha_provisoria:
            return Response(
                {'error': 'Esta loja não possui senha provisória cadastrada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            assunto = f"Reenvio - Acesso à sua loja {loja.nome}"
            mensagem = f"""
Olá!

Conforme solicitado, seguem novamente os dados de acesso à sua loja "{loja.nome}":

🔐 DADOS DE ACESSO:
• URL de Login: https://lwksistemas.com.br{loja.login_page_url}
• Usuário: {loja.owner.username}
• Senha Provisória: {loja.senha_provisoria}

⚠️ IMPORTANTE:
• Esta é uma senha provisória gerada automaticamente
• Recomendamos alterar a senha no primeiro acesso
• Mantenha seus dados de acesso em segurança

📋 INFORMAÇÕES DA LOJA:
• Nome: {loja.nome}
• Tipo: {loja.tipo_loja.nome}
• Plano: {loja.plano.nome}
• Assinatura: {loja.get_tipo_assinatura_display()}

Se você já alterou sua senha, pode ignorar este email.

---
Equipe de Suporte
Sistema Multi-Loja
            """.strip()
            
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[loja.owner.email],
                fail_silently=False
            )
            
            return Response({
                'message': f'Senha provisória reenviada para {loja.owner.email}',
                'email_enviado': loja.owner.email,
                'loja': loja.nome
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao enviar email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def criar_banco(self, request, pk=None):
        """Cria banco de dados isolado para a loja"""
        loja = self.get_object()
        
        if loja.database_created:
            return Response(
                {'error': 'Banco já foi criado para esta loja'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Adicionar banco às configurações
            db_name = loja.database_name
            db_path = settings.BASE_DIR / f'db_{db_name}.sqlite3'
            
            settings.DATABASES[db_name] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'OPTIONS': {},
                'TIME_ZONE': None,
            }
            
            # Executar migrations
            call_command('migrate', '--database', db_name, verbosity=0)
            
            # Criar usuário admin da loja no banco isolado
            from django.contrib.auth.models import User as UserModel
            admin_loja = UserModel.objects.db_manager(db_name).create_user(
                username=loja.owner.username,
                email=loja.owner.email,
                password='senha123',  # Senha padrão
                is_staff=True
            )
            
            # Marcar como criado
            loja.database_created = True
            loja.save()
            
            return Response({
                'message': 'Banco criado com sucesso',
                'database_name': db_name,
                'database_path': str(db_path),
                'admin_username': loja.owner.username,
                'admin_password': 'senha123'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais do sistema"""
        total_lojas = Loja.objects.count()
        lojas_ativas = Loja.objects.filter(is_active=True).count()
        lojas_trial = Loja.objects.filter(is_trial=True).count()
        
        # Receita mensal
        from django.db.models import Sum
        receita_mensal = FinanceiroLoja.objects.filter(
            status_pagamento='ativo'
        ).aggregate(total=Sum('valor_mensalidade'))['total'] or 0
        
        return Response({
            'total_lojas': total_lojas,
            'lojas_ativas': lojas_ativas,
            'lojas_trial': lojas_trial,
            'lojas_inativas': total_lojas - lojas_ativas,
            'receita_mensal_estimada': float(receita_mensal),
        })


class FinanceiroLojaViewSet(viewsets.ModelViewSet):
    queryset = FinanceiroLoja.objects.all()
    serializer_class = FinanceiroLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def pendentes(self, request):
        """Lojas com pagamento pendente"""
        pendentes = self.queryset.filter(status_pagamento__in=['pendente', 'atrasado'])
        serializer = self.get_serializer(pendentes, many=True)
        return Response(serializer.data)


class PagamentoLojaViewSet(viewsets.ModelViewSet):
    queryset = PagamentoLoja.objects.all()
    serializer_class = PagamentoLojaSerializer
    permission_classes = [IsSuperAdmin]
    
    @action(detail=True, methods=['post'])
    def confirmar_pagamento(self, request, pk=None):
        """Confirmar pagamento de uma loja"""
        pagamento = self.get_object()
        
        from django.utils import timezone
        pagamento.status = 'pago'
        pagamento.data_pagamento = timezone.now()
        pagamento.save()
        
        # Atualizar financeiro
        financeiro = pagamento.financeiro
        financeiro.status_pagamento = 'ativo'
        financeiro.ultimo_pagamento = timezone.now()
        financeiro.total_pago += pagamento.valor
        financeiro.save()
        
        return Response({'message': 'Pagamento confirmado com sucesso'})


class UsuarioSistemaViewSet(viewsets.ModelViewSet):
    queryset = UsuarioSistema.objects.all()
    serializer_class = UsuarioSistemaSerializer
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def suporte(self, request):
        """Listar apenas usuários de suporte"""
        suporte = self.queryset.filter(tipo='suporte')
        serializer = self.get_serializer(suporte, many=True)
        return Response(serializer.data)
