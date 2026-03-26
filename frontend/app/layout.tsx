import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { InstallPWA } from "@/components/pwa/InstallPWA";

const inter = Inter({ subsets: ["latin"] });

export const viewport: Viewport = {
  themeColor: "#46cce4ff",
};

export const metadata: Metadata = {
  title: "LWK Sistemas - Gestão de Lojas",
  description: "Sistema de gestão multi-loja: clínica estética, agenda, financeiro",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "LWK Sistemas",
  },
  other: {
    "cache-control": "no-cache, no-store, must-revalidate",
    "pragma": "no-cache",
    "expires": "0",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning className="w-full min-w-full m-0 p-0 overflow-x-hidden">
      <head>
        <link rel="apple-touch-icon" href="/icons/icon.svg" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  // Padrão: sempre modo CLARO.
                  // Só ativa dark se o usuário tiver escolhido explicitamente.
                  if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.className} bg-white dark:bg-gray-900 transition-colors duration-200 w-full min-w-full m-0 p-0 overflow-x-hidden antialiased`}>
        <Providers>{children}</Providers>
        <InstallPWA />
      </body>
    </html>
  );
}
