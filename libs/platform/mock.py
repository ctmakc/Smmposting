"""Mock platform client for development and testing."""

from __future__ import annotations

import random
import uuid

from libs.platform.base import PlatformClient, TrendingItem

_MOCK_NICHES = {
    "tech": [
        ("5 AI Tools You're Not Using Yet", "tech_guru"),
        ("Why I Switched From React to HTMX", "dev_sarah"),
        ("Building a SaaS in 30 Days Challenge", "indie_hacker"),
        ("The Hidden Cost of Microservices", "arch_mike"),
        ("PostgreSQL vs MongoDB in 2025", "db_expert"),
    ],
    "finance": [
        ("How I Save 60% of My Income", "money_coach"),
        ("Index Funds vs Individual Stocks", "invest_pro"),
        ("The Side Hustle Nobody Talks About", "hustle_queen"),
        ("Why Your Budget Doesn't Work", "fin_advisor"),
        ("Crypto Lessons From 2024", "blockchain_bob"),
    ],
    "default": [
        ("Morning Routine for Productivity", "life_hacker"),
        ("The 80/20 Rule Changed My Life", "growth_mind"),
        ("Stop Doing These 5 Things", "coach_alex"),
        ("How to Learn Anything Faster", "study_tips"),
        ("The Minimalist Lifestyle Guide", "simple_living"),
    ],
}

_MOCK_HOOKS = ["question", "shock_stat", "bold_claim", "story_opener", "list_tease"]
_MOCK_PACING = ["fast", "medium", "slow"]


class MockPlatformClient(PlatformClient):
    """Mock platform client that returns synthetic trending data."""

    def __init__(self, platform: str = "mock") -> None:
        self._platform = platform

    @property
    def platform_name(self) -> str:
        return self._platform

    async def fetch_trending(self, niche: str, limit: int = 20) -> list[TrendingItem]:
        templates = _MOCK_NICHES.get(niche, _MOCK_NICHES["default"])
        items: list[TrendingItem] = []

        for i in range(min(limit, len(templates))):
            title, author = templates[i]
            items.append(
                TrendingItem(
                    platform=self._platform,
                    url=f"https://{self._platform}.example.com/v/{uuid.uuid4().hex[:12]}",
                    author=author,
                    title=title,
                    transcript=f"[Mock transcript for: {title}] "
                    f"This is a simulated transcript that would normally come from "
                    f"whisper or the platform's own transcript API.",
                    features={
                        "hook_type": random.choice(_MOCK_HOOKS),
                        "pacing": random.choice(_MOCK_PACING),
                        "duration": random.randint(15, 180),
                        "overlays": random.randint(0, 10),
                    },
                    scores={
                        "views": random.randint(1000, 5_000_000),
                        "engagement_rate": round(random.uniform(0.01, 0.15), 4),
                        "share_rate": round(random.uniform(0.001, 0.05), 4),
                    },
                )
            )
        return items

    async def fetch_comments(self, url: str, limit: int = 50) -> list[dict]:
        templates = [
            "How do I get started with this?",
            "Can you make a follow-up video?",
            "This is exactly what I needed!",
            "I disagree, here's why...",
            "What tools do you recommend?",
            "Part 2 please!",
            "This changed my perspective.",
            "Where can I learn more about this?",
        ]
        return [
            {
                "author": f"user_{uuid.uuid4().hex[:6]}",
                "text": templates[i % len(templates)],
                "likes": random.randint(0, 500),
                "is_question": "?" in templates[i % len(templates)],
            }
            for i in range(min(limit, len(templates)))
        ]
