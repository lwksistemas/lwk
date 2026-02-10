/**
 * Sistema de Roles e Permissões - Cabeleireiro
 * 
 * Define os níveis de acesso e permissões para cada tipo de usuário
 * Aplicando boas práticas: DRY, SOLID, Clean Code
 */

// ============================================================================
// TYPES E INTERFACES
// ============================================================================

export type UserRole = 
  | 'administrador'      // Dono do salão - acesso total
  | 'gerente'            // Gerente - acesso quase total (sem financeiro sensível)
  | 'atendente'          // Recepção - agendamentos, clientes
  | 'profissional'       // Cabeleireiro - apenas sua agenda
  | 'caixa'              // Caixa - vendas e pagamentos
  | 'estoquista'         // Estoquista - produtos e estoque
  | 'visualizador';      // Apenas leitura

export interface Permission {
  view: boolean;         // Pode visualizar
  create: boolean;       // Pode criar
  edit: boolean;         // Pode editar
  delete: boolean;       // Pode excluir
}

export interface RolePermissions {
  // Dashboard
  verEstatisticas: boolean;
  verFaturamento: boolean;
  verRelatorios: boolean;
  
  // Agendamentos
  agendamentos: Permission;
  verTodosAgendamentos: boolean;
  verApenasPropriosAgendamentos: boolean;
  
  // Clientes
  clientes: Permission;
  
  // Serviços
  servicos: Permission;
  
  // Produtos
  produtos: Permission;
  
  // Vendas
  vendas: Permission;
  verTodasVendas: boolean;
  
  // Funcionários
  funcionarios: Permission;
  
  // Configurações
  configuracoes: Permission;
  horarios: Permission;
  bloqueios: Permission;
  
  // Financeiro
  verFinanceiro: boolean;
  editarPrecos: boolean;
}

// ============================================================================
// CONFIGURAÇÃO DE PERMISSÕES - SINGLE SOURCE OF TRUTH
// ============================================================================

const FULL_PERMISSION: Permission = { view: true, create: true, edit: true, delete: true };
const READ_ONLY: Permission = { view: true, create: false, edit: false, delete: false };
const NO_PERMISSION: Permission = { view: false, create: false, edit: false, delete: false };
const CREATE_EDIT: Permission = { view: true, create: true, edit: true, delete: false };

/**
 * Mapa de permissões por role
 * 
 * Cada role tem um conjunto específico de permissões
 * Facilita manutenção e evita duplicação de código
 */
export const ROLE_PERMISSIONS: Record<UserRole, RolePermissions> = {
  // 👑 ADMINISTRADOR (Dono do Salão) - Acesso Total
  administrador: {
    verEstatisticas: true,
    verFaturamento: true,
    verRelatorios: true,
    agendamentos: FULL_PERMISSION,
    verTodosAgendamentos: true,
    verApenasPropriosAgendamentos: false,
    clientes: FULL_PERMISSION,
    servicos: FULL_PERMISSION,
    produtos: FULL_PERMISSION,
    vendas: FULL_PERMISSION,
    verTodasVendas: true,
    funcionarios: FULL_PERMISSION,
    configuracoes: FULL_PERMISSION,
    horarios: FULL_PERMISSION,
    bloqueios: FULL_PERMISSION,
    verFinanceiro: true,
    editarPrecos: true,
  },
  
  // 👔 GERENTE - Acesso Quase Total (sem financeiro sensível)
  gerente: {
    verEstatisticas: true,
    verFaturamento: true,
    verRelatorios: true,
    agendamentos: FULL_PERMISSION,
    verTodosAgendamentos: true,
    verApenasPropriosAgendamentos: false,
    clientes: FULL_PERMISSION,
    servicos: FULL_PERMISSION,
    produtos: FULL_PERMISSION,
    vendas: FULL_PERMISSION,
    verTodasVendas: true,
    funcionarios: CREATE_EDIT,
    configuracoes: CREATE_EDIT,
    horarios: FULL_PERMISSION,
    bloqueios: FULL_PERMISSION,
    verFinanceiro: false,
    editarPrecos: false,
  },
  
  // 📞 ATENDENTE/RECEPÇÃO - Agendamentos e Clientes
  atendente: {
    verEstatisticas: true,
    verFaturamento: false,
    verRelatorios: false,
    agendamentos: FULL_PERMISSION,
    verTodosAgendamentos: true,
    verApenasPropriosAgendamentos: false,
    clientes: FULL_PERMISSION,
    servicos: READ_ONLY,
    produtos: READ_ONLY,
    vendas: CREATE_EDIT,
    verTodasVendas: true,
    funcionarios: READ_ONLY,
    configuracoes: NO_PERMISSION,
    horarios: READ_ONLY,
    bloqueios: CREATE_EDIT,
    verFinanceiro: false,
    editarPrecos: false,
  },
  
  // ✂️ PROFISSIONAL/CABELEIREIRO - Apenas Sua Agenda
  profissional: {
    verEstatisticas: false,
    verFaturamento: false,
    verRelatorios: false,
    agendamentos: READ_ONLY,
    verTodosAgendamentos: false,
    verApenasPropriosAgendamentos: true,
    clientes: READ_ONLY,
    servicos: READ_ONLY,
    produtos: READ_ONLY,
    vendas: NO_PERMISSION,
    verTodasVendas: false,
    funcionarios: NO_PERMISSION,
    configuracoes: NO_PERMISSION,
    horarios: READ_ONLY,
    bloqueios: NO_PERMISSION,
    verFinanceiro: false,
    editarPrecos: false,
  },
  
  // 💰 CAIXA - Vendas e Pagamentos
  caixa: {
    verEstatisticas: true,
    verFaturamento: false,
    verRelatorios: false,
    agendamentos: READ_ONLY,
    verTodosAgendamentos: true,
    verApenasPropriosAgendamentos: false,
    clientes: READ_ONLY,
    servicos: READ_ONLY,
    produtos: READ_ONLY,
    vendas: FULL_PERMISSION,
    verTodasVendas: true,
    funcionarios: NO_PERMISSION,
    configuracoes: NO_PERMISSION,
    horarios: NO_PERMISSION,
    bloqueios: NO_PERMISSION,
    verFinanceiro: false,
    editarPrecos: false,
  },
  
  // 📦 ESTOQUISTA - Produtos e Estoque
  estoquista: {
    verEstatisticas: false,
    verFaturamento: false,
    verRelatorios: false,
    agendamentos: NO_PERMISSION,
    verTodosAgendamentos: false,
    verApenasPropriosAgendamentos: false,
    clientes: NO_PERMISSION,
    servicos: NO_PERMISSION,
    produtos: FULL_PERMISSION,
    vendas: NO_PERMISSION,
    verTodasVendas: false,
    funcionarios: NO_PERMISSION,
    configuracoes: NO_PERMISSION,
    horarios: NO_PERMISSION,
    bloqueios: NO_PERMISSION,
    verFinanceiro: false,
    editarPrecos: false,
  },
  
  // 👁️ VISUALIZADOR - Apenas Leitura
  visualizador: {
    verEstatisticas: true,
    verFaturamento: false,
    verRelatorios: true,
    agendamentos: READ_ONLY,
    verTodosAgendamentos: true,
    verApenasPropriosAgendamentos: false,
    clientes: READ_ONLY,
    servicos: READ_ONLY,
    produtos: READ_ONLY,
    vendas: READ_ONLY,
    verTodasVendas: true,
    funcionarios: READ_ONLY,
    configuracoes: NO_PERMISSION,
    horarios: READ_ONLY,
    bloqueios: NO_PERMISSION,
    verFinanceiro: false,
    editarPrecos: false,
  },
};

