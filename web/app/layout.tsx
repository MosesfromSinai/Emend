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
  metadataBase: new URL("https://emend-two.vercel.app"),
  title: "Emend",
  description,
  openGraph: {
    title: "Emend",
    description,
    url: "https://emend-two.vercel.app",
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
      <body>{children}</body>
    </html>
  );
}
