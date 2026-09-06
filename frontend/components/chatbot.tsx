"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  MessageSquareCode,
  X,
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  RotateCcw,
  Copy,
  Check,
  Waves,
  ShieldAlert,
  Compass,
  FileText,
} from "lucide-react"

interface Message {
  id: string
  content: string
  sender: "user" | "bot"
  timestamp: Date
  provider?: string
}

const INITIAL_MESSAGE: Message = {
  id: "welcome",
  content:
    "Hello! I'm your AI Sonar & Marine Intelligence Assistant for Varuna. How can I help you with side-scan sonar analysis, marine debris classification, or survey operations today?",
  sender: "bot",
  timestamp: new Date(),
}

const QUICK_PROMPTS = [
  {
    label: "Debris Classes",
    icon: Compass,
    prompt: "What 8 marine debris categories can Varuna detect?",
  },
  {
    label: "Sonar Physics",
    icon: Waves,
    prompt: "How does acoustic shadow validation work in Side-Scan Sonar?",
  },
  {
    label: "Ghost Nets",
    icon: ShieldAlert,
    prompt: "Explain how ghost nets (ALDFG) are detected and prioritized.",
  },
  {
    label: "Survey Reports",
    icon: FileText,
    prompt: "How can I export survey reports in PDF, CSV, and JSON formats?",
  },
]

