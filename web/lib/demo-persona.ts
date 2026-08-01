// Sam Reyes — the fictional persona the landing page's demo grounds to.
// Source of truth: docs/demo-persona.md. Every sentence and rewrite here
// must trace back to a fact listed there — the "never invent" rule applies
// to our own marketing page too.

export const PERSONA_NAME = "Sam Reyes";
export const PERSONA_CONTACT =
  "(555) 014-2210 · sam.reyes@example.com · github.com/samreyes-demo · samreyes.example.com";

export const PERSONA_EDUCATION = {
  title: "Northgate University",
  sub: "B.S. Computer Science",
  dates: "Expected 2027",
  text: "Coursework: Operating Systems, Data Structures & Algorithms, Databases, Embedded Systems.",
};

export const PERSONA_SKILLS =
  "Languages: Python, C++, TypeScript, SQL, Bash · Frameworks: Flask, React, Next.js · Tools: Linux, Git, Docker, CMake · Libraries: OpenCV, NumPy, Pandas";

export type DemoBullet = {
  sources: string[];
  original: string;
  variants: [string, string, string];
};

export type DemoBlock = {
  id: string;
  title: string;
  sub: string;
  dates: string;
  bullets: DemoBullet[];
};

export type DemoSection = {
  heading: string;
  blocks: DemoBlock[];
};
