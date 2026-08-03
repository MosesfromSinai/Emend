# Emend Demo Persona — Sam Reyes (`docs/demo-persona.md`)

**Purpose.** This file is the single source of truth for every sentence shown in the landing page's "Every sentence, your call" demo and the hero product mock. The persona is **fictional**; the resume mirrors the shape of the original design content so the existing demo layout ports 1:1 (Helix Dynamics ↔ the defense internship block, Northgate CS Society ↔ the campus web block, Robotics Lab ↔ the embedded block, LayoverLog / TrailScout / PackList ↔ the three project blocks).

**Rules.**
- **One fact per bullet, no exceptions.** A fact id is used by exactly one bullet, and it's shared by all three of that bullet's rewrite phrasings — they're different wordings of the same confirmed claim, never different claims. Never a comma-joined fact list (`% HX-02, HX-03`) on a single bullet. The fact's own text carries the *complete* claim, metric included, even when that means folding what used to be two separate facts into one.
- No derived numbers: a rewrite may not contain a percentage, delta, or subtraction computed from a fact's stated values — only the numbers as they literally appear in the cited fact. Per the brief's "Grounding design" rule, this must hold for the real product's tailor output too, not just the demo.
- Numbers are deliberately modest-realistic, not impressive-fake.
- Contact details and handles are placeholders — do not swap in real domains or accounts.
- Education's coursework line and each Technical Skills category are also single facts, one per line, cyclable exactly like an experience/project bullet.
- To change demo copy: add or edit a fact here first, then update the sentence. Keep the "grounded n/n" pill equal to the number of demo sentences actually shipped (currently **17/17**).

---

## Persona header

**Sam Reyes** · (555) 014-2210 · sam.reyes@example.com · github.com/samreyes-demo · samreyes.example.com · U.S. work-authorized

**Education:** Northgate University — B.S. Computer Science, expected 2027. Coursework is its own fact (`EDU-01`) — the school/degree/dates line above it is metadata, same as an Experience header, never a fact.

**Skills:** four categories, each its own fact — `SK-01` Languages, `SK-02` Frameworks/Libraries, `SK-03` Systems/Platforms, `SK-04` Tools/Testing. Matches core's real `skills: dict[str, list[str]]` shape (one category = one row), not one run-on paragraph.

---

## Fact list

**Education**
- `EDU-01` — Coursework: Operating Systems, Data Structures & Algorithms, Databases, Embedded Systems

**Skills**
- `SK-01` (Languages) — Python, C++, TypeScript, SQL, Bash
- `SK-02` (Frameworks/Libraries) — Flask, React, Next.js, OpenCV, NumPy, Pandas
- `SK-03` (Systems/Platforms) — Linux, Docker
- `SK-04` (Tools/Testing) — Git, CMake

**Helix Dynamics — Software Engineer Intern (Jun 2026 – Present, San Diego, CA)**
- `HX-01` — Wrote 20+ behave (Gherkin) integration tests in Python validating end-to-end message flow across 5 microservices in a Linux environment
- `HX-02` — Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers, cutting setup time from ~45 minutes to under 10
- `HX-03` — Documented the environment and test workflow on the team wiki (not currently cited by a demo sentence)

**Northgate CS Society — Web Developer (Jan – Mar 2025)**
- `NCS-01` — Built and deployed the society's website with Next.js, TypeScript, and Tailwind CSS, including 15+ reusable components across 4 feature areas
- `NCS-02` — Raised the Lighthouse performance score from 62 to 89 and set up GitHub Actions CI/CD (build + deploy on merge) through PR-reviewed merges

**University Robotics Lab — Undergraduate Research Assistant (Jun – Aug 2024)**
- `LAB-01` — Wrote Arduino/C++ firmware integrating 4 water-quality sensors (pH, temperature, turbidity, TDS) with serial telemetry every 2 seconds
- `LAB-02` — Implemented a composite anomaly-scoring algorithm evaluating all 4 water-quality sensor readings against their safe ranges to flag issues

**LayoverLog** | Flask, PostgreSQL, Docker
- `LOG-01` — Built a Flask + PostgreSQL flight-logging app on a normalized 5-table schema with Alembic migrations and a stats dashboard
- `LOG-02` — Containerized the app with Docker Compose and deployed it

