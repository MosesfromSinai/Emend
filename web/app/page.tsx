import { LandingNav } from "@/components/landing/nav";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { SentenceDemo } from "@/components/landing/sentence-demo";
import { WhatItIs } from "@/components/landing/what-it-is";
import { Faq } from "@/components/landing/faq";
import { CtaBand } from "@/components/landing/cta-band";

export default function Home() {
  return (
    <main>
      <LandingNav />
      <Hero />
      <HowItWorks />
      <SentenceDemo />
      <WhatItIs />
      <Faq />
      <CtaBand />
    </main>
  );
}
