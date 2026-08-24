/**
 * GeneratePrompt.tsx — Build 3: AI Prompt Engine chat interface
 * =============================================================
 * A dedicated chat-style page for natural-language scenario generation.
 *
 * Flow:
 *   1. User types a scenario description
 *   2. Calls POST /prompt/parse for live preview
 *   3. Displays parsed Scenario JSON for review/edit
 *   4. Shows validation errors or follow-up questions inline
 *   5. "Generate" submits to POST /prompt/generate (real job pipeline)
 *
 * Coexists with the form-based GenerateDataset.tsx — this is additive.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  Sparkles, Loader2, Send, ChevronDown, ChevronUp,
  CheckCircle2, AlertCircle, X, Play, FileText
} from 'lucide-react'
import { parsePrompt, parseAndSubmit } from '../services/prompt'
import type { PromptParseResult } from '../services/prompt'
import Navbar from '../components/Navbar'
import { useAuth } from '../contexts/AuthContext'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  scenario?: PromptParseResult
  error?: string
  jobId?: string
}

export default function GeneratePrompt() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [projects, setProjects] = useState<Array<{ id: string; name: string }>>([])
  const [selectedProject, setSelectedProject] = useState('')
  const [showJson, setShowJson] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    async function fetchProjects() {
      try {
        const res = await fetch('http://127.0.0.1:8000/projects', {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        setProjects(data)
        if (data.length > 0) setSelectedProject(data[0].id)
      } catch (e) {
        console.error(e)
      }
    }
    if (token) fetchProjects()
  }, [token])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const parseMutation = useMutation({
    mutationFn: parsePrompt,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Here is the parsed configuration. Review it below and click Generate when ready.',
          scenario: data,
        },
      ])
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.message || 'Parse failed'
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: msg,
          error: msg,
        },
      ])
    },
  })

  const generateMutation = useMutation({
    mutationFn: ({ prompt, projectId }: { prompt: string; projectId: string }) =>
      parseAndSubmit(prompt, projectId),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Job submitted successfully! Job ID: ${data.job_id}. You can track progress on the Jobs page.`,
          jobId: data.job_id,
        },
      ])
      setTimeout(() => navigate('/jobs'), 1500)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || err?.message || 'Generation failed'
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Generation failed: ${msg}`,
          error: msg,
        },
      ])
    },
  })

  const handleSend = useCallback(() => {
    if (!input.trim()) return
    const prompt = input.trim()
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: prompt }])
    setInput('')
    parseMutation.mutate(prompt)
  }, [input, parseMutation])

  const handleGenerate = useCallback(() => {
    if (!selectedProject) return alert('Please select a project first.')
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
    if (!lastUserMsg) return
    generateMutation.mutate({ prompt: lastUserMsg.content, projectId: selectedProject })
  }, [selectedProject, messages, generateMutation])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="animate-fade-in h-screen flex flex-col">
      <Navbar title="AI Prompt Engine" subtitle="Describe a scenario in plain English" />

      <div className="flex-1 overflow-hidden flex flex-col max-w-3xl mx-auto w-full">
        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-500 text-sm mt-20">
              <Sparkles size={48} className="mx-auto mb-4 text-brand-500/40" />
              <p className="text-lg font-semibold text-slate-300 mb-2">Describe your driving scenario</p>
              <p>Try: "Rainy Tokyo highway at night with heavy truck traffic"</p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-brand-600 text-white rounded-br-md'
                    : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-md'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {msg.error && (
                  <div className="mt-2 flex items-center gap-1.5 text-red-400 text-xs">
                    <AlertCircle size={12} />
                    <span>{msg.error}</span>
                  </div>
                )}

                {msg.jobId && (
                  <div className="mt-2 flex items-center gap-1.5 text-emerald-400 text-xs">
                    <CheckCircle2 size={12} />
                    <span>Job queued: {msg.jobId.slice(0, 12)}...</span>
                  </div>
                )}

                {msg.scenario && (
                  <div className="mt-3 border-t border-slate-700/60 pt-3">
                    <button
                      onClick={() => setShowJson((v) => !v)}
                      className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors"
                    >
                      <FileText size={12} />
                      Parsed Configuration
                      {showJson ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>

                    {showJson && (
                      <pre className="mt-2 bg-slate-900/80 rounded-lg p-3 text-xs text-slate-300 overflow-x-auto border border-slate-700/50">
                        {JSON.stringify(msg.scenario, null, 2)}
                      </pre>
                    )}

                    {!msg.jobId && selectedProject && (
                      <button
                        onClick={handleGenerate}
                        disabled={generateMutation.isPending}
                        className="mt-3 btn-primary w-full justify-center py-2.5 text-xs disabled:opacity-60"
                      >
                        {generateMutation.isPending ? (
                          <><Loader2 size={13} className="animate-spin" /> Submitting...</>
                        ) : (
                          <><Play size={13} /> Generate Dataset</>
                        )}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {(parseMutation.isPending || generateMutation.isPending) && (
            <div className="flex justify-start">
              <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-md px-4 py-3">
                <Loader2 size={16} className="animate-spin text-brand-400" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-slate-800 p-4 bg-slate-900/50">
          <div className="flex gap-2">
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-brand-500/60"
            >
              <option value="" disabled>Select project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe a scenario..."
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500/60 focus:ring-1 focus:ring-brand-500/30 transition-all placeholder:text-slate-600"
              />
              {input && (
                <button
                  onClick={() => setInput('')}
                  className="absolute right-10 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || parseMutation.isPending}
              className="btn-primary px-4 py-2.5 disabled:opacity-60"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
