import { NextResponse } from "next/server";
import { startVideoGeneration } from "@/lib/replicate";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as {
      prompt?: string;
      style?: string;
      duration?: number;
      aspectRatio?: string;
      apiKey?: string;
    };

    const { prompt, style, duration, aspectRatio, apiKey } = body;

    if (!prompt || !style || !duration || !aspectRatio || !apiKey) {
      return NextResponse.json(
        { error: "Missing required fields: prompt, style, duration, aspectRatio, apiKey" },
        { status: 400 }
      );
    }

    if (prompt.length > 500) {
      return NextResponse.json(
        { error: "Prompt must be 500 characters or less" },
        { status: 400 }
      );
    }

    const result = await startVideoGeneration({
      apiKey,
      prompt,
      style,
      duration,
      aspectRatio,
    });

    return NextResponse.json({
      predictionId: result.id,
      status: result.status,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
