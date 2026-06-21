"use client"
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, useRouter } from "next/navigation"
import { interviewsApi, jobsApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, Zap, ChevronDown, ChevronUp, MessageSquare, Star } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import type { InterviewPreparation, MockInterview, Job } from "@/types"

function QuestionAccordion({ title, questions, color }: { title: string; questions: string[]; color: string }) {
  const [open, setOpen] = useState(false)
  return (
    <Card>
      <button
        className="w-full text-left"
        onClick={() => setOpen(!open)}
      >
        <CardHeader className="flex flex-row items-center justify-between py-3">
          <CardTitle className={cn("text-base", color)}>{title} ({questions.length})</CardTitle>
          {open ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </CardHeader>
      </button>
      {open && (
        <CardContent className="pt-0 pb-4">
          <ol className="space-y-3">
            {questions.map((q, i) => (
              <li key={i} className="flex gap-3">
                <span className="text-xs font-bold text-muted-foreground mt-0.5 w-5 shrink-0">{i + 1}.</span>
                <p className="text-sm">{q}</p>
              </li>
            ))}
          </ol>
        </CardContent>
      )}
    </Card>
  )
}

function MockInterviewSection({ jobId, prep }: { jobId: string; prep: InterviewPreparation }) {
  const qc = useQueryClient()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [currentAnswer, setCurrentAnswer] = useState("")
  const [feedbacks, setFeedbacks] = useState<Record<number, any>>({})

  const { data: session } = useQuery<MockInterview>({
    queryKey: ["mock-interview", sessionId],
    queryFn: () => interviewsApi.getMock(sessionId!).then((r) => r.data),
    enabled: !!sessionId,
    refetchInterval: false,
  })

  const startMutation = useMutation({
    mutationFn: () => interviewsApi.startMock(jobId),
    onSuccess: (res) => {
      setSessionId(res.data.id || res.data.session_id)
      toast.success("Mock interview started!")
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to start"),
  })

  const answerMutation = useMutation({
    mutationFn: ({ sid, answer }: { sid: string; answer: string }) =>
      interviewsApi.submitAnswer(sid, answer),
    onSuccess: (res) => {
      const data = res.data
      if (data.feedback) {
        setFeedbacks((prev) => ({ ...prev, [(session?.current_question_index || 0)]: data.feedback }))
      }
      setCurrentAnswer("")
      qc.invalidateQueries({ queryKey: ["mock-interview", sessionId] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to submit"),
  })

  if (!sessionId) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><MessageSquare className="w-4 h-4" />Mock Interview</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Practice answering interview questions with AI feedback. The AI will ask you questions and evaluate your answers.
          </p>
          <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
            {startMutation.isPending ? "Starting..." : "Start Mock Interview"}
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!session) return <Skeleton className="h-48" />

  const isComplete = session.status === "completed"
  const questions = session.questions || []
  const answers = session.answers || []
  const sessionFeedbacks = session.feedbacks || []
  const currentIdx = session.current_question_index || 0
  const currentQ = questions[currentIdx]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <MessageSquare className="w-4 h-4" />
          Mock Interview
          {isComplete && <Badge className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">Completed</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Question {Math.min(currentIdx + 1, questions.length)} of {questions.length}</span>
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${(answers.length / Math.max(questions.length, 1)) * 100}%` }}
            />
          </div>
        </div>

        {/* Previous Q&A */}
        {answers.map((ans: string, i: number) => (
          <div key={i} className="space-y-2">
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs font-semibold text-muted-foreground mb-1">Q{i + 1}</p>
              <p className="text-sm">{questions[i]}</p>
            </div>
            <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 p-3">
              <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1">Your Answer</p>
              <p className="text-sm">{ans}</p>
            </div>
            {(sessionFeedbacks[i] || feedbacks[i]) && (() => {
              const fb = sessionFeedbacks[i] || feedbacks[i]
              return (
                <div className="rounded-lg bg-green-50 dark:bg-green-950/30 p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-semibold text-green-700 dark:text-green-400">AI Feedback</p>
                    {fb.score !== undefined && (
                      <span className="flex items-center gap-0.5 text-xs text-yellow-600">
                        <Star className="w-3 h-3 fill-current" />{fb.score}/100
                      </span>
                    )}
                  </div>
                  {typeof fb.feedback === "string" && <p className="text-sm">{fb.feedback}</p>}
                  {fb.strengths && fb.strengths.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-green-600 dark:text-green-400">Strengths:</p>
                      <ul className="mt-1 space-y-0.5">{fb.strengths.map((s: string, j: number) => <li key={j} className="text-sm flex gap-1.5"><span className="text-green-500">✓</span>{s}</li>)}</ul>
                    </div>
                  )}
                  {fb.improvements && fb.improvements.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-orange-600 dark:text-orange-400">Improvements:</p>
                      <ul className="mt-1 space-y-0.5">{fb.improvements.map((s: string, j: number) => <li key={j} className="text-sm flex gap-1.5"><span className="text-orange-500">→</span>{s}</li>)}</ul>
                    </div>
                  )}
                  {(fb.example_better_answer || fb.improved_answer) && (
                    <div className="mt-2 pt-2 border-t border-green-200 dark:border-green-800">
                      <p className="text-xs font-medium text-green-600 dark:text-green-400">Example better answer:</p>
                      <p className="text-sm mt-1 text-muted-foreground">{fb.example_better_answer || fb.improved_answer}</p>
                    </div>
                  )}
                </div>
              )
            })()}
            <Separator />
          </div>
        ))}

        {/* Current question */}
        {!isComplete && currentQ && (
          <div className="space-y-3">
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs font-semibold text-muted-foreground mb-1">Q{currentIdx + 1}</p>
              <p className="text-sm font-medium">{currentQ}</p>
            </div>
            <Textarea
              placeholder="Type your answer here..."
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <Button
              onClick={() => answerMutation.mutate({ sid: sessionId, answer: currentAnswer })}
              disabled={answerMutation.isPending || !currentAnswer.trim()}
              className="w-full"
            >
              {answerMutation.isPending ? "Submitting..." : currentIdx === questions.length - 1 ? "Submit Final Answer" : "Submit Answer →"}
            </Button>
          </div>
        )}

        {isComplete && (
          <div className="text-center py-4 space-y-2">
            <p className="text-lg font-semibold text-green-600 dark:text-green-400">Interview Complete!</p>
            <p className="text-sm text-muted-foreground">Review your answers and AI feedback above.</p>
            <Button variant="outline" size="sm" onClick={() => { setSessionId(null); setFeedbacks({}) }}>
              Start New Session
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function InterviewPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const router = useRouter()

  const { data: job } = useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: () => jobsApi.get(jobId).then((r) => r.data),
  })

  const { data: prep, isLoading, refetch } = useQuery<InterviewPreparation>({
    queryKey: ["interview-prep", jobId],
    queryFn: () => interviewsApi.get(jobId).then((r) => r.data),
    retry: false,
  })

  const prepMutation = useMutation({
    mutationFn: () => interviewsApi.generate(jobId),
    onSuccess: () => { toast.success("Interview prep generated!"); refetch() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to generate"),
  })

  return (
    <DashboardLayout>
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="w-4 h-4" /></Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold truncate">Interview Prep{job ? `: ${job.title}` : ""}</h1>
            {job?.company && <p className="text-sm text-muted-foreground">{job.company}</p>}
          </div>
          {!prep && !isLoading && (
            <Button size="sm" onClick={() => prepMutation.mutate()} disabled={prepMutation.isPending}>
              <Zap className="w-4 h-4 mr-2" />
              {prepMutation.isPending ? "Generating..." : "Generate Prep"}
            </Button>
          )}
          {prep && (
            <Button variant="outline" size="sm" onClick={() => prepMutation.mutate()} disabled={prepMutation.isPending}>
              <Zap className="w-4 h-4 mr-2" />
              {prepMutation.isPending ? "Regenerating..." : "Regenerate"}
            </Button>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : !prep ? (
          <Card>
            <CardContent className="py-12 text-center space-y-3">
              <MessageSquare className="w-10 h-10 mx-auto opacity-30" />
              <p className="text-muted-foreground">No interview prep yet.</p>
              <Button onClick={() => prepMutation.mutate()} disabled={prepMutation.isPending}>
                <Zap className="w-4 h-4 mr-2" />
                {prepMutation.isPending ? "Generating..." : "Generate Interview Prep"}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Question categories */}
            <div className="space-y-3">
              <h2 className="font-semibold">Interview Questions</h2>
              <QuestionAccordion title="HR Questions" questions={prep.hr_questions || []} color="text-blue-600 dark:text-blue-400" />
              <QuestionAccordion title="Product Questions" questions={prep.product_questions || []} color="text-purple-600 dark:text-purple-400" />
              <QuestionAccordion title="Technical Questions" questions={prep.technical_questions || []} color="text-green-600 dark:text-green-400" />
              <QuestionAccordion title="Behavioral Questions" questions={prep.behavioral_questions || []} color="text-orange-600 dark:text-orange-400" />
            </div>

            {/* STAR suggestions */}
            {(prep.star_suggestions || []).length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-base">STAR Story Suggestions</CardTitle></CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {prep.star_suggestions.map((s: string, i: number) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-primary">★</span>{s}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Company prep */}
            {(prep.company_preparation || []).length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-base">Company Research Tips</CardTitle></CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {prep.company_preparation.map((s: string, i: number) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-muted-foreground">→</span>{s}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            <Separator />

            {/* Mock interview */}
            <MockInterviewSection jobId={jobId} prep={prep} />
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
