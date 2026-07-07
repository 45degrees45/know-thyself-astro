#!/usr/bin/env python3
"""
Generate per-profile business area + product recommendations.
Combines: best skill domain + Lagna archetype + dasha themes + key planetary placements.
"""
import sys
from datetime import datetime, date
sys.path.insert(0, "/home/jo/claude_projects/P046_202604_KnowThyselfAstro")

from astro_engine.calc import calculate_chart, SIGNS
from astro_engine.yoga import SIGN_LORD, EXALT_SIGN, DEBIL_SIGN, OWN_SIGNS
from astro_engine.match import _sign_dignity

# ---------------------------------------------------------------------------
# Business domain library — (Lagna, best_domain, dasha) → product ideas
# Hand-crafted from chart context for each profile
# ---------------------------------------------------------------------------

PROFILE_BUSINESS = {
    "Joseph TC": {
        "tier": "🚀", "best_domain": "Operations",
        "primary_area":  "EdTech / Knowledge Consulting",
        "products": [
            "📘 Professional coaching platform (live + async)",
            "🏫 Corporate learning & upskilling SaaS",
            "🤝 B2B advisory marketplace for SMEs",
        ],
        "why": "Jupiter own-sign H1 (wisdom identity) + Mercury H9 (teaching 10th lord) + Venus/Venus dasha = peak window for knowledge products now",
        "avoid": "Physical products, retail, consumer mass market",
        "window": "Now → Oct 2026 (Venus/Venus/Mercury peak)",
    },
    "Remya": {
        "tier": "🚀", "best_domain": "Product",
        "primary_area":  "Analytics SaaS / Communication Tools",
        "products": [
            "📊 Data analytics dashboard for SMEs",
            "✍️ AI writing / content intelligence platform",
            "🔍 Research & insight automation tool",
        ],
        "why": "Mercury exalted H1 (Bhadra Yoga) + 4-planet Gemini stellium = sharpest analyst in the group; Mercury/Jupiter dasha = product + teaching peak",
        "avoid": "Heavy operational execution, physical manufacturing",
        "window": "Now → 2028 (Mercury/Jupiter bhukti = analytical goldmine)",
    },
    "Sai": {
        "tier": "🌱", "best_domain": "Finance",
        "primary_area":  "Fintech / Wealth Infrastructure",
        "products": [
            "💰 Wealth management platform for HNIs",
            "📈 Investment portfolio SaaS for advisors",
            "🏦 Financial compliance / audit automation",
        ],
        "why": "Sasa Yoga (Saturn) + Hamsa Yoga (Jupiter exalted Cancer) + Yoga Karaka Venus = structural financial authority; Finance score 93 is highest in the group",
        "avoid": "Fast consumer apps, entertainment, speculative ventures",
        "window": "2027–2030 (Mercury bhukti within Saturn MD = systems + communication peak)",
    },
    "Gewin": {
        "tier": "🌱", "best_domain": "Operations",
        "primary_area":  "Tech Infrastructure / Community Platforms",
        "products": [
            "⚙️ DevOps / FinOps SaaS for tech teams",
            "🌐 Online community infrastructure platform",
            "🔐 Enterprise security operations tool",
        ],
        "why": "Aquarius Lagna (systems + collective) + Ops 80 + Finance 80 = natural FinOps/TechOps builder; currently Ketu = plan now, launch in Mercury dasha (2026)",
        "avoid": "Solo consumer brand (needs collective/community angle)",
        "window": "2026 Mercury dasha starts — that's the execution window",
    },
    "Tintu": {
        "tier": "🌱", "best_domain": "Finance",
        "primary_area":  "Real Estate Finance / PropTech",
        "products": [
            "🏠 Real estate investment platform",
            "📑 Property deal structuring SaaS",
            "🤝 Joint venture matching for developers",
        ],
        "why": "Capricorn Lagna (structure/real estate) + Jupiter exalted H7 (partner-driven wealth) + Hamsa+Sasa yogas + Finance 73; H12 stellium = international property angle",
        "avoid": "Consumer apps, entertainment, fast-fashion",
        "window": "Mercury antara (late 2026) — Jupiter exalted H7 = ideal for JV/partner deals",
    },
    "Ammu CH": {
        "tier": "🌱", "best_domain": "Product",
        "primary_area":  "Creative Tools / Leadership Development",
        "products": [
            "🎨 Creative collaboration platform for teams",
            "🏆 Leadership coaching program / app",
            "⚡ Sports performance analytics tool",
        ],
        "why": "Leo Lagna (natural authority + creative) + Yoga Karaka Mars (engineering/sports) + H1 triple stellium (Sun/Mercury/Venus) + Viparita Raja Jupiter exalted H12",
        "avoid": "Quiet back-office roles, heavy B2B enterprise",
        "window": "Jupiter bhukti (current) = expansion window for visible platforms",
    },
    "Reddit Girl": {
        "tier": "🌱", "best_domain": "Finance",
        "primary_area":  "Luxury Fintech / Millennial Wealth",
        "products": [
            "💎 Luxury lifestyle subscription platform",
            "📱 Wealth planning app for Gen Z / millennials",
            "🛍️ Premium D2C beauty / wellness brand",
        ],
        "why": "Malavya Yoga (Venus exalted = luxury/beauty) + Hamsa Yoga + Finance 80; Capricorn Lagna = structured wealth instinct; Venus/Venus dasha = beauty/luxury activation",
        "avoid": "Heavy tech infrastructure; better as design-forward consumer brand",
        "window": "Now (Venus/Venus) = launch a brand, not build infrastructure",
    },
    "Spirilla Guy": {
        "tier": "🌱", "best_domain": "Product",
        "primary_area":  "International SaaS / Wellness Tech",
        "products": [
            "🌍 International market entry SaaS",
            "🧘 Meditation / mental wellness app",
            "🎯 Enterprise talent/skills platform",
        ],
        "why": "Malavya Yoga (Venus exalted) + Capricorn Lagna (enterprise) + H12 stellium (international/hidden) + Product 67; Moon/Venus dasha = consumer wellness timing",
        "avoid": "Heavy sales roles, high-street retail",
        "window": "Venus bhukti (now) → Jupiter antara 2026 = international product expansion",
    },
    "Kiran": {
        "tier": "🌱", "best_domain": "Operations",
        "primary_area":  "Real Estate Tech / Supply Chain",
        "products": [
            "🏗️ Construction project management SaaS",
            "📦 Supply chain optimization platform",
            "🏘️ Real estate operations & leasing tool",
        ],
        "why": "Capricorn Lagna (structure) + Sasa Yoga + Yoga Karaka + Ops 73; Saturn H10 exalted = real estate/construction authority; Sun H10 = career-defining power",
        "avoid": "Creative/entertainment, consumer lifestyle brands",
        "window": "Jupiter/Venus now = expansion; Sun bhukti starting = authority/launch phase",
    },
    "Yaqza": {
        "tier": "🌱", "best_domain": "Operations",
        "primary_area":  "Research Platforms / Knowledge Analytics",
        "products": [
            "🔬 Research intelligence platform",
            "📊 Academic / market analytics SaaS",
            "🎓 Knowledge consulting for corporates",
        ],
        "why": "Jupiter+Mercury(R) H10 Leo (2 Raja Yogas = research authority) + Scorpio Lagna (deep investigation) + Jupiter/Mercury dasha = peak intellectual window",
        "avoid": "Mass-market sales, consumer brand",
        "window": "Now → Oct 2027 (Jupiter/Mercury = analytical authority peak)",
    },
    "Bodhi CH": {
        "tier": "🌱", "best_domain": "Operations",
        "primary_area":  "Sustainable Food / AgriTech",
        "products": [
            "🌱 Sustainable food supply platform",
            "🌾 Agri-operations management tool",
            "🍃 Wellness / organic consumer brand",
        ],
        "why": "Taurus Lagna (earth, food, sustainability) + Ops 53 + stable balanced scores; Jupiter/Mercury dasha = knowledge-based food systems; Taurus = beauty meets utility",
        "avoid": "High-risk speculative ventures, fast consumer apps",
        "window": "Mercury bhukti → Jupiter antara 2026 = product validation window",
    },
    "Ruhi CH": {
        "tier": "🌱", "best_domain": "Operations",
        "primary_area":  "Sports Tech / Educational Platforms",
        "products": [
            "🏅 Sports performance tracking app",
            "📚 Student learning operations tool",
            "🎯 Youth skill development platform",
        ],
        "why": "Mars exalted H5 (creative initiative + sports) + Sagittarius Lagna (education/sports/adventure) + Jupiter/Mercury dasha; age 24 = best as co-founder or early employee",
        "avoid": "Solo founding; complex B2B enterprise",
        "window": "2027–2030 (Saturn bhukti = discipline + structures that last)",
    },
    "Jinx": {
        "tier": "🌱", "best_domain": "Operations",
        "primary_area":  "Healthcare Ops / Spiritual Wellness",
        "products": [
            "🏥 Healthcare operations management tool",
            "🧘 Spiritual wellness platform (B2C)",
            "🎵 Sound healing / therapeutic content brand",
        ],
        "why": "Pisces Lagna (healing/spiritual) + Adhi Yoga (prosperity through knowledge) + Ops 67 from Mercury/Saturn; Mercury/Ketu bhukti = transition — healing/research products align",
        "avoid": "Aggressive sales, corporate enterprise",
        "window": "Mercury/Mercury antara 2026 = product definition window",
    },
    "Khayel CH": {
        "tier": "🌱", "best_domain": "Marketing",
        "primary_area":  "Health & Wellness Brand / Precision Marketing",
        "products": [
            "💊 Health/wellness D2C brand",
            "📱 Women's wellness app",
            "🎯 Precision health marketing agency",
        ],
        "why": "Virgo Lagna (health, detail, precision) + Budha-Aditya (intelligence) + Gajakesari (Jupiter-Moon) + Marketing 53; only Marketing-native in the group",
        "avoid": "Heavy ops/infrastructure; abstract tech products",
        "window": "Jupiter antara 2026 = expansion of brand reach",
    },

    # --- CONDITIONAL group ---
    "Athens CH": {
        "tier": "🔄", "best_domain": "Sales",
        "primary_area":  "Service Delivery / Healthcare Sales",
        "products": [
            "🏥 Healthcare service delivery company",
            "⚽ Sports/fitness brand or academy",
            "🛒 High-ticket D2C product sales",
        ],
        "why": "4-planet H6 stellium (service orientation) + Sales 73 + Sun/Mars dasha (high energy, leadership impulse); best as sales-focused co-founder, not solo CEO",
        "avoid": "Abstract product-building; back-office operations",
        "window": "Mars antara (now) = high-action window; don't overthink, execute",
    },
    "Isolda": {
        "tier": "🔄", "best_domain": "Sales",
        "primary_area":  "Luxury Brands / Financial Product Sales",
        "products": [
            "💎 Luxury goods / premium brand sales",
            "📋 Financial product advisory (insurance, wealth)",
            "🏡 High-end real estate sales",
        ],
        "why": "Venus exalted H7 (Malavya = luxury partnerships) + Scorpio Lagna (depth, transformation) + Sales 67; Saturn/Mercury dasha = systematic, long-arc selling",
        "avoid": "Fast consumer apps, speculative founding",
        "window": "Mercury antara (current) = best for structured financial sales roles",
    },
    "Pi CH": {
        "tier": "🔄", "best_domain": "Sales",
        "primary_area":  "Bold Consumer Brand / Fitness Products",
        "products": [
            "🏋️ Fitness / sports consumer brand",
            "💄 Luxury beauty / lifestyle D2C",
            "📣 Consumer tech hardware brand",
        ],
        "why": "Aries Lagna (bold, pioneering) + Malavya Yoga (Venus exalted) + Sales 73 + Marketing 73; 2x Viparita Raja = rises through adversity; best solo founder if she commits",
        "avoid": "B2B software, heavy enterprise, slow methodical roles",
        "window": "Saturn/Mercury antara 2026 = real execution possible despite Ketu fog now",
    },
    "Gracious George": {
        "tier": "🔄", "best_domain": "Sales",
        "primary_area":  "Real Estate / Hospitality / Care Services",
        "products": [
            "🏘️ Real estate development / sales",
            "🍽️ Restaurant / hospitality brand",
            "👴 Elder care / home services platform",
        ],
        "why": "Cancer Lagna (home, food, care) + Yoga Karaka Mars exalted (engineering/building) + Sasa Yoga + Sales 67 + Marketing 67; Saturn/Saturn = infrastructure phase",
        "avoid": "Tech startups, abstract products, international ventures",
        "window": "2028 (Mercury bhukti) = communication/brand launch window",
    },
    "Lalu": {
        "tier": "🔄", "best_domain": "Sales",
        "primary_area":  "Advisory / Consulting (Senior Expert)",
        "products": [
            "🏛️ Senior advisory / mentorship program",
            "🏥 Healthcare consulting (as domain expert)",
            "📖 Knowledge product / memoir / teaching",
        ],
        "why": "Scorpio Lagna + Raja+DKA+Viparita Raja yogas + Sales 80 — but age 68 = wisdom transmission, not active founding. Saturn/Ketu = completion/legacy phase",
        "avoid": "Active founding, scaling, fundraising",
        "window": "Saturn/Mars active — advisory / teaching is the right mode",
    },
    "Soniya": {
        "tier": "🔄", "best_domain": "Finance",
        "primary_area":  "Alternative Investment / Insurance Products",
        "products": [
            "💰 Alternative investment advisory",
            "🛡️ Insurance / wealth protection products",
            "🏦 Transformation finance (distressed assets)",
        ],
        "why": "H8 stellium (Sun/Mercury/Venus/Rahu) = wealth through transformation/others' resources + 7 yogas + Finance 87; Moon MD = emotional public-facing phase — best as face of a finance brand",
        "avoid": "Clean consumer product startup; prefers hidden-wealth structures",
        "window": "Saturn bhukti 2026–2028 = structured financial authority phase",
    },
    "Kunal": {
        "tier": "🔄", "best_domain": "Operations",
        "primary_area":  "Creative Agency / Spiritual Marketing",
        "products": [
            "🎨 Creative operations agency",
            "🌐 Spiritual / wellness marketing brand",
            "🧑‍💻 Tech consulting with creative overlay",
        ],
        "why": "Pisces Lagna (visionary/creative) + Ops 67 + Marketing 67 + Saturn/Saturn = discipline in creative domain; Rahu antara = tech disruption angle works",
        "avoid": "Pure finance, heavy enterprise sales",
        "window": "Mercury bhukti 2028 = communication platform / content product",
    },
    "Always CH": {
        "tier": "🔄", "best_domain": "Operations",
        "primary_area":  "HR Tech / Legal Operations / Consulting",
        "products": [
            "👥 HR operations & compliance tool",
            "⚖️ Legal workflow SaaS",
            "🤝 Partnership / vendor management platform",
        ],
        "why": "Libra Lagna (partnerships, law, balance) + Ops 53 + Budha-Aditya + Jupiter/Mercury dasha; best in structured collaborative environments",
        "avoid": "Solo consumer brand, aggressive B2C sales",
        "window": "Mercury bhukti (now) = best for analytical/systematic product work",
    },
    "Zerin": {
        "tier": "🔄", "best_domain": "Operations",
        "primary_area":  "EdTech / Travel / Adventure (early career)",
        "products": [
            "✈️ Student travel / experiential learning platform",
            "📚 Educational content for Gen Z",
            "🌿 Sustainable lifestyle brand (entry-level)",
        ],
        "why": "Sagittarius Lagna (travel/education/philosophy) + Venus/Sun dasha; age 25 = best as early employee or apprentice founder; Kemadruma needs to be addressed before founding solo",
        "avoid": "Heavy B2B, complex enterprise, solo founding now",
        "window": "Jupiter mahadasha (from ~2028) = real founding window",
    },
    "Athens CH_": {  # duplicate key guard — use Athens
        "tier": "🔄", "best_domain": "Sales",
        "primary_area": "Service Delivery / Healthcare Sales",
        "products": [],
        "why": "", "avoid": "", "window": "",
    },
    "Prakashji": {
        "tier": "🔄", "best_domain": "Operations",
        "primary_area":  "Leadership Consulting / Executive Advisory",
        "products": [
            "🏛️ Executive leadership advisory firm",
            "📋 Org design & operations consulting",
            "🎓 Corporate training & certification",
        ],
        "why": "Leo Lagna (natural authority) + Ops 60 + age 52 = wisdom + experience combination; Saturn/Moon/Mercury = systematic thought + public communication; better as founder of advisory firm than tech startup",
        "avoid": "Consumer tech, fast D2C, youth-oriented products",
        "window": "Mercury antara (now) = best for publishing, teaching, speaking",
    },

    # --- SPECIALIST group — best roles, not founding ---
    "Goldy": {
        "tier": "🏢", "best_domain": "Sales",
        "primary_area":  "Creative / Spiritual Sales (Role, not Founder)",
        "products": [
            "🎨 Art / spiritual product sales lead",
            "🌍 International business development",
            "✍️ Creative consulting & writing",
        ],
        "why": "Pisces Lagna (spiritual/creative) + Sales 53; Rahu/Venus dasha = creative obsession phase — best as sales lead in a creative/spiritual company, not founder",
        "avoid": "Operations, finance, founding solo",
        "window": "Venus bhukti (now) = creative output, not company building",
    },
    "Vi CH": {
        "tier": "🏢", "best_domain": "Product",
        "primary_area":  "Research / Investigation / Back-end Product",
        "products": [
            "🔍 Research analyst at a fintech/product company",
            "🧬 Deep-dive product researcher",
            "🛡️ Security / investigative analyst",
        ],
        "why": "Scorpio Lagna (depth, investigation) + Mars H12 (private internal drive); Ops score 7 = cannot execute publicly; best in back-office product/research role",
        "avoid": "Customer-facing roles, sales, public leadership, founding",
        "window": "Venus antara (now) = relationship-building phase within a team",
    },
    "Biju Jacob": {
        "tier": "🏢", "best_domain": "Operations",
        "primary_area":  "Operations / Project Management (Role)",
        "products": [
            "⚙️ Head of Operations at a growing startup",
            "📋 Project / program manager (enterprise)",
            "🤝 Ops consultant for SMEs",
        ],
        "why": "Libra Lagna (harmony/balance) + Sasa+Raja Yogas BUT Venus (Lagna lord) H12 = identity in loss house; Rahu/Moon/Sun dasha = emotional turbulence — best as excellent #2, not founder",
        "avoid": "Starting own company in this dasha; will lose clarity under pressure",
        "window": "Jupiter mahadasha (from ~2029) = real authority window",
    },
    "Vasudevan": {
        "tier": "🏢", "best_domain": "Product",
        "primary_area":  "Creative Lead / Visual Product (Role)",
        "products": [
            "🎨 Creative director at a product company",
            "🎬 Content / media production lead",
            "🌟 Brand storytelling specialist",
        ],
        "why": "Leo Lagna (creative flair + authority need) + Kemadruma Yoga (needs team to shine) + all scores ≤ 33 = chart works in a supported creative role, not solo founding",
        "avoid": "Solo founding, operations, finance, heavy enterprise",
        "window": "Jupiter/Venus (now) = idealistic creative surge — join a company, not found one",
    },
    "Ann CH": {
        "tier": "🏢", "best_domain": "Operations",
        "primary_area":  "Security / Investigation / Compliance (Role)",
        "products": [
            "🔒 Cybersecurity analyst",
            "⚖️ Legal compliance specialist",
            "🔍 Research / audit professional",
        ],
        "why": "Scorpio Lagna (depth/intensity) + Mars in own house (investigative drive) BUT Mars/Saturn/Ketu = brutal dasha combo; all scores low; best in structured security/investigation org",
        "avoid": "Any startup founding until dasha improves; self-employment now = high stress",
        "window": "Venus mahadasha (from ~2030) = professional flowering",
    },
    "Cini": {
        "tier": "🏢", "best_domain": "Operations",
        "primary_area":  "Education / Counseling / Spiritual Teaching (Role)",
        "products": [
            "📖 Educator / teacher / counselor",
            "🧘 Spiritual facilitator / retreat organizer",
            "🌍 Cross-cultural facilitator (Muscat background)",
        ],
        "why": "Sagittarius Lagna (teaching/philosophy) + despite 8 yogas, planets don't fire well (all scores < 30) + Rahu/Saturn dasha = karmic heavy phase; best in service/teaching role",
        "avoid": "Any business founding during this dasha; heavy financial risk",
        "window": "Jupiter mahadasha (from ~2033) = the real window",
    },
    "Hari CH": {
        "tier": "🚀", "best_domain": "Marketing",
        "primary_area": "Strategic Communications / Thought Leadership / Advisory",
        "products": [
            "🎙️ Executive communications consulting firm",
            "📊 Research & strategic intelligence platform",
            "🖊️ Thought leadership / content advisory for CEOs",
        ],
        "why": "Mercury exalted H1 (Bhadra Yoga) = analytical precision as brand identity; Moon in H10 Gemini = public-facing communicative authority; Jupiter bhukti activating wisdom transmission; age 57 = peak credibility window",
        "avoid": "Finance-heavy ventures (Finance score 20 = two planetary debilitations); partnership-dependent models (Venus debilitated)",
        "window": "Mercury/Jupiter (now) = peak for thought leadership and advisory — the exact alignment needed for this domain",
    },
}

