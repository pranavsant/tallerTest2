/**
 * Small presentation-layer utilities shared across components.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge conditional class names and de-duplicate conflicting Tailwind classes.
 * The standard `cn` helper used throughout the UI.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format an ISO-8601 timestamp (as returned by the API) for display.
 * Falls back to the raw input if it cannot be parsed.
 */
export function formatDate(
  value: string | number | Date | null | undefined,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  },
): string {
  if (value === null || value === undefined) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(undefined, options).format(date);
}