**TrailScout** | Python, YOLOv8, Jetson Nano
- `TS-01` — Ran real-time YOLOv8 wildlife detection on a Jetson Nano against simulated trail-camera feeds, forwarding detections and frames to a Flask dashboard in under 3 seconds
- `TS-02` — Demoed the system live at the campus engineering showcase

**PackList** | C++, CMake, GoogleTest
- `PL-01` — Developed a modular C++ CLI task/packing tool (categories, priorities, due dates) structured into 4 classes with 25 GoogleTest unit tests across 3 suites
- `PL-02` — Led a 3-member team using GitHub Projects and a CMake build

---

## Demo sentences (original + 3 grounded rewrites each)

### Education

**EDU-A** — source: `EDU-01`
- original: "took classes in OS, data structures, databases, and embedded systems."
- rewrite 1: "Coursework: Operating Systems, Data Structures & Algorithms, Databases, Embedded Systems."
- rewrite 2: "Relevant coursework: Data Structures & Algorithms, Operating Systems, Databases, Embedded Systems."
- rewrite 3: "Studied Operating Systems, Data Structures & Algorithms, Databases, and Embedded Systems."

### Skills

**SK-A (Languages)** — source: `SK-01`
- original: "python, c++, ts, sql, bash"
- rewrite 1: "Python, C++, TypeScript, SQL, Bash"
- rewrite 2: "Python · C++ · TypeScript · SQL · Bash"
- rewrite 3: "TypeScript, Python, C++, SQL, Bash"

**SK-B (Frameworks/Libraries)** — source: `SK-02`
- original: "flask, react, next.js, opencv, numpy, pandas"
- rewrite 1: "Flask, React, Next.js, OpenCV, NumPy, Pandas"
- rewrite 2: "Flask · React · Next.js · OpenCV · NumPy · Pandas"
- rewrite 3: "React, Next.js, Flask, NumPy, Pandas, OpenCV"

**SK-C (Systems/Platforms)** — source: `SK-03`
- original: "linux, docker"
- rewrite 1: "Linux, Docker"
- rewrite 2: "Linux · Docker"
- rewrite 3: "Docker, Linux"

**SK-D (Tools/Testing)** — source: `SK-04`
- original: "git, cmake"
- rewrite 1: "Git, CMake"
- rewrite 2: "Git · CMake"
- rewrite 3: "CMake, Git"

### Helix Dynamics

**HX-A** — source: `HX-01`
- original: "Writing integration tests in Python for our microservices."
- rewrite 1: "Developed 20+ behave integration tests in Python, validating end-to-end message flow across 5 microservices."
- rewrite 2: "Built a Gherkin-based integration suite of 20+ scenarios covering cross-service message flow in a Linux environment."
- rewrite 3: "Authored 20+ Python integration tests verifying end-to-end behavior across a 5-microservice backend."

**HX-B** — source: `HX-02`
- original: "Made scripts to set up the dev environment faster."
- rewrite 1: "Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers, cutting setup from ~45 to under 10 minutes."
- rewrite 2: "Cut environment setup time from ~45 minutes to under 10 by scripting one-command VM and container provisioning in Bash."
- rewrite 3: "Replaced a manual, multi-step environment checklist with one-command Bash automation for VMs and Docker, taking setup from ~45 minutes down to under 10."

### Northgate CS Society

**NCS-A** — source: `NCS-01`
- original: "Worked on the club website using React."
- rewrite 1: "Built and deployed the society's website with Next.js, TypeScript, and Tailwind, creating 15+ reusable components across 4 feature areas."
- rewrite 2: "Developed 15+ reusable React components across 4 feature areas for the society's Next.js/TypeScript site."
- rewrite 3: "Delivered the society's Next.js website (TypeScript, Tailwind) backed by a library of 15+ reusable components across 4 feature areas."

**NCS-B** — source: `NCS-02`
- original: "Improved site performance and helped with deploys."
- rewrite 1: "Raised the Lighthouse performance score from 62 to 89 and automated build-and-deploy on merge with GitHub Actions."
- rewrite 2: "Improved Lighthouse performance 62 → 89 while maintaining CI/CD pipelines (GitHub Actions) through PR-reviewed merges."
- rewrite 3: "Set up merge-triggered CI/CD with GitHub Actions and lifted the site's Lighthouse score from 62 to 89."

