import { NextResponse } from 'next/server';

export function middleware(request) {
  // Get the origin from the request headers
  const origin = request.headers.get('origin');
  
  // Get allowed origins from environment variable
  const allowedOrigins = process.env.NEXT_PUBLIC_ALLOWED_ORIGINS?.split(',') || ['http://localhost'];
  
  // Check if the origin is allowed
  if (origin && !allowedOrigins.includes(origin)) {
    console.log('Blocked request from unauthorized origin:', origin);
    return new NextResponse(null, {
      status: 403,
      statusText: 'Forbidden',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  return NextResponse.next();
}

// Configure which paths the middleware should run on
export const config = {
  matcher: [
    '/api/:path*',
    '/trains/:path*',
  ],
}; 