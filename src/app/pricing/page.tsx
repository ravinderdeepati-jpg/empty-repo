"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Container } from "@/components/ui/Container";

const fadeInUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.5 },
};

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "/month",
    description: "Get started with the basics",
    features: [
      "3 videos per day",
      "Basic templates (5 styles)",
      "Bring your own API key",
      "720p output",
      "Community support",
    ],
    cta: "Get Started Free",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$4.99",
    period: "/month",
    description: "For serious content creators",
    features: [
      "20 videos per day",
      "All premium templates",
      "Priority processing queue",
      "Advanced prompt engineering",
      "1080p output",
      "Email support",
    ],
    cta: "Start Pro Trial",
    highlighted: true,
  },
  {
    name: "Business",
    price: "$14.99",
    period: "/month",
    description: "For teams and agencies",
    features: [
      "Unlimited videos",
      "All templates + custom",
      "API access for automation",
      "Team features (5 seats)",
      "Custom branding",
      "4K output",
      "Priority support",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

const faqs = [
  {
    question: "What does 'Bring Your Own Key' mean?",
    answer:
      "Instead of us charging you for AI usage, you connect your own API key from providers like Replicate or HuggingFace. This way, you only pay for what you use at their rates, and we don't add any markup.",
  },
  {
    question: "How do I get a Replicate API key?",
    answer:
      "Sign up at replicate.com, go to your account settings, and create an API token. Then paste it into your BrainFog.mov settings. It takes less than a minute.",
  },
  {
    question: "Can I cancel anytime?",
    answer:
      "Yes, absolutely. You can cancel your subscription at any time from your account settings. No questions asked, no hidden fees.",
  },
  {
    question: "What video models are supported?",
    answer:
      "We support multiple state-of-the-art video generation models available through Replicate and HuggingFace, including the latest open-source models optimized for short-form content.",
  },
  {
    question: "Is there a free trial for Pro?",
    answer:
      "Yes! The Pro plan comes with a 7-day free trial. You can explore all Pro features before being charged.",
  },
  {
    question: "What payment methods do you accept?",
    answer:
      "We accept all major credit and debit cards (Visa, Mastercard, American Express) through our secure payment processor Stripe.",
  },
];

export default function PricingPage() {
  return (
    <>
      <Header />
      <main className="flex-1">
        {/* Pricing Header */}
        <section className="py-24 sm:py-32">
          <Container>
            <motion.div className="text-center mb-16" {...fadeInUp}>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4">
                Simple, Transparent Pricing
              </h1>
              <p className="text-lg text-foreground/70">
                Start free. Scale when you&apos;re ready.
              </p>
            </motion.div>

            {/* Pricing Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {plans.map((plan, index) => (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card
                    className={`h-full flex flex-col relative ${
                      plan.highlighted
                        ? "border-accent shadow-lg shadow-accent/10"
                        : ""
                    }`}
                  >
                    {plan.highlighted && (
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent/10 text-accent border-accent/20">
                        Most Popular
                      </Badge>
                    )}
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-1">
                        {plan.name}
                      </h3>
                      <p className="text-sm text-foreground/60">
                        {plan.description}
                      </p>
                    </div>
                    <div className="mb-6">
                      <span className="text-4xl font-bold">{plan.price}</span>
                      <span className="text-foreground/60">{plan.period}</span>
                    </div>
                    <ul className="space-y-3 mb-8 flex-1">
                      {plan.features.map((feature) => (
                        <li
                          key={feature}
                          className="flex items-start gap-2 text-sm"
                        >
                          <Check className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                          <span className="text-foreground/80">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button
                      variant={plan.highlighted ? "primary" : "secondary"}
                      size="md"
                      className="w-full"
                    >
                      {plan.cta}
                    </Button>
                  </Card>
                </motion.div>
              ))}
            </div>
          </Container>
        </section>

        {/* FAQ Section */}
        <section className="py-24 sm:py-32 border-t border-border">
          <Container>
            <motion.div className="text-center mb-16" {...fadeInUp}>
              <h2 className="text-3xl sm:text-4xl font-bold">
                Frequently Asked Questions
              </h2>
            </motion.div>
            <div className="max-w-3xl mx-auto space-y-6">
              {faqs.map((faq, index) => (
                <motion.div
                  key={faq.question}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                >
                  <Card>
                    <h3 className="font-semibold mb-2">{faq.question}</h3>
                    <p className="text-sm text-foreground/70">{faq.answer}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </Container>
        </section>
      </main>
      <Footer />
    </>
  );
}
