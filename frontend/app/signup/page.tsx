"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, Loader2 } from "lucide-react"
import { motion } from "framer-motion"
import { useAuth } from "@/lib/auth/auth-context"
import { MicSparklesIcon } from "@/components/ui/mic-sparkles-icon"

export default function SignupPage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showVerification, setShowVerification] = useState(false)
  const [verificationCode, setVerificationCode] = useState("")
  const [isVerifying, setIsVerifying] = useState(false)
  
  const { register } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    
    // Validate passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }
    
    // Validate password strength
    if (password.length < 8) {
      setError("Password must be at least 8 characters long")
      return
    }
    
    setIsLoading(true)
    
    try {
      const result = await register({
        email,
        password,
        name,
      })
      
      setSuccess(result.message)
      setShowVerification(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerification = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    
    if (!verificationCode || verificationCode.length !== 6) {
      setError("Please enter a valid 6-digit verification code")
      return
    }
    
    setIsVerifying(true)
    
    try {
      const { confirmRegistration } = await import("@/lib/api/auth")
      await confirmRegistration(email, verificationCode)
      
      setSuccess("Email verified successfully! Redirecting to login...")
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed. Please try again.")
    } finally {
      setIsVerifying(false)
    }
  }

  const handleResendCode = async () => {
    setError("")
    setSuccess("")
    setIsLoading(true)
    
    try {
      // Re-register to resend the code
      const result = await register({
        email,
        password,
        name,
      })
      setSuccess("Verification code resent! Check your email.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend code.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      {/* Back to Home Link */}
      <Link
        href="/"
        className="absolute top-6 left-6 flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Home</span>
      </Link>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-accent flex items-center justify-center">
              <MicSparklesIcon size={40} className="text-accent-foreground" />
            </div>
            <span className="text-2xl font-bold">Oratio</span>
          </Link>
        </div>

        {/* Signup Card */}
        <div className="bg-card border border-border rounded-lg p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold mb-2">
              {showVerification ? "Verify your email" : "Create an account"}
            </h1>
            <p className="text-muted-foreground">
              {showVerification 
                ? `We sent a verification code to ${email}` 
                : "Get started with Oratio today"}
            </p>
          </div>

          {!showVerification ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                {error}
              </div>
            )}
            
            {success && (
              <div className="bg-green-500/10 text-green-600 text-sm p-3 rounded-md">
                {success}
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={isLoading}
                className="bg-background"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                className="bg-background"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                className="bg-background"
              />
              <p className="text-xs text-muted-foreground">
                Minimum 8 characters with uppercase, lowercase, number, and symbol
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
                className="bg-background"
              />
            </div>

            <Button 
              type="submit" 
              className="w-full bg-accent hover:bg-accent/90"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create account"
              )}
            </Button>
          </form>
          ) : (
          <form onSubmit={handleVerification} className="space-y-4">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                {error}
              </div>
            )}
            
            {success && (
              <div className="bg-green-500/10 text-green-600 text-sm p-3 rounded-md">
                {success}
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="verificationCode">Verification Code</Label>
              <Input
                id="verificationCode"
                type="text"
                placeholder="Enter 6-digit code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                required
                disabled={isVerifying}
                className="bg-background text-center text-2xl tracking-widest"
                maxLength={6}
              />
              <p className="text-xs text-muted-foreground text-center">
                Check your email for the verification code
              </p>
            </div>

            <Button 
              type="submit" 
              className="w-full bg-accent hover:bg-accent/90"
              disabled={isVerifying || verificationCode.length !== 6}
            >
              {isVerifying ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                "Verify Email"
              )}
            </Button>

            <Button 
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleResendCode}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Resending...
                </>
              ) : (
                "Resend Code"
              )}
            </Button>
          </form>
          )}

          <div className="mt-6 text-center text-sm">
            <span className="text-muted-foreground">Already have an account? </span>
            <Link href="/login" className="text-accent hover:text-accent/80 transition-colors font-medium">
              Sign in
            </Link>
          </div>
        </div>

        {/* Additional Info */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          By creating an account, you agree to our{" "}
          <Link href="#" className="text-accent hover:text-accent/80 transition-colors">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="#" className="text-accent hover:text-accent/80 transition-colors">
            Privacy Policy
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
