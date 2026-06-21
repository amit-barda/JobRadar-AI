"use client"
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useRouter } from "next/navigation"
import { jobsApi, matchesApi, interviewsApi, cvsApi, coverLetterApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { getStatusColor, getScoreColor, getScoreBg, getRecommendationColor, formatDate, cn } from "@/lib/utils"
import {
  ArrowLeft, ExternalLink, Cpu, MessageSquare, FileText,
  MapPin, Building2, Calendar, Zap,
} from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"
import type { Job, JobCVMatch, InterviewPreparation } from "@/types"

const JOB_STATUSES = ["new", "saved", "applied", "interview", "rejected", "offer", "archived", "not_relevant"]

function ScoreBar({ label, value, weight }: { label: string; value: number; weight: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label} <span className="text-muted-foreground text-xs">({weight})</span></span>
        <span className={cn("font-semibold", getScoreColor(value))}>{Math.round(value)}%</span>
      </div>
      <Progress value={value} className="h-2" />
    </div>
  )
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const router = useRouter()

  const { data: job, isLoading } = useQuery<Job>({
    queryKey: ["job", id],
    queryFn: () => jobsApi.get(id).then((r) => r.data),
  })

  const { data: cvs } = useQuery({
    queryKey: ["cvs"],
    queryFn: () => cvsApi.list().then((r) => r.data),
  })

  const { data: match, refetch: refetchMatch } = useQuery<JobCVMatch>({
    queryKey: ["match", id],
    queryFn: () => {
      const activeCv = cvs?.find((c: any) => c.is_active)
      if (!activeCv) return Promise.reject("No active CV")
      return matchesApi.getMatch(id, activeCv.id).then((r) => r.data)
    },
    enabled: !!cvs,
    retry: false,
  })

  const { data: prep } = useQuery<InterviewPreparation>({
    queryKey: ["interview-prep", id],
    queryFn: () => interviewsApi.get(id).then((r) => r.data),
    retry: false,
  })

  const { data: coverLetter, refetch: refetchCoverLetter } = useQuery<{ cover_letter: string }>({
    queryKey: ["cover-letter", id],
    queryFn: () => {
      const activeCv = cvs?.find((c: any) => c.is_active)
      if (!activeCv) return Promise.reject("No active CV")
      return coverLetterApi.generate(id, activeCv.id).then((r) => r.data)
    },
    enabled: false,
  })

  const analyzeMutation = useMutation({
    mutationFn: () => jobsApi.analyze(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["job", id] }); toast.success("Analysis triggered") },
  })

  const matchMutation = useMutation({
    mutationFn: () => {
      const activeCv = cvs?.find((c: any) => c.is_active)
      if (!activeCv) throw new Error("Upload and set an active CV first")
      return matchesApi.matchJobCv(id, activeCv.id)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["match", id] }); refetchMatch(); toast.success("Match complete") },
    onError: (e: any) => toast.error(e.message || "Match failed"),
  })

  const prepMutation = useMutation({
    mutationFn: () => interviewsApi.generate(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["interview-prep", id] }); toast.success("Interview prep ready") },
  })

  const statusMutation = useMutation({
    mutationFn: (status: string) => jobsApi.updateStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job", id] }),
  })

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="p-6 space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-32" />
          <Skeleton className="h-96" />
        </div>
      </DashboardLayout>
    )
  }

  if (!job) return null

  const activeCv = cvs?.find((c: any) => c.is_active)

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold">{job.title}</h1>
                <div className="flex items-center gap-3 mt-1 text-muted-foreground text-sm">
                  <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{job.company}</span>
                  {job.location && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>}
                  {job.source && <Badge variant="outline">{job.source}</Badge>}
                  <Badge variant="outline" className="capitalize">{job.work_type}</Badge>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {job.url && (
                  <a href={job.url} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" size="sm"><ExternalLink className="w-3 h-3 mr-1" />View</Button>
                  </a>
                )}
                <Select defaultValue={job.status} onValueChange={(v) => statusMutation.mutate(v)}>
                  <SelectTrigger className="w-36 h-9">
                    <Badge className={getStatusColor(job.status)}>{job.status.replace("_", " ")}</Badge>
                  </SelectTrigger>
                  <SelectContent>
                    {JOB_STATUSES.map((s) => <SelectItem key={s} value={s}>{s.replace("_", " ")}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap gap-2 mt-3">
              <Button size="sm" variant="outline" onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
                <Cpu className="w-3 h-3 mr-1" />{analyzeMutation.isPending ? "Analyzing..." : "Analyze"}
              </Button>
              <Button size="sm" variant="outline" onClick={() => matchMutation.mutate()} disabled={matchMutation.isPending || !activeCv}>
                <Zap className="w-3 h-3 mr-1" />{matchMutation.isPending ? "Matching..." : "Match CV"}
              </Button>
              <Button size="sm" variant="outline" onClick={() => prepMutation.mutate()} disabled={prepMutation.isPending}>
                <MessageSquare className="w-3 h-3 mr-1" />{prepMutation.isPending ? "Generating..." : "Interview Prep"}
              </Button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview">
          <TabsList className="grid grid-cols-5 w-full">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="analysis">AI Analysis</TabsTrigger>
            <TabsTrigger value="match">CV Match</TabsTrigger>
            <TabsTrigger value="interview">Interview</TabsTrigger>
            <TabsTrigger value="cover">Cover Letter</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            {job.description && (
              <Card>
                <CardHeader><CardTitle className="text-base">Job Description</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap text-muted-foreground">{job.description}</p></CardContent>
              </Card>
            )}
            {job.requirements && (
              <Card>
                <CardHeader><CardTitle className="text-base">Requirements</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap text-muted-foreground">{job.requirements}</p></CardContent>
              </Card>
            )}
            {job.responsibilities && (
              <Card>
                <CardHeader><CardTitle className="text-base">Responsibilities</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap text-muted-foreground">{job.responsibilities}</p></CardContent>
              </Card>
            )}
            {!job.description && !job.requirements && (
              <Card><CardContent className="py-8 text-center text-muted-foreground">
                <p>No job content yet.</p>
                <Button className="mt-3" size="sm" onClick={() => analyzeMutation.mutate()}>Analyze Job</Button>
              </CardContent></Card>
            )}
          </TabsContent>

          <TabsContent value="analysis">
            {job.analysis ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader><CardTitle className="text-base">Role Info</CardTitle></CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-muted-foreground">Category</span><span className="font-medium">{job.analysis.role_category || "—"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Seniority</span><Badge className="capitalize">{job.analysis.seniority_level || "—"}</Badge></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Experience</span><span>{job.analysis.required_years_experience != null ? `${job.analysis.required_years_experience} years` : "Not specified"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Industry</span><span>{job.analysis.industry || "—"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Junior Fit</span><Badge className={job.analysis.is_junior_fit ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" : "bg-red-100 text-red-800"}>{job.analysis.is_junior_fit ? "Yes" : "No"}</Badge></div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle className="text-base">Required Skills</CardTitle></CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1.5">
                      {(job.analysis.required_skills || []).map((s) => (
                        <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle className="text-base">Nice to Have</CardTitle></CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1.5">
                      {(job.analysis.nice_to_have_skills || []).map((s) => (
                        <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle className="text-base">ATS Keywords</CardTitle></CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1.5">
                      {(job.analysis.ats_keywords || []).map((k) => (
                        <Badge key={k} className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">{k}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {(job.analysis.red_flags || []).length > 0 && (
                  <Card className="md:col-span-2 border-destructive/40">
                    <CardHeader><CardTitle className="text-base text-destructive">⚠ Red Flags</CardTitle></CardHeader>
                    <CardContent>
                      <ul className="list-disc list-inside space-y-1 text-sm">
                        {job.analysis.red_flags.map((f, i) => <li key={i}>{f}</li>)}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">
                <p>No AI analysis yet.</p>
                <Button className="mt-3" size="sm" onClick={() => analyzeMutation.mutate()}>Run Analysis</Button>
              </CardContent></Card>
            )}
          </TabsContent>

          <TabsContent value="match">
            {match ? (
              <div className="space-y-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <div className={cn("text-5xl font-bold", getScoreColor(match.final_score))}>{Math.round(match.final_score)}</div>
                        <div className="text-xs text-muted-foreground mt-1">Match Score</div>
                      </div>
                      <div className="flex-1 space-y-3">
                        <ScoreBar label="Required Skills" value={match.score_breakdown?.required_skills_match || 0} weight="30%" />
                        <ScoreBar label="Experience" value={match.score_breakdown?.experience_match || 0} weight="20%" />
                        <ScoreBar label="Role Fit" value={match.score_breakdown?.role_fit || 0} weight="15%" />
                        <ScoreBar label="ATS Keywords" value={match.score_breakdown?.ats_keyword_match || 0} weight="15%" />
                        <ScoreBar label="Tools" value={match.score_breakdown?.tools_match || 0} weight="10%" />
                        <ScoreBar label="Education" value={match.score_breakdown?.education_certifications_match || 0} weight="10%" />
                      </div>
                      <div className="text-center">
                        <Badge className={cn("text-base px-4 py-2", getRecommendationColor(match.recommendation))}>
                          {match.recommendation === "apply" ? "✓ Apply" : match.recommendation === "maybe" ? "~ Maybe" : "✗ Skip"}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-1">Confidence: {match.confidence}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader><CardTitle className="text-base text-green-600 dark:text-green-400">✓ Matching Skills</CardTitle></CardHeader>
                    <CardContent><div className="flex flex-wrap gap-1.5">{match.matching_skills.map((s) => <Badge key={s} className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 text-xs">{s}</Badge>)}</div></CardContent>
                  </Card>
                  <Card>
                    <CardHeader><CardTitle className="text-base text-red-600 dark:text-red-400">✗ Missing Skills</CardTitle></CardHeader>
                    <CardContent><div className="flex flex-wrap gap-1.5">{match.missing_required_skills.map((s) => <Badge key={s} className="bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 text-xs">{s}</Badge>)}</div></CardContent>
                  </Card>
                </div>

                {match.ats_feedback && (
                  <Card>
                    <CardHeader><CardTitle className="text-base">ATS Feedback</CardTitle></CardHeader>
                    <CardContent><p className="text-sm text-muted-foreground">{match.ats_feedback}</p></CardContent>
                  </Card>
                )}

                {(match.cv_improvement_suggestions || []).length > 0 && (
                  <Card>
                    <CardHeader><CardTitle className="text-base">CV Improvement Suggestions</CardTitle></CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {match.cv_improvement_suggestions.map((s, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm">
                            <span className="text-primary mt-0.5">→</span>{s}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">
                <p>{!activeCv ? "Upload and set an active CV first." : "No match yet."}</p>
                {activeCv && <Button className="mt-3" size="sm" onClick={() => matchMutation.mutate()}>Run CV Match</Button>}
                {!activeCv && <Link href="/cv"><Button className="mt-3" size="sm">Upload CV</Button></Link>}
              </CardContent></Card>
            )}
          </TabsContent>

          <TabsContent value="interview">
            {prep ? (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <Link href={`/interviews/${job.id}`}>
                    <Button><MessageSquare className="w-4 h-4 mr-2" />Start Mock Interview</Button>
                  </Link>
                </div>
                {[
                  { label: "HR Questions", items: prep.hr_questions },
                  { label: "Product/Project Questions", items: prep.product_questions },
                  { label: "Technical Questions", items: prep.technical_questions },
                  { label: "Behavioral Questions", items: prep.behavioral_questions },
                ].map(({ label, items }) => items.length > 0 && (
                  <Card key={label}>
                    <CardHeader><CardTitle className="text-base">{label}</CardTitle></CardHeader>
                    <CardContent>
                      <ol className="space-y-2">
                        {items.map((q, i) => <li key={i} className="text-sm flex gap-2"><span className="text-muted-foreground shrink-0">{i + 1}.</span>{q}</li>)}
                      </ol>
                    </CardContent>
                  </Card>
                ))}
                {prep.company_preparation && (
                  <Card>
                    <CardHeader><CardTitle className="text-base">Company Preparation</CardTitle></CardHeader>
                    <CardContent><p className="text-sm text-muted-foreground">{prep.company_preparation}</p></CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">
                <p>No interview prep yet.</p>
                <Button className="mt-3" size="sm" onClick={() => prepMutation.mutate()}>Generate Interview Prep</Button>
              </CardContent></Card>
            )}
          </TabsContent>

          <TabsContent value="cover">
            {match?.cover_letter_text ? (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base">Cover Letter</CardTitle>
                  <Button size="sm" variant="outline" onClick={() => refetchCoverLetter()}>Regenerate</Button>
                </CardHeader>
                <CardContent>
                  <pre className="whitespace-pre-wrap text-sm font-sans">{match.cover_letter_text}</pre>
                </CardContent>
              </Card>
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">
                <p>{!activeCv ? "Upload a CV first to generate a cover letter." : "No cover letter yet."}</p>
                {activeCv && (
                  <Button className="mt-3" size="sm" onClick={() => {
                    const cv = cvs?.find((c: any) => c.is_active)
                    if (cv) coverLetterApi.generate(id, cv.id).then(() => qc.invalidateQueries({ queryKey: ["match", id] }))
                  }}>Generate Cover Letter</Button>
                )}
              </CardContent></Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}
