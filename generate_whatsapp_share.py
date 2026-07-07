#!/usr/bin/env python3
"""
Generate WhatsApp-shareable group insights HTML.
- CH names kept as-is
- All other names anonymised as "The [Adj] [Animal] · Age"
- Goldy = "Me 🐬" (user is Goldy)
- Mobile-first, single-file, works without JS
"""
import sys
from datetime import datetime, date
sys.path.insert(0, "/home/jo/claude_projects/P046_202604_KnowThyselfAstro")

from astro_engine.calc import calculate_chart, SIGNS
from astro_engine.yoga import SIGN_LORD
from astro_engine.match import _sign_dignity

# ---------------------------------------------------------------------------
# Anonymous name mapping  (non-CH names get "The Adj Animal · Age")
# CH names stay exactly as given. Goldy = "Me"
# ---------------------------------------------------------------------------
ANON = {
    "Joseph TC":      ("The Wise Eagle",       "🦅"),
    "Goldy":          ("Me",                   "🐬"),   # user
    "Prakashji":      ("The Royal Lion",        "🦁"),
    "Gewin":          ("The Mystic Eagle",      "🦅"),
    "Mirjam":         ("The White Swan",        "🦢"),
    "Zerin":          ("The Golden Deer",       "🦌"),
    "Spirilla Guy":   ("The Deep Dolphin",      "🐬"),
    "Gracious George":("The Steady Elephant",   "🐘"),
    "Yaqza":          ("The Storm Eagle",       "🦅"),
    "Isolda":         ("The Dark Peacock",      "🦚"),
    "Jinx":           ("The Midnight Tiger",    "🐅"),
    "Sai":            ("The Mountain Eagle",    "🦅"),
    "Lalu":           ("The Ancient Cobra",     "🐍"),
    "Reddit Girl":    ("The Moonlit Swan",      "🦢"),
    "Tintu":          ("The Gentle Elephant",   "🐘"),
    "Cini":           ("The Desert Elephant",   "🐘"),
    "Soniya":         ("The Celestial Peacock", "🦚"),
    "Vasudevan":      ("The Golden Lion",       "🦁"),
    "Remya":          ("The Swift Dolphin",     "🐬"),
    "Biju Jacob":     ("The Wandering Butterfly","🦋"),
    "Kiran":          ("The Stone Lion",        "🦁"),
    "Ann CH":         ("Ann CH",               "🦋"),   # CH → keep
    "Athens CH":      ("Athens CH",            "🦅"),
    "Ruhi CH":        ("Ruhi CH",              "🦌"),
    "Vi CH":          ("Vi CH",                "🦅"),
    "Pi CH":          ("Pi CH",                "🐅"),
    "Bodhi CH":       ("Bodhi CH",             "🐘"),
    "Ammu CH":        ("Ammu CH",              "🦁"),
    "Always CH":      ("Always CH",            "🦋"),
    "Khayel CH":      ("Khayel CH",            "🦁"),
    "Kunal":          ("The Indigo Tiger",      "🐅"),
    "Hari CH":        ("Hari CH",              "🦊"),
}

