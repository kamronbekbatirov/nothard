const createNextIntlPlugin = require('next-intl/plugin')

const withNextIntl = createNextIntlPlugin('./i18n/request.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'media.rightmove.co.uk',
                port: '',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: '*.rightmove.co.uk',
                port: '',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: 'lc.zoocdn.com',
                port: '',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: 'lid.zoocdn.com',
                port: '',
                pathname: '/**',
            }
        ],
        unoptimized: true
    }
}

module.exports = withNextIntl(nextConfig)
