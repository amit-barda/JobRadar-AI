"use client"
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { jobsApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { getStatusColor, getRecommendationColor, getScoreBg, formatDate, cn } from "@/lib/utils"
import { Plus, ExternalLink, Search, Trash2, Cpu, RefreshCw } from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"
import type { Job, JobListResponse } from "@/types"

const JOB_STATUSES = ["new", "saved", "applied", "interview", "rejected", "offer", "archived", "not_relevant"]
const WORK_TYPES = ["remote", "hybrid", "onsite", "unknown"]

export default function JobsPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [urlInput, setUrlInput] = useState("")
  const [addOpen, setAddOpen] = useState(false)
  const [adding, setAdding] = useState(false)

  const { data, isLoading } = useQuery<JobListResponse>({
    queryKey: ["jobs", page, filters],
    queryFn: () => jobsApi.list({ page, per_page: 20, ...filters }).then((r) => r.data),
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => jobsApi.updateStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  })

  const analyzeMutation = useMutation({
    mutationFn: (id: string) => jobsApi.analyze(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] })
      toast.success("Analysis started")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => jobsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] })
      toast.success("Job deleted")
    },
  })

  const handleAddUrl = async () => {
    if (!urlInput.trim()) return
    setAdding(true)
    try {
      await jobsApi.addUrl(urlInput.trim())
      toast.success("Job added! It will be analyzed shortly.")
      setUrlInput("")
      setAddOpen(false)
      qc.invalidateQueries({ queryKey: ["jobs"] })
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add job")
    } finally {
      setAdding(false)
    }
  }

  const setFilter = (key: string, val: string) => {
    setPage(1)
    setFilters((prev) => val && val !== "all" ? { ...prev, [key]: val } : Object.fromEntries(Object.entries(prev).filter(([k]) => k !== key)))
  }

  return (
    <DashboardLayout>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Jobs</h1>
            <p className="text-muted-foreground text-sm">{data?.total || 0} jobs tracked</p>
          </div>
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="w-4 h-4 mr-2" />Add Job URL</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Add Job by URL</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Paste a job URL from LinkedIn, Glassdoor, Drushim, or any job site.
                  The AI will automatically fetch and analyze the job.
                </p>
                <Input
                  placeholder="https://www.linkedin.com/jobs/view/..."
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddUrl()}
                />
                <Button onClick={handleAddUrl} disabled={adding || !urlInput.trim()} className="w-full">
                  {adding ? <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />Adding...</span> : "Add Job"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input placeholder="Search title..." className="pl-9 w-48" onChange={(e) => setFilter("title", e.target.value)} />
          </div>
          <Input placeholder="Company..." className="w-36" onChange={(e) => setFilter("company", e.target.value)} />
          <Select onValueChange={(v) => setFilter("status", v)}>
            <SelectTrigger className="w-32"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All status</SelectItem>
              {JOB_STATUSES.map((s) => <SelectItem key={s} value={s}>{s.replace("_", " ")}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select onValueChange={(v) => setFilter("work_type", v)}>
            <SelectTrigger className="w-32"><SelectValue placeholder="Work type" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {WORK_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        {/* Jobs table */}
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Job</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Location</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Source</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Added</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? [...Array(5)].map((_, i) => (
                      <tr key={i} className="border-b">
                        {[...Array(7)].map((_, j) => <td key={j} className="px-4 py-3"><Skeleton className="h-5 w-full" /></td>)}
                      </tr>
                    ))
                  : (data?.items || []).map((job) => (
                      <tr key={job.id} className="border-b hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-3">
                          <Link href={`/jobs/${job.id}`} className="group">
                            <p className="font-medium group-hover:text-primary transition-colors">{job.title}</p>
                            <p className="text-xs text-muted-foreground">{job.company}</p>
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{job.location || "—"}</td>
                        <td className="px-4 py-3">
                          {job.source && <Badge variant="outline" className="text-xs">{job.source}</Badge>}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className="text-xs capitalize">{job.work_type}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Select
                            defaultValue={job.status}
                            onValueChange={(v) => statusMutation.mutate({ id: job.id, status: v })}
                          >
                            <SelectTrigger className="h-7 text-xs border-0 p-0 shadow-none focus:ring-0">
                              <Badge className={cn(getStatusColor(job.status), "cursor-pointer")}>
                                {job.status.replace("_", " ")}
                              </Badge>
                            </SelectTrigger>
                            <SelectContent>
                              {JOB_STATUSES.map((s) => <SelectItem key={s} value={s}>{s.replace("_", " ")}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">{formatDate(job.date_added)}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            {job.url && (
                              <a href={job.url} target="_blank" rel="noopener noreferrer">
                                <Button variant="ghost" size="icon" className="h-7 w-7"><ExternalLink className="w-3 h-3" /></Button>
                              </a>
                            )}
                            {!job.is_analyzed && (
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => analyzeMutation.mutate(job.id)}>
                                <Cpu className="w-3 h-3" />
                              </Button>
                            )}
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={() => deleteMutation.mutate(job.id)}>
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total > data.per_page && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * data.per_page + 1}–{Math.min(page * data.per_page, data.total)} of {data.total}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</Button>
                <Button variant="outline" size="sm" disabled={page * data.per_page >= data.total} onClick={() => setPage(page + 1)}>Next</Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}
