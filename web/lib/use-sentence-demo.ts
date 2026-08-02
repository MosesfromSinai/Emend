"use client";

import { useCallback, useEffect, useState } from "react";

// Mirrors the design component's per-bullet state shape exactly, including
// the `rev` counter used purely to force the contenteditable span's `key` to
// change so React remounts it (see sentence-demo.tsx) instead of fighting a
// live-edited DOM node.
export type BulletState = {
  idx: number;
  orig: boolean;
  custom: string | null;
  dirty: boolean;
  rev: number;
};

const DEFAULT_STATE: BulletState = { idx: 0, orig: false, custom: null, dirty: false, rev: 0 };

export function useSentenceDemo() {
  const [selected, setSelected] = useState<string | null>(null);
  const [sentences, setSentences] = useState<Record<string, BulletState>>({});

  // Deselect on any click outside a bullet. React 17+ delegates synthetic
  // events to the app root, not `document` — a bullet's `stopPropagation()`
  // only blocks other React handlers, not this raw listener, which still
  // sees every native click. So check the real target instead of relying
  // on propagation being stopped.
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (e.target instanceof Element && e.target.closest("[data-demo-interactive]")) {
        return;
      }
      setSelected(null);
    };
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  const get = useCallback(
    (key: string): BulletState => sentences[key] ?? DEFAULT_STATE,
    [sentences]
  );

  // functional update — avoids the stale-closure race the design's own
  // comment calls out when several bullets update in quick succession
  const patch = useCallback((key: string, next: Partial<BulletState>) => {
    setSentences((prev) => ({ ...prev, [key]: { ...(prev[key] ?? DEFAULT_STATE), ...next } }));
  }, []);

  return { selected, setSelected, get, patch };
}
