import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

// Browser-tab favicon -- a simple mark, not the full wordmark, since
// "Emend" reads as noise at 16-32px. Same oxblood/paper brand pair as the
// OG image's accent square, just carrying the initial instead.
export default function Icon() {
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
          borderRadius: 7,
        }}
      >
        <div
          style={{
            display: "flex",
            fontSize: 22,
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
