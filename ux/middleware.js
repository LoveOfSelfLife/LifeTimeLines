
import { NextResponse } from 'next/server'
 
export function middleware(request) {
  
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-hello-from-middleware-request-1', 'hello')
 
  // You can also set request headers in NextResponse.rewrite
  const response = NextResponse.next({
    request: {
      // New request headers
      headers: requestHeaders,
    },
  })
 
  // Set a new response header `x-hello-from-middleware2`
  response.headers.set('x-hello-from-middleware-response-2', 'hello')
  return response
}

export const config = {
    matcher: '/api/:path*',
}