export function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const renderFormattedText = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={idx} className="font-semibold text-cyan-200">
            {part.slice(2, -2)}
          </strong>
        )
      }
      if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
        return (
          <code
            key={idx}
            className="bg-slate-900/90 text-cyan-300 px-1 py-0.5 rounded text-xs font-mono"
          >
            {part.slice(1, -1)}
          </code>
        )
      }
      return part
    })
  }

  const formatMessageContent = (content: string) => {
    return content.split("\n").map((line, index) => {
      const trimmed = line.trim()

      if (!trimmed) {
        return <div key={index} className="h-1.5" />
      }

      if (trimmed.startsWith("### ")) {
        return (
          <div
            key={index}
            className="text-xs font-semibold text-cyan-300 mt-2 mb-1 uppercase tracking-wider"
          >
            {renderFormattedText(trimmed.substring(4))}
          </div>
        )
      }

      if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
        const bulletText = trimmed.substring(2).trim()
        return (
          <div key={index} className="flex items-start gap-2 mb-1.5 pl-1">
            <span className="text-cyan-400 mt-0.5 text-xs select-none">•</span>
            <span className="flex-1 leading-relaxed">
              {renderFormattedText(bulletText)}
            </span>
          </div>
        )
      }

      const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/)
      if (numberedMatch) {
        return (
          <div key={index} className="flex items-start gap-2 mb-1.5 pl-1">
            <span className="text-cyan-400 font-medium text-xs mt-0.5 select-none">
              {numberedMatch[1]}.
            </span>
            <span className="flex-1 leading-relaxed">
              {renderFormattedText(numberedMatch[2])}
            </span>
          </div>
        )
      }

      return (
        <div key={index} className="mb-1.5 leading-relaxed">
          {renderFormattedText(trimmed)}
        </div>
      )
    })
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen])

  const copyToClipboard = (id: string, text: string) => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(text)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 2000)
    }
  }

  const resetChat = () => {
    setMessages([
      {
        ...INITIAL_MESSAGE,
        timestamp: new Date(),
      },
    ])
  }

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim()
    if (!text || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: text,
      sender: "user",
      timestamp: new Date(),
    }

    // Build history for conversational memory
    const historyPayload = messages.slice(-8).map((m) => ({
      sender: m.sender,
      content: m.content,
    }))

    setMessages((prev) => [...prev, userMessage])
    if (!textToSend) setInputMessage("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/ai/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          history: historyPayload,
          context:
            "Varuna - Automated Underwater Marine Debris and Ghost Net Detection System using Side-Scan Sonar (SSS) Imagery (SIH26057 / MoES & NIOT)",
        }),
      })

      let data: any = null
      try {
        data = await response.json()
      } catch {
        data = null
      }

      if (!response.ok) {
        const msg =
          data?.error ||
          data?.message ||
          `Request failed with status ${response.status}`
        throw new Error(msg)
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          data?.response ||
          "I received your inquiry but couldn't generate a response.",
        sender: "bot",
        timestamp: new Date(),
        provider: data?.provider,
      }

      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          error instanceof Error
            ? error.message
            : "I'm having trouble connecting to the AI service right now. Please try again later.",
        sender: "bot",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <>
      {/* Floating Chatbot Toggle Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <div className="relative group">
          <Button
            onClick={() => setIsOpen(!isOpen)}
            className="w-14 h-14 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-105 transition-all duration-300 flex items-center justify-center relative border border-cyan-400/30"
            aria-label="Toggle Varuna AI Chat"
          >
            {isOpen ? (
              <X className="h-6 w-6 transition-transform" />
            ) : (
              <>
                <MessageSquareCode className="h-6 w-6" />
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-400 ring-2 ring-slate-950 shadow">
                  <Sparkles className="h-2.5 w-2.5 text-slate-950" />
                </span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Chatbot Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-4 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-[420px] max-w-full">
          <Card className="bg-slate-900/95 backdrop-blur-md border-slate-700/80 shadow-2xl overflow-hidden flex flex-col rounded-xl">
            {/* Header */}
            <CardHeader className="pb-3 px-4 pt-3.5 border-b border-slate-800 bg-slate-900/90">
              <CardTitle className="flex items-center justify-between text-white text-sm">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/25 to-blue-600/25 border border-cyan-400/30 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-cyan-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 font-semibold text-slate-100 text-sm">
                      Varuna AI
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full">
                        <Sparkles className="h-2.5 w-2.5 text-cyan-400 animate-pulse" />
                        Gemini
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400">
                      Sonar Intelligence & Marine Security
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={resetChat}
                    title="Reset Conversation"
                    className="h-7 w-7 p-0 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsOpen(false)}
                    title="Close Chat"
                    className="h-7 w-7 p-0 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>

            <CardContent className="p-0 flex flex-col">
              {/* Messages Area */}
              <div className="h-[360px] overflow-y-auto p-4 space-y-3.5 scrollbar-thin scrollbar-thumb-slate-700">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex items-start gap-2.5 ${
                      message.sender === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.sender === "bot" && (
                      <div className="w-6 h-6 rounded-md bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Bot className="h-3.5 w-3.5 text-cyan-400" />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-lg text-xs sm:text-sm shadow-sm group relative ${
                        message.sender === "user"
                          ? "bg-cyan-600 text-white p-3 ml-auto"
                          : "bg-slate-800/90 text-slate-200 border border-slate-700/60 p-3.5"
                      }`}
                    >
                      {message.sender === "bot"
                        ? formatMessageContent(message.content)
                        : message.content}

                      {message.sender === "bot" && message.id !== "welcome" && (
                        <div className="mt-2 pt-1.5 border-t border-slate-700/40 flex items-center justify-between text-[10px] text-slate-400">
                          <span className="flex items-center gap-1">
                            <Sparkles className="h-2.5 w-2.5 text-cyan-400" />
                            {message.provider || "Gemini AI"}
                          </span>
                          <button
                            onClick={() =>
                              copyToClipboard(message.id, message.content)
                            }
                            className="inline-flex items-center gap-1 hover:text-cyan-300 transition-colors"
                            title="Copy message"
                          >
                            {copiedId === message.id ? (
                              <>
                                <Check className="h-3 w-3 text-emerald-400" />
                                <span className="text-emerald-400">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>

                    {message.sender === "user" && (
                      <div className="w-6 h-6 rounded-md bg-slate-700 border border-slate-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <User className="h-3.5 w-3.5 text-slate-300" />
                      </div>
                    )}
                  </div>
                ))}

                {/* Quick Prompts when only welcome message exists */}
                {messages.length === 1 && !isLoading && (
                  <div className="pt-2">
                    <p className="text-[11px] text-slate-400 font-medium mb-2 flex items-center gap-1.5">
                      <Sparkles className="h-3 w-3 text-cyan-400" />
                      Quick Topics:
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      {QUICK_PROMPTS.map((qp, idx) => {
                        const IconComponent = qp.icon
                        return (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(qp.prompt)}
                            className="text-left text-xs bg-slate-800/80 hover:bg-slate-750 border border-slate-700/70 hover:border-cyan-500/50 p-2.5 rounded-lg text-slate-300 hover:text-cyan-200 transition-all flex items-start gap-2"
                          >
                            <IconComponent className="h-3.5 w-3.5 text-cyan-400 mt-0.5 flex-shrink-0" />
                            <span className="leading-tight font-medium">
                              {qp.label}
                            </span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {isLoading && (
                  <div className="flex items-start gap-2.5">
                    <div className="w-6 h-6 rounded-md bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-3.5 w-3.5 text-cyan-400" />
                    </div>
                    <div className="bg-slate-800/90 text-slate-200 border border-slate-700/60 p-3 rounded-lg text-xs flex items-center gap-2">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                      <span>Analyzing with Gemini AI...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-3 border-t border-slate-800 bg-slate-900/90">
                <div className="flex gap-2">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about sonar physics, debris, AUV..."
                    className="bg-slate-800/90 border-slate-700 text-white placeholder:text-slate-400 text-xs sm:text-sm focus-visible:ring-cyan-500"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={() => handleSendMessage()}
                    disabled={!inputMessage.trim() || isLoading}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white px-3 h-10 transition-colors shadow-sm"
                    aria-label="Send message"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center justify-between mt-1.5 px-1 text-[10px] text-slate-400">
                  <span>Press Enter to send</span>
                  <span className="flex items-center gap-1 text-cyan-400/80">
                    <Sparkles className="h-2.5 w-2.5" />
                    MoES SIH26057
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}

