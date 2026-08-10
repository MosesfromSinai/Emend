import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Emend",
    short_name: "Emend",
    description: "A tailored resume that can't lie about you.",
    start_url: "/",
    display: "standalone",
    background_color: "#faf8f4",
    theme_color: "#5c2620",
    icons: [
      { src: "/emend-mark-192.png", sizes: "192x192", type: "image/png" },
      { src: "/emend-mark-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