# ---------------------------------------------------------------------------
# Profile metadata (matches generate_profiles_dashboard.py)
# ---------------------------------------------------------------------------

PROFILES = [
    ("Joseph TC",    "1984-08-05", "15:30", 10.10, 76.36, "Asia/Kolkata",   "Sagittarius", "Venus/Venus/Mercury",    "🦅", "M"),
    ("Goldy",        "1985-03-07", "07:15",  9.60, 76.45, "Asia/Kolkata",   "Pisces",      "Rahu/Venus/Venus",       "🐬", "M"),
    ("Prakashji",    "1973-11-04", "01:22", 10.77, 76.65, "Asia/Kolkata",   "Leo",         "Saturn/Moon/Mercury",    "🦁", "M"),
    ("Gewin",        "1984-12-11", "11:55", 23.61, 58.59, "Asia/Muscat",    "Aquarius",    "Ketu/Moon/Saturn",       "🦅", "M"),
    ("Mirjam",       "1975-05-27", "23:00", 52.63,  4.75, "Europe/Amsterdam","Sagittarius","Rahu/Ketu/Rahu",         "🦢", "F"),
    ("Ruhi CH",      "2002-03-03", "02:00",  9.49, 76.33, "Asia/Kolkata",   "Sagittarius", "Jupiter/Mercury/Saturn", "🦌", "F"),
    ("Athens CH",    "2000-06-07", "20:08",  9.55, 76.78, "Asia/Kolkata",   "Sagittarius", "Sun/Mars/Jupiter",       "🦅", "M"),
    ("Zerin",        "2000-11-09", "09:25", 10.87, 76.33, "Asia/Kolkata",   "Sagittarius", "Venus/Sun/Mercury",      "🦌", "F"),
    ("Spirilla Guy", "1996-12-12", "10:15", 13.08, 80.27, "Asia/Kolkata",   "Capricorn",   "Moon/Venus/Jupiter",     "🐬", "M"),
    ("Gracious George","1985-07-24","07:30", 9.75, 77.08, "Asia/Kolkata",   "Cancer",      "Saturn/Saturn/Ketu",     "🐘", "M"),
    ("Yaqza",        "2003-09-19", "12:00", 11.25, 75.77, "Asia/Kolkata",   "Scorpio",     "Jupiter/Mercury/Sun",    "🦅", "M"),
    ("Isolda",       "1985-07-24", "14:04",  9.93, 76.26, "Asia/Kolkata",   "Scorpio",     "Saturn/Mercury/Mercury", "🦚", "F"),
    ("Jinx",         "2001-07-01", "23:30",  8.52, 76.94, "Asia/Kolkata",   "Pisces",      "Mercury/Ketu/Mercury",   "🐅", "F"),
    ("Sai",          "1991-02-24", "04:40",  8.52, 76.94, "Asia/Kolkata",   "Capricorn",   "Saturn/Saturn/Rahu",     "🦅", "M"),
    ("Vi CH",        "1998-08-23", "11:55",  8.52, 76.94, "Asia/Kolkata",   "Scorpio",     "Mars/Rahu/Venus",        "🦅", "F"),
    ("Pi CH",        "1989-10-01", "20:43", 10.52, 76.21, "Asia/Kolkata",   "Aries",       "Saturn/Saturn/Ketu",     "🐅", "F"),
    ("Lalu",         "1958-05-18", "19:30", 10.10, 76.36, "Asia/Kolkata",   "Scorpio",     "Saturn/Mars/Ketu",       "🐍", "F"),
    ("Reddit Girl",  "2002-11-16", "11:25", 26.91, 75.79, "Asia/Kolkata",   "Capricorn",   "Venus/Venus/Rahu",       "🦢", "F"),
    ("Tintu",        "1990-12-26", "09:30", 10.10, 76.36, "Asia/Kolkata",   "Capricorn",   "Venus/Ketu/Mercury",     "🐘", "M"),
    ("Cini",         "1985-10-29", "11:30", 23.61, 58.59, "Asia/Muscat",    "Sagittarius", "Rahu/Saturn/Saturn",     "🐘", "F"),
    ("Khayel CH",    "2001-01-01", "00:02", 25.20, 55.27, "Asia/Dubai",     "Virgo",       "Saturn/Mars/Jupiter",    "🦁", "F"),
    ("Soniya",       "1984-06-13", "16:15", 10.77, 76.65, "Asia/Kolkata",   "Libra",       "Moon/Saturn/Venus",      "🦚", "F"),
    ("Vasudevan",    "1999-06-23", "10:30", 10.02, 76.31, "Asia/Kolkata",   "Leo",         "Jupiter/Venus/Venus",    "🦁", "M"),
    ("Remya",        "1987-06-18", "06:30", 10.10, 76.36, "Asia/Kolkata",   "Gemini",      "Mercury/Jupiter/Mercury","🐬", "F"),
    ("Ammu CH",      "1990-09-05", "05:30",  8.52, 76.94, "Asia/Kolkata",   "Leo",         "Saturn/Jupiter/Jupiter", "🦁", "F"),
    ("Biju Jacob",   "1983-11-10", "05:30", 23.61, 58.59, "Asia/Muscat",    "Libra",       "Rahu/Moon/Sun",          "🦋", "M"),
    ("Kiran",        "1983-11-02", "12:58", 10.77, 76.00, "Asia/Kolkata",   "Capricorn",   "Jupiter/Venus/Sun",      "🦁", "M"),
    ("Ann CH",       "1994-08-09", "13:30",  9.94, 76.35, "Asia/Kolkata",   "Scorpio",     "Mars/Saturn/Ketu",       "🦋", "F"),
    ("Always CH",    "1991-09-21", "08:45", 28.70, 77.10, "Asia/Kolkata",   "Libra",       "Jupiter/Mercury/Sun",    "🦋", "M"),
    ("Bodhi CH",     "1991-09-05", "21:50",  9.73, 76.33, "Asia/Kolkata",   "Taurus",      "Jupiter/Mercury/Jupiter","🐘", "M"),
    ("Kunal",        "1993-09-10", "18:50", 27.56, 76.61, "Asia/Kolkata",   "Pisces",      "Saturn/Saturn/Rahu",     "🐅", "M"),
    ("Hari CH",      "1968-09-16", "07:15",  8.52, 76.94, "Asia/Kolkata",   "Virgo",       "Mercury/Jupiter/Sun",    "🦊", "M"),
]