# ---------------------------------------------------------------------------
# All profile data — added location as last field
# ---------------------------------------------------------------------------
PROFILES = [
    ("Joseph TC",     "1984-08-05","15:30", 10.10, 76.36,"Asia/Kolkata",  "Sagittarius","Venus/Venus/Mercury",    "🦅","M", "🚀",73, "EdTech / Knowledge Consulting",  ["Professional coaching platform","Corporate learning SaaS","B2B advisory marketplace"], "Aluva, Kerala"),
    ("Goldy",         "1985-03-07","07:15",  9.60, 76.45,"Asia/Kolkata",  "Pisces",     "Rahu/Venus/Venus",       "🐬","M", "🏢",39, "Creative / Spiritual Sales",      ["Art & spiritual product sales","International biz development","Creative consulting"], "Kangazha, Kerala"),
    ("Prakashji",     "1973-11-04","01:22", 10.77, 76.65,"Asia/Kolkata",  "Leo",        "Saturn/Moon/Mercury",    "🦁","M", "🔄",43, "Leadership Consulting / Advisory", ["Executive advisory firm","Org design consulting","Corporate training"], "Palakkad, Kerala"),
    ("Gewin",         "1984-12-11","11:55", 23.61, 58.59,"Asia/Muscat",   "Aquarius",   "Ketu/Moon/Saturn",       "🦅","M", "🌱",67, "Tech Infrastructure / Community",  ["DevOps / FinOps SaaS","Community infrastructure","Enterprise security ops"], "Muscat, Oman"),
    ("Mirjam",        "1975-05-27","23:00", 52.63,  4.75,"Europe/Amsterdam","Sagittarius","Rahu/Ketu/Rahu",       "🦢","F", "🔄",57, "International Consulting",         ["Cross-border advisory","Spiritual wellness platform","Educational content"], "Alkmaar, Netherlands"),
    ("Ruhi CH",       "2002-03-03","02:00",  9.49, 76.33,"Asia/Kolkata",  "Sagittarius","Jupiter/Mercury/Saturn", "🦌","F", "🌱",58, "Sports Tech / EdTech",            ["Sports performance app","Student learning tool","Youth skill platform"], "Alleppey, Kerala"),
    ("Athens CH",     "2000-06-07","20:08",  9.55, 76.78,"Asia/Kolkata",  "Sagittarius","Sun/Mars/Jupiter",       "🦅","M", "🔄",54, "Healthcare / Service Delivery",    ["Healthcare service delivery","Sports / fitness brand","High-ticket D2C sales"], "Kanjirapally, Kerala"),
    ("Zerin",         "2000-11-09","09:25", 10.87, 76.33,"Asia/Kolkata",  "Sagittarius","Venus/Sun/Mercury",      "🦌","F", "🔄",49, "EdTech / Travel (early career)",   ["Student travel platform","Gen Z educational content","Sustainable lifestyle brand"], "Cherpulassery, Kerala"),
    ("Spirilla Guy",  "1996-12-12","10:15", 13.08, 80.27,"Asia/Kolkata",  "Capricorn",  "Moon/Venus/Jupiter",     "🐬","M", "🌱",61, "International SaaS / Wellness",    ["International market entry SaaS","Meditation / wellness app","Enterprise talent platform"], "Chennai, India"),
    ("Gracious George","1985-07-24","07:30", 9.75, 77.08,"Asia/Kolkata",  "Cancer",     "Saturn/Saturn/Ketu",     "🐘","M", "🔄",50, "Real Estate / Hospitality",        ["Real estate development","Restaurant / hospitality brand","Elder care platform"], "Kattappana, Kerala"),
    ("Yaqza",         "2003-09-19","12:00", 11.25, 75.77,"Asia/Kolkata",  "Scorpio",    "Jupiter/Mercury/Sun",    "🦅","M", "🌱",60, "Research Platforms / Analytics",   ["Research intelligence platform","Academic analytics SaaS","Knowledge consulting"], "Kozhikode, Kerala"),
    ("Isolda",        "1985-07-24","14:04",  9.93, 76.26,"Asia/Kolkata",  "Scorpio",    "Saturn/Mercury/Mercury", "🦚","F", "🔄",52, "Luxury Brands / Financial Sales",  ["Luxury goods / premium brand","Financial product advisory","High-end real estate sales"], "Cochin, Kerala"),
    ("Jinx",          "2001-07-01","23:30",  8.52, 76.94,"Asia/Kolkata",  "Pisces",     "Mercury/Ketu/Mercury",   "🐅","F", "🌱",55, "Healthcare Ops / Spiritual Wellness",["Healthcare operations tool","Spiritual wellness platform","Sound healing brand"], "Trivandrum, Kerala"),
    ("Sai",           "1991-02-24","04:40",  8.52, 76.94,"Asia/Kolkata",  "Capricorn",  "Saturn/Saturn/Rahu",     "🦅","M", "🌱",65, "Fintech / Wealth Infrastructure",  ["Wealth management platform","Investment portfolio SaaS","Financial compliance tool"], "Trivandrum, Kerala"),
    ("Vi CH",         "1998-08-23","11:55",  8.52, 76.94,"Asia/Kolkata",  "Scorpio",    "Mars/Rahu/Venus",        "🦅","F", "🏢",28, "Research / Investigation (Role)",  ["Research analyst (fintech/product)","Deep-dive product researcher","Security / investigative analyst"], "Trivandrum, Kerala"),
    ("Pi CH",         "1989-10-01","20:43", 10.52, 76.21,"Asia/Kolkata",  "Aries",      "Saturn/Saturn/Ketu",     "🐅","F", "🔄",44, "Bold Consumer Brand / Fitness",    ["Fitness / sports consumer brand","Luxury beauty D2C","Consumer tech hardware brand"], "Thrissur, Kerala"),
    ("Lalu",          "1958-05-18","19:30", 10.10, 76.36,"Asia/Kolkata",  "Scorpio",    "Saturn/Mars/Ketu",       "🐍","F", "🔄",51, "Advisory / Consulting (Senior)",   ["Senior advisory / mentorship","Healthcare consulting","Knowledge product / teaching"], "Aluva, Kerala"),
    ("Reddit Girl",   "2002-11-16","11:25", 26.91, 75.79,"Asia/Kolkata",  "Capricorn",  "Venus/Venus/Rahu",       "🦢","F", "🌱",61, "Luxury Fintech / Millennial Wealth",["Luxury lifestyle subscription","Gen Z wealth planning app","Premium D2C beauty brand"], "Jaipur, Rajasthan"),
    ("Tintu",         "1990-12-26","09:30", 10.10, 76.36,"Asia/Kolkata",  "Capricorn",  "Venus/Ketu/Mercury",     "🐘","M", "🌱",63, "Real Estate Finance / PropTech",   ["Real estate investment platform","Property deal structuring SaaS","JV matching for developers"], "Aluva, Kerala"),
    ("Cini",          "1985-10-29","11:30", 23.61, 58.59,"Asia/Muscat",   "Sagittarius","Rahu/Saturn/Saturn",     "🐘","F", "🏢", 6, "Education / Counseling (Role)",    ["Educator / teacher / counselor","Spiritual facilitator","Cross-cultural facilitator"], "Muscat, Oman"),
    ("Khayel CH",     "2001-01-01","00:02", 25.20, 55.27,"Asia/Dubai",    "Virgo",      "Saturn/Mars/Jupiter",    "🦁","F", "🌱",55, "Health & Wellness Brand",          ["Health/wellness D2C brand","Women's wellness app","Precision health marketing agency"], "Dubai, UAE"),
    ("Soniya",        "1984-06-13","16:15", 10.77, 76.65,"Asia/Kolkata",  "Libra",      "Moon/Saturn/Venus",      "🦚","F", "🔄",50, "Alternative Investment / Insurance",["Alternative investment advisory","Insurance / wealth protection","Transformation finance"], "Palakkad, Kerala"),
    ("Vasudevan",     "1999-06-23","10:30", 10.02, 76.31,"Asia/Kolkata",  "Leo",        "Jupiter/Venus/Venus",    "🦁","M", "🏢",40, "Creative Lead / Visual Product (Role)",["Creative director (product co)","Content / media production lead","Brand storytelling specialist"], "Edappally, Kerala"),
    ("Remya",         "1987-06-18","06:30", 10.10, 76.36,"Asia/Kolkata",  "Gemini",     "Mercury/Jupiter/Mercury","🐬","F", "🚀",70, "Analytics SaaS / Comm Tools",      ["Data analytics dashboard","AI writing / content intelligence","Research & insight automation"], "Aluva, Kerala"),
    ("Ammu CH",       "1990-09-05","05:30",  8.52, 76.94,"Asia/Kolkata",  "Leo",        "Saturn/Jupiter/Jupiter", "🦁","F", "🌱",66, "Creative Tools / Leadership Dev",  ["Creative collaboration platform","Leadership coaching app","Sports performance analytics"], "Trivandrum, Kerala"),
    ("Biju Jacob",    "1983-11-10","05:30", 23.61, 58.59,"Asia/Muscat",   "Libra",      "Rahu/Moon/Sun",          "🦋","M", "🏢",19, "Operations / Project Mgmt (Role)", ["Head of Operations at startup","Project / program manager","Ops consultant for SMEs"], "Muscat, Oman"),
    ("Kiran",         "1983-11-02","12:58", 10.77, 76.00,"Asia/Kolkata",  "Capricorn",  "Jupiter/Venus/Sun",      "🦁","M", "🌱",58, "Real Estate Tech / Supply Chain",  ["Construction project mgmt SaaS","Supply chain optimization","Real estate operations tool"], "Ottapalam, Kerala"),
    ("Ann CH",        "1994-08-09","13:30",  9.94, 76.35,"Asia/Kolkata",  "Scorpio",    "Mars/Saturn/Ketu",       "🦋","F", "🏢",21, "Security / Compliance (Role)",     ["Cybersecurity analyst","Legal compliance specialist","Research / audit professional"], "Tripunithura, Kerala"),
    ("Always CH",     "1991-09-21","08:45", 28.70, 77.10,"Asia/Kolkata",  "Libra",      "Jupiter/Mercury/Sun",    "🦋","M", "🔄",54, "HR Tech / Legal Operations",       ["HR operations & compliance tool","Legal workflow SaaS","Partnership management platform"], "Delhi, India"),
    ("Bodhi CH",      "1991-09-05","21:50",  9.73, 76.33,"Asia/Kolkata",  "Taurus",     "Jupiter/Mercury/Jupiter","🐘","M", "🌱",60, "Sustainable Food / AgriTech",      ["Sustainable food supply platform","Agri-operations management","Wellness / organic brand"], "Cherthala, Kerala"),
    ("Kunal",         "1993-09-10","18:50", 27.56, 76.61,"Asia/Kolkata",  "Pisces",     "Saturn/Saturn/Rahu",     "🐅","M", "🔄",51, "Creative Agency / Spiritual Mktg", ["Creative operations agency","Spiritual / wellness marketing","Tech consulting + creative overlay"], "Alwar, Rajasthan"),
    ("Hari CH",       "1968-09-16","07:15",  8.52, 76.94,"Asia/Kolkata",  "Virgo",      "Mercury/Jupiter/Sun",    "🦊","M", "🚀",69, "Strategic Comms / Thought Leadership", ["Executive communications consulting","Research & intelligence platform","Thought leadership advisory"], "Trivandrum, Kerala"),
]

