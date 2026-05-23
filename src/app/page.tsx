export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-background">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-center gap-6 px-6 py-32 text-center">
        <h1 className="text-4xl font-bold text-primary">BrainFog.mov</h1>
        <p className="text-lg text-foreground/70">
          AI-powered brainrot video generator. Coming soon.
        </p>
      </main>
    </div>
  );
}
