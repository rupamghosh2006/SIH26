import { NextRequest, NextResponse } from "next/server"
import { generateGroqResponse } from "@/lib/groq-client"

// Helper to load detections from client (we'll pass data from client)
interface ThreatData {
  totalDetections: number
  totalThreats: number
  criticalThreats: number
  highThreats: number
  mediumThreats: number
  lowThreats: number
  avgConfidence: number
  recentDetections: Array<{
    level: string
    objects: number
    confidence: number
    time: string
    classes: string[]
  }>
  threatBreakdown: {
    critical: number
    high: number
    medium: number
    low: number
  }
  classDistribution: Record<string, number>
  detectionRate: number
  threatTrend: string
  mostDetectedClass: string
  peakThreatLevel: string
  recentActivityCount: number
}

export async function POST(request: NextRequest) {
  try {
    const { type, threatData, query } = await request.json()

    if (!threatData) {
      return NextResponse.json(
        { error: "Threat data is required" },
        { status: 400 }
      )
    }

    const data: ThreatData = threatData

    let prompt = ""
    let context = ""

    switch (type) {
      case "analysis":
        prompt = `Analyze the following Side-Scan Sonar (SSS) marine debris survey data and provide a comprehensive ecological intelligence report:

DEBRIS SURVEY STATISTICS:
- Total Sonar Scans: ${data.totalDetections}
- Total Marine Debris Objects Isolated: ${data.totalThreats}
- Critical Ecological Hazards (Ghost Nets / Toxicity): ${data.criticalThreats}
- High Priority Debris (Subsea Containers / Metal Obstructions): ${data.highThreats}
- Medium Risk Pollution (Tires / Rubber Waste): ${data.mediumThreats}
- Low Risk / Seabed Geology Control: ${data.lowThreats}
- Average Classification Confidence: ${data.avgConfidence}%
- Debris Isolation Rate: ${data.detectionRate.toFixed(2)} objects/hour
- Debris Accumulation Trend: ${data.threatTrend}
- Dominant Debris Category: ${data.mostDetectedClass}
- Peak Ecological Risk: ${data.peakThreatLevel}
- Recent Survey Activity (24h): ${data.recentActivityCount} records

ECOLOGICAL RISK BREAKDOWN:
- Critical (Entanglement / Reef Damage): ${data.threatBreakdown.critical}
- High (Navigation Obstruction / Toxic Storage): ${data.threatBreakdown.high}
- Medium (Anthropogenic Polymer Pollution): ${data.threatBreakdown.medium}
- Low (Seafloor Geology / False Positive Control): ${data.threatBreakdown.low}

DEBRIS CLASS DISTRIBUTION:
${Object.entries(data.classDistribution).map(([cls, count]) => `- ${cls}: ${count} objects`).join('\n')}

RECENT DETECTIONS (Last 10):
${data.recentDetections.slice(0, 10).map((det, idx) => 
  `${idx + 1}. Risk: ${det.level}, Objects: ${det.objects}, Confidence: ${det.confidence}%, Classes: ${det.classes.join(', ')}, Time: ${det.time}`
).join('\n')}

Provide a comprehensive ecological survey intelligence report with:
1. **Executive Summary**: Key findings and seabed debris density assessment
2. **Debris Spatial Patterns**: Identify acoustic clustering, ALDFG entanglement hotspots, and benthic degradation
3. **Ecological Impact Rating**: Evaluate risk to marine biodiversity, coral reefs, and vessel navigation
4. **Human-in-the-Loop Audit Recommendations**: Critical items requiring ROV/diver verification
5. **Targeted Cleanup Strategy**: Recommended AUV swath paths and retrieval priorities
6. **Drift & Accumulation Forecast**: Predicted debris migration based on oceanographic currents

Format the response in clear sections with bullet points.`

        context = "Varuna AI Marine Debris & Ecological Hazard Assessment - Autonomous Underwater SSS Classification"
        break

      case "recommendations":
        prompt = `Based on the following Side-Scan Sonar marine debris survey data, provide actionable ocean cleanup, AUV swath survey, and ecological restoration recommendations:

SURVEY OVERVIEW:
- Total Sonar Detections: ${data.totalDetections}
- Critical Entanglement Hazards (Ghost Nets): ${data.criticalThreats}
- High Priority Debris: ${data.highThreats}
- Dominant Class: ${data.mostDetectedClass}
- Accumulation Trend: ${data.threatTrend}

DEBRIS DISTRIBUTION:
${JSON.stringify(data.classDistribution, null, 2)}

Provide strategic recommendations in the following categories:
1. **Immediate ROV / Diver Extraction**: High-risk targets (ALDFG ghost nets, chemical drums)
2. **AUV Swath Path Optimization**: Recommended survey coordinates for unmapped seafloor
3. **Coral Reef & Benthic Ecosystem Protection**: Safeguards for sensitive marine habitats
4. **Fisheries & Port Waste Mitigation**: Preventative measures for fishing gear loss
5. **Sensor & Algorithm Tuning**: Preprocessing adjustments for local seafloor backscatter

Format with clear sections and actionable bullet points.`

        context = "Varuna AI Marine Debris Remediation and Ecosystem Recovery Strategy"
        break

      case "prediction":
        prompt = `Analyze marine debris accumulation patterns and ocean current dynamics to predict future debris drift and deposition hotspots:

SURVEY DATA:
- Total Sonar Detections: ${data.totalDetections}
- Recent Activity (24h): ${data.recentActivityCount}
- Isolation Rate: ${data.detectionRate.toFixed(2)} objects/hour
- Accumulation Trend: ${data.threatTrend}
- Dominant Class: ${data.mostDetectedClass}
- Peak Ecological Risk: ${data.peakThreatLevel}

RECENT ANOMALY RECORDS:
${data.recentDetections.slice(0, 10).map((det, idx) => 
  `${idx + 1}. ${det.level} risk with ${det.objects} debris items (${det.classes.join(', ')}) at ${det.time}`
).join('\n')}

Provide predictive debris modeling including:
1. **48-Hour Debris Drift Forecast**: Expected displacement due to bottom currents & tides
2. **Entanglement Risk Zones**: High-probability reef and benthic impact corridors
3. **Ghost Fishing Potential**: Estimated ongoing mortality risk to marine fauna
4. **Acoustic Backscatter Anomalies**: Sub-seabed partial burial predictions
5. **Targeted AUV Interception Coordinates**: Best waypoints for cleanup dispatch`

        context = "Varuna AI Predictive Marine Debris Drift & Accumulation Modeling"
        break

      case "query":
        if (!query) {
          return NextResponse.json(
            { error: "Query is required for query type" },
            { status: 400 }
          )
        }
        prompt = `Answer the following question about marine security threats based on this data:

QUESTION: ${query}

THREAT DATA:
- Total Detections: ${data.totalDetections}
- Critical Threats: ${data.criticalThreats}
- High Threats: ${data.highThreats}
- Average Confidence: ${data.avgConfidence}%
- Threat Trend: ${data.threatTrend}
- Most Detected Class: ${data.mostDetectedClass}
- Recent Activity: ${data.recentActivityCount} detections in last 24 hours

THREAT BREAKDOWN:
${JSON.stringify(data.threatBreakdown, null, 2)}

CLASS DISTRIBUTION:
${JSON.stringify(data.classDistribution, null, 2)}

Provide a detailed, accurate answer based on the data provided. If the question cannot be answered with the available data, explain what information would be needed.`

        context = "Marine Security Threat Intelligence Q&A - AI-powered threat data analysis and insights"
        break

      default:
        return NextResponse.json(
          { error: "Invalid type. Must be 'analysis', 'recommendations', 'prediction', or 'query'" },
          { status: 400 }
        )
    }

    const response = await generateGroqResponse(prompt, context)

    return NextResponse.json({
      success: true,
      response,
      type,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error("Threat Intelligence API error:", error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    return NextResponse.json(
      { 
        error: `Failed to generate threat intelligence: ${errorMessage}`,
        success: false
      },
      { status: 500 }
    )
  }
}


