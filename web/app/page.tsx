import { LandingNav } from "@/components/landing/nav";
import { Hero } from "@/components/landing/hero";
import { ProofStrip } from "@/components/landing/proof-strip";
import { HowItWorks } from "@/components/landing/how-it-works";
import { SentenceDemo } from "@/components/landing/sentence-demo";
import { WhatItIs } from "@/components/landing/what-it-is";
import { Faq } from "@/components/landing/faq";
import { CtaBand } from "@/components/landing/cta-band";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <main>
      <LandingNav />
      <Hero />
      <ProofStrip />
      <HowItWorks />
      <SentenceDemo />
      <WhatItIs />
      <Faq />
      <CtaBand />
      <Footer />
    </main>
  );
}