# ---------------------------------------------------------------------------
# Planetary insights — 1–2 plain-English sentences per person
# Written to make the domain recommendation "click"
# ---------------------------------------------------------------------------
PLANET_INSIGHT = {
    "Joseph TC":
        "Jupiter sits in its own sign right on your Ascendant — wisdom and teaching are literally your face to the world. "
        "Saturn exalted in H11 quietly builds wealth through networks; you don't hustle, your reputation does the work.",

    "Goldy":
        "Jupiter rules Pisces but is in Gemini (H4), scattered across too many ideas — the vision is cosmic, the execution gets pulled in many directions. "
        "Rahu in H2 creates intense desire for wealth and speech, which can either magnetise money or make promises you can't keep.",

    "Prakashji":
        "Sun rules Leo Lagna and sits in H4 Scorpio — authority is real but wielded in private, behind closed doors. "
        "Saturn dasha is demanding patience and karmic clearing before the world gives you the recognition you've earned.",

    "Gewin":
        "Saturn exalted in H9 (Libra) — dharma, systems and higher philosophy all strengthened at once. "
        "Your Ops 80 + Finance 80 double peak is pure Saturn: structure, discipline and long-term thinking in both domains.",

    "Mirjam":
        "Jupiter in own sign Sagittarius forms Hamsa Yoga — a rare mark of grace, wisdom and teaching ability. "
        "Rahu mahadasha is pulling you toward foreign lands, unconventional paths and tech-enabled expansion.",

    "Ruhi CH":
        "Mars exalted in Capricorn in H5 — fierce, disciplined creative initiative. You can outwork almost anyone in a focused sprint. "
        "Jupiter on your Lagna keeps the purpose anchored; the risk is scattered energy without a structured container.",

    "Athens CH":
        "Four planets packed into H6 — service, problem-solving and handling adversity are what you're literally built for. "
        "Sun + Mars dasha = your highest-energy window; act now, don't overthink.",

    "Zerin":
        "Jupiter in H1 gives philosophical depth and a natural teaching instinct. "
        "Moon stands alone without flanking planets (Kemadruma) — emotional intensity spikes under pressure; build a support system before founding solo.",

    "Spirilla Guy":
        "Venus exalted in Pisces forms Malavya Yoga — beauty of mind, aesthetic intelligence and wealth potential. "
        "A cluster of planets in H12 (foreign lands, hidden work) means your best output often happens far from home or behind the scenes.",

    "Gracious George":
        "Mars exalted in Capricorn is Yoga Karaka for Cancer Lagna — building, engineering and real estate are your planetary dharma. "
        "Saturn's Sasa Yoga adds structural authority; you're a builder, not a speculator.",

    "Yaqza":
        "Jupiter and Mercury both sit in Leo H10 — two Raja Yogas forming right at the top of your chart, in public visibility. "
        "This is the classic signature of someone who becomes an authority figure through knowledge and communication.",

    "Isolda":
        "Venus exalted in Pisces in H7 forms Malavya Yoga — partnerships, beauty and luxury are divinely supported. "
        "Saturn/Mercury dasha makes you precise and systematic; high-ticket sales or luxury advisory is where this combination shines.",

    "Jinx":
        "Three benefics in angular/trine positions form Adhi Yoga — prosperity through wisdom, not hustle. "
        "Mercury/Ketu bhukti is a dissolution phase; old patterns are falling away to make space for the real path.",

    "Sai":
        "Saturn exalted in Libra (Sasa Yoga) + Jupiter exalted in Cancer — two Pancha Mahapurusha exaltations in one chart. "
        "Finance score 93 is the highest in the group; this is a chart literally designed for wealth management and long-term structures.",

    "Vi CH":
        "Mars is your Lagna lord for Scorpio but sits in H12 — all that intensity and drive flows inward, not outward. "
        "This gives extraordinary depth of focus in private research but makes public leadership feel unnatural and draining.",

    "Pi CH":
        "Venus exalted in Pisces forms Malavya Yoga — luxury, beauty and boldness as a superpower. "
        "Two Viparita Raja Yogas mean your biggest wins come after adversity, not despite it; don't quit in the middle.",

    "Lalu":
        "Three major yogas — Raja, Dharma Karma Adhipati and Viparita Raja — all present in one chart. "
        "Six decades of lived experience are the activating force; these yogas now speak through wisdom and authority, not ambition.",

    "Reddit Girl":
        "Hamsa Yoga (Jupiter exalted) + Malavya Yoga (Venus exalted) — two of Jyotish's five great planetary yogas in one chart. "
        "Finance 80 and Product 73 reflect this double exaltation; Venus/Venus dasha is activating the wealth and beauty dimension right now.",

    "Tintu":
        "Jupiter exalted in Cancer in H7 — wealth and expansion come through partnerships, not solo ventures. "
        "Ten yogas including Hamsa and Sasa; the chart is built for long arcs, not quick wins.",

    "Cini":
        "Eight yogas on paper — but the planets forming them are placed in weak positions. "
        "Yogas are potential, not guarantee; without strong planetary fuel behind them, they stay dormant. Rahu/Saturn dasha is the heaviest double-burden period.",

    "Khayel CH":
        "Budha-Aditya Yoga (Sun + Mercury together) — intelligence that commands public respect and recognition. "
        "Gajakesari (Jupiter trine Moon) adds social grace and public goodwill; Virgo's precision is what makes the health/wellness domain a natural fit.",

    "Soniya":
        "Four planets in H8 (Sun, Mercury, Venus, Rahu) — hidden wealth, transformation and other people's money are your arena. "
        "Two Viparita Raja Yogas mean crises become catapults; Finance 87 comes from depth and complexity, not surface simplicity.",

    "Vasudevan":
        "Kemadruma Yoga: Moon has no planets flanking it — emotional instability under pressure is the core challenge to work through. "
        "The creative fire is real (Leo Lagna + Yoga Karaka Mars) but the foundation needs intentional structural support.",

    "Remya":
        "Mercury exalted in its own sign Gemini in H1 — Bhadra Yoga, the Pancha Mahapurusha yoga of pure intellect. "
        "Four planets in H1 mean you literally embody your brand; Product score 73 is the sharpest analytical chart in the group.",

    "Ammu CH":
        "Yoga Karaka Mars (rules both kendra and trikona for Leo) — career and purpose are one and the same for you. "
        "Jupiter exalted in H12 means wisdom works quietly behind the scenes; your biggest asset is often invisible to others.",

    "Biju Jacob":
        "Sasa Yoga (Saturn exalted) + Raja Yoga (Saturn conjunct Mercury) — structural authority and intellectual precision. "
        "But Venus, your Lagna lord, sits in H12 — your personal identity stays hidden, making you an outstanding #2 or COO rather than the face of a company.",

    "Kiran":
        "Saturn exalted in Libra in H10 — Sasa Yoga happening right at the career house, the most powerful possible placement. "
        "Sun also in H10 adds solar authority; your career IS your dharma and it shows.",

    "Ann CH":
        "Mars in own sign Scorpio in H1 — fierce investigative intensity and deep perceptive power. "
        "Mars/Saturn/Ketu is one of the harshest dasha sequences; this is a time to build skills in a protected environment, not take on solo risk.",

    "Always CH":
        "Budha-Aditya Yoga in Libra — intellect expressed through balance, fairness and partnership. "
        "Jupiter/Mercury dasha activates knowledge and communication; Libra Lagna works best in collaborative structures rather than solo roles.",

    "Bodhi CH":
        "Taurus Lagna ruled by Venus — beauty meets utility, comfort meets craft. "
        "All five skill scores cluster around 53, which is rare; no glaring weakness, no towering peak — a balanced chart that thrives in stable, quality-focused environments.",

    "Kunal":
        "Pisces Lagna ruled by Jupiter — the visionary archetype, imaginative and spiritually attuned. "
        "Saturn/Saturn mahadasha is a 20-year karma-clearing and discipline phase; whatever you build during this period will outlast the next three decades.",

    "Hari CH":
        "Mercury exalted in its own sign Virgo in H1 forms Bhadra Yoga — the Pancha Mahapurusha yoga of analytical precision and intellectual authority. "
        "Three planets in H12 (Sun, Mars, Jupiter) form Viparita Raja Yoga: the deepest and most impactful work often happens quietly, behind the scenes — which is exactly where this chart thrives.",
}