// ============================================================================
// FUNÇÕES AUXILIARES - CLEAN CODE
// ============================================================================

/**
 * Obtém as permissões de um role específico
 */
export function getRolePermissions(role: UserRole): RolePermissions {
  return ROLE_PERMISSIONS[role];
}

/**
 * Verifica se um role tem permissão para uma ação específica
 */
export function hasPermission(
  role: UserRole,
  resource: keyof RolePermissions,
  action?: 'view' | 'create' | 'edit' | 'delete'
): boolean {
  const permissions = getRolePermissions(role);
  const resourcePermission = permissions[resource];
  
  // Se for boolean, retornar direto
  if (typeof resourcePermission === 'boolean') {
    return resourcePermission;
  }
  
  // Se for Permission object, verificar ação específica
  if (action && typeof resourcePermission === 'object') {
    return resourcePermission[action];
  }
  
  return false;
}

/**
 * Verifica se um role pode visualizar um recurso
 */
export function canView(role: UserRole, resource: keyof RolePermissions): boolean {
  return hasPermission(role, resource, 'view');
}

/**
 * Verifica se um role pode criar um recurso
 */
export function canCreate(role: UserRole, resource: keyof RolePermissions): boolean {
  return hasPermission(role, resource, 'create');
}

/**
 * Verifica se um role pode editar um recurso
 */
export function canEdit(role: UserRole, resource: keyof RolePermissions): boolean {
  return hasPermission(role, resource, 'edit');
}

/**
 * Verifica se um role pode excluir um recurso
 */
export function canDelete(role: UserRole, resource: keyof RolePermissions): boolean {
  return hasPermission(role, resource, 'delete');
}

/**
 * Obtém o nome amigável de um role
 */
export function getRoleName(role: UserRole): string {
  const roleNames: Record<UserRole, string> = {
    administrador: 'Administrador',
    gerente: 'Gerente',
    atendente: 'Atendente/Recepção',
    profissional: 'Profissional/Cabeleireiro',
    caixa: 'Caixa',
    estoquista: 'Estoquista',
    visualizador: 'Visualizador',
  };
  
  return roleNames[role] || role;
}

/**
 * Obtém o ícone de um role
 */
export function getRoleIcon(role: UserRole): string {
  const roleIcons: Record<UserRole, string> = {
    administrador: '👑',
    gerente: '👔',
    atendente: '📞',
    profissional: '✂️',
    caixa: '💰',
    estoquista: '📦',
    visualizador: '👁️',
  };
  
  return roleIcons[role] || '👤';
}

/**
 * Obtém a cor de um role
 */
export function getRoleColor(role: UserRole): string {
  const roleColors: Record<UserRole, string> = {
    administrador: '#9333EA',  // Purple
    gerente: '#3B82F6',        // Blue
    atendente: '#06B6D4',      // Cyan
    profissional: '#8B5CF6',   // Violet
    caixa: '#10B981',          // Green
    estoquista: '#F59E0B',     // Amber
    visualizador: '#6B7280',   // Gray
  };
  
  return roleColors[role] || '#6B7280';
}

/**
 * Filtra botões de ação baseado nas permissões do role
 */
export function filterActionsByRole<T extends { permission?: keyof RolePermissions }>(
  actions: T[],
  role: UserRole
): T[] {
  return actions.filter(action => {
    if (!action.permission) return true;
    return canView(role, action.permission);
  });
}
