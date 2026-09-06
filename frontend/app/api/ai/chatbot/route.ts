import { NextRequest, NextResponse } from "next/server"
import {
  generateGeminiChatResponse,
  getGeminiApiKey,
  ChatMessageItem,
} from "@/lib/gemini-client"
import { generateGroqResponse } from "@/lib/groq-client"

function getOfflineAnswer(query: string): string {
  const q = query.toLowerCase()

  if (q.includes("ghost net") || q.includes("aldfg") || q.includes("fishing gear")) {
    return [
      "**Ghost Nets & ALDFG (Abandoned, Lost, or Discarded Fishing Gear)**:",
      "- Ghost nets are one of the most critical benthic ecological hazards.",
      "- In Side-Scan Sonar (SSS) imagery, they appear as irregular, high-scattering fibrous textures often accompanied by characteristic acoustic shadows.",
      "- Varuna isolates ghost net coordinates with 0-100% confidence scoring and calculates entanglement risk indices to prioritize ROV and diver retrieval.",
    ].join("\n")
  }

  if (q.includes("debris") || q.includes("categor") || q.includes("class")) {
    return [
      "**Varuna classifies 8 distinct marine debris categories from SSS imagery**:",
      "1. **Ghost Nets & ALDFG**: High entanglement hazard for benthic ecosystems.",
      "2. **Fishing Gear & Longlines**: Subsea lines, traps, and synthetic ropes.",
      "3. **Tires & Rubber Waste**: Common near harbors and ship channels.",
      "4. **Containers & Chemical Drums**: Toxic benthic leakage hazards.",
      "5. **Subsea Metal Objects & Pipelines**: Structural navigation hazards.",
      "6. **Shipwreck & Structural Fragments**: Sunken timber, steel hulls, and debris fields.",
      "7. **Natural Rock Clusters & Seabed Geology**: Used for false-positive suppression.",
      "8. **Unidentified Acoustic Anomalies**: Irregular highlights flagged for operator audit.",
    ].join("\n")
  }

  if (q.includes("sonar") || q.includes("physics") || q.includes("shadow")) {
    return [
      "**Side-Scan Sonar (SSS) & Acoustic Shadow Validation**:",
      "- SSS emits high-frequency acoustic pings across seafloor swaths.",
      "- Hard seafloor objects reflect sound waves back (high backscatter / highlight).",
      "- The area directly behind an elevated object receives no acoustic energy, producing an **acoustic shadow**.",
      "- Varuna analyzes shadow length, grazing angle, and vehicle altitude to calculate object elevation and confirm detections.",
    ].join("\n")
  }

  if (q.includes("report") || q.includes("export") || q.includes("pdf")) {
    return [
      "**Survey Reporting & Export Formats**:",
      "- **PDF Survey Report**: Printable, publication-ready summary with detection tables, confidence metrics, and acoustic snapshots.",
      "- **Structured JSON**: Complete machine-readable anomaly payload for GIS pipelines.",
      "- **Geotagged CSV**: Lat/Long coordinate list for AUV swath planning and salvage vessels.",
      "- Head over to the **Detections** or **Analytics** page to export reports.",
    ].join("\n")
  }

  return [
    "I’m currently running in **offline mode** because `GEMINI_API_KEY` has not yet been detected.",
    "",
    "### How to activate Live Gemini AI:",
    "- **On Vercel**: Go to **Project Settings > Environment Variables**, add `GEMINI_API_KEY` (with your Gemini API key), and redeploy.",
    "- **Locally**: Add `GEMINI_API_KEY=your_key` to `.env.local`.",
    "",
    "### Platform Navigation:",
    "- Explore **Live Detections** to test sonar image preprocessing and YOLOv8 inference.",
    "- Check **Analytics & Threat Intel** for benthic hazard clustering.",
    "- Use **/profile** to configure your operator credentials.",
  ].join("\n")
}

export async function POST(request: NextRequest) {
  try {
    const { message, context, history } = await request.json()

    if (!message || typeof message !== "string" || !message.trim()) {
      return NextResponse.json(
        { error: "A valid message string is required" },
        { status: 400 }
      )
    }

    const ctx = context || ""
    const chatHistory: ChatMessageItem[] = Array.isArray(history) ? history : []

    const geminiKey = getGeminiApiKey()
    const hasGroq = Boolean(process.env.GROQ_API_KEY)

    const debugFlags = {
      hasGEMINI_KEY: Boolean(geminiKey),
      hasGROQ_KEY: hasGroq,
      nodeEnv: process.env.NODE_ENV || "unknown",
      geminiModel: process.env.GEMINI_MODEL || "gemini-1.5-flash",
    }

    if (process.env.NODE_ENV !== "production") {
      console.log("[chatbot] AI provider flags:", debugFlags)
    }

    // 1. Primary: Gemini API
    if (geminiKey) {
      try {
        const response = await generateGeminiChatResponse(message, chatHistory, ctx)
        return NextResponse.json({
          response,
          provider: "gemini",
          model: process.env.GEMINI_MODEL || "gemini-1.5-flash",
        })
      } catch (geminiError) {
        console.error("[chatbot] Gemini error:", geminiError)
        // If Groq is configured, fall back to Groq
        if (hasGroq) {
          console.log("[chatbot] Falling back to Groq...")
          try {
            const response = await generateGroqResponse(message, ctx)
            return NextResponse.json({ response, provider: "groq (fallback)" })
          } catch (groqError) {
            console.error("[chatbot] Groq fallback error:", groqError)
          }
        }
        throw geminiError
      }
    }

    // 2. Secondary: Groq API
    if (hasGroq) {
      try {
        const response = await generateGroqResponse(message, ctx)
        return NextResponse.json({ response, provider: "groq" })
      } catch (groqError) {
        console.error("[chatbot] Groq error:", groqError)
        throw groqError
      }
    }

    // 3. Informative Offline Fallback
    const response = getOfflineAnswer(message)

    return NextResponse.json({
      response,
      provider: "offline",
      ...(process.env.NODE_ENV !== "production" ? { debug: debugFlags } : {}),
    })
  } catch (error) {
    console.error("Chatbot API error:", error)
    const errorMessage = error instanceof Error ? error.message : "Unknown error"
    return NextResponse.json(
      { error: `Failed to generate AI response: ${errorMessage}` },
      { status: 500 }
    )
  }
}
