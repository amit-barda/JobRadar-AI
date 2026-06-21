"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Target, Briefcase, Brain, BarChart3 } from "lucide-react"
import { useAuthContext } from "@/context/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const schema = z.object({
  email: z.string().email("Valid email required"),
  password: z.string().min(6, "Min 6 characters"),
  full_name: z.string().optional(),
})
type FormData = z.infer<typeof schema>

const features = [
  { icon: Briefcase, title: "Smart Job Tracking", desc: "Collect jobs from LinkedIn, Glassdoor, Drushim, and more" },
  { icon: Brain, title: "AI-Powered Analysis", desc: "AI analyzes every job and matches it against your CV" },
  { icon: BarChart3, title: "ATS Score Matching", desc: "Know your match score before you apply" },
]

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuthContext()
  const router = useRouter()

  const { register: reg, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      if (isRegister) {
        await register(data.email, data.password, data.full_name || "")
      } else {
        await login(data.email, data.password)
      }
      router.replace("/dashboard")
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Something went wrong"
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* Left side */}
      <div className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/10 via-primary/5 to-background p-12">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary">
            <Target className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="font-bold text-xl">JobRadar <span className="text-primary">AI</span></span>
        </div>

        <div className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold leading-tight">
              Land your first PM role faster with AI
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Track jobs, analyze your CV, and get tailored interview prep — all in one place.
            </p>
          </div>

          <div className="space-y-4">
            {features.map((f) => {
              const Icon = f.icon
              return (
                <div key={f.title} className="flex items-start gap-3">
                  <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10 shrink-0">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{f.title}</p>
                    <p className="text-sm text-muted-foreground">{f.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <p className="text-sm text-muted-foreground">
          Demo: demo@jobradar.ai / demo123
        </p>
      </div>

      {/* Right side */}
      <div className="flex items-center justify-center p-8">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2 mb-2 lg:hidden">
              <Target className="w-6 h-6 text-primary" />
              <span className="font-bold text-lg">JobRadar AI</span>
            </div>
            <CardTitle>{isRegister ? "Create your account" : "Welcome back"}</CardTitle>
            <CardDescription>
              {isRegister ? "Start tracking your job search journey" : "Sign in to your account"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input id="full_name" placeholder="Your name" {...reg("full_name")} />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="you@example.com" {...reg("email")} />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" placeholder="••••••••" {...reg("password")} />
                {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    {isRegister ? "Creating account..." : "Signing in..."}
                  </span>
                ) : (
                  isRegister ? "Create account" : "Sign in"
                )}
              </Button>
            </form>

            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {isRegister ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
              </button>
            </div>

            {!isRegister && (
              <div className="mt-4 p-3 rounded-lg bg-muted text-xs text-muted-foreground text-center">
                Demo: demo@jobradar.ai / demo123
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
