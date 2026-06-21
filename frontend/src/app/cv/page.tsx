"use client"
import { useCallback, useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useDropzone } from "react-dropzone"
import { cvsApi } from "@/lib/api"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDate, cn } from "@/lib/utils"
import { Upload, FileText, Trash2, Star, Cpu, Eye } from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"
import type { CV } from "@/types"

function FileDrop({ onUpload }: { onUpload: (file: File) => void }) {
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(async (accepted: File[]) => {
    if (!accepted[0]) return
    setUploading(true)
    try {
      await onUpload(accepted[0])
    } finally {
      setUploading(false)
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
  })

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
        isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary/50 hover:bg-accent/30"
      )}
    >
      <input {...getInputProps()} />
      <Upload className="w-10 h-10 mx-auto mb-3 text-muted-foreground" />
      {uploading ? (
        <div className="flex items-center justify-center gap-2 text-sm">
          <span className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          Uploading...
        </div>
      ) : (
        <>
          <p className="font-medium">{isDragActive ? "Drop it here" : "Drag & drop your CV"}</p>
          <p className="text-sm text-muted-foreground mt-1">PDF or DOCX, max 10MB</p>
          <Button variant="outline" size="sm" className="mt-3">Browse files</Button>
        </>
      )}
    </div>
  )
}

export default function CVPage() {
  const qc = useQueryClient()

  const { data: cvs, isLoading } = useQuery<CV[]>({
    queryKey: ["cvs"],
    queryFn: () => cvsApi.list().then((r) => r.data),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => cvsApi.upload(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cvs"] })
      toast.success("CV uploaded! Analysis will start shortly.")
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Upload failed"),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => cvsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["cvs"] }); toast.success("CV deleted") },
  })

  const setActiveMutation = useMutation({
    mutationFn: (id: string) => cvsApi.setActive(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["cvs"] }); toast.success("Active CV updated") },
  })

  const analyzeMutation = useMutation({
    mutationFn: (id: string) => cvsApi.analyze(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["cvs"] }); toast.success("Analysis triggered") },
  })

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">My CVs</h1>
          <p className="text-muted-foreground text-sm">Upload and manage your CV versions</p>
        </div>

        <FileDrop onUpload={(file) => uploadMutation.mutate(file)} />

        <div className="space-y-3">
          <h2 className="font-semibold">Uploaded CVs ({cvs?.length || 0})</h2>
          {isLoading ? (
            [...Array(2)].map((_, i) => <Skeleton key={i} className="h-24" />)
          ) : cvs?.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p>No CVs yet. Upload your first one above.</p>
              </CardContent>
            </Card>
          ) : (
            cvs?.map((cv) => (
              <Card key={cv.id} className={cn(cv.is_active && "border-primary/40")}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="p-2 rounded-lg bg-muted">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium truncate">{cv.original_filename}</p>
                        {cv.is_active && <Badge className="bg-primary text-primary-foreground text-xs">Active</Badge>}
                        <Badge variant="outline" className="text-xs uppercase">{cv.file_type}</Badge>
                        <Badge variant={cv.is_analyzed ? "secondary" : "outline"} className="text-xs">
                          {cv.is_analyzed ? "Analyzed" : "Pending analysis"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {Math.round(cv.file_size / 1024)} KB · Uploaded {formatDate(cv.created_at)}
                      </p>
                      {cv.analysis && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {cv.analysis.skills?.length || 0} skills · {cv.analysis.work_experience?.length || 0} positions
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {cv.is_analyzed && (
                        <Link href={`/cv/${cv.id}`}>
                          <Button variant="ghost" size="icon" className="h-8 w-8"><Eye className="w-4 h-4" /></Button>
                        </Link>
                      )}
                      {!cv.is_analyzed && (
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => analyzeMutation.mutate(cv.id)}>
                          <Cpu className="w-4 h-4" />
                        </Button>
                      )}
                      {!cv.is_active && (
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setActiveMutation.mutate(cv.id)} title="Set as active">
                          <Star className="w-4 h-4" />
                        </Button>
                      )}
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => deleteMutation.mutate(cv.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
