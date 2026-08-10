// Two interlocked proofreader's carets: the first dotted (the original, a
// faint trace), the second solid oxblood (the emended line). See
// brand/README.md for the full mark system (favicons, tiles, dark variant).
// Never recolor the solid caret off oxblood, and never make the dotted
// caret solid -- the contrast between the two is the logo.
export function EmendMark({ size = 28 }: { size?: number }) {
  const small = size < 24;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" role="img" aria-label="Emend">
      <polyline
        points={small ? "2,22 11,10.5 20,22" : "2,22 11,10 20,22"}
        fill="none"
        stroke={small ? "#c9917f" : "#cc9a8e"}
        strokeWidth={small ? 3.4 : 3}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={small ? "0.1 3.9" : "0.1 4.6"}
      />
      <polyline
        points={small ? "12,22 21,10.5 30,22" : "12,22 21,10 30,22"}
        fill="none"
        stroke="#8a3a30"
        strokeWidth={small ? 3.8 : 3.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function EmendLockup() {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 11 }}>
      <EmendMark size={28} />
      <span
        style={{
          font: "600 25px 'Source Serif 4', Georgia, serif",
          color: "#1c1b18",
          letterSpacing: "-0.01em",
        }}
      >
        Emend
      </span>
    </span>
  );
}
