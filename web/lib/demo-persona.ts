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
      {
        id: "ncs",
        title: "Web Developer",
        sub: "Northgate CS Society — Riverside, CA",
        dates: "Jan – Mar 2025",
        bullets: [
          {
            sources: ["NCS-01", "NCS-02"],
            original: "Worked on the club website using React.",
            variants: [
              "Built and deployed the society's website with Next.js, TypeScript, and Tailwind, creating 15+ reusable components across 4 feature areas.",
              "Developed 15+ reusable React components across 4 feature areas for the society's Next.js/TypeScript site.",
              "Shipped the club's production website (Next.js, TypeScript, Tailwind) built on a 15-component design system.",
            ],
          },
          {
            sources: ["NCS-03", "NCS-04"],
            original: "Improved site performance and helped with deploys.",
            variants: [
              "Raised the Lighthouse performance score from 62 to 89 and automated build-and-deploy on merge with GitHub Actions.",
              "Improved Lighthouse performance 62 → 89 while maintaining CI/CD pipelines (GitHub Actions) through PR-reviewed merges.",
              "Lifted the site's Lighthouse score 27 points (62 → 89) and set up merge-triggered CI/CD with GitHub Actions.",
            ],
          },
        ],
      },
      {
        id: "lab",
        title: "Undergraduate Research Assistant",
        sub: "University Robotics Lab",
        dates: "Jun – Aug 2024",
        bullets: [
          {
            sources: ["LAB-01", "LAB-02"],
            original: "Programmed sensors for a water monitoring project.",
            variants: [
              "Wrote Arduino/C++ firmware integrating 4 water-quality sensors (pH, temperature, turbidity, TDS) with serial telemetry every 2 seconds.",
              "Built C++ firmware for a 4-sensor water-monitoring buoy, streaming readings over serial at 2-second intervals.",
              "Integrated pH, temperature, turbidity, and TDS sensors into Arduino firmware with 2-second telemetry.",
            ],
          },
          {
            sources: ["LAB-03"],
            original: "Wrote code to detect when the water readings looked wrong.",
            variants: [
              "Implemented a composite anomaly score weighting each sensor reading against its safe range to flag water-quality issues.",
              "Designed a weighted anomaly-scoring algorithm that evaluates all 4 sensor readings against safe thresholds.",
              "Built the anomaly-detection logic: a composite score across sensor channels, each weighted against its safe range.",
            ],
          },
        ],
      },
    ],
  },
  {
    heading: "PROJECTS",
    blocks: [
      {
        id: "log",
        title: "LayoverLog",
        sub: "Flask, PostgreSQL, Docker",
        dates: "",
        bullets: [
          {
            sources: ["LOG-01", "LOG-02"],
            original: "A website I made to keep track of my flights.",
            variants: [
              "Built a Flask + PostgreSQL flight-logging app on a normalized 5-table schema with Alembic migrations.",
              "Designed a 5-table relational schema (PostgreSQL, Alembic) powering a Flask app with a flight-stats dashboard.",
              "Developed a full-stack flight logger — Flask API, PostgreSQL with versioned migrations, and a stats dashboard.",
            ],
          },
          {
            sources: ["LOG-03"],
            original: "Put the app in Docker and got it running online.",
            variants: [
              "Containerized the app with Docker Compose and deployed it to production.",
              "Packaged the full stack into Docker Compose services and shipped a deployed instance.",
              "Deployed the application via a Docker Compose setup covering app and database.",
            ],
          },
        ],
      },
    ],
  },
];
