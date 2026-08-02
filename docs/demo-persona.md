# Emend Demo Persona — Sam Reyes (`docs/demo-persona.md`)

**Purpose.** This file is the single source of truth for every sentence shown in the landing page's "Every sentence, your call" demo and the hero product mock. The persona is **fictional**; the resume mirrors the shape of the original design content so the existing demo layout ports 1:1 (Helix Dynamics ↔ the defense internship block, Northgate CS Society ↔ the campus web block, Robotics Lab ↔ the embedded block, LayoverLog / TrailScout / PackList ↔ the three project blocks).

**Rules.**
- Every demo sentence and every rewrite must trace to fact ids below — the site's "never invent" convention applies to its own marketing. Sources are tracked per rewrite, not per sentence: two rewrites of the same line can cite different (or additional) facts from the same block.
- No derived numbers: a rewrite may not contain a percentage, delta, or subtraction computed from a fact's stated values — only the numbers as they literally appear in the cited fact. Per the brief's "Grounding design" rule, this must hold for the real product's tailor output too, not just the demo.
- Numbers are deliberately modest-realistic, not impressive-fake.
- Contact details and handles are placeholders — do not swap in real domains or accounts.
- To change demo copy: add or edit a fact here first, then update the sentence. Keep the "grounded n/n" pill equal to the number of demo sentences actually shipped (currently **12/12**).

---

## Persona header

**Sam Reyes** · (555) 014-2210 · sam.reyes@example.com · github.com/samreyes-demo · samreyes.example.com · U.S. work-authorized

**Education (EDU-01):** Northgate University — B.S. Computer Science, expected 2027. Coursework: Operating Systems, Data Structures & Algorithms, Databases, Embedded Systems.

**Skills (SKL-01):** Languages: Python, C++, TypeScript, SQL, Bash · Frameworks: Flask, React, Next.js · Tools: Linux, Git, Docker, CMake · Libraries: OpenCV, NumPy, Pandas

---

## Fact list

**Helix Dynamics — Software Engineer Intern (Jun 2026 – Present, San Diego, CA)**
- `HX-01` — Wrote 20+ behave (Gherkin) integration tests in Python validating end-to-end message flow across 5 microservices in a Linux environment
- `HX-02` — Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers
- `HX-03` — Environment setup time dropped from ~45 minutes to under 10
- `HX-04` — Documented the environment and test workflow on the team wiki

**Northgate CS Society — Web Developer (Jan – Mar 2025)**
- `NCS-01` — Built and deployed the society's website with Next.js, TypeScript, and Tailwind CSS
- `NCS-02` — Created 15+ reusable React components across 4 feature areas
- `NCS-03` — Raised the Lighthouse performance score from 62 to 89
- `NCS-04` — Set up GitHub Actions CI/CD (build + deploy on merge) and worked through PR code reviews

**University Robotics Lab — Undergraduate Research Assistant (Jun – Aug 2024)**
- `LAB-01` — Wrote Arduino/C++ firmware for a water-monitoring buoy integrating 4 sensors (pH, temperature, turbidity, TDS)
- `LAB-02` — Streamed serial telemetry from all sensors every 2 seconds
- `LAB-03` — Implemented a composite anomaly score weighting each reading against its safe range

**LayoverLog** | Flask, PostgreSQL, Docker
- `LOG-01` — Built a Flask + PostgreSQL web app for logging flights with a stats dashboard
- `LOG-02` — Designed a normalized 5-table schema with Alembic migrations
- `LOG-03` — Containerized the app with Docker Compose and deployed it

**TrailScout** | Python, YOLOv8, Jetson Nano
- `TS-01` — Ran real-time YOLOv8 wildlife detection on a Jetson Nano against simulated trail-camera feeds
- `TS-02` — Forwarded detections and frames to a Flask dashboard in under 3 seconds
- `TS-03` — Demoed the system live at the campus engineering showcase

**PackList** | C++, CMake, GoogleTest
- `PL-01` — Developed a C++ CLI task/packing tool with categories, priorities, and due dates
- `PL-02` — Structured it into 4 modular classes with 25 GoogleTest unit tests across 3 suites
- `PL-03` — Led a 3-member team using GitHub Projects and a CMake build

---

## Demo sentences (original + 3 grounded rewrites each)

### Helix Dynamics

**HX-A** — sources: `HX-01`
- original: "Writing integration tests in Python for our microservices."
- rewrite 1: "Developed 20+ behave integration tests in Python, validating end-to-end message flow across 5 microservices."
- rewrite 2: "Built a Gherkin-based integration suite of 20+ scenarios covering cross-service message flow in a Linux environment."
- rewrite 3: "Authored 20+ Python integration tests verifying end-to-end behavior across a 5-microservice backend."

**HX-B** — sources: `HX-02`, `HX-03` (all three rewrites)
- original: "Made scripts to set up the dev environment faster."
- rewrite 1: "Automated a multi-step dev-environment setup into one-command Bash scripts managing VMs and Docker containers, cutting setup from ~45 to under 10 minutes."
- rewrite 2: "Cut environment setup time from ~45 minutes to under 10 by scripting one-command VM and container provisioning in Bash."
- rewrite 3: "Replaced a manual, multi-step environment checklist with one-command Bash automation for VMs and Docker, taking setup from ~45 minutes down to under 10."

### Northgate CS Society

