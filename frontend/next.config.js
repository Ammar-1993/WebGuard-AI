/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // إعدادات بيئية للاتصال بالخادم المركزي
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010',
  },
};

module.exports = nextConfig;
