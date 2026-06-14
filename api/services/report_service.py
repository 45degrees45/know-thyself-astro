from api.services.llm_adapter import LLMAdapter
from api.config import settings

REPORT_SYSTEM = """You are AstroWise — a Vedic astrology report writer using Lahiri ayanamsha.
Write in warm, direct, non-fatalistic language. Avoid fortune-teller certainty.
Use "you may notice" and "this period invites" rather than "you will".
Structure: use clear headings. No bullet points — flowing paragraphs only."""

REPORT_PROMPT_TEMPLATE = """
Write a complete AstroWise personal report for {name}.

CHART DATA (ground truth — do not contradict):
- Lagna (Ascendant): {lagna} {lagna_deg}°
- Current Dasha: {current_dasha}
- Key Yogas: {yogas}
- Spirit Animal: {animal} {animal_emoji}
- Planets: {planets_summary}

SECTIONS TO WRITE:
1. Core Nature — personality, dominant traits, lagna character, emotional style
2. Career — best domains, strengths, supportive yogas, leadership vs support style
3. Relationships — 7th house, Venus, partner profile, how they love and want to be loved
4. Spiritual Pointers — soul lesson, karma being cleared, dharma, best practice for this chart
5. Career Window — specific dasha/transit periods for breakthroughs (next 3 years)
6. Marriage Window — dasha/transit windows for committed relationship (next 3 years)
7. Shadow Side — honest blind spots, challenging yogas, where growth is needed
8. Remedies — Tier 1 Universal (behavioural, gemstones, sound), Tier 3 Neuroscience/CBT
   Do NOT include Vedic mantras/puja unless specifically requested.
9. Weekly Practice Calendar — 7-column Mon–Sun grid with daily practices

Write with depth and care. This person paid for insight, not platitudes.
"""


class ReportService:
    def __init__(self):
        self.adapter = LLMAdapter(
            provider="anthropic",
            api_key=settings.anthropic_api_key,
        )

    def _build_prompt(self, chart_json: dict, name: str) -> str:
        planets = chart_json.get("planets", {})
        planets_summary = ", ".join(
            f"{p} in {d.get('sign', '?')} H{d.get('house', '?')}"
            for p, d in planets.items()
        ) if planets else "see chart"

        return REPORT_PROMPT_TEMPLATE.format(
            name=name,
            lagna=chart_json.get("lagna", "unknown"),
            lagna_deg=chart_json.get("lagna_deg", 0.0),
            current_dasha=chart_json.get("current_dasha", "unknown"),
            yogas=", ".join(chart_json.get("yogas", [])),
            animal=chart_json.get("animal", "unknown"),
            animal_emoji=chart_json.get("animal_emoji", ""),
            planets_summary=planets_summary,
        )

    async def stream_report(self, chart_json: dict, name: str):
        prompt = self._build_prompt(chart_json, name)
        async for chunk in self.adapter.stream(prompt, REPORT_SYSTEM):
            yield chunk
