// Sam Reyes — the fictional persona the landing page's demo grounds to.
// Source of truth: docs/demo-persona.md. Every sentence and rewrite here
// must trace back to a fact listed there — the "never invent" rule applies
// to our own marketing page too.

export const PERSONA_NAME = "Sam Reyes";
export const PERSONA_CONTACT =
  "(555) 014-2210 · sam.reyes@example.com · github.com/samreyes-demo · samreyes.example.com";

export const PERSONA_EDUCATION_HEADER = {
  title: "Northgate University",
  sub: "B.S. Computer Science",
  dates: "Expected 2027",
};

// A fact is the unit of one resume bullet: exactly one id, shared by all
// three rewrite phrasings (they're different wordings of the same
// confirmed claim, not different claims) — never a comma-joined list.
export type DemoVariant = {
  text: string;
};

export type DemoBullet = {
  source: string;
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

// Education's only content-bearing line is coursework (school/degree/dates
// are metadata, same as an Experience header — never a fact); rendered
// through the same DemoBulletRow as everything else.
export const PERSONA_EDUCATION_COURSEWORK: DemoBullet = {
  source: "EDU-01",
  original: "took classes in OS, data structures, databases, and embedded systems.",
  variants: [
    {
      text: "Coursework: Operating Systems, Data Structures & Algorithms, Databases, Embedded Systems.",
    },
    {
      text: "Relevant coursework: Data Structures & Algorithms, Operating Systems, Databases, Embedded Systems.",
    },
    {
      text: "Studied Operating Systems, Data Structures & Algorithms, Databases, and Embedded Systems.",
    },
  ],
};

// One fact per skill category (matches core's real `skills: dict[str,
// list[str]]` shape), each its own selectable, cyclable line.
export const PERSONA_SKILLS: { label: string; bullet: DemoBullet }[] = [
  {
    label: "Languages",
    bullet: {
      source: "SK-01",
      original: "python, c++, ts, sql, bash",
      variants: [
        { text: "Python, C++, TypeScript, SQL, Bash" },
        { text: "Python · C++ · TypeScript · SQL · Bash" },
        { text: "TypeScript, Python, C++, SQL, Bash" },
      ],
    },
  },
  {
    label: "Frameworks/Libraries",
    bullet: {
      source: "SK-02",
      original: "flask, react, next.js, opencv, numpy, pandas",
      variants: [
        { text: "Flask, React, Next.js, OpenCV, NumPy, Pandas" },
        { text: "Flask · React · Next.js · OpenCV · NumPy · Pandas" },
        { text: "React, Next.js, Flask, NumPy, Pandas, OpenCV" },
      ],
    },
  },
  {
    label: "Systems/Platforms",
    bullet: {
      source: "SK-03",
      original: "linux, docker",
      variants: [
        { text: "Linux, Docker" },
        { text: "Linux · Docker" },
        { text: "Docker, Linux" },
      ],
    },
  },
  {
    label: "Tools/Testing",
    bullet: {
      source: "SK-04",
      original: "git, cmake",
      variants: [
        { text: "Git, CMake" },
        { text: "Git · CMake" },
        { text: "CMake, Git" },
      ],
    },
  },
];

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
            source: "HX-01",
            original: "Writing integration tests in Python for our microservices.",
            variants: [
              {
                text: "Developed 20+ behave integration tests in Python, validating end-to-end message flow across 5 microservices.",
              },
              {
                text: "Built a Gherkin-based integration suite of 20+ scenarios covering cross-service message flow in a Linux environment.",
              },
              {
                text: "Authored 20+ Python integration tests verifying end-to-end behavior across a 5-microservice backend.",
              },
            ],
          },
          {
            source: "HX-02",
            original: "Made scripts to set up the dev environment faster.",
            variants: [
              {
                text: "Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers, cutting setup from ~45 to under 10 minutes.",
              },
              {
                text: "Cut environment setup time from ~45 minutes to under 10 by scripting one-command VM and container provisioning in Bash.",
              },
              {
                text: "Replaced a manual, multi-step environment checklist with one-command Bash automation for VMs and Docker, taking setup from ~45 minutes down to under 10.",
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
            source: "NCS-01",
            original: "Worked on the club website using React.",
            variants: [
              {
                text: "Built and deployed the society's website with Next.js, TypeScript, and Tailwind, creating 15+ reusable components across 4 feature areas.",
              },
              {
                text: "Developed 15+ reusable React components across 4 feature areas for the society's Next.js/TypeScript site.",
              },
              {
                text: "Delivered the society's Next.js website (TypeScript, Tailwind) backed by a library of 15+ reusable components across 4 feature areas.",
              },
            ],
          },
          {
            source: "NCS-02",
            original: "Improved site performance and helped with deploys.",
            variants: [
              {
                text: "Raised the Lighthouse performance score from 62 to 89 and automated build-and-deploy on merge with GitHub Actions.",
              },
              {
                text: "Improved Lighthouse performance 62 → 89 while maintaining CI/CD pipelines (GitHub Actions) through PR-reviewed merges.",
              },
              {
                text: "Set up merge-triggered CI/CD with GitHub Actions and lifted the site's Lighthouse score from 62 to 89.",
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
            source: "LAB-01",
            original: "Programmed sensors for a water monitoring project.",
            variants: [
              {
                text: "Wrote Arduino/C++ firmware integrating 4 water-quality sensors (pH, temperature, turbidity, TDS) with serial telemetry every 2 seconds.",
              },
              {
                text: "Built C++ firmware for a 4-sensor water-monitoring buoy, streaming readings over serial at 2-second intervals.",
              },
              {
                text: "Integrated pH, temperature, turbidity, and TDS sensors into Arduino firmware with 2-second telemetry.",
              },
            ],
          },
          {
            source: "LAB-02",
            original: "Wrote code to detect when the water readings looked wrong.",
            variants: [
              {
                text: "Implemented a composite anomaly score weighting each sensor reading against its safe range to flag water-quality issues.",
              },
              {
                text: "Designed a weighted anomaly-scoring algorithm that evaluates all 4 sensor readings against safe thresholds.",
              },
              {
                text: "Built the anomaly-detection logic: a composite score across sensor channels, each weighted against its safe range.",
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
            source: "LOG-01",
            original: "A website I made to keep track of my flights.",
            variants: [
              {
                text: "Built a Flask + PostgreSQL flight-logging app on a normalized 5-table schema with Alembic migrations.",
              },
              {
                text: "Designed a 5-table relational schema (PostgreSQL, Alembic) powering a Flask app with a flight-stats dashboard.",
              },
              {
                text: "Developed a full-stack flight logger — Flask API, PostgreSQL with versioned migrations, and a stats dashboard.",
              },
            ],
          },
          {
            source: "LOG-02",
            original: "Put the app in Docker and got it running online.",
            variants: [
              { text: "Containerized the app with Docker Compose and deployed it to production." },
              {
                text: "Packaged the full stack into Docker Compose services and shipped a deployed instance.",
              },
              {
                text: "Moved the app from local development to a live deployment using Docker Compose.",
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
            source: "TS-01",
            original: "Detects animals on trail cameras using AI.",
            variants: [
              {
                text: "Ran real-time YOLOv8 wildlife detection on a Jetson Nano, forwarding detections and frames to a Flask dashboard in under 3 seconds.",
              },
              {
                text: "Built an edge-inference pipeline (YOLOv8 on Jetson Nano) pushing detection alerts to a web dashboard in <3s.",
              },
              {
                text: "Deployed YOLOv8 on embedded hardware for real-time detection against simulated trail-camera feeds, with a live Flask dashboard.",
              },
            ],
          },
          {
            source: "TS-02",
            original: "Showed the project at a school event.",
            variants: [
              { text: "Demoed the system live at the campus engineering showcase." },
              { text: "Presented a live end-to-end demo at the university engineering showcase." },
              { text: "Ran a live demonstration of the detection pipeline at the campus showcase." },
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
            source: "PL-01",
            original: "A C++ command line tool for organizing tasks.",
            variants: [
              {
                text: "Developed a C++ CLI task tool (categories, priorities, due dates) structured into 4 modular classes with 25 GoogleTest unit tests.",
              },
              {
                text: "Built a modular C++ command-line organizer — 4 classes, 25 unit tests across 3 GoogleTest suites.",
              },
              {
                text: "Engineered a modular C++ CLI for task management with priorities and due dates, structured into 4 classes and covered by 25 GoogleTest tests.",
              },
            ],
          },
          {
            source: "PL-02",
            original: "Worked on it with some classmates.",
            variants: [
              { text: "Led a 3-member team using GitHub Projects and a CMake build system." },
              { text: "Coordinated a 3-person team via GitHub Projects, owning the CMake build." },
              { text: "Drove planning and delivery for a 3-member team on GitHub Projects." },
            ],
          },
        ],
      },
    ],
  },
];

// Computed, not hardcoded — a hardcoded pill drifts the moment a bullet is
// added or removed (exactly what happened before this was added).
export const DEMO_SENTENCE_COUNT =
  1 + // education coursework
  PERSONA_SKILLS.length +
  DEMO_RESUME.reduce(
    (sum, section) =>
      sum + section.blocks.reduce((blockSum, block) => blockSum + block.bullets.length, 0),
    0
  );

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
  {
    q: "I'm not comfortable putting my resume online. Is this safe?",
    a: "That's a fair instinct. There's no sign-up, so nothing here is tied to your name or email unless your resume itself contains them. Your data sits behind a private, anonymous session tied to your browser, not a public account anyone can look up or browse. It's used only to build your tailored resume.",
  },
];
