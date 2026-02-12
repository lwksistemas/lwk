import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware de Isolamento de Grupos
 * 
 * REGRAS DE SEGURANÇA:
 * 1. Super Admin: APENAS /superadmin/*
 * 2. Suporte: APENAS /suporte/*
 * 3. Lojas: APENAS /loja/{slug}/*
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const userType = request.cookies.get('user_type')?.value;
  const lojaSlug = request.cookies.get('loja_slug')?.value;

  // ========================================
  // ROTAS PÚBLICAS (sem autenticação)
  // ========================================
  const publicRoutes = [
    '/',
    '/forcar-atualizacao',
  ];
  
  if (publicRoutes.includes(pathname)) {
    return NextResponse.next();
  }

  // ========================================
  // GRUPO 1: SUPER ADMIN
  // ========================================
  if (pathname.startsWith('/superadmin')) {
    // Permitir acesso à página de login sempre (sem verificar cookies)
    if (pathname === '/superadmin/login') {
      return NextResponse.next();
    }
    
    // Para outras páginas, verificar se é superadmin
    if (userType && userType !== 'superadmin') {
      return NextResponse.redirect(new URL(getRedirectUrl(userType, lojaSlug), request.url));
    }
    
    return NextResponse.next();
  }

  // ========================================
  // GRUPO 2: SUPORTE
  // ========================================
  if (pathname.startsWith('/suporte')) {
    // Permitir acesso à página de login sempre (sem verificar cookies)
    if (pathname === '/suporte/login') {
      return NextResponse.next();
    }
    
    // Para outras páginas, verificar se é suporte
    if (userType && userType !== 'suporte') {
      return NextResponse.redirect(new URL(getRedirectUrl(userType, lojaSlug), request.url));
    }
    
    return NextResponse.next();
  }

  // ========================================
  // GRUPO 3: LOJAS
  // ========================================
  if (pathname.startsWith('/loja')) {
    const slugMatch = pathname.match(/^\/loja\/([^\/]+)/);
    const requestedSlug = slugMatch ? slugMatch[1] : null;
    
    // Permitir acesso à página de login sempre (sem verificar cookies)
    if (pathname.match(/^\/loja\/[^\/]+\/login$/)) {
      return NextResponse.next();
    }
    
    // Rota de troca de senha (não tem slug no path, mas precisa de autenticação de loja)
    if (pathname === '/loja/trocar-senha') {
      // Permitir acesso se for usuário de loja autenticado
      if (userType === 'loja') {
        return NextResponse.next();
      }
      // Se não for loja, redirecionar para a home
      return NextResponse.redirect(new URL('/', request.url));
    }
    
    // Para outras páginas de loja, verificar se é loja
    if (userType && userType !== 'loja') {
      return NextResponse.redirect(new URL(getRedirectUrl(userType, lojaSlug), request.url));
    }
    
    // Se for loja mas tentando acessar outra loja
    if (userType === 'loja' && lojaSlug && requestedSlug && requestedSlug !== lojaSlug) {
      return NextResponse.redirect(new URL(`/loja/${lojaSlug}/dashboard`, request.url));
    }
    
    return NextResponse.next();
  }

  return NextResponse.next();
}

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
