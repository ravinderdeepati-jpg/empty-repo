import { NextResponse } from "next/server";
import { checkGenerationStatus } from "@/lib/replicate";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const apiKey = request.headers.get("X-Api-Key");

    if (!apiKey) {
      return NextResponse.json(
        { error: "Missing X-Api-Key header" },
        { status: 400 }
      );
    }

    if (!id) {
      return NextResponse.json(
        { error: "Missing prediction ID" },
        { status: 400 }
      );
    }

    const result = await checkGenerationStatus({
      apiKey,
      predictionId: id,
    });

    return NextResponse.json(result);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
