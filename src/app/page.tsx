"use client";

import { motion } from "framer-motion";
import {
  Sparkles,
  Zap,
  Palette,
  Key,
  Download,
  Users,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Container } from "@/components/ui/Container";

const fadeInUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.5 },
};

const features = [
  {
    icon: Sparkles,
    title: "AI-Powered Generation",
    description:
      "Transform text prompts into engaging short-form videos using state-of-the-art AI models",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description:
      "Get your video in under 60 seconds. No rendering queues, no waiting around",
  },
  {
    icon: Palette,
    title: "Multiple Styles",
    description:
      "Choose from brainrot, meme, educational, product showcase, and storytelling formats",
  },
  {
    icon: Key,
    title: "Bring Your Own Key",
    description:
      "Use your own Replicate or HuggingFace API key. Full control over your usage and costs",
  },
  {
    icon: Download,
    title: "Export Anywhere",
    description:
      "Download in any aspect ratio - 9:16 for TikTok, 16:9 for YouTube, 1:1 for Instagram",
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description:
      "Share templates, manage team API keys, and collaborate on content (Business plan)",
  },
];

const steps = [
  {
    number: "1",
    title: "Enter Your Prompt",
    description:
      "Describe the video you want. Be creative - the weirder the better for brainrot.",
  },
  {
    number: "2",
    title: "Choose Your Style",
    description:
      "Pick from our curated styles optimized for different platforms and audiences.",
  },
  {
    number: "3",
    title: "Download & Post",
    description:
      "Get your video in seconds. Download and post directly to TikTok, Reels, or Shorts.",
  },
];

const testimonials = [
  {
    name: "Alex K.",
    handle: "@contentcreator",
    quote:
      "I went from 500 to 50k followers in a month using BrainFog. The AI just gets the brainrot aesthetic.",
  },
  {
    name: "Sarah M.",
    handle: "@maboroshi.daily",
    quote:
      "Finally a tool that doesn't charge $50/month for basic video gen. BYOK model is genius.",
  },
  {
    name: "Jordan T.",
    handle: "@viralclips247",
    quote:
      "The speed is insane. I pump out 20 videos a day and my Reels engagement is through the roof.",
  },
];

export default function Home() {
  return (
    <>
      <Header />
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden py-24 sm:py-32">
          <Container>
            <motion.div
              className="text-center max-w-4xl mx-auto"
              {...fadeInUp}
            >
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight">
                Turn Any Idea Into{" "}
                <span className="bg-gradient-to-r from-primary via-accent to-secondary bg-clip-text text-transparent">
                  Viral Brainrot
                </span>
              </h1>
              <p className="mt-6 text-lg sm:text-xl text-foreground/70 max-w-2xl mx-auto">
                Generate scroll-stopping short videos for TikTok, YouTube Shorts,
                and Reels in seconds with AI. Bring your own API key, pay nothing
                to start.
              </p>
              <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button variant="primary" size="lg">
                  Start Creating Free
                </Button>
                <Button variant="secondary" size="lg">
                  See Pricing
                </Button>
              </div>
            </motion.div>

            {/* Decorative mock video player */}
            <motion.div
              className="mt-16 max-w-3xl mx-auto"
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              <div className="relative rounded-2xl p-[2px] bg-gradient-to-r from-primary via-accent to-secondary">
                <div className="rounded-2xl bg-surface p-8 sm:p-12">
                  <div className="aspect-video rounded-lg bg-background/50 border border-border flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-r from-primary to-accent flex items-center justify-center">
                        <Sparkles className="w-8 h-8 text-white" />
                      </div>
                      <p className="mt-4 text-sm text-foreground/50">
                        Your generated video appears here
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </Container>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 sm:py-32">
          <Container>
            <motion.div className="text-center mb-16" {...fadeInUp}>
              <h2 className="text-3xl sm:text-4xl font-bold">
                Everything You Need to Go Viral
              </h2>
            </motion.div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card className="h-full hover:border-primary/50 transition-colors">
                    <feature.icon className="w-10 h-10 text-primary mb-4" />
                    <h3 className="text-lg font-semibold mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-foreground/70">
                      {feature.description}
                    </p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </Container>
        </section>

        {/* How It Works Section */}
        <section className="py-24 sm:py-32 border-t border-border">
          <Container>
            <motion.div className="text-center mb-16" {...fadeInUp}>
              <h2 className="text-3xl sm:text-4xl font-bold">
                Three Steps to Viral
              </h2>
            </motion.div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {steps.map((step, index) => (
                <motion.div
                  key={step.title}
                  className="text-center"
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.15 }}
                >
                  <div className="w-12 h-12 mx-auto rounded-full bg-gradient-to-r from-primary to-accent flex items-center justify-center text-white font-bold text-lg mb-4">
                    {step.number}
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                  <p className="text-sm text-foreground/70">
                    {step.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </Container>
        </section>

        {/* Testimonials Section */}
        <section className="py-24 sm:py-32 border-t border-border">
          <Container>
            <motion.div className="text-center mb-16" {...fadeInUp}>
              <h2 className="text-3xl sm:text-4xl font-bold">
                Creators Love BrainFog
              </h2>
            </motion.div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {testimonials.map((testimonial, index) => (
                <motion.div
                  key={testimonial.name}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card className="h-full">
                    <p className="text-sm text-foreground/80 mb-4">
                      &ldquo;{testimonial.quote}&rdquo;
                    </p>
                    <div>
                      <p className="text-sm font-semibold">
                        {testimonial.name}
                      </p>
                      <p className="text-xs text-foreground/50">
                        {testimonial.handle}
                      </p>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </Container>
        </section>

        {/* Final CTA Section */}
        <section className="py-24 sm:py-32">
          <Container>
            <motion.div
              className="relative rounded-2xl p-[1px] bg-gradient-to-r from-primary via-accent to-secondary"
              {...fadeInUp}
            >
              <div className="rounded-2xl bg-surface px-8 py-16 sm:px-16 sm:py-20 text-center">
                <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                  Ready to Break the Internet?
                </h2>
                <p className="text-foreground/70 mb-8 max-w-xl mx-auto">
                  Join thousands of creators using BrainFog.mov to generate viral
                  content. Start free, no credit card required.
                </p>
                <Button variant="primary" size="lg">
                  Start Creating Free
                </Button>
              </div>
            </motion.div>
          </Container>
        </section>
      </main>
      <Footer />
    </>
  );
}
