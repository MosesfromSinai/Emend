// Ink & Paper ships four color schemes (00-project-brief.md "Theming/tweaks
// to preserve"). Amber is the default and needs no data attribute; the other
// three set data-scheme on <html>, which app/globals.css maps to --em-* vars.
export const COLOR_SCHEMES = ["amber", "teal", "oxblood", "forest"] as const;
export type ColorScheme = (typeof COLOR_SCHEMES)[number];

const STORAGE_KEY = "emend-color-scheme";

export function isColorScheme(value: string | null): value is ColorScheme {
  return !!value && (COLOR_SCHEMES as readonly string[]).includes(value);
}

export function applyColorScheme(scheme: ColorScheme) {
  if (scheme === "amber") {
    document.documentElement.removeAttribute("data-scheme");
  } else {
    document.documentElement.setAttribute("data-scheme", scheme);
  }
  window.localStorage.setItem(STORAGE_KEY, scheme);
}

// Inline script string, run before hydration to avoid a flash of the wrong
// scheme. Kept as a template string (not a .ts import) so it can be dropped
// into a <script dangerouslySetInnerHTML> in the root layout.
export const COLOR_SCHEME_INIT_SCRIPT = `
(function () {
  try {
    var v = window.localStorage.getItem("${STORAGE_KEY}");
    if (v && v !== "amber") document.documentElement.setAttribute("data-scheme", v);
  } catch (e) {}
})();
`;
