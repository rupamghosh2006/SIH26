import { GoogleGenerativeAI } from "@google/generative-ai"

export const TEXT_MODEL_ID = "gemini-2.5-flash"
export const VISION_MODEL_ID = process.env.GEMINI_VISION_MODEL_ID || "gemini-2.5-flash"

function sanitizeKey(key: string): string {
  if (!key) return ""
  return key
    .trim()
    .replace(/^['"`]|['"`]$/g, "")
    .trim()
}

export function getGeminiApiKey(): string {
  const rawKey =
    process.env.GEMINI_API_KEY ||
    process.env.GOOGLE_API_KEY ||
    process.env.GOOGLE_GENERATIVE_AI_API_KEY ||
    ""
  return sanitizeKey(rawKey)
}

const getGeminiClient = (apiKeyOverride?: string) => {
  const key = apiKeyOverride || getGeminiApiKey()
  if (!key) {
    throw new Error("Missing GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable")
  }
  return new GoogleGenerativeAI(key)
}

// Cached list of models returned from Google API for the given key
let cachedModels: { timestamp: number; models: string[] } | null = null

async function getAvailableGeminiModels(apiKey: string): Promise<string[]> {
  const now = Date.now()
  if (
    cachedModels &&
    now - cachedModels.timestamp < 10 * 60 * 1000 &&
    cachedModels.models.length > 0
  ) {
    return cachedModels.models
  }

  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`,
      { headers: { Accept: "application/json" } }
    )
    if (res.ok) {
      const data = await res.json()
      if (data?.models && Array.isArray(data.models)) {
        const models: string[] = data.models
          .filter(
            (m: any) =>
              Array.isArray(m.supportedGenerationMethods) &&
              m.supportedGenerationMethods.includes("generateContent")
          )
          .map((m: any) => m.name.replace(/^models\//, ""))

        if (models.length > 0) {
          cachedModels = { timestamp: now, models }
          return models
        }
      }
    }
  } catch (err) {
    console.warn("[Gemini] Unable to list models from Google API, using fallback candidates:", err)
  }

  return []
}

// Get the Gemini Flash model for text generation
export const getGeminiFlashModel = () => {
  const genAI = getGeminiClient()
  return genAI.getGenerativeModel({ model: TEXT_MODEL_ID })
}

// Get the Gemini Flash model for image analysis
export const getGeminiFlashVisionModel = () => {
  const genAI = getGeminiClient()
  return genAI.getGenerativeModel({ model: VISION_MODEL_ID })
}

export interface ChatMessageItem {
  sender: "user" | "bot"
  content: string
}

export async function generateGeminiChatResponse(
  message: string,
  history: ChatMessageItem[] = [],
  context: string = ""
): Promise<string> {
  const apiKey = getGeminiApiKey()
  if (!apiKey) {
    throw new Error("Missing GEMINI_API_KEY in environment variables")
  }

  const genAI = getGeminiClient(apiKey)

  const systemInstruction = `You are the AI Marine Operations & Sonar Intelligence Assistant for Varuna — an advanced deep-sea intelligence platform developed for SIH26057: Automated Underwater Marine Debris and Ghost Net Detection System using Side-Scan Sonar (SSS) Imagery (MoES & NIOT).

${context ? `Platform Context: ${context}\n` : ""}
Platform Capabilities & Domain Knowledge:
- Side-Scan Sonar (SSS) raw acoustic waterfall processing (speckle noise filtering, CLAHE contrast equalization, slant-range correction, Lee filter).
- Detection of 8 marine debris categories:
  1. Ghost Nets & ALDFG (Abandoned, Lost, or Discarded Fishing Gear) - highest entanglement hazard
  2. Fishing Gear / Lines & Longlines
  3. Tires & Rubber Waste
  4. Containers & Industrial Chemical Drums - toxic benthic hazards
  5. Subsea Metal Objects & Pipelines
  6. Shipwreck & Structural Fragments
  7. Natural Rock Clusters & Seabed Geology (False Positive Control)
  8. Unidentified Acoustic Anomalies
- Sonar Physics Validation: Distinguishes high-backscatter sonar reflections from acoustic shadows cast by raised seafloor debris.
- Human-in-the-Loop Operator Verification widget (Confirm, False Alarm, Reclassify, Operator Field Notes).
- GIS Bathymetry Mapping, AUV Swath Survey Planning, and autonomous debris recovery dispatch.
- Multi-format survey report exports (PDF Survey Document, GeoJSON, CSV).

Guidance for responses:
- Tone: Expert, authoritative yet accessible marine hydrographer and AI analyst.
- Format: Use clear bullet points starting with '-' when providing lists or multi-step recommendations.
- Keep answers focused, insightful, and actionable for marine conservationists and sonar operators.
`

  const preferredModel = (process.env.GEMINI_MODEL || "").trim()
  const liveModels = await getAvailableGeminiModels(apiKey)

  const priorityOrder = [
    preferredModel,
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
  ].filter(Boolean)

  let candidateModels: string[] = []
  if (liveModels.length > 0) {
    const sortedLive = [...liveModels].sort((a, b) => {
      const idxA = priorityOrder.indexOf(a)
      const idxB = priorityOrder.indexOf(b)
      if (idxA !== -1 && idxB !== -1) return idxA - idxB
      if (idxA !== -1) return -1
      if (idxB !== -1) return 1
      if (a.includes("flash") && !b.includes("flash")) return -1
      if (!a.includes("flash") && b.includes("flash")) return 1
      return 0
    })
    candidateModels = preferredModel
      ? [preferredModel, ...sortedLive.filter((m) => m !== preferredModel)]
      : sortedLive
  } else {
    candidateModels = priorityOrder
  }

  // Normalize history to alternate strictly: user, model, user, model...
  const alternatingHistory: Array<{ role: "user" | "model"; parts: [{ text: string }] }> = []
  for (const h of history) {
    if (!h.content || !h.content.trim()) continue
    const role = h.sender === "user" ? "user" : "model"
    if (alternatingHistory.length === 0) {
      if (role === "user") {
        alternatingHistory.push({ role, parts: [{ text: h.content.trim() }] })
      }
    } else {
      const lastRole = alternatingHistory[alternatingHistory.length - 1].role
      if (lastRole !== role) {
        alternatingHistory.push({ role, parts: [{ text: h.content.trim() }] })
      } else {
        alternatingHistory[alternatingHistory.length - 1].parts[0].text += `\n${h.content.trim()}`
      }
    }
  }

  // Multi-turn chats in Gemini must end on 'model' before user sends next message
  if (alternatingHistory.length > 0 && alternatingHistory[alternatingHistory.length - 1].role === "user") {
    alternatingHistory.pop()
  }

  // Keep recent context within reasonable token bounds
  const trimmedHistory = alternatingHistory.slice(-8)

  const triedModels: string[] = []
  let lastError: unknown = null

  for (const modelId of candidateModels) {
    triedModels.push(modelId)
    try {
      const model = genAI.getGenerativeModel({
        model: modelId,
        systemInstruction: systemInstruction,
      })

      if (trimmedHistory.length > 0) {
        try {
          const chat = model.startChat({
            history: trimmedHistory,
          })
          const result = await chat.sendMessage(message)
          const text = result.response.text()
          if (text) return text
        } catch (chatErr) {
          console.warn(`[Gemini] Chat session with model ${modelId} failed, falling back to generateContent:`, chatErr)
          // Fall back to direct content generation if chat session fails
          const directResult = await model.generateContent(message)
          const text = directResult.response.text()
          if (text) return text
        }
      } else {
        const result = await model.generateContent(message)
        const text = result.response.text()
        if (text) return text
      }
    } catch (err) {
      lastError = err
      console.warn(`[Gemini] Attempt with model '${modelId}' failed:`, err)
      continue
    }
  }

  const errorMsg = lastError instanceof Error ? lastError.message : String(lastError)
  throw new Error(`Gemini generation failed across models (attempted: ${triedModels.slice(0, 5).join(", ")}): ${errorMsg}`)
}

export interface SpeciesIdentificationResult {
  species: string
  confidence: number
  scientificName: string
  commonName?: string
  classification: {
    kingdom: string
    phylum: string
    class: string
    order: string
    family: string
    genus: string
  }
  habitat: string
  conservationStatus: string
  threats: string[]
  description: string
}

export interface ThreatAssessmentResult {
  threatLevel: "low" | "moderate" | "high" | "critical"
  primaryThreats: string[]
  humanImpactFactors: string[]
  affectedSpecies: string[]
  timeframe: string
  recommendations: string[]
  urgency: number // 1-10 scale
}

export interface ConservationRecommendation {
  priority: "low" | "medium" | "high" | "urgent"
  actions: string[]
  timeline: string
  resources: string[]
  expectedOutcome: string
  monitoringPlan: string[]
  stakeholders: string[]
}

export interface WaterQualityAnalysis {
  overallQuality: "excellent" | "good" | "moderate" | "poor" | "critical"
  qualityIndex: number // 0-100
  contaminationLevel: "low" | "moderate" | "high" | "severe"
  primaryContaminants: string[]
  healthRisks: string[]
  ecosystemImpact: string
  recommendations: string[]
  monitoringNeeds: string[]
}