### University Robotics Lab

**LAB-A** — source: `LAB-01`
- original: "Programmed sensors for a water monitoring project."
- rewrite 1: "Wrote Arduino/C++ firmware integrating 4 water-quality sensors (pH, temperature, turbidity, TDS) with serial telemetry every 2 seconds."
- rewrite 2: "Built C++ firmware for a 4-sensor water-monitoring buoy, streaming readings over serial at 2-second intervals."
- rewrite 3: "Integrated pH, temperature, turbidity, and TDS sensors into Arduino firmware with 2-second telemetry."

**LAB-B** — source: `LAB-02`
- original: "Wrote code to detect when the water readings looked wrong."
- rewrite 1: "Implemented a composite anomaly score weighting each sensor reading against its safe range to flag water-quality issues."
- rewrite 2: "Designed a weighted anomaly-scoring algorithm that evaluates all 4 sensor readings against safe thresholds."
- rewrite 3: "Built the anomaly-detection logic: a composite score across sensor channels, each weighted against its safe range."

### LayoverLog

**LOG-A** — source: `LOG-01`
- original: "A website I made to keep track of my flights."
- rewrite 1: "Built a Flask + PostgreSQL flight-logging app on a normalized 5-table schema with Alembic migrations."
- rewrite 2: "Designed a 5-table relational schema (PostgreSQL, Alembic) powering a Flask app with a flight-stats dashboard."
- rewrite 3: "Developed a full-stack flight logger — Flask API, PostgreSQL with versioned migrations, and a stats dashboard."

**LOG-B** — source: `LOG-02`
- original: "Put the app in Docker and got it running online."
- rewrite 1: "Containerized the app with Docker Compose and deployed it to production."
- rewrite 2: "Packaged the full stack into Docker Compose services and shipped a deployed instance."
- rewrite 3: "Moved the app from local development to a live deployment using Docker Compose."

### TrailScout

**TS-A** — source: `TS-01`
- original: "Detects animals on trail cameras using AI."
- rewrite 1: "Ran real-time YOLOv8 wildlife detection on a Jetson Nano, forwarding detections and frames to a Flask dashboard in under 3 seconds."
- rewrite 2: "Built an edge-inference pipeline (YOLOv8 on Jetson Nano) pushing detection alerts to a web dashboard in <3s."
- rewrite 3: "Deployed YOLOv8 on embedded hardware for real-time detection against simulated trail-camera feeds, with a live Flask dashboard."

**TS-B** — source: `TS-02`
- original: "Showed the project at a school event."
- rewrite 1: "Demoed the system live at the campus engineering showcase."
- rewrite 2: "Presented a live end-to-end demo at the university engineering showcase."
- rewrite 3: "Ran a live demonstration of the detection pipeline at the campus showcase."

### PackList

**PL-A** — source: `PL-01`
- original: "A C++ command line tool for organizing tasks."
- rewrite 1: "Developed a C++ CLI task tool (categories, priorities, due dates) structured into 4 modular classes with 25 GoogleTest unit tests."
- rewrite 2: "Built a modular C++ command-line organizer — 4 classes, 25 unit tests across 3 GoogleTest suites."
- rewrite 3: "Engineered a modular C++ CLI for task management with priorities and due dates, structured into 4 classes and covered by 25 GoogleTest tests."

**PL-B** — source: `PL-02`
- original: "Worked on it with some classmates."
- rewrite 1: "Led a 3-member team using GitHub Projects and a CMake build system."
- rewrite 2: "Coordinated a 3-person team via GitHub Projects, owning the CMake build."
- rewrite 3: "Drove planning and delivery for a 3-member team on GitHub Projects."

---

## Porting notes for Workflow D

- Swap all demo blocks and the hero mock's floating fact tags to the entities and ids above; the hero's grounded pill is **17/17** (or the shipped count — recompute if the sentence count changes).
- The demo toolbar label example becomes "your edit · based on fact HX-01".
- Remove the meta "Emend" resume entry from the old design content; LayoverLog fills that slot (and adds database flavor to the persona).
- The real resume PDF in `uploads/` is no longer referenced by any public page — it remains a private eval fixture for Workflow A.
