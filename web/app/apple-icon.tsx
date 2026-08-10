import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

// Home-screen bookmark icon (iOS "Add to Home Screen") -- same mark as
// icon.tsx, scaled up; Apple ignores rounding/transparency here and applies
// its own corner mask, so this stays a plain filled square.
export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#5c2620",
        }}
      >
        <div
          style={{
            display: "flex",
            fontSize: 120,
            fontWeight: 800,
            color: "#faf8f4",
          }}
        >
          E
        </div>
      </div>
    ),
    { ...size }
  );
}
