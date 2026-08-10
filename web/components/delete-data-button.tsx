"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createPortal } from "react-dom";

import { Button } from "@/components/ui/button";
import { ApiError, deleteMyData } from "@/lib/api";

// The one place in the app a visitor can see that their data persists (the
// session cookie lasts a year) and actually get rid of it -- there's no
// account/settings page otherwise. Lives in the app header so it's reachable
// from every screen, not just one buried settings page nobody finds.
export function DeleteDataButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirmDelete() {
    setBusy(true);
    setError(null);
    try {
      await deleteMyData();
      sessionStorage.clear();
      router.push("/");
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-[12.5px] font-medium text-ink/70 hover:text-ink"
      >
        Delete my data
      </button>
      {open &&
        createPortal(
          // Rendered via portal straight onto <body> -- the header this
          // button lives in has `backdrop-blur-sm`, and backdrop-filter on
          // an ancestor makes it the containing block for any descendant
          // `position: fixed` element. Left in the header's DOM subtree,
          // this modal centered itself inside the header's own (much
          // shorter) bounds instead of the viewport, cutting it off.
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
            <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
              <h2 className="font-serif text-lg font-semibold">Delete everything?</h2>
              <p className="mt-2 text-sm text-ink/70">
                This permanently deletes your confirmed resume, every application you&apos;ve
                tailored, and their exported files. There&apos;s no undo.
              </p>
              {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
              <div className="mt-4 flex justify-end gap-3">
                <Button variant="ghost" onClick={() => setOpen(false)} disabled={busy}>
                  Cancel
                </Button>
                <Button onClick={confirmDelete} disabled={busy}>
                  {busy ? "Deleting…" : "Delete everything"}
                </Button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  );
}
