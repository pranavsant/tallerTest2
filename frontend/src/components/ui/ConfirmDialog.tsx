"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

export type ConfirmTone = "default" | "danger";

export interface ConfirmDialogProps {
  /** Whether the dialog is mounted/visible. */
  open: boolean;
  title: string;
  /** Body content — a description of what confirming will do. */
  description: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  /** `danger` styles the confirm button red (destructive actions). */
  tone?: ConfirmTone;
  /** Disables the buttons and shows progress on confirm (e.g. while saving). */
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Accessible confirmation modal (acceptance criterion: actions confirmed via a
 * modal before submitting).
 *
 * Renders into a portal on `document.body`, traps initial focus on the confirm
 * button, closes on Escape or backdrop click, and is labelled for screen
 * readers via `aria-modal` + `aria-labelledby`/`aria-describedby`. Purely
 * presentational: it knows nothing about what is being confirmed.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "default",
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null);

  // Close on Escape while open.
  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !busy) onCancel();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, busy, onCancel]);

  // Move focus to the confirm button when the dialog opens.
  useEffect(() => {
    if (open) confirmRef.current?.focus();
  }, [open]);

  // Portals require the DOM; guard for SSR / first render.
  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="presentation">
      {/* Backdrop */}
      <div
        className="absolute inset-0 animate-fade-in bg-black/40"
        onClick={() => !busy && onCancel()}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        className="relative w-full max-w-md animate-fade-in rounded-card bg-white p-6 shadow-card-hover dark:bg-gray-900"
      >
        <h3
          id="confirm-dialog-title"
          className="text-lg font-semibold text-gray-900 dark:text-white"
        >
          {title}
        </h3>
        <div
          id="confirm-dialog-description"
          className="mt-2 text-sm text-gray-500 dark:text-gray-400"
        >
          {description}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50",
              tone === "danger" ? "bg-red-600 hover:bg-red-700" : "bg-brand-600 hover:bg-brand-700",
            )}
          >
            {busy ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
