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

export const DEMO_RESUME: DemoSection[] = [
  {
    heading: "EXPERIENCE",
    blocks: [
      {
        id: "hx",
        title: "Software Engineer Intern",
        sub: "Helix Dynamics — San Diego, CA",
        dates: "Jun 2026 – Present",
        bullets: [
          {
            sources: ["HX-01"],
            original: "Writing integration tests in Python for our microservices.",
            variants: [
              "Developed 20+ behave integration tests in Python, validating end-to-end message flow across 5 microservices.",
              "Built a Gherkin-based integration suite of 20+ scenarios covering cross-service message flow in a Linux environment.",
              "Authored 20+ Python integration tests verifying end-to-end behavior across a 5-microservice backend.",
            ],
          },
          {
            sources: ["HX-02", "HX-03"],
            original: "Made scripts to set up the dev environment faster.",
            variants: [
              "Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers, cutting setup from ~45 to under 10 minutes.",
              "Reduced new-machine setup time by ~80% by scripting VM and container provisioning behind a single Bash entry point.",
              "Replaced a manual environment checklist with one-command Bash automation for VMs and Docker, saving ~35 minutes per setup.",
            ],
          },
        ],
      },
    ],
  },
];
