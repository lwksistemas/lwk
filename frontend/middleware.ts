import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware de Isolamento de Grupos
 * 
 * REGRAS DE SEGURANÇA:
 * 1. Super Admin: APENAS /superadmin/*
 * 2. Suporte: APENAS /suporte/*
 * 3. Lojas: APENAS /loja/{slug}/*
 * 
 * Nenhum grupo pode acessar páginas de outro grupo
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Obter informações do usuário dos cookies/localStorage
  const userType = request.cookies.get('user_type')?.value;
  const lojaSlug = request.cookies.get('loja_slug')?.value;

  // ========================================
  // ROTAS PÚBLICAS (sem autenticação)
  // ========================================
  const publicRoutes = [
    '/',
    '/diagnostico',
    '/debug-mobile',
  ];
  
  if (publicRoutes.includes(pathname)) {
    return NextResponse.next();
  }

  // ========================================
  // GRUPO 1: SUPER ADMIN
  // ========================================
  if (pathname.startsWith('/superadmin')) {
    // Permitir acesso à página de login do superadmin
    if (pathname === '/superadmin/login') {
      // Se já está logado como outro tipo, bloquear
      if (userType && userType !== 'superadmin') {
        console.log(`🚨 BLOQUEIO: Usuário tipo "${userType}" tentou acessar /superadmin/login`);
        return NextResponse.redirect(new URL(getRedirectUrl(userType, lojaSlug), request.url));
      }
      return NextResponse.next();
    }
    
    // Para outras rotas de superadmin, verificar autenticação no cliente
    return NextResponse.next();
  }

  // ========================================
  // GRUPO 2: SUPORTE
  // ========================================
  if (pathname.startsWith('/suporte')) {
    // Permitir acesso à página de login do suporte
    if (pathname === '/suporte/login') {
      // Se já está logado como outro tipo, bloquear
      if (userType && userType !== 'suporte') {
        console.log(`🚨 BLOQUEIO: Usuário tipo "${userType}" tentou acessar /suporte/login`);
        return NextResponse.redirect(new URL(getRedirectUrl(userType, lojaSlug), request.url));
      }
      return NextResponse.next();
    }
    
    // Para outras rotas de suporte, verificar autenticação no cliente
    return NextResponse.next();
  }

  // ========================================
  // GRUPO 3: LOJAS
  // ========================================
  if (pathname.startsWith('/loja')) {
    // Extrair slug da URL
    const slugMatch = pathname.match(/^\/loja\/([^\/]+)/);
    const requestedSlug = slugMatch ? slugMatch[1] : null;
    
    // Permitir acesso à página de login da loja
    if (pathname.match(/^\/loja\/[^\/]+\/login$/)) {
      // Se já está logado como outro tipo, bloquear
      if (userType && userType !== 'loja') {
        console.log(`🚨 BLOQUEIO: Usuário tipo "${userType}" tentou acessar login de loja`);
        return NextResponse.redirect(new URL(getRedirectUrl(userType, lojaSlug), request.url));
      }
      return NextResponse.next();
    }
    
    // Para outras rotas de loja, verificar autenticação no cliente
    return NextResponse.next();
  }

  // Permitir acesso a outras rotas
  return NextResponse.next();
}

/**
 * Retorna a URL de redirecionamento baseada no tipo de usuário
 */
function getRedirectUrl(userType: string, lojaSlug?: string): string {
  switch (userType) {
    case 'superadmin':
      return '/superadmin/dashboard';
    case 'suporte':
      return '/suporte/dashboard';
    case 'loja':
      return lojaSlug ? `/loja/${lojaSlug}/dashboard` : '/';
    default:
      return '/';
  }
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)'],
};