SKILL_PLANETS = {
    "Product":    ["Jupiter", "Venus", "Mercury"],
    "Operations": ["Saturn", "Mars", "Mercury"],
    "Sales":      ["Venus", "Mercury", "Moon"],
    "Marketing":  ["Venus", "Mercury", "Sun"],
    "Finance":    ["Jupiter", "Saturn", "Venus"],
}
SKILL_MIN, SKILL_MAX = -6, 9

DOMAIN_COLORS = {
    "Product":"#7c5cbf","Operations":"#c4607a","Sales":"#5b8fd4",
    "Marketing":"#c49e40","Finance":"#5a8f72",
}
DOMAIN_ICONS = {"Product":"🔮","Operations":"⚙️","Sales":"🤝","Marketing":"📣","Finance":"💰"}
LAGNA_ICONS = {
    "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋","Leo":"♌","Virgo":"♍",
    "Libra":"♎","Scorpio":"♏","Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓",
}
TIER_COLORS = {"🚀":"#5a8f72","🌱":"#c49e40","🔄":"#5b8fd4","🏢":"#c4607a"}
TIER_NAMES  = {"🚀":"Startup-Ready","🌱":"Founder-Track","🔄":"Conditional","🏢":"Specialist"}

def compute_skills(chart):
    skills = {}
    for skill, planets in SKILL_PLANETS.items():
        raw = sum(_sign_dignity(p, chart["planets"][p]["sign"]) for p in planets)
        skills[skill] = round((raw - SKILL_MIN) / (SKILL_MAX - SKILL_MIN) * 100)
    return skills

