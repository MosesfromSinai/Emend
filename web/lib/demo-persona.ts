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

// Sources are per-variant, not per-bullet: two rewrites of the same
// sentence can lean on different (or additional) facts from the same
// block, so each needs its own citation list rather than one shared list.
export type DemoVariant = {
  text: string;
  sources: string[];
};

export type DemoBullet = {
  original: string;
  variants: [DemoVariant, DemoVariant, DemoVariant];
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
            original: "Writing integration tests in Python for our microservices.",
            variants: [
              {
                text: "Developed 20+ behave integration tests in Python, validating end-to-end message flow across 5 microservices.",
                sources: ["HX-01"],
              },
              {
                text: "Built a Gherkin-based integration suite of 20+ scenarios covering cross-service message flow in a Linux environment.",
                sources: ["HX-01"],
              },
              {
                text: "Authored 20+ Python integration tests verifying end-to-end behavior across a 5-microservice backend.",
                sources: ["HX-01"],
              },
            ],
          },
          {
            original: "Made scripts to set up the dev environment faster.",
            variants: [
              {
                text: "Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers, cutting setup from ~45 to under 10 minutes.",
                sources: ["HX-02", "HX-03"],
              },
              {
                text: "Cut environment setup time from ~45 minutes to under 10 by scripting one-command VM and container provisioning in Bash.",
                sources: ["HX-02", "HX-03"],
              },
              {
                text: "Replaced a manual, multi-step environment checklist with one-command Bash automation for VMs and Docker, taking setup from ~45 minutes down to under 10.",
                sources: ["HX-02", "HX-03"],
              },
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
            original: "Worked on the club website using React.",
            variants: [
              {
                text: "Built and deployed the society's website with Next.js, TypeScript, and Tailwind, creating 15+ reusable components across 4 feature areas.",
                sources: ["NCS-01", "NCS-02"],
              },
              {
                text: "Developed 15+ reusable React components across 4 feature areas for the society's Next.js/TypeScript site.",
                sources: ["NCS-01", "NCS-02"],
              },
              {
                text: "Shipped the club's production website in Next.js, TypeScript, and Tailwind, backed by 15+ reusable React components across 4 feature areas.",
                sources: ["NCS-01", "NCS-02"],
              },
            ],
          },
          {
            original: "Improved site performance and helped with deploys.",
            variants: [
              {
                text: "Raised the Lighthouse performance score from 62 to 89 and automated build-and-deploy on merge with GitHub Actions.",
                sources: ["NCS-03", "NCS-04"],
              },
              {
                text: "Improved Lighthouse performance 62 → 89 while maintaining CI/CD pipelines (GitHub Actions) through PR-reviewed merges.",
                sources: ["NCS-03", "NCS-04"],
              },
              {
                text: "Set up merge-triggered CI/CD with GitHub Actions and lifted the site's Lighthouse score from 62 to 89.",
                sources: ["NCS-03", "NCS-04"],
              },
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
            original: "Programmed sensors for a water monitoring project.",
            variants: [
              {
                text: "Wrote Arduino/C++ firmware integrating 4 water-quality sensors (pH, temperature, turbidity, TDS) with serial telemetry every 2 seconds.",
                sources: ["LAB-01", "LAB-02"],
              },
              {
                text: "Built C++ firmware for a 4-sensor water-monitoring buoy, streaming readings over serial at 2-second intervals.",
                sources: ["LAB-01", "LAB-02"],
              },
              {
                text: "Integrated pH, temperature, turbidity, and TDS sensors into Arduino firmware with 2-second telemetry.",
                sources: ["LAB-01", "LAB-02"],
              },
            ],
          },
          {
            original: "Wrote code to detect when the water readings looked wrong.",
            variants: [
              {
                text: "Implemented a composite anomaly score weighting each sensor reading against its safe range to flag water-quality issues.",
                sources: ["LAB-01", "LAB-03"],
              },
              {
                text: "Designed a weighted anomaly-scoring algorithm that evaluates all 4 sensor readings against safe thresholds.",
                sources: ["LAB-01", "LAB-03"],
              },
              {
                text: "Built the anomaly-detection logic: a composite score across sensor channels, each weighted against its safe range.",
                sources: ["LAB-03"],
              },
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
            original: "A website I made to keep track of my flights.",
            variants: [
              {
                text: "Built a Flask + PostgreSQL flight-logging app on a normalized 5-table schema with Alembic migrations.",
                sources: ["LOG-01", "LOG-02"],
              },
              {
                text: "Designed a 5-table relational schema (PostgreSQL, Alembic) powering a Flask app with a flight-stats dashboard.",
                sources: ["LOG-01", "LOG-02"],
              },
              {
                text: "Developed a full-stack flight logger — Flask API, PostgreSQL with versioned migrations, and a stats dashboard.",
                sources: ["LOG-01", "LOG-02"],
              },
            ],
          },
          {
            original: "Put the app in Docker and got it running online.",
            variants: [
              {
                text: "Containerized the app with Docker Compose and deployed it to production.",
                sources: ["LOG-03"],
              },
              {
                text: "Packaged the full stack into Docker Compose services and shipped a deployed instance.",
                sources: ["LOG-03"],
              },
              {
                text: "Used Docker Compose to containerize and deploy the app end to end.",
                sources: ["LOG-03"],
              },
            ],
          },
        ],
      },
      {
        id: "ts",
        title: "TrailScout",
        sub: "Python, YOLOv8, Jetson Nano",
        dates: "",
        bullets: [
          {
            original: "Detects animals on trail cameras using AI.",
            variants: [
              {
                text: "Ran real-time YOLOv8 wildlife detection on a Jetson Nano, forwarding detections and frames to a Flask dashboard in under 3 seconds.",
                sources: ["TS-01", "TS-02"],
              },
              {
                text: "Built an edge-inference pipeline (YOLOv8 on Jetson Nano) pushing detection alerts to a web dashboard in <3s.",
                sources: ["TS-01", "TS-02"],
              },
              {
                text: "Deployed YOLOv8 on embedded hardware for real-time detection against simulated trail-camera feeds, with a live Flask dashboard.",
                sources: ["TS-01", "TS-02"],
              },
            ],
          },
          {
            original: "Showed the project at a school event.",
            variants: [
              {
                text: "Demoed the system live at the campus engineering showcase.",
                sources: ["TS-03"],
              },
              {
                text: "Presented a live end-to-end demo at the university engineering showcase.",
                sources: ["TS-03"],
              },
              {
                text: "Ran a live demonstration of the detection pipeline at the campus showcase.",
                sources: ["TS-03"],
              },
            ],
          },
        ],
      },
      {
        id: "pl",
        title: "PackList",
        sub: "C++, CMake, GoogleTest",
        dates: "",
        bullets: [
          {
            original: "A C++ command line tool for organizing tasks.",
            variants: [
              {
                text: "Developed a C++ CLI task tool (categories, priorities, due dates) structured into 4 modular classes with 25 GoogleTest unit tests.",
                sources: ["PL-01", "PL-02"],
              },
              {
                text: "Built a modular C++ command-line organizer — 4 classes, 25 unit tests across 3 GoogleTest suites.",
                sources: ["PL-01", "PL-02"],
              },
              {
                text: "Engineered a C++/CMake CLI for task management with priorities and due dates, covered by 25 GoogleTest tests.",
                sources: ["PL-01", "PL-02", "PL-03"],
              },
            ],
          },
          {
            original: "Worked on it with some classmates.",
            variants: [
              {
                text: "Led a 3-member team using GitHub Projects and a CMake build system.",
                sources: ["PL-03"],
              },
              {
                text: "Coordinated a 3-person team via GitHub Projects, owning the CMake build.",
                sources: ["PL-03"],
              },
              {
                text: "Drove planning and delivery for a 3-member team on GitHub Projects.",
                sources: ["PL-03"],
              },
            ],
          },
        ],
      },
    ],
  },
];

export type FaqItem = { q: string; a: string };

export const DEMO_FAQS: FaqItem[] = [
  {
    q: "How is this different from ChatGPT writing my resume?",
    a: "Free-form AI can invent experience you never had. Emend is structured: the writer's only input is the fact list you confirmed, and every output line is tagged with its source fact. If a line has no source, it doesn't ship.",
  },
  {
    q: "Will it pass applicant tracking systems (ATS)?",
    a: "Yes. The LaTeX templates are single-column, standard-heading layouts that parse cleanly in major ATS platforms — and the keyword matching is built around what those systems scan for.",
  },
  {
    q: "Do I need to know LaTeX?",
    a: "No. You get a finished PDF with one click. The .tex source is included for people who want it — your resume is yours to keep and edit anywhere.",
  },
  {
    q: "What if I don't like a rewritten sentence?",
    a: "Every sentence is interactive: cycle through three grounded rewrites, edit the words in place, or revert to your original phrasing for that line. You approve everything before it exports.",
  },
];
