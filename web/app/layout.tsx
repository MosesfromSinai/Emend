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

export const metadata: Metadata = {
  title: "Emend",
  description: "A tailored resume that can't lie about you.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${jetBrainsMono.variable}`}>
      <head>
        {/* set before paint so a saved color scheme never flashes amber first */}
        <script dangerouslySetInnerHTML={{ __html: COLOR_SCHEME_INIT_SCRIPT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