print("Computing charts...", flush=True)
rows = []
for (name, dob, t, lat, lon, tz, lagna, dasha, animal, gender) in PROFILES:
    try:
        chart = calculate_chart(dob, t, lat, lon, tz)
        skills = compute_skills(chart)
        best = max(skills, key=skills.get)
        age = (date.today() - datetime.strptime(dob, "%Y-%m-%d").date()).days // 365
        biz = PROFILE_BUSINESS.get(name)
        if not biz:
            biz = {"tier":"🔄","best_domain":best,"primary_area":"TBD","products":[],"why":"—","avoid":"—","window":"—"}
        rows.append({
            "name": name, "lagna": lagna, "dasha": dasha,
            "animal": animal, "age": age, "skills": skills,
            "best": best, "overall": round(sum(skills.values())/5),
            **biz,
        })
        print(f"  ✓ {name:18s} → {biz['primary_area']}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# Sort by tier priority then overall score
TIER_RANK = {"🚀":0,"🌱":1,"🔄":2,"🏢":3}
rows.sort(key=lambda r: (TIER_RANK.get(r["tier"],4), -r["overall"]))

# ---------------------------------------------------------------------------
# Build HTML
# ---------------------------------------------------------------------------

today = datetime.today().strftime("%B %d, %Y")

cards_html = ""
for r in rows:
    tc = TIER_COLORS.get(r["tier"], "#c49e40")
    bc = DOMAIN_COLORS.get(r["best_domain"], "#c49e40")
    bi = DOMAIN_ICONS.get(r["best_domain"], "✦")
    ls = LAGNA_ICONS.get(r["lagna"], "✦")
    tn = TIER_NAMES.get(r["tier"], r["tier"])

    products_li = "".join(f'<li>{p}</li>' for p in r["products"])

    cards_html += f"""
    <div class="bcard">
      <div class="bcard-top" style="border-left:4px solid {tc}">
        <div class="bcard-head">
          <div class="bcard-animal">{r["animal"]}</div>
          <div>
            <div class="bcard-name">{r["name"]}</div>
            <div class="bcard-meta">{ls} {r["lagna"]} · {r["age"]}y · <span style="color:{tc}">{r["tier"]} {tn}</span></div>
          </div>
          <div class="bcard-domain" style="background:{bc}22;color:{bc};border:1px solid {bc}44">{bi} {r["best_domain"]}</div>
        </div>
        <div class="bcard-area" style="color:{tc}">{r["primary_area"]}</div>
      </div>

      <div class="bcard-body">
        <div class="bcard-products">
          <div class="blabel">Best Products / Roles</div>
          <ul class="product-list">{products_li}</ul>
        </div>
        <div class="bcard-detail">
          <div class="blabel">Why this fits</div>
          <div class="bcard-why">{r["why"]}</div>
          <div class="blabel" style="margin-top:12px">Avoid</div>
          <div class="bcard-avoid">{r["avoid"]}</div>
          <div class="blabel" style="margin-top:12px">⏱ Best Window</div>
          <div class="bcard-window" style="color:{tc}">{r["window"]}</div>
        </div>
      </div>

      <div class="bcard-dasha">Current dasha: <strong style="color:rgba(196,158,64,0.8)">{r["dasha"]}</strong></div>
    </div>"""

# Cluster by tier for the summary view
from collections import defaultdict
by_tier = defaultdict(list)
for r in rows:
    by_tier[r["tier"]].append(r)

cluster_html = ""
for tier_icon in ["🚀","🌱","🔄","🏢"]:
    members = by_tier[tier_icon]
    if not members:
        continue
    tc = TIER_COLORS[tier_icon]
    tn = TIER_NAMES[tier_icon]

    table_rows = ""
    for r in members:
        bc = DOMAIN_COLORS.get(r["best_domain"], "#c49e40")
        bi = DOMAIN_ICONS.get(r["best_domain"], "✦")
        products_mini = " · ".join(p.split(" ",1)[1] if " " in p else p for p in r["products"][:2])
        table_rows += f"""
        <tr>
          <td>{r["animal"]} <strong>{r["name"]}</strong><br>
            <span style="font-size:.68rem;color:var(--muted)">{LAGNA_ICONS.get(r["lagna"],"✦")} {r["lagna"]} · {r["age"]}y</span></td>
          <td><strong style="color:{tc}">{r["primary_area"]}</strong></td>
          <td style="font-size:.75rem;color:{bc}">{bi} {r["best_domain"]}</td>
          <td style="font-size:.75rem;color:rgba(240,232,216,0.65)">{products_mini}</td>
          <td style="font-size:.72rem;color:rgba(196,158,64,0.65)">{r["dasha"]}</td>
          <td style="font-size:.72rem;color:{tc};font-style:italic">{r["window"].split(" =")[0] if r["window"] != "—" else "—"}</td>
        </tr>"""

    cluster_html += f"""
    <div class="cluster" style="border-top:3px solid {tc}">
      <div class="cluster-head">
        <span style="font-size:1.8rem">{tier_icon}</span>
        <div>
          <div style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;color:{tc}">{tn}</div>
          <div style="font-size:.78rem;color:var(--muted);">{len(members)} profiles</div>
        </div>
      </div>
      <table class="ctable">
        <thead><tr>
          <th>Name</th><th>Business Area</th><th>Domain Strength</th>
          <th>Top Products</th><th>Current Dasha</th><th>Best Window</th>
        </tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="robots" content="noindex, nofollow">
  <title>Astrowise — Business Areas & Products by Chart</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root{{--bg:#0b0b18;--surface:rgba(255,255,255,0.035);--border:rgba(196,158,64,0.18);
      --gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.55);
      --plum:#7c5cbf;--rose:#c4607a;--sage:#5a8f72;--blue:#5b8fd4;
      --shadow:0 20px 60px rgba(0,0,0,0.45);--r:22px}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'DM Sans',system-ui,sans-serif;background-color:var(--bg);
      background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(124,92,191,0.18),transparent),
        radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.12),transparent);
      background-attachment:fixed;color:var(--cream);min-height:100vh;padding:48px 24px 80px}}
    .container{{max-width:1360px;margin:0 auto}}

    .hero{{text-align:center;margin-bottom:52px}}
    .hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(2.4rem,6vw,4.2rem);font-weight:300;color:#fff8f0}}
    .hero-sub{{font-size:.84rem;color:var(--muted);margin-top:10px}}
    .eyebrow{{font-size:.7rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}}

    .divider{{display:flex;align-items:center;gap:16px;margin:44px 0 28px;font-size:.65rem;
      letter-spacing:.3em;text-transform:uppercase;color:rgba(240,232,216,0.3)}}
    .divider::before,.divider::after{{content:'';flex:1;height:1px;background:var(--border)}}

    /* CLUSTER SUMMARY */
    .cluster{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
      padding:22px 26px;margin-bottom:22px;box-shadow:var(--shadow)}}
    .cluster-head{{display:flex;align-items:center;gap:14px;margin-bottom:16px}}
    .ctable{{width:100%;border-collapse:collapse;font-size:.84rem}}
    .ctable th{{text-align:left;padding:8px 12px;background:rgba(196,158,64,0.08);color:var(--gold);
      font-size:.65rem;letter-spacing:.15em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,0.15)}}
    .ctable td{{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.04);vertical-align:top;line-height:1.55}}
    .ctable tr:last-child td{{border-bottom:none}}
    .ctable tr:hover td{{background:rgba(255,255,255,0.02)}}

    /* CARDS */
    .cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px}}
    .bcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
      overflow:hidden;box-shadow:var(--shadow);transition:.2s}}
    .bcard:hover{{transform:translateY(-3px);box-shadow:0 32px 80px rgba(0,0,0,0.5)}}
    .bcard-top{{padding:18px 20px 14px}}
    .bcard-head{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
    .bcard-animal{{font-size:1.9rem;flex-shrink:0;width:38px;text-align:center}}
    .bcard-name{{font-family:'Cormorant Garamond',serif;font-size:1.15rem;font-weight:400;color:#fff8f0}}
    .bcard-meta{{font-size:.7rem;color:var(--muted);margin-top:2px}}
    .bcard-domain{{margin-left:auto;flex-shrink:0;padding:4px 10px;border-radius:999px;font-size:.68rem;font-weight:600;white-space:nowrap}}
    .bcard-area{{font-family:'Cormorant Garamond',serif;font-size:1.1rem;font-weight:400;padding-top:4px}}

    .bcard-body{{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid rgba(255,255,255,0.06)}}
    .bcard-products{{padding:14px 16px;border-right:1px solid rgba(255,255,255,0.06)}}
    .bcard-detail{{padding:14px 16px}}
    .blabel{{font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:6px}}
    .product-list{{list-style:none;padding:0;display:flex;flex-direction:column;gap:5px}}
    .product-list li{{font-size:.8rem;color:rgba(240,232,216,0.8);line-height:1.5;
      padding:5px 8px;background:rgba(255,255,255,0.04);border-radius:8px}}
    .bcard-why{{font-size:.78rem;color:rgba(240,232,216,0.7);line-height:1.6}}
    .bcard-avoid{{font-size:.76rem;color:rgba(196,96,122,0.8);line-height:1.5}}
    .bcard-window{{font-size:.76rem;font-weight:500;line-height:1.5}}
    .bcard-dasha{{padding:10px 16px;background:rgba(196,158,64,0.04);border-top:1px solid rgba(196,158,64,0.1);
      font-size:.72rem;color:var(--muted)}}

    .footer{{text-align:center;padding:24px 0;font-size:.72rem;color:rgba(240,232,216,0.3);
      letter-spacing:.08em;border-top:1px solid var(--border);margin-top:40px}}

    @media(max-width:768px){{
      .cards-grid{{grid-template-columns:1fr}}
      .bcard-body{{grid-template-columns:1fr}}
      .bcard-products{{border-right:none;border-bottom:1px solid rgba(255,255,255,0.06)}}
      .ctable{{font-size:.74rem}}
    }}
  </style>
</head>
<body>
<div class="container">

  <div class="hero">
    <div class="eyebrow">Vedic Jyotish · Lagna + Domain + Dasha = Business Fit</div>
    <h1>Business Areas & Products by Chart</h1>
    <div class="hero-sub">{len(rows)} profiles · Best startup domain · Specific product ideas · Timing windows · {today}</div>
  </div>

  <div class="divider">Summary by Tier</div>
  {cluster_html}

  <div class="divider">Full Profile Cards</div>
  <div class="cards-grid">{cards_html}</div>

  <div class="footer">Generated {today} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris · {len(rows)} profiles<br>
    Business fit = Lagna archetype + skill domain strength + dasha planet themes + key yogas</div>
</div>
</body>
</html>"""

out_path = "docs/profiles_business_domains.html"
with open(out_path, "w") as f:
    f.write(html)

print(f"\n✅ Written → {out_path}")
print(f"\nQuick summary:")
for tier in ["🚀","🌱","🔄","🏢"]:
    members = by_tier[tier]
    print(f"  {tier} {TIER_NAMES[tier]}: {', '.join(r['name'] for r in members)}")
    for r in members:
        print(f"       → {r['name']}: {r['primary_area']}")
