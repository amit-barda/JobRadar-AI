"use client"
import { useQuery } from "@tanstack/react-query"
import { dashboardApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { getStatusColor, getRecommendationColor, formatDate, getScoreBg } from "@/lib/utils"
import {
  Briefcase, TrendingUp, Send, Calendar, BarChart3,
  AlertCircle, Star, Building2,
} from "lucide-react"
import Link from "next/link"
import type { DashboardStats } from "@/types"
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts"

const STATUS_COLORS: Record<string, string> = {
  new: "#3b82f6", saved: "#8b5cf6", applied: "#6366f1",
  interview: "#f59e0b", rejected: "#ef4444", offer: "#10b981",
  archived: "#6b7280", not_relevant: "#9ca3af",
}

function StatCard({ title, value, icon: Icon, subtitle, color = "text-primary" }: {
  title: string; value: string | number; icon: React.ElementType;
  subtitle?: string; color?: string;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
          </div>
          <div className="p-3 rounded-full bg-primary/10">
            <Icon className={`w-6 h-6 ${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard"],
    queryFn: () => dashboardApi.stats().then((r) => r.data),
  })

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
          </div>
        </div>
      </DashboardLayout>
    )
  }

  const pieData = Object.entries(stats?.jobs_by_status || {}).map(([name, value]) => ({ name, value }))
  const barData = (stats?.top_missing_skills || []).slice(0, 8).map((s) => ({
    name: s.skill.length > 15 ? s.skill.slice(0, 15) + "…" : s.skill,
    count: s.count,
  }))

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Your job search at a glance</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard title="Total Jobs" value={stats?.total_jobs || 0} icon={Briefcase} />
          <StatCard title="New" value={stats?.new_jobs || 0} icon={TrendingUp} color="text-blue-500" />
          <StatCard title="Applied" value={stats?.applied_jobs || 0} icon={Send} color="text-indigo-500" />
          <StatCard title="Interviews" value={stats?.interview_jobs || 0} icon={Calendar} color="text-orange-500" />
          <StatCard
            title="Avg Match"
            value={`${stats?.avg_cv_match_score || 0}%`}
            icon={BarChart3}
            color={(stats?.avg_cv_match_score ?? 0) >= 70 ? "text-green-500" : (stats?.avg_cv_match_score ?? 0) >= 50 ? "text-yellow-500" : "text-red-500"}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Jobs by status pie chart */}
          <Card>
            <CardHeader><CardTitle className="text-base">Jobs by Status</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2} dataKey="value" label={({ name, value }) => `${name} (${value})`} labelLine={false}>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={STATUS_COLORS[entry.name] || "#6b7280"} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top missing skills */}
          <Card>
            <CardHeader><CardTitle className="text-base">Top Missing Skills</CardTitle></CardHeader>
            <CardContent>
              {barData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={barData} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={4} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[220px] text-muted-foreground text-sm">
                  No data yet — match your CV against some jobs
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* High priority jobs */}
        {(stats?.best_matches || []).length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Star className="w-4 h-4 text-yellow-500" />Best Matches</CardTitle></CardHeader>
            <CardContent>
              <div className="divide-y">
                {stats?.best_matches.slice(0, 5).map((job) => (
                  <Link key={job.id} href={`/jobs/${job.id}`} className="flex items-center justify-between py-3 hover:bg-accent/50 px-2 -mx-2 rounded transition-colors">
                    <div>
                      <p className="font-medium text-sm">{job.title}</p>
                      <p className="text-xs text-muted-foreground">{job.company} · {job.location}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getStatusColor(job.status)}>{job.status.replace("_", " ")}</Badge>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent jobs */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent Jobs</CardTitle>
            <Link href="/jobs" className="text-sm text-primary hover:underline">View all →</Link>
          </CardHeader>
          <CardContent>
            {(stats?.recent_jobs || []).length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <Briefcase className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-sm">No jobs yet. Add your first job URL.</p>
                <Link href="/jobs" className="mt-2 text-sm text-primary hover:underline">Add a job →</Link>
              </div>
            ) : (
              <div className="divide-y">
                {stats?.recent_jobs.map((job) => (
                  <Link key={job.id} href={`/jobs/${job.id}`} className="flex items-center gap-3 py-3 hover:bg-accent/50 px-2 -mx-2 rounded transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{job.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{job.company} · {formatDate(job.date_added)}</p>
                    </div>
                    <Badge className={getStatusColor(job.status)}>{job.status.replace("_", " ")}</Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
