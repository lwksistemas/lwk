/** JWT em cookies httpOnly (backend JWT_USE_HTTPONLY_COOKIES + withCredentials). */
export const USE_JWT_HTTPONLY_COOKIES =
  process.env.NEXT_PUBLIC_JWT_HTTPONLY_COOKIES === 'true';
