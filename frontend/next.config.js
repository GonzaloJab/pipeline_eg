// next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
    async headers() {
      // Get allowed origins from environment variable
      const allowedOrigins = process.env.NEXT_PUBLIC_ALLOWED_ORIGINS?.split(',') || ['http://localhost'];
      
      return [
        {
          source: "/api/:path*",
          headers: [
            { key: "Access-Control-Allow-Credentials", value: "true" },
            { key: "Access-Control-Allow-Origin", value: allowedOrigins.join(',') },
            { key: "Access-Control-Allow-Methods", value: "GET,DELETE,PATCH,POST,PUT" },
            { key: "Access-Control-Allow-Headers", value: "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version" },
            { key: "Access-Control-Max-Age", value: "86400" }, // 24 hours
          ],
        },
        {
          source: "/:path*",
          headers: [
            { key: "X-Frame-Options", value: "DENY" },
            { key: "X-Content-Type-Options", value: "nosniff" },
            { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          ],
        },
      ];
    },
    async rewrites() {
      return [
        {
          source: '/trains/:path*',
          destination: 'http://172.26.1.50:8000/trains/:path*',
          has: [
            {
              type: 'header',
              key: 'origin',
              value: '(http://172.26.7.10|http://localhost)',
            },
          ],
        },
      ];
    },
  };
  
  module.exports = nextConfig;
  