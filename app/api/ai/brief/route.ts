import { generateGroqResponse } from "@/lib/groq-client";
import { NextResponse } from "next/server";

const BRIEF_PROMPT = `
You are 'BENTHIC-SURVEY-ANALYST', an autonomous hydrographic survey fusion agent for the Ministry of Earth Sciences (MoES) and National Institute of Ocean Technology (NIOT).
Your goal is to provide concise operational summaries for Chief Hydrographers and Marine Cleanup Teams.

CONTEXT TO PROCESS:
1. Live Sea State / Benthic acoustic conditions (Wave heights, swell, turbidity).
2. Ecological Hazard Severity (Ghost nets, marine debris clustering).
3. Recent Sonar Detections (YOLOv8 + Acoustic Shadow Validation).
4. Survey Trackline Status (AUV coverage, ROV recovery targets).

RULES:
- Be strictly focused on marine ecology, hydrographic acoustic survey quality, and debris extraction.
- Maximum 2 sentences.
- Focus on the ACTIONABLE relationship between sea conditions and debris recovery feasibility.
- Example: "Seabed backscatter conditions at Gulf of Mannar show high acoustic contrast; 3 verified ghost net clusters ready for ROV grapple retrieval."
- Example: "Wave heights (1.8m) permit continued AUV side-scan swath mapping; prioritize low-tier acoustic shadow verification in Sector 4."

Do NOT use conversational filler. Start immediately.
`;

export async function POST(req: Request) {
  try {
    const { zoneData, detections, intercepts, missionStats } = await req.json();

    const context = `
ZONE: ${zoneData?.name || "Unknown"}
SEA STATE: Wave Height ${zoneData?.marine?.wave_height}m, Wind ${zoneData?.weather?.wind_speed}km/h
INTEL: Threat Score ${zoneData?.threatLevel}%, Piracy Index ${zoneData?.piracyIndex}/10
DETECTIONS: ${detections || "None"}
INTERCEPTS: ${intercepts || "None"}
MISSION MISSION STATS: ${missionStats || "Normal ops"}
    `.trim();

    const response = await generateGroqResponse(context, BRIEF_PROMPT);

    return NextResponse.json({ brief: response });
  } catch (error: any) {
    console.error("Fusion Brief Error:", error);
    return NextResponse.json(
      { error: "Failed to generate briefing: " + error.message },
      { status: 500 },
    );
  }
}