**NCS-A** — sources: `NCS-01`, `NCS-02` (all three rewrites)
- original: "Worked on the club website using React."
- rewrite 1: "Built and deployed the society's website with Next.js, TypeScript, and Tailwind, creating 15+ reusable components across 4 feature areas."
- rewrite 2: "Developed 15+ reusable React components across 4 feature areas for the society's Next.js/TypeScript site."
- rewrite 3: "Delivered the society's Next.js website (TypeScript, Tailwind) backed by a library of 15+ reusable components across 4 feature areas."

**NCS-B** — sources: `NCS-03`, `NCS-04` (all three rewrites)
- original: "Improved site performance and helped with deploys."
- rewrite 1: "Raised the Lighthouse performance score from 62 to 89 and automated build-and-deploy on merge with GitHub Actions."
- rewrite 2: "Improved Lighthouse performance 62 → 89 while maintaining CI/CD pipelines (GitHub Actions) through PR-reviewed merges."
- rewrite 3: "Set up merge-triggered CI/CD with GitHub Actions and lifted the site's Lighthouse score from 62 to 89."

### University Robotics Lab

**LAB-A** — sources: `LAB-01`, `LAB-02`
- original: "Programmed sensors for a water monitoring project."
- rewrite 1: "Wrote Arduino/C++ firmware integrating 4 water-quality sensors (pH, temperature, turbidity, TDS) with serial telemetry every 2 seconds."
- rewrite 2: "Built C++ firmware for a 4-sensor water-monitoring buoy, streaming readings over serial at 2-second intervals."
- rewrite 3: "Integrated pH, temperature, turbidity, and TDS sensors into Arduino firmware with 2-second telemetry."

**LAB-B** — sources vary by rewrite: `LAB-01` supplies the "water-quality" framing (r1) and the sensor count "4" (r2), neither of which is in `LAB-03` alone.
- original: "Wrote code to detect when the water readings looked wrong."
- rewrite 1: "Implemented a composite anomaly score weighting each sensor reading against its safe range to flag water-quality issues." — sources: `LAB-01`, `LAB-03`
- rewrite 2: "Designed a weighted anomaly-scoring algorithm that evaluates all 4 sensor readings against safe thresholds." — sources: `LAB-01`, `LAB-03`
- rewrite 3: "Built the anomaly-detection logic: a composite score across sensor channels, each weighted against its safe range." — sources: `LAB-03`

### LayoverLog

**LOG-A** — sources: `LOG-01`, `LOG-02`
- original: "A website I made to keep track of my flights."
- rewrite 1: "Built a Flask + PostgreSQL flight-logging app on a normalized 5-table schema with Alembic migrations."
- rewrite 2: "Designed a 5-table relational schema (PostgreSQL, Alembic) powering a Flask app with a flight-stats dashboard."
- rewrite 3: "Developed a full-stack flight logger — Flask API, PostgreSQL with versioned migrations, and a stats dashboard."

**LOG-B** — sources: `LOG-03` (all three rewrites)
- original: "Put the app in Docker and got it running online."
- rewrite 1: "Containerized the app with Docker Compose and deployed it to production."
- rewrite 2: "Packaged the full stack into Docker Compose services and shipped a deployed instance."
- rewrite 3: "Moved the app from local development to a live deployment using Docker Compose."

### TrailScout

**TS-A** — sources: `TS-01`, `TS-02`
- original: "Detects animals on trail cameras using AI."
- rewrite 1: "Ran real-time YOLOv8 wildlife detection on a Jetson Nano, forwarding detections and frames to a Flask dashboard in under 3 seconds."
- rewrite 2: "Built an edge-inference pipeline (YOLOv8 on Jetson Nano) pushing detection alerts to a web dashboard in <3s."
- rewrite 3: "Deployed YOLOv8 on embedded hardware for real-time detection against simulated trail-camera feeds, with a live Flask dashboard."

**TS-B** — sources: `TS-03`
- original: "Showed the project at a school event."
- rewrite 1: "Demoed the system live at the campus engineering showcase."
- rewrite 2: "Presented a live end-to-end demo at the university engineering showcase."
- rewrite 3: "Ran a live demonstration of the detection pipeline at the campus showcase."

### PackList

**PL-A** — sources: `PL-01`, `PL-02` (rewrites 1–2); rewrite 3 also cites `PL-03`, which is where "CMake" comes from.
- original: "A C++ command line tool for organizing tasks."
- rewrite 1: "Developed a C++ CLI task tool (categories, priorities, due dates) structured into 4 modular classes with 25 GoogleTest unit tests." — sources: `PL-01`, `PL-02`
- rewrite 2: "Built a modular C++ command-line organizer — 4 classes, 25 unit tests across 3 GoogleTest suites." — sources: `PL-01`, `PL-02`
- rewrite 3: "Engineered a C++/CMake CLI for task management with priorities and due dates, covered by 25 GoogleTest tests." — sources: `PL-01`, `PL-02`, `PL-03`

**PL-B** — sources: `PL-03`
- original: "Worked on it with some classmates."
- rewrite 1: "Led a 3-member team using GitHub Projects and a CMake build system."
- rewrite 2: "Coordinated a 3-person team via GitHub Projects, owning the CMake build."
- rewrite 3: "Drove planning and delivery for a 3-member team on GitHub Projects."

---

## Porting notes for Workflow D

- Swap all demo blocks and the hero mock's floating fact tags to the entities and ids above; the hero's "grounded 18/18" pill becomes **12/12** (or the shipped count).
- The demo toolbar label example becomes "your edit · based on fact HX-01".
- Remove the meta "Emend" resume entry from the old design content; LayoverLog fills that slot (and adds database flavor to the persona).
- The real resume PDF in `uploads/` is no longer referenced by any public page — it remains a private eval fixture for Workflow A.
