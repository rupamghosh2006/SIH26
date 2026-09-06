import { groq, createGroq } from "@ai-sdk/groq"
import { generateText } from "ai"

function sanitizeKey(key: string) {
  if (!key) return ""
  // common .env mistakes: quotes, backticks, trailing spaces, and hidden characters
  return key
    .trim()
    .replace(/^['"`]|['"`]$/g, "") // Remove starting/ending quotes or backticks
    .trim()
}

function isInvalidKeyError(err: unknown) {
  const msg = err instanceof Error ? err.message : String(err)
  return /invalid api key|invalid_api_key|statuscode:\s*401/i.test(msg)
}

function isModelError(err: unknown) {
  const msg = err instanceof Error ? err.message : String(err)
  return /decommissioned|model_decommissioned|model not found|invalid model/i.test(msg)
}

export async function generateGroqResponse(message: string, context: string = "") {
  const rawKey = process.env.GROQ_API_KEY || ""
  const key = sanitizeKey(rawKey)

  if (process.env.NODE_ENV !== "production") {
    const masked =
      key.length > 8
        ? `${key.slice(0, 4)}...${key.slice(-4)}`
        : "INVALID_LENGTH"
    console.log(`[Groq] Debug: Key Length: ${key.length}, Masked: ${masked}`)
  }

  if (!key) {
    throw new Error("Missing GROQ_API_KEY in environment variables")
  }

  // Ensure the SDK sees GROQ_API_KEY
  process.env.GROQ_API_KEY = key

  const systemPrompt = `You are an AI assistant for Varuna AI — an advanced AI-powered platform for SIH26057: Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar (SSS) Imagery.

${context}

Key features of the platform include:
- Side-Scan Sonar (SSS) raw waterfall image ingestion and preprocessing (speckle noise reduction, CLAHE contrast enhancement, Lee filtering)
- AI/ML computer-vision detection (YOLOv8 & U-Net) for 8 marine debris categories:
  1. Ghost Nets & ALDFG (Abandoned, Lost, or Discarded Fishing Gear)
  2. Fishing Gear / Lines
  3. Tires & Rubber Waste
  4. Containers & Industrial Chemical Drums
  5. Subsea Metal Objects & Pipelines
  6. Shipwreck & Structural Fragments
  7. Natural Rock Clusters & Seabed Geology (False Positive Control)
  8. Unidentified Acoustic Anomalies
- Physics-based acoustic shadow validation and unambiguous 0-100% confidence scoring
- Human-in-the-Loop Operator Verification widget (Confirm, False Alarm, Reclassify, Operator Field Notes)
- Multi-format survey report generation (Printable PDF Survey Document, Structured JSON, Geotagged CSV)
- GIS bathymetry mapping, AUV swath survey planning, and ocean cleanup dispatch telemetry.

You should assist marine researchers, sonar operators, and conservationists with:
- Understanding side-scan sonar backscatter and acoustic shadow physics
- Explaining marine debris classification and ecological risk severity
- Guiding users through survey image uploads and AI detection pipelines
- Assisting with survey report exports and AUV swath planning.

IMPORTANT: When providing lists or multiple points, use proper bullet point formatting with "-" at the beginning of each line. This will ensure proper display in the chat interface.

Keep responses helpful, informative, and focused on the platform's capabilities. Be concise but thorough.

User message: ${message}`

  // Allow override via env, but fall back to a safe list.
  // Use a cheaper/free-ish default first.
  const preferred = (process.env.GROQ_MODEL || "").trim()
  const candidates = [
    preferred,
    // cheaper / fast
    "llama-3.1-8b-instant",
    // fallbacks (may or may not be enabled on a given account)
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
  ].filter(Boolean)

  let lastError: any = null
  for (const modelId of candidates) {
    try {
      // Create a specific groq instance with our sanitized key
      const groqProvider = createGroq({ apiKey: key })
      const model = groqProvider(modelId)

      const result = await generateText({
        model,
        prompt: systemPrompt,
        temperature: 0.7,
      })
      return result.text
    } catch (err) {
      lastError = err
      console.error(`[Groq] Attempt failed with model ${modelId}:`, err)

      if (isInvalidKeyError(err)) {
        throw new Error(
          `Invalid GROQ_API_KEY. Key length: ${key.length}. Error details: ${err instanceof Error ? err.message : String(err)}`
        )
      }
      // If this model is invalid/decommissioned, try the next one.
      if (isModelError(err)) {
        continue
      }
      // For other errors, try the next model as well.
      continue
    }
  }

  const msg = lastError instanceof Error ? lastError.message : String(lastError)
  throw new Error(`Groq request failed across models. Last error: ${msg}`)
}






