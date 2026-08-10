import fs from "node:fs";
import path from "node:path";

import { ImageResponse } from "next/og";

import { DEMO_SENTENCE_COUNT, PERSONA_NAME } from "@/lib/demo-persona";

// Satori (the renderer behind ImageResponse) doesn't support arbitrary
// inline <svg> element trees -- embedding the real mark as a data-URI <img>
// is the documented workaround, and keeps this the same file every other
// surface uses (brand/emend-mark.svg via public/).
const MARK_DATA_URI = `data:image/svg+xml;base64,${fs
  .readFileSync(path.join(process.cwd(), "public/emend-mark.svg"))
  .toString("base64")}`;

export const alt = "Emend — a tailored resume that can't lie about you.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Brand tokens, copied from app/globals.css (--color-paper/ink/em-* under
// the default oxblood scheme) -- Satori renders this in isolation from the
// app's CSS, so the values have to be inlined rather than read from theme.
const PAPER = "#faf8f4";
const INK = "#1c1b18";
const MUTED = "#6b6558";
const ACCENT = "#8a3a30";
const DEEP = "#5c2620";
const SOFT = "#f6e4e0";
const OK_BG = "#eef0e2";
const OK_FG = "#5a6a34";
const PANEL_BG = "#e7ded0";

function FactRow({
  text,
  tag,
  highlighted,
}: {
  text: string;
  tag: string;
  highlighted?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 10,
        marginTop: 8,
        padding: highlighted ? "6px 10px" : "6px 10px",
        borderRadius: 6,
        backgroundColor: highlighted ? SOFT : "transparent",
      }}
    >
      <div style={{ display: "flex", fontSize: 13, color: INK, lineHeight: 1.35 }}>{text}</div>
      <div
        style={{
          display: "flex",
          fontSize: 10.5,
          fontFamily: "monospace",
          color: highlighted ? ACCENT : "#9a927f",
          whiteSpace: "nowrap",
        }}
      >
        {tag}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div
      style={{
        display: "flex",
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: 1,
        color: INK,
        borderBottom: `1px solid ${INK}`,
        paddingBottom: 4,
        marginTop: 18,
        width: "100%",
      }}
    >
      {children}
    </div>
  );
}

export default function Image() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex" }}>
        {/* Left: brand + pitch, mirrors components/landing/hero.tsx */}
        <div
          style={{
            width: "46%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            backgroundColor: PAPER,
            padding: "0 56px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 26,
            }}
          >
            <img src={MARK_DATA_URI} width={72} height={72} alt="" />
            <div
              style={{
                display: "flex",
                fontSize: 64,
                fontWeight: 800,
                color: DEEP,
                letterSpacing: -2,
              }}
            >
              Emend
            </div>
          </div>
          <div
            style={{
              display: "flex",
              marginTop: 30,
              fontSize: 38,
              fontWeight: 700,
              color: INK,
              lineHeight: 1.2,
            }}
          >
            A tailored resume that can&apos;t lie about you.
          </div>
          <div
            style={{
              display: "flex",
              marginTop: 20,
              fontSize: 19,
              color: MUTED,
              lineHeight: 1.45,
            }}
          >
            Paste a job posting. Every line we write traces back to a fact
            you confirmed.
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
            <div
              style={{
                display: "flex",
                fontFamily: "monospace",
                fontSize: 15,
                color: ACCENT,
                backgroundColor: SOFT,
                padding: "8px 16px",
                borderRadius: 999,
              }}
            >
              grounded {DEMO_SENTENCE_COUNT}/{DEMO_SENTENCE_COUNT}
            </div>
            <div
              style={{
                display: "flex",
                fontFamily: "monospace",
                fontSize: 15,
                color: OK_FG,
                backgroundColor: OK_BG,
                padding: "8px 16px",
                borderRadius: 999,
              }}
            >
              LaTeX typeset
            </div>
          </div>
        </div>

        {/* Right: a resume-paper preview using Emend's own fictional demo
            persona (lib/demo-persona.ts) -- never a real user's data in a
            publicly-shared asset. */}
        <div
          style={{
            width: "54%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: PANEL_BG,
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              width: 490,
              backgroundColor: "#ffffff",
              borderRadius: 14,
              padding: "32px 36px",
              transform: "rotate(1.4deg)",
              boxShadow: "0 18px 40px rgba(28,27,24,0.22)",
            }}
          >
            <div style={{ display: "flex", fontSize: 24, fontWeight: 700, color: INK }}>
              {PERSONA_NAME}
            </div>
            <div
              style={{
                display: "flex",
                marginTop: 4,
                fontSize: 11.5,
                fontFamily: "monospace",
                color: MUTED,
              }}
            >
              sam.reyes@example.com · github.com/samreyes-demo
            </div>

            <SectionLabel>EXPERIENCE</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column", marginTop: 10 }}>
              <div style={{ display: "flex", fontSize: 14.5, fontWeight: 700, color: INK }}>
                Software Engineer Intern
              </div>
              <div style={{ display: "flex", fontSize: 12.5, fontStyle: "italic", color: "#3a372f" }}>
                Helix Dynamics — San Diego, CA
              </div>
              <FactRow
                highlighted
                tag="HX-01"
                text="Developed 20+ Python integration tests validating message flow across 5 microservices"
              />
              <FactRow
                tag="HX-02"
                text="Automated dev-environment setup into one-command scripts, cutting setup to under 10 minutes"
              />
            </div>

            <SectionLabel>PROJECTS</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column", marginTop: 10 }}>
              <div style={{ display: "flex", fontSize: 14.5, fontWeight: 700, color: INK }}>
                TrailScout
              </div>
              <div style={{ display: "flex", fontSize: 12.5, fontStyle: "italic", color: "#3a372f" }}>
                Python · YOLOv8 · Jetson Nano
              </div>
              <FactRow
                tag="TS-01"
                text="Deployed real-time wildlife detection at the edge with a live dashboard"
              />
            </div>
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
