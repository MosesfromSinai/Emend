import { Analytics } from "@vercel/analytics/next";
import type { Metadata } from "next";
import { JetBrains_Mono, Source_Serif_4 } from "next/font/google";

import { COLOR_SCHEME_INIT_SCRIPT } from "@/lib/color-scheme";

import "./globals.css";

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const description = "A tailored resume that can't lie about you.";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.useemend.com"),
  title: "Emend",
  description,
  icons: {
    icon: [
      { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/emend-mark.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180" }],
  },
  openGraph: {
    title: "Emend",
    description,
    url: "https://www.useemend.com",
    siteName: "Emend",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Emend",
    description,
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${jetBrainsMono.variable}`}>
      <head>
        {/* set before paint so a saved color scheme never flashes oxblood first */}
        <script dangerouslySetInnerHTML={{ __html: COLOR_SCHEME_INIT_SCRIPT }} />
      </head>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
