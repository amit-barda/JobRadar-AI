"use client"
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { sourcesApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { Plus, RefreshCw, Trash2, Rss, Mail, Globe, Link2 } from "lucide-react"
import { toast } from "sonner"
import { formatDate } from "@/lib/utils"
import type { JobSource } from "@/types"

const SOURCE_ICONS: Record<string, React.ElementType> = {
  rss: Rss, email: Mail, api: Globe, manual_url: Link2, manual: Link2,
}

const SOURCE_TYPE_LABELS: Record<string, string> = {
  rss: "RSS Feed", email: "Email Alert", api: "API", manual_url: "Manual URL", manual: "Manual",
}

function SyncStatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    idle: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    syncing: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
    success: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
    error: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  }
  return <Badge className={map[status] || map.idle}>{status}</Badge>
}

function AddSourceDialog({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    name: "", source_type: "rss", url: "", keywords: "", config: "",
  })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    // #region agent log
    fetch('http://127.0.0.1:7258/ingest/c0fc8b9f-abeb-4f04-8b15-72e25c3cc2b0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'1d3f66'},body:JSON.stringify({sessionId:'1d3f66',runId:'post-fix',hypothesisId:'H1',location:'sources/page.tsx:handleSubmit:start',message:'create source submit',data:{source_type:form.source_type,hasUrl:!!form.url,hasConfig:!!form.config},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    try {
      const payload: any = {
        name: form.name,
        source_type: form.source_type,
        url: form.url || undefined,
        keywords: form.keywords ? form.keywords.split(",").map((k) => k.trim()).filter(Boolean) : [],
        config: form.config ? JSON.parse(form.config) : {},
      }
      await sourcesApi.create(payload)
      // #region agent log
      fetch('http://127.0.0.1:7258/ingest/c0fc8b9f-abeb-4f04-8b15-72e25c3cc2b0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'1d3f66'},body:JSON.stringify({sessionId:'1d3f66',runId:'post-fix',hypothesisId:'H1',location:'sources/page.tsx:handleSubmit:success',message:'create source ok',data:{name:form.name},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      toast.success("Source added")
      qc.invalidateQueries({ queryKey: ["sources"] })
      onClose()
    } catch (err: any) {
      // #region agent log
      fetch('http://127.0.0.1:7258/ingest/c0fc8b9f-abeb-4f04-8b15-72e25c3cc2b0',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'1d3f66'},body:JSON.stringify({sessionId:'1d3f66',runId:'post-fix',hypothesisId:'H1',location:'sources/page.tsx:handleSubmit:error',message:'create source failed',data:{message:err?.message,status:err?.response?.status,detail:err?.response?.data?.detail,code:err?.code},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      toast.error(err?.response?.data?.detail || err?.message || "Failed to add source")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label>Name</Label>
        <Input placeholder="LinkedIn PM Jobs" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
      </div>
      <div>
        <Label>Source Type</Label>
        <Select value={form.source_type} onValueChange={(v) => setForm({ ...form, source_type: v })}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            {Object.entries(SOURCE_TYPE_LABELS).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      {(form.source_type === "rss" || form.source_type === "manual_url" || form.source_type === "api") && (
        <div>
          <Label>URL</Label>
          <Input placeholder="https://..." value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} />
        </div>
      )}
      <div>
        <Label>Keywords (comma-separated)</Label>
        <Input placeholder="Product Manager, PM, APM" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} />
      </div>
      <div>
        <Label>Config JSON (optional)</Label>
        <Textarea placeholder='{"interval_hours": 6}' value={form.config} onChange={(e) => setForm({ ...form, config: e.target.value })} className="font-mono text-sm" rows={3} />
      </div>
      <Button type="submit" className="w-full" disabled={submitting || !form.name}>
        {submitting ? "Adding..." : "Add Source"}
      </Button>
    </form>
  )
}

export default function SourcesPage() {
  const qc = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)

  const { data: sources, isLoading } = useQuery<JobSource[]>({
    queryKey: ["sources"],
    queryFn: () => sourcesApi.list().then((r) => r.data),
  })

  const syncMutation = useMutation({
    mutationFn: (id: string) => sourcesApi.sync(id),
    onSuccess: (_, id) => {
      toast.success("Sync started")
      qc.invalidateQueries({ queryKey: ["sources"] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Sync failed"),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => sourcesApi.update(id, { is_enabled: active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => sourcesApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sources"] }); toast.success("Source deleted") },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Delete failed"),
  })

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Job Sources</h1>
            <p className="text-sm text-muted-foreground">Manage where jobs are collected from</p>
          </div>
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="w-4 h-4 mr-2" />Add Source</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Add Job Source</DialogTitle></DialogHeader>
              <AddSourceDialog onClose={() => setAddOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>

        <div className="space-y-3">
          {isLoading ? (
            [...Array(3)].map((_, i) => <Skeleton key={i} className="h-28" />)
          ) : (sources || []).length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <Rss className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No sources configured. Add your first source above.</p>
              </CardContent>
            </Card>
          ) : (
            sources?.map((source) => {
              const Icon = SOURCE_ICONS[source.source_type] || Globe
              return (
                <Card key={source.id} className={source.is_enabled ? "" : "opacity-60"}>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="p-2 rounded-lg bg-muted mt-0.5">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-medium">{source.name}</p>
                          <Badge variant="outline" className="text-xs">{SOURCE_TYPE_LABELS[source.source_type]}</Badge>
                          <SyncStatusBadge status={source.sync_status} />
                        </div>
                        {source.url && (
                          <p className="text-xs text-muted-foreground mt-0.5 truncate">{source.url}</p>
                        )}
                        {(source.keywords || []).length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {source.keywords.map((k: string) => (
                              <span key={k} className="text-xs bg-muted px-1.5 py-0.5 rounded">{k}</span>
                            ))}
                          </div>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                          {source.last_sync_at && <span>Last sync: {formatDate(source.last_sync_at)}</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Switch
                          checked={source.is_enabled}
                          onCheckedChange={(v) => toggleMutation.mutate({ id: source.id, active: v })}
                        />
                        <Button
                          variant="ghost" size="icon" className="h-8 w-8"
                          onClick={() => syncMutation.mutate(source.id)}
                          disabled={syncMutation.isPending || source.sync_status === "syncing"}
                          title="Sync now"
                        >
                          <RefreshCw className={`w-4 h-4 ${source.sync_status === "syncing" ? "animate-spin" : ""}`} />
                        </Button>
                        <Button
                          variant="ghost" size="icon" className="h-8 w-8 text-destructive"
                          onClick={() => deleteMutation.mutate(source.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
