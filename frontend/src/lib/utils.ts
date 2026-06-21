import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, parseISO } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "—"
  try {
    const d = typeof date === "string" ? parseISO(date) : date
    return format(d, "MMM d, yyyy")
  } catch {
    return "—"
  }
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600 dark:text-green-400"
  if (score >= 60) return "text-yellow-600 dark:text-yellow-400"
  return "text-red-600 dark:text-red-400"
}

export function getScoreBg(score: number): string {
  if (score >= 80) return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
  if (score >= 60) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
  return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
}

export function getRecommendationColor(rec: string): string {
  switch (rec) {
    case "apply": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
    case "maybe": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
    case "skip": return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
    default: return "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400"
  }
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    new: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    saved: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    applied: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
    interview: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    rejected: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    offer: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    archived: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
    not_relevant: "bg-gray-100 text-gray-600 dark:bg-gray-900/30 dark:text-gray-500",
  }
  return map[status] ?? "bg-gray-100 text-gray-800"
}

export function truncate(str: string, n: number): string {
  return str.length > n ? str.slice(0, n) + "…" : str
}
