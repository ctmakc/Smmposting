"""Mock LLM client for development and testing."""

from __future__ import annotations

import json
import uuid

from libs.llm.base import LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """Mock LLM that returns deterministic, structured responses."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        content = self._route_response(prompt, structured=False)
        return LLMResponse(
            content=content,
            model="mock-v1",
            input_tokens=len(prompt) // 4,
            output_tokens=len(content) // 4,
        )

    async def generate_structured(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        content = self._route_response(prompt, structured=True)
        return LLMResponse(
            content=content,
            model="mock-v1",
            input_tokens=len(prompt) // 4,
            output_tokens=len(content) // 4,
        )

    def _route_response(self, prompt: str, *, structured: bool) -> str:
        prompt_lower = prompt.lower()
        if "gap" in prompt_lower or "analyze" in prompt_lower:
            return self._gap_analysis_response()
        if "idea" in prompt_lower or "generate ideas" in prompt_lower:
            return self._idea_generation_response()
        if "quality" in prompt_lower or "qc" in prompt_lower or "check" in prompt_lower:
            return self._qc_check_response()
        if "script" in prompt_lower or "scenario" in prompt_lower:
            return self._script_generation_response()
        return self._default_response()

    def _gap_analysis_response(self) -> str:
        return json.dumps({
            "gaps": [
                {
                    "topic": "AI automation for small businesses",
                    "gap_type": "underserved_audience",
                    "opportunity_score": 82,
                    "rationale": "High search volume, few quality videos targeting SMBs",
                },
                {
                    "topic": "No-code tools comparison 2025",
                    "gap_type": "outdated_content",
                    "opportunity_score": 75,
                    "rationale": "Existing content is 6+ months old, landscape changed",
                },
                {
                    "topic": "Remote work productivity systems",
                    "gap_type": "angle_gap",
                    "opportunity_score": 68,
                    "rationale": "Most content is generic tips, no systems-thinking approach",
                },
            ],
            "top_questions": [
                "How do I automate my business with AI?",
                "What no-code tool should I use in 2025?",
                "How do I stay productive working from home?",
            ],
        })

    def _idea_generation_response(self) -> str:
        return json.dumps({
            "ideas": [
                {
                    "title": "5 AI Automations That Replaced My Assistant",
                    "angle": "personal_experience",
                    "persona": "small_business_owner",
                    "format": "listicle",
                    "trend_score": 85,
                    "gap_score": 78,
                    "brand_fit": 90,
                    "effort_inverse": 70,
                    "conversion_intent": 65,
                    "claim_risk": 15,
                    "competitor_risk": 10,
                    "policy_violation": 5,
                    "ambiguity": 20,
                    "platform_risk": 10,
                },
                {
                    "title": "The No-Code Stack That Runs My $10K/mo Business",
                    "angle": "case_study",
                    "persona": "aspiring_entrepreneur",
                    "format": "tutorial",
                    "trend_score": 72,
                    "gap_score": 80,
                    "brand_fit": 85,
                    "effort_inverse": 60,
                    "conversion_intent": 80,
                    "claim_risk": 30,
                    "competitor_risk": 20,
                    "policy_violation": 10,
                    "ambiguity": 25,
                    "platform_risk": 15,
                },
                {
                    "title": "My Remote Work System After 5 Years",
                    "angle": "framework",
                    "persona": "remote_worker",
                    "format": "storytelling",
                    "trend_score": 65,
                    "gap_score": 70,
                    "brand_fit": 75,
                    "effort_inverse": 80,
                    "conversion_intent": 50,
                    "claim_risk": 5,
                    "competitor_risk": 5,
                    "policy_violation": 0,
                    "ambiguity": 10,
                    "platform_risk": 5,
                },
            ],
        })

    def _script_generation_response(self) -> str:
        return json.dumps({
            "hook_variants": [
                "I fired my virtual assistant and replaced them with "
                "5 AI tools. Here's what happened.",
                "These 5 AI tools do the work of a full-time employee. And they cost $0.",
                "Stop hiring humans for these 5 tasks. AI does them better.",
            ],
            "script_sections": {
                "hook": "I used to spend $2000/month on a virtual assistant. "
                "Then I found these 5 AI tools that do everything she did — for free.",
                "body": "Tool number 1: Calendar management. I use Reclaim AI to automatically "
                "schedule my meetings, block focus time, and handle rescheduling. "
                "It saved me 3 hours per week.\n\n"
                "Tool number 2: Email triage. I set up an AI filter that categorizes "
                "my emails into action-required, FYI, and spam. I only see what matters.\n\n"
                "Tool number 3: Content repurposing. This one tool takes my long-form "
                "videos and creates clips, tweets, and newsletter drafts automatically.\n\n"
                "Tool number 4: Customer support. An AI chatbot handles 80% of customer "
                "questions with answers from my knowledge base.\n\n"
                "Tool number 5: Bookkeeping. AI categorizes transactions, flags anomalies, "
                "and generates monthly reports.",
                "payoff": "The result? I saved $24,000 per year and actually got better "
                "output. The AI doesn't take sick days, doesn't need training, "
                "and works 24/7.",
                "cta": "Follow for more AI automation tips. "
                "Link in bio for the full tool list with tutorials.",
            },
            "on_screen_text": {
                "0:00": "I fired my VA...",
                "0:03": "...and replaced them with AI",
                "0:08": "Tool #1: Calendar AI",
                "0:15": "Tool #2: Email Triage",
                "0:25": "Tool #3: Content Repurposing",
                "0:35": "Tool #4: Customer Support Bot",
                "0:45": "Tool #5: AI Bookkeeping",
                "0:55": "$24K/year saved",
            },
            "broll_list": [
                "Screen recording of Reclaim AI dashboard",
                "Email inbox before/after comparison",
                "Content repurposing tool in action",
                "Chatbot conversation example",
                "Financial dashboard with AI categories",
            ],
        })

    def _qc_check_response(self) -> str:
        return json.dumps({
            "approved": True,
            "score": 88,
            "issues": [],
            "suggestions": [
                "Consider adding a disclaimer about results varying by business type",
                "The $24K savings claim should note this is a personal example",
            ],
            "forbidden_topics_found": [],
            "claim_risks": [],
            "vocabulary_violations": [],
        })

    def _default_response(self) -> str:
        return json.dumps({"response": "Mock LLM response", "id": uuid.uuid4().hex[:8]})
