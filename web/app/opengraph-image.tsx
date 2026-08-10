import { ImageResponse } from "next/og";

export const alt = "Emend — a tailored resume that can't lie about you.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#faf6f0",
          fontFamily: "Georgia, serif",
        }}
      >
        <div
          style={{
            fontSize: 160,
            fontWeight: 700,
            color: "#5c2620",
            letterSpacing: -4,
            display: "flex",
          }}
        >
          Emend
        </div>
        <div
          style={{
            marginTop: 24,
            fontSize: 34,
            color: "#8a3a30",
            display: "flex",
          }}
        >
          A tailored resume that can&apos;t lie about you.
        </div>
      </div>
    ),
    { ...size }
  );
}
