const REPLICATE_API_URL = "https://api.replicate.com/v1/predictions";

/** Model version hash for minimax/video-01-live (text-to-video model) */
const REPLICATE_MODEL_VERSION =
  "c0a4015dc68a6da82e26aa02e1b0704c2634816495550a1e4e22e10b8e4b02c4";

/** Frames per second produced by the video model; used to calculate num_frames from duration */
const MODEL_FPS = 8;

const STYLE_MODIFIERS: Record<string, string> = {
  "Brainrot Classic":
    "in a fast-paced brainrot meme style with zooming effects and chaotic energy",
  "Meme Format":
    "in a viral meme format with bold text overlays and exaggerated reactions",
  "Educational Parody":
    "as an educational parody with dramatic narration and absurd visuals",
  "Product Showcase":
    "as a satirical product showcase with over-the-top effects and hype energy",
  Storytelling:
    "as an epic storytelling sequence with dramatic camera movements and cinematic flair",
  "Satisfying Loop":
    "as a perfectly looping satisfying video with smooth transitions and ASMR vibes",
};

export async function startVideoGeneration(params: {
  apiKey: string;
  prompt: string;
  style: string;
  duration: number;
  aspectRatio: string;
}): Promise<{ id: string; status: string }> {
  const styleModifier = STYLE_MODIFIERS[params.style] || "";
  const enhancedPrompt = styleModifier
    ? `${params.prompt}, ${styleModifier}`
    : params.prompt;

  const response = await fetch(REPLICATE_API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${params.apiKey}`,
      "Content-Type": "application/json",
      Prefer: "wait",
    },
    body: JSON.stringify({
      version: REPLICATE_MODEL_VERSION,
      input: {
        prompt: enhancedPrompt,
        num_frames: params.duration * MODEL_FPS,
        aspect_ratio: params.aspectRatio,
      },
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      (error as { detail?: string }).detail ||
        `Replicate API error: ${response.status}`
    );
  }

  const data = (await response.json()) as { id: string; status: string };
  return { id: data.id, status: data.status };
}

export async function checkGenerationStatus(params: {
  apiKey: string;
  predictionId: string;
}): Promise<{ status: string; output: string | null; error: string | null }> {
  const response = await fetch(
    `${REPLICATE_API_URL}/${params.predictionId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${params.apiKey}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      (error as { detail?: string }).detail ||
        `Replicate API error: ${response.status}`
    );
  }

  const data = (await response.json()) as {
    status: string;
    output: string | string[] | null;
    error: string | null;
  };

  let output: string | null = null;
  if (data.output) {
    output = Array.isArray(data.output) ? data.output[0] : data.output;
  }

  return {
    status: data.status,
    output,
    error: data.error,
  };
}