# ---------------------------------------------------------------------------
# Compute skill scores
# ---------------------------------------------------------------------------
SKILL_PLANETS = {
    "Product":["Jupiter","Venus","Mercury"],"Operations":["Saturn","Mars","Mercury"],
    "Sales":["Venus","Mercury","Moon"],"Marketing":["Venus","Mercury","Sun"],"Finance":["Jupiter","Saturn","Venus"],
}
SKILL_MIN, SKILL_MAX = -6, 9
DASHA_QUALITY = {"Jupiter":85,"Venus":80,"Mercury":75,"Sun":70,"Moon":55,"Mars":55,"Saturn":40,"Rahu":35,"Ketu":20}

def compute_skills(chart):
    return {
        s: round((sum(_sign_dignity(p, chart["planets"][p]["sign"]) for p in pl) - SKILL_MIN)/(SKILL_MAX-SKILL_MIN)*100)
        for s, pl in SKILL_PLANETS.items()
    }

print("Computing charts...", flush=True)
all_data = []
for row in PROFILES:
    name,dob,t,lat,lon,tz,lagna,dasha,animal,gender,tier_icon,startup_sc,biz_area,products,location = row
    try:
        chart = calculate_chart(dob, t, lat, lon, tz)
        skills = compute_skills(chart)
        best = max(skills, key=skills.get)
        age = (date.today() - datetime.strptime(dob,"%Y-%m-%d").date()).days // 365
        anon_name, anon_emoji = ANON.get(name, (name, animal))
        gender_label = "Male" if gender == "M" else "Female"
        all_data.append({
            "real_name": name, "anon": anon_name, "emoji": anon_emoji,
            "lagna": lagna, "dasha": dasha, "age": age,
            "gender": gender, "gender_label": gender_label, "location": location,
            "skills": skills, "best": best, "overall": round(sum(skills.values())/5),
            "tier": tier_icon, "startup_score": startup_sc,
            "biz_area": biz_area, "products": products,
            "planet_insight": PLANET_INSIGHT.get(name, ""),
        })
        print(f"  ✓ {name:18s} → {anon_name} · {age}y {gender} · {location}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# Sort: tier priority then startup score
TIER_RANK = {"🚀":0,"🌱":1,"🔄":2,"🏢":3}
TIER_LABEL = {"🚀":"Startup-Ready","🌱":"Founder-Track","🔄":"Conditional","🏢":"Specialist"}
TIER_COLOR = {"🚀":"#5a8f72","🌱":"#c49e40","🔄":"#5b8fd4","🏢":"#c4607a"}
TIER_DESC  = {
    "🚀":"Built to lead — strong enough to go alone",
    "🌱":"Can found with the right co-founder",
    "🔄":"Thrives as early employee or domain expert",
    "🏢":"Best in structured, supportive environment",
}
DOMAIN_COLOR = {"Product":"#7c5cbf","Operations":"#c4607a","Sales":"#5b8fd4","Marketing":"#c49e40","Finance":"#5a8f72"}
DOMAIN_ICON  = {"Product":"🔮","Operations":"⚙️","Sales":"🤝","Marketing":"📣","Finance":"💰"}
LAGNA_ICON   = {"Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋","Leo":"♌","Virgo":"♍",
                "Libra":"♎","Scorpio":"♏","Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓"}

all_data.sort(key=lambda r: (TIER_RANK.get(r["tier"],4), -r["startup_score"]))

from collections import defaultdict
by_tier = defaultdict(list)
for r in all_data:
    by_tier[r["tier"]].append(r)

today = datetime.today().strftime("%d %b %Y")

# ---------------------------------------------------------------------------
# Build individual profile cards (the main content)
# ---------------------------------------------------------------------------
cards_html = ""
for r in all_data:
    tc = TIER_COLOR[r["tier"]]
    bc = DOMAIN_COLOR.get(r["best"], "#c49e40")
    bi = DOMAIN_ICON.get(r["best"], "✦")
    ls = LAGNA_ICON.get(r["lagna"], "✦")
    tl = TIER_LABEL[r["tier"]]
    is_me = (r["real_name"] == "Goldy")
    display_name = r["anon"]
    if display_name != r["anon"] or is_me:
        display_name = r["anon"]

    # Skill bars (mini)
    skill_bars = ""
    for s in ["Product","Operations","Sales","Marketing","Finance"]:
        v = r["skills"][s]
        sc = DOMAIN_COLOR[s]
        bold = "font-weight:700;" if s == r["best"] else ""
        skill_bars += f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px"><span style="font-size:.6rem;color:rgba(240,232,216,0.45);width:28px;flex-shrink:0">{s[:3].upper()}</span><div style="flex:1;background:rgba(255,255,255,0.08);border-radius:99px;height:5px"><div style="width:{v}%;height:5px;background:{sc};border-radius:99px"></div></div><span style="font-size:.65rem;{bold}color:{sc};min-width:22px;text-align:right">{v}</span></div>'

    products_html = "".join(f'<div class="prod-item">{p}</div>' for p in r["products"][:3])

    gender_icon = "♂" if r["gender"] == "M" else "♀"
    me_badge = '<span class="me-badge">You</span>' if is_me else ''
    anon_sub = (
        f'<span style="font-size:.65rem;color:rgba(240,232,216,0.35);display:block;margin-top:1px">'
        f'{ls} {r["lagna"]} &nbsp;·&nbsp; {r["age"]}y {gender_icon} &nbsp;·&nbsp; 📍{r["location"]}'
        f'</span>'
    )

    cards_html += f"""
<div class="card" id="c-{r['real_name'].replace(' ','_')}">
  <div class="card-stripe" style="background:{tc}"></div>
  <div class="card-inner">

    <div class="card-top">
      <div class="card-emoji">{r["emoji"]}</div>
      <div style="flex:1;min-width:0">
        <div class="card-name">{display_name} {me_badge}</div>
        {anon_sub}
      </div>
      <div class="tier-pill" style="background:{tc}22;color:{tc};border:1px solid {tc}55">{r["tier"]} {tl}</div>
    </div>

    <div class="card-area" style="color:{tc}">{r["biz_area"]}</div>

    <div class="card-score-row">
      <div class="startup-score-block" style="border:1px solid {tc}44;background:{tc}11">
        <div class="ss-val" style="color:{tc}">{r["startup_score"]}</div>
        <div class="ss-label">Startup<br>Fit</div>
      </div>
      <div style="flex:1">{skill_bars}</div>
    </div>

    <div class="card-best">
      Best domain: <strong style="color:{bc}">{bi} {r["best"]}</strong>
      <span style="color:var(--muted)">· avg {r["overall"]}/100</span>
    </div>

    <div class="planet-insight">
      <div class="prod-label">🪐 Why this fits — planets</div>
      <div class="insight-text">{r["planet_insight"]}</div>
    </div>

    <div class="products-section">
      <div class="prod-label">Best Products / Roles</div>
      {products_html}
    </div>

    <div class="dasha-line">⏱ <span style="color:rgba(196,158,64,0.75)">{r["dasha"]}</span></div>
  </div>
</div>"""

# ---------------------------------------------------------------------------
# Tier summary (compact leaderboard per tier)
# ---------------------------------------------------------------------------
tier_summary_html = ""
for tier_icon in ["🚀","🌱","🔄","🏢"]:
    members = by_tier[tier_icon]
    if not members:
        continue
    tc = TIER_COLOR[tier_icon]
    tl = TIER_LABEL[tier_icon]
    td = TIER_DESC[tier_icon]

    items = ""
    for r in members:
        bc = DOMAIN_COLOR.get(r["best"],"#c49e40")
        bi = DOMAIN_ICON.get(r["best"],"✦")
        is_me = r["real_name"] == "Goldy"
        dn = r["anon"]
        me_tag = " (You)" if is_me else ""
        gender_icon = "♂" if r["gender"] == "M" else "♀"
        demo = f'{r["age"]}y {gender_icon} · {r["location"]}'
        items += f"""
      <div class="tier-item">
        <span class="tier-item-emoji">{r["emoji"]}</span>
        <div class="tier-item-body">
          <div class="tier-item-name">{dn}{me_tag}</div>
          <div class="tier-item-demo">{demo}</div>
          <div class="tier-item-area">{r["biz_area"]}</div>
        </div>
        <div class="tier-item-right">
          <span style="color:{bc};font-size:.72rem">{bi} {r["best"]}</span><br>
          <span style="color:{tc};font-weight:700;font-size:.9rem">{r["startup_score"]}</span>
        </div>
      </div>"""

    tier_summary_html += f"""
  <div class="tier-block" style="border-left:3px solid {tc}">
    <div class="tier-header">
      <span class="tier-big-emoji">{tier_icon}</span>
      <div>
        <div class="tier-title" style="color:{tc}">{tl}</div>
        <div class="tier-subdesc">{td}</div>
      </div>
      <div class="tier-count-pill" style="background:{tc}22;color:{tc};border:1px solid {tc}44">{len(members)}</div>
    </div>
    <div class="tier-items">{items}</div>
  </div>"""

# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
stat_html = ""
for tier_icon in ["🚀","🌱","🔄","🏢"]:
    count = len(by_tier[tier_icon])
    tc = TIER_COLOR[tier_icon]
    tl = TIER_LABEL[tier_icon]
    stat_html += f'<div class="stat-chip" style="border:1px solid {tc}44;background:{tc}11"><span style="font-size:1rem">{tier_icon}</span><div><div style="font-size:.65rem;color:{tc};font-weight:600">{tl}</div><div style="font-size:1.1rem;color:#fff8f0;font-weight:700">{count}</div></div></div>'

# ---------------------------------------------------------------------------
# Render HTML
# ---------------------------------------------------------------------------

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="robots" content="noindex, nofollow">
  <meta property="og:title" content="Our Group — Startup Fitness & Business Blueprint">
  <meta property="og:description" content="{len(all_data)} charts · Vedic Jyotish business insights · {today}">
  <title>Our Group — Startup Fitness & Business Blueprint</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root{{--bg:#0b0b18;--surface:rgba(255,255,255,0.04);--border:rgba(196,158,64,0.16);
      --gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.5);
      --r:18px;--shadow:0 12px 40px rgba(0,0,0,0.4)}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    html{{scroll-behavior:smooth}}
    body{{font-family:'DM Sans',system-ui,sans-serif;background:#0b0b18;
      background-image:radial-gradient(ellipse 80% 40% at 20% -10%,rgba(124,92,191,0.15),transparent),
        radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.1),transparent);
      background-attachment:fixed;color:var(--cream);min-height:100vh;
      padding:0 0 60px}}
    a{{color:inherit;text-decoration:none}}

    /* HERO */
    .hero{{padding:36px 20px 28px;text-align:center;
      background:linear-gradient(160deg,rgba(20,12,44,0.98),rgba(40,20,60,0.96) 60%,rgba(70,30,50,0.92));
      border-bottom:1px solid rgba(196,158,64,0.15)}}
    .hero-badge{{display:inline-block;font-size:.65rem;letter-spacing:.28em;text-transform:uppercase;
      color:var(--gold);border:1px solid rgba(196,158,64,0.3);border-radius:999px;padding:5px 14px;margin-bottom:14px}}
    .hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(1.9rem,7vw,3rem);font-weight:300;
      color:#fff8f0;line-height:1.2;margin-bottom:8px}}
    .hero-sub{{font-size:.8rem;color:var(--muted);line-height:1.6;max-width:340px;margin:0 auto}}

    /* NAV PILLS */
    .nav-bar{{display:flex;gap:8px;overflow-x:auto;padding:16px 16px 0;scrollbar-width:none;
      -webkit-overflow-scrolling:touch;border-bottom:1px solid var(--border)}}
    .nav-bar::-webkit-scrollbar{{display:none}}
    .nav-pill{{flex-shrink:0;padding:8px 16px;border-radius:999px;font-size:.78rem;
      border:1px solid var(--border);background:var(--surface);color:var(--muted);cursor:pointer;
      white-space:nowrap;transition:.2s}}
    .nav-pill.active,.nav-pill:hover{{color:var(--cream);border-color:rgba(196,158,64,0.4)}}

    /* CONTENT SECTIONS */
    .section{{padding:24px 16px;max-width:520px;margin:0 auto}}
    .section-title{{font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:300;
      color:#fff8f0;margin-bottom:4px}}
    .section-sub{{font-size:.75rem;color:var(--muted);margin-bottom:20px}}

    /* STATS */
    .stats-row{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px}}
    .stat-chip{{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:14px;}}
    .stat-chip div{{display:flex;flex-direction:column;gap:1px}}

    /* TIER BLOCKS */
    .tier-block{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
      margin-bottom:16px;overflow:hidden;box-shadow:var(--shadow)}}
    .tier-header{{display:flex;align-items:center;gap:12px;padding:14px 16px;
      border-bottom:1px solid rgba(255,255,255,0.06)}}
    .tier-big-emoji{{font-size:1.6rem;flex-shrink:0}}
    .tier-title{{font-family:'Cormorant Garamond',serif;font-size:1.1rem;font-weight:400}}
    .tier-subdesc{{font-size:.7rem;color:var(--muted);margin-top:2px}}
    .tier-count-pill{{margin-left:auto;padding:4px 12px;border-radius:999px;font-size:.75rem;font-weight:700;flex-shrink:0}}
    .tier-items{{padding:4px 0}}
    .tier-item{{display:flex;align-items:center;gap:10px;padding:11px 16px;
      border-bottom:1px solid rgba(255,255,255,0.04)}}
    .tier-item:last-child{{border-bottom:none}}
    .tier-item-emoji{{font-size:1.4rem;flex-shrink:0;width:32px;text-align:center}}
    .tier-item-body{{flex:1;min-width:0}}
    .tier-item-name{{font-size:.85rem;font-weight:500;color:#fff8f0}}
    .tier-item-demo{{font-size:.65rem;color:rgba(196,158,64,0.55);margin-top:1px}}
    .tier-item-area{{font-size:.72rem;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
    .tier-item-right{{text-align:right;flex-shrink:0}}

    /* PROFILE CARDS */
    .card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
      margin-bottom:16px;overflow:hidden;box-shadow:var(--shadow)}}
    .card-stripe{{height:3px}}
    .card-inner{{padding:16px}}
    .card-top{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
    .card-emoji{{font-size:2rem;flex-shrink:0;width:42px;text-align:center}}
    .card-name{{font-family:'Cormorant Garamond',serif;font-size:1.1rem;font-weight:400;color:#fff8f0}}
    .me-badge{{background:rgba(196,158,64,0.2);color:var(--gold2);border:1px solid rgba(196,158,64,0.35);
      padding:1px 8px;border-radius:999px;font-size:.62rem;font-weight:600;
      font-family:'DM Sans',sans-serif;vertical-align:middle;margin-left:4px}}
    .tier-pill{{padding:4px 10px;border-radius:999px;font-size:.64rem;font-weight:600;
      white-space:nowrap;flex-shrink:0;margin-left:auto}}
    .card-area{{font-family:'Cormorant Garamond',serif;font-size:1rem;font-weight:300;
      margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.06)}}
    .card-score-row{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
    .startup-score-block{{flex-shrink:0;width:52px;height:52px;border-radius:12px;
      display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0}}
    .ss-val{{font-size:1.3rem;font-weight:700;line-height:1}}
    .ss-label{{font-size:.5rem;color:rgba(240,232,216,0.45);text-align:center;letter-spacing:.05em;text-transform:uppercase;line-height:1.4}}
    .card-best{{font-size:.78rem;color:var(--muted);margin-bottom:10px;padding-bottom:10px;
      border-bottom:1px solid rgba(255,255,255,0.06)}}
    .products-section{{margin-bottom:10px}}
    .prod-label{{font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:6px}}
    .prod-item{{font-size:.78rem;color:rgba(240,232,216,0.75);padding:5px 8px;
      background:rgba(255,255,255,0.04);border-radius:8px;margin-bottom:4px;line-height:1.4}}
    .planet-insight{{padding:12px 16px;background:rgba(124,92,191,0.07);
      border-left:3px solid rgba(124,92,191,0.4);margin:0 -16px 0;padding:10px 16px}}
    .insight-text{{font-size:.8rem;color:rgba(240,232,216,0.78);line-height:1.65;font-style:italic}}
    .dasha-line{{font-size:.7rem;color:var(--muted)}}

    /* FOOTER */
    .footer{{text-align:center;padding:24px 16px;font-size:.7rem;color:rgba(240,232,216,0.3);
      border-top:1px solid var(--border);margin-top:12px;line-height:1.8}}

    /* HIDDEN SECTIONS */
    .tab-section{{display:none}}
    .tab-section.active{{display:block}}
  </style>
</head>
<body>

<!-- HERO -->
<div class="hero">
  <div class="hero-badge">Astrowise · Vedic Jyotish · {today}</div>
  <h1>Our Group<br>Business Blueprint</h1>
  <div class="hero-sub">{len(all_data)} charts read · Swiss Ephemeris precision<br>Startup fitness + best business domain per chart</div>
</div>

<!-- NAV -->
<div class="nav-bar">
  <div class="nav-pill active" onclick="showTab('overview',this)">Overview</div>
  <div class="nav-pill" onclick="showTab('cards',this)">All Profiles</div>
  <div class="nav-pill" onclick="showTab('ready',this)">🚀 Startup-Ready</div>
  <div class="nav-pill" onclick="showTab('track',this)">🌱 Founder-Track</div>
  <div class="nav-pill" onclick="showTab('cond',this)">🔄 Conditional</div>
  <div class="nav-pill" onclick="showTab('spec',this)">🏢 Specialist</div>
</div>

<!-- OVERVIEW TAB -->
<div class="tab-section active" id="tab-overview">
  <div class="section">
    <div class="section-title">Group Snapshot</div>
    <div class="section-sub">Scored on lagna lord strength · 10th lord · Mars drive · Current dasha timing</div>

    <div class="stats-row">{stat_html}</div>

    {tier_summary_html}
  </div>
</div>

<!-- ALL PROFILES TAB -->
<div class="tab-section" id="tab-cards">
  <div class="section">
    <div class="section-title">All Profiles</div>
    <div class="section-sub">Sorted by startup fitness · Best domain · Business areas</div>
    {cards_html}
  </div>
</div>

<!-- STARTUP READY TAB -->
<div class="tab-section" id="tab-ready">
  <div class="section">
    <div class="section-title">🚀 Startup-Ready</div>
    <div class="section-sub">Built to lead — strong enough to go alone or lead a team</div>
    {"".join(f"""
    <div class="card">
      <div class="card-stripe" style="background:#5a8f72"></div>
      <div class="card-inner">
        <div class="card-top">
          <div class="card-emoji">{r["emoji"]}</div>
          <div style="flex:1"><div class="card-name">{r["anon"]}{"&nbsp;<span class='me-badge'>You</span>" if r["real_name"]=="Goldy" else ""}</div>
            <span style="font-size:.65rem;color:var(--muted)">{LAGNA_ICON.get(r["lagna"],"✦")} {r["lagna"]} · {r["age"]}y {"♂" if r["gender"]=="M" else "♀"} · 📍{r["location"]}</span></div>
          <div style="color:#5a8f72;font-weight:700;font-size:1.3rem">{r["startup_score"]}</div>
        </div>
        <div class="card-area" style="color:#5a8f72">{r["biz_area"]}</div>
        <div class="planet-insight"><div class="prod-label">🪐 Why this fits</div><div class="insight-text">{r["planet_insight"]}</div></div>
        {"".join(f'<div class="prod-item">{p}</div>' for p in r["products"])}
        <div class="dasha-line" style="margin-top:8px">⏱ {r["dasha"]}</div>
      </div>
    </div>""" for r in by_tier["🚀"])}
  </div>
</div>

<!-- FOUNDER TRACK TAB -->
<div class="tab-section" id="tab-track">
  <div class="section">
    <div class="section-title">🌱 Founder-Track</div>
    <div class="section-sub">Can found with the right co-founder covering gaps</div>
    {"".join(f"""
    <div class="card">
      <div class="card-stripe" style="background:#c49e40"></div>
      <div class="card-inner">
        <div class="card-top">
          <div class="card-emoji">{r["emoji"]}</div>
          <div style="flex:1"><div class="card-name">{r["anon"]}{"&nbsp;<span class='me-badge'>You</span>" if r["real_name"]=="Goldy" else ""}</div>
            <span style="font-size:.65rem;color:var(--muted)">{LAGNA_ICON.get(r["lagna"],"✦")} {r["lagna"]} · {r["age"]}y {"♂" if r["gender"]=="M" else "♀"} · 📍{r["location"]}</span></div>
          <div style="color:#c49e40;font-weight:700;font-size:1.3rem">{r["startup_score"]}</div>
        </div>
        <div class="card-area" style="color:#c49e40">{r["biz_area"]}</div>
        <div class="planet-insight"><div class="prod-label">🪐 Why this fits</div><div class="insight-text">{r["planet_insight"]}</div></div>
        {"".join(f'<div class="prod-item">{p}</div>' for p in r["products"][:2])}
        <div class="dasha-line" style="margin-top:8px">⏱ {r["dasha"]}</div>
      </div>
    </div>""" for r in by_tier["🌱"])}
  </div>
</div>

<!-- CONDITIONAL TAB -->
<div class="tab-section" id="tab-cond">
  <div class="section">
    <div class="section-title">🔄 Conditional</div>
    <div class="section-sub">Strong in one domain · better as early employee or domain co-founder</div>
    {"".join(f"""
    <div class="card">
      <div class="card-stripe" style="background:#5b8fd4"></div>
      <div class="card-inner">
        <div class="card-top">
          <div class="card-emoji">{r["emoji"]}</div>
          <div style="flex:1"><div class="card-name">{r["anon"]}{"&nbsp;<span class='me-badge'>You</span>" if r["real_name"]=="Goldy" else ""}</div>
            <span style="font-size:.65rem;color:var(--muted)">{LAGNA_ICON.get(r["lagna"],"✦")} {r["lagna"]} · {r["age"]}y {"♂" if r["gender"]=="M" else "♀"} · 📍{r["location"]}</span></div>
          <div style="color:#5b8fd4;font-weight:700;font-size:1.3rem">{r["startup_score"]}</div>
        </div>
        <div class="card-area" style="color:#5b8fd4">{r["biz_area"]}</div>
        <div class="planet-insight"><div class="prod-label">🪐 Why this fits</div><div class="insight-text">{r["planet_insight"]}</div></div>
        {"".join(f'<div class="prod-item">{p}</div>' for p in r["products"][:2])}
        <div class="dasha-line" style="margin-top:8px">⏱ {r["dasha"]}</div>
      </div>
    </div>""" for r in by_tier["🔄"])}
  </div>
</div>

<!-- SPECIALIST TAB -->
<div class="tab-section" id="tab-spec">
  <div class="section">
    <div class="section-title">🏢 Specialist</div>
    <div class="section-sub">Thrives in structured, supportive environment — not solo founding</div>
    {"".join(f"""
    <div class="card">
      <div class="card-stripe" style="background:#c4607a"></div>
      <div class="card-inner">
        <div class="card-top">
          <div class="card-emoji">{r["emoji"]}</div>
          <div style="flex:1"><div class="card-name">{r["anon"]}{"&nbsp;<span class='me-badge'>You</span>" if r["real_name"]=="Goldy" else ""}</div>
            <span style="font-size:.65rem;color:var(--muted)">{LAGNA_ICON.get(r["lagna"],"✦")} {r["lagna"]} · {r["age"]}y {"♂" if r["gender"]=="M" else "♀"} · 📍{r["location"]}</span></div>
          <div style="color:#c4607a;font-weight:700;font-size:1.3rem">{r["startup_score"]}</div>
        </div>
        <div class="card-area" style="color:#c4607a">{r["biz_area"]}</div>
        <div class="planet-insight"><div class="prod-label">🪐 Why this fits</div><div class="insight-text">{r["planet_insight"]}</div></div>
        {"".join(f'<div class="prod-item">{p}</div>' for p in r["products"][:2])}
        <div class="dasha-line" style="margin-top:8px">⏱ {r["dasha"]}</div>
      </div>
    </div>""" for r in by_tier["🏢"])}
  </div>
</div>

<div class="footer">
  🔮 Astrowise · Vedic Jyotish · Lahiri Ayanamsha · Swiss Ephemeris<br>
  {len(all_data)} charts · Startup score = Lagna lord + 10th lord + Mars + Dasha timing<br>
  Names anonymised — CH names kept · {today}
</div>

<script>
function showTab(id, btn) {{
  document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-pill').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
  window.scrollTo({{top:0,behavior:'smooth'}});
}}
</script>
</body>
</html>"""

out = "docs/group_insights.html"
with open(out, "w") as f:
    f.write(html)

print(f"\n✅ Written → {out}")
print(f"   Local:  http://192.168.1.102:8765/{out}")
print(f"   Pages:  https://45degrees45.github.io/know-thyself-astro/group_insights.html")
