"use client"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useRouter } from "next/navigation"
import { cvsApi, matchesApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, Zap, Briefcase } from "lucide-react"
import { toast } from "sonner"
import { getScoreColor, getRecommendationColor, formatDate, cn } from "@/lib/utils"
import Link from "next/link"
import type { CV, JobCVMatch } from "@/types"

export default function CVDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const qc = useQueryClient()

  const { data: cv, isLoading } = useQuery<CV>({
    queryKey: ["cv", id],
    queryFn: () => cvsApi.get(id).then((r) => r.data),
  })

  const { data: matches } = useQuery<JobCVMatch[]>({
    queryKey: ["cv-matches", id],
    queryFn: () => matchesApi.getCvMatches(id).then((r) => r.data),
  })

  const matchAllMutation = useMutation({
    mutationFn: () => matchesApi.matchCvAllJobs(id),
    onSuccess: (res) => {
      toast.success(`Matching against ${res.data.count} jobs started`)
      qc.invalidateQueries({ queryKey: ["cv-matches", id] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to start matching"),
  })

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="p-6 space-y-4">
          <Skeleton className="h-8 w-48" />
          <div className="grid grid-cols-2 gap-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
        </div>
      </DashboardLayout>
    )
  }

  if (!cv?.analysis) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <Button variant="ghost" size="sm" onClick={() => router.back()}><ArrowLeft className="w-4 h-4 mr-1" />Back</Button>
          <Card className="mt-4"><CardContent className="py-8 text-center text-muted-foreground">
            CV analysis not ready yet. It will appear here once complete.
          </CardContent></Card>
        </div>
      </DashboardLayout>
    )
  }

  const a = cv.analysis

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="w-4 h-4" /></Button>
          <div className="flex-1">
            <h1 className="text-xl font-bold">{cv.original_filename}</h1>
            <p className="text-sm text-muted-foreground">CV Analysis</p>
          </div>
          <Button size="sm" onClick={() => matchAllMutation.mutate()} disabled={matchAllMutation.isPending}>
            <Zap className="w-4 h-4 mr-2" />
            {matchAllMutation.isPending ? "Matching..." : "Match All Jobs"}
          </Button>
        </div>

        {a.professional_summary && (
          <Card>
            <CardHeader><CardTitle className="text-base">Professional Summary</CardTitle></CardHeader>
            <CardContent><p className="text-sm text-muted-foreground">{a.professional_summary}</p></CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader><CardTitle className="text-base">Skills ({a.skills.length})</CardTitle></CardHeader>
            <CardContent><div className="flex flex-wrap gap-1.5">{a.skills.map((s) => <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>)}</div></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Tools ({a.tools.length})</CardTitle></CardHeader>
            <CardContent><div className="flex flex-wrap gap-1.5">{a.tools.map((t) => <Badge key={t} variant="outline" className="text-xs">{t}</Badge>)}</div></CardContent>
          </Card>

          {a.work_experience.length > 0 && (
            <Card className="md:col-span-2">
              <CardHeader><CardTitle className="text-base">Work Experience</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {a.work_experience.map((exp: any, i: number) => (
                    <div key={i} className="border-l-2 border-primary/30 pl-4">
                      <p className="font-medium">{exp.title}</p>
                      <p className="text-sm text-muted-foreground">{exp.company} · {exp.duration}</p>
                      {exp.responsibilities?.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {exp.responsibilities.map((r: string, j: number) => (
                            <li key={j} className="text-sm text-muted-foreground flex gap-1.5"><span className="shrink-0">•</span>{r}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {a.education.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-base">Education</CardTitle></CardHeader>
              <CardContent>
                {a.education.map((e: any, i: number) => (
                  <div key={i} className="mb-2">
                    <p className="font-medium text-sm">{e.degree} in {e.field}</p>
                    <p className="text-xs text-muted-foreground">{e.institution} · {e.year}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {a.certifications.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-base">Certifications</CardTitle></CardHeader>
              <CardContent><ul className="space-y-1">{a.certifications.map((c: string, i: number) => <li key={i} className="text-sm">• {c}</li>)}</ul></CardContent>
            </Card>
          )}

          {a.product_management_indicators.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-base text-green-600 dark:text-green-400">PM Indicators</CardTitle></CardHeader>
              <CardContent><ul className="space-y-1">{a.product_management_indicators.map((s: string, i: number) => <li key={i} className="text-sm flex gap-1.5"><span className="text-green-500">✓</span>{s}</li>)}</ul></CardContent>
            </Card>
          )}

          {a.weak_areas.length > 0 && (
            <Card className="border-yellow-500/30">
              <CardHeader><CardTitle className="text-base text-yellow-600 dark:text-yellow-400">Areas to Improve</CardTitle></CardHeader>
              <CardContent><ul className="space-y-1">{a.weak_areas.map((w: string, i: number) => <li key={i} className="text-sm flex gap-1.5"><span className="text-yellow-500">→</span>{w}</li>)}</ul></CardContent>
            </Card>
          )}
        </div>

        {(matches || []).length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Briefcase className="w-4 h-4" />Job Matches ({matches?.length})</CardTitle></CardHeader>
            <CardContent>
              <div className="divide-y">
                {matches?.slice(0, 10).map((m) => (
                  <div key={m.id} className="flex items-center justify-between py-2">
                    <Link href={`/jobs/${m.job_id}`} className="text-sm hover:text-primary transition-colors">View Job</Link>
                    <div className="flex items-center gap-2">
                      <span className={cn("font-bold text-sm", getScoreColor(m.final_score))}>{Math.round(m.final_score)}%</span>
                      <Badge className={getRecommendationColor(m.recommendation)}>{m.recommendation}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
