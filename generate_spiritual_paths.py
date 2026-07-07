#!/usr/bin/env python3
"""Generate spiritual paths & inclinations HTML for all 31 profiles."""
from datetime import datetime, date
from collections import Counter

ANON = {
    "Joseph TC":      ("The Wise Eagle",        "🦅"),
    "Goldy":          ("Me",                    "🐬"),
    "Prakashji":      ("The Royal Lion",         "🦁"),
    "Gewin":          ("The Mystic Eagle",       "🦅"),
    "Mirjam":         ("The White Swan",         "🦢"),
    "Zerin":          ("The Golden Deer",        "🦌"),
    "Spirilla Guy":   ("The Deep Dolphin",       "🐬"),
    "Gracious George":("The Steady Elephant",    "🐘"),
    "Yaqza":          ("The Storm Eagle",        "🦅"),
    "Isolda":         ("The Dark Peacock",       "🦚"),
    "Jinx":           ("The Midnight Tiger",     "🐅"),
    "Sai":            ("The Mountain Eagle",     "🦅"),
    "Lalu":           ("The Ancient Cobra",      "🐍"),
    "Reddit Girl":    ("The Moonlit Swan",       "🦢"),
    "Tintu":          ("The Gentle Elephant",    "🐘"),
    "Cini":           ("The Desert Elephant",    "🐘"),
    "Soniya":         ("The Celestial Peacock",  "🦚"),
    "Vasudevan":      ("The Golden Lion",        "🦁"),
    "Remya":          ("The Swift Dolphin",      "🐬"),
    "Biju Jacob":     ("The Wandering Butterfly","🦋"),
    "Kiran":          ("The Stone Lion",         "🦁"),
    "Ann CH":         ("Ann CH",                "🦋"),
    "Athens CH":      ("Athens CH",             "🦅"),
    "Ruhi CH":        ("Ruhi CH",               "🦌"),
    "Vi CH":          ("Vi CH",                 "🦅"),
    "Pi CH":          ("Pi CH",                 "🐅"),
    "Bodhi CH":       ("Bodhi CH",              "🐘"),
    "Ammu CH":        ("Ammu CH",               "🦁"),
    "Always CH":      ("Always CH",             "🦋"),
    "Khayel CH":      ("Khayel CH",             "🦁"),
    "Kunal":          ("The Indigo Tiger",       "🐅"),
}

PATH_KEYS = {
    "Dharmic": {"label":"Dharmic Teacher","icon":"🎓","color":"#c49e40","bg":"rgba(196,158,64,0.09)","border":"rgba(196,158,64,0.28)","stripe":"rgba(196,158,64,0.5)"},
    "Jnana":   {"label":"Jnana — Wisdom","icon":"🧠","color":"#5b8fd4","bg":"rgba(91,143,212,0.09)","border":"rgba(91,143,212,0.28)","stripe":"rgba(91,143,212,0.5)"},
    "Bhakti":  {"label":"Bhakti — Devotion","icon":"💗","color":"#c4607a","bg":"rgba(196,96,122,0.09)","border":"rgba(196,96,122,0.28)","stripe":"rgba(196,96,122,0.5)"},
    "Karma":   {"label":"Karma Yoga — Service","icon":"⚙️","color":"#5a8f72","bg":"rgba(90,143,114,0.09)","border":"rgba(90,143,114,0.28)","stripe":"rgba(90,143,114,0.5)"},
    "Mystic":  {"label":"Mystic / Tantric","icon":"🔮","color":"#7c5cbf","bg":"rgba(124,92,191,0.09)","border":"rgba(124,92,191,0.28)","stripe":"rgba(124,92,191,0.5)"},
}

SPIRITUAL = {
    "Joseph TC": {
        "path":"Dharmic",
        "archetype":"The Knowledge Carrier",
        "indicators":["Jupiter H1 own sign — Hamsa Yoga","Saturn exalted H11 — community as sangha","9th house (Leo) anchored by Sun"],
        "description":"Jupiter in his own sign on the Ascendant marks a born teacher — wisdom is literally the face this soul shows the world. Spiritual growth happens through sharing knowledge, mentorship and building structures that serve others long-term. Saturn exalted in H11 means the community he builds becomes his spiritual sangha.",
        "strengths":["Natural philosophical depth","Inspiring clarity in transmission","Patient long-term dharmic vision"],
        "shadow":"Spiritual pride — Jupiter on Lagna can breed certainty that one is always right; the lesson is humility before the teaching itself",
        "practices":["Teaching and mentorship circles as primary sadhana","Systematic study of sacred texts","Building learning communities as seva"],
    },
    "Goldy": {
        "path":"Bhakti",
        "archetype":"The Ocean Seeker",
        "indicators":["Pisces Lagna — the moksha sign of dissolution","Rahu H2 — intense longing between material and transcendent","Jupiter H4 — wisdom scattered across inner world"],
        "description":"Pisces is the most moksha-oriented sign — the soul here is meant to dissolve into the cosmic ocean rather than accumulate. Rahu in H2 creates spiritual hunger that oscillates between material desire and transcendence. True peace comes through surrender, not achievement — devotional practice, ocean, music and non-attachment are the doorways.",
        "strengths":["Deep empathy and natural non-judgment","Access to subtle emotional and spiritual dimensions","Capacity for profound surrender"],
        "shadow":"Escapism — confusing spiritual yearning with avoidance; dissolving boundaries under the guise of non-attachment",
        "practices":["Ocean or water meditation","Devotional music and bhajans","Dream journaling and conscious surrender practices"],
    },
    "Prakashji": {
        "path":"Dharmic",
        "archetype":"The Disciplined King",
        "indicators":["Leo Lagna — Sun as authority principle","Sun H4 Scorpio — authority earned through depth","Saturn dasha — karmic clearing through structured leadership"],
        "description":"Leo Lagna with Sun in Scorpio means authority earned through depth and transformation, not appearance. Saturn dasha is a long karmic reckoning — the spiritual path is honest service and patient working through old debts. True dharmic leadership requires ego surrender; the lesson is that real authority comes from within, not from titles.",
        "strengths":["Natural authority earned through lived experience","Ability to face and transmit difficult truths","Disciplined long-term vision"],
        "shadow":"Ego attachment to the leadership role — difficulty acknowledging vulnerability or being wrong in front of others",
        "practices":["Seva — selfless service in the community","Shiva or transformative deity practice","Structured morning sadhana"],
    },
    "Gewin": {
        "path":"Jnana",
        "archetype":"The Systematic Detacher",
        "indicators":["Ketu mahadasha — stripping attachments to reveal what is eternal","Saturn exalted H9 Libra — dharma through ordered systems","Aquarius Lagna — universal consciousness archetype"],
        "description":"Ketu mahadasha is one of the most spiritually charged periods in Jyotish — it systematically dissolves what is non-essential. Aquarius Lagna ruled by Saturn naturally gravitates toward detachment, universal consciousness and humanitarian service. The path is inward and analytical: understanding the nature of mind and releasing identification with the personal self.",
        "strengths":["Natural detachment from ego-driven outcomes","Ability to see through conventional illusions clearly","Analytical access to philosophical truth"],
        "shadow":"Dissociation — using detachment as a shield against emotional vulnerability; spirituality as withdrawal rather than expansion",
        "practices":["Vipassana or silent retreat","Humanitarian service without personal agenda","Pranayama and breath awareness"],
    },
    "Mirjam": {
        "path":"Dharmic",
        "archetype":"The Wandering Philosopher",
        "indicators":["Jupiter H1 own sign Sagittarius — Hamsa Yoga","Rahu/Ketu axis H1–H7 — soul vs. relationship","Rahu dasha driving cross-border expansion"],
        "description":"Hamsa Yoga (Jupiter in own sign on the Ascendant) marks a dharma teacher carrying wisdom across lifetimes. The Rahu/Ketu axis through H1-H7 pushes this soul to stop seeking itself through others and stand as an independent beacon. The spiritual journey is becoming the teaching, not endlessly finding the next teacher.",
        "strengths":["Philosophical depth and cross-cultural wisdom","Natural grace and inspiration","Ability to transmit across cultural and linguistic boundaries"],
        "shadow":"Seeking external validation through relationship rather than resting in inner spiritual authority",
        "practices":["Cross-cultural spiritual study and pilgrimage","Wisdom-sharing circles and group teaching","Solitary retreats to consolidate inner authority"],
    },
    "Ruhi CH": {
        "path":"Karma",
        "archetype":"The Sacred Athlete",
        "indicators":["Mars exalted H5 Capricorn — fierce disciplined creative force","Jupiter rules Lagna — purpose holds the container","Sagittarius Lagna — philosophical archer seeking meaning through action"],
        "description":"Mars exalted in the house of sport and creativity means the spiritual path runs through the body and disciplined action. Sacred exertion, training and competition are her forms of prayer. Jupiter provides the philosophical container to hold the meaning; Mars provides the will to actually live it.",
        "strengths":["Physical and mental discipline as genuine spiritual path","Inspiring others through action and embodied example","Kinesthetic spiritual intelligence — the body as teacher"],
        "shadow":"Spiritual bypass through constant busyness and doing; avoiding inner stillness and silence",
        "practices":["Athletic training as moving meditation — conscious intention before each session","Pranayama for the warrior body","Service in sports coaching or youth development"],
    },
    "Athens CH": {
        "path":"Karma",
        "archetype":"The Sacred Servant",
        "indicators":["4-planet H6 stellium — service and problem-solving as dharma","Bhadra + 2 Raja Yogas — knowledge used in service","Sun/Mars dasha — peak action energy"],
        "description":"A 4-planet H6 stellium is the clearest karma yogi signature in Jyotish — service, problem-solving and showing up for others is dharma, not just work. The spiritual path is to offer each act of service fully and without expectation. The divine is encountered not in retreat but in complete presence for those who need help.",
        "strengths":["Tireless service energy as spiritual fuel","Problem-solving as sacred craft","Health consciousness as offering"],
        "shadow":"Martyrdom — giving so completely that personal needs are neglected, then resenting others for not filling the void",
        "practices":["Healthcare or community volunteering","Energy healing study (Reiki, pranic healing)","Body-based spiritual practices — yoga, tai chi"],
    },
    "Zerin": {
        "path":"Bhakti",
        "archetype":"The Longing Heart",
        "indicators":["Jupiter H1 — philosophical depth","Kemadruma Moon — isolated emotional intensity as spiritual driver","Venus dasha — heart opening now"],
        "description":"The Kemadruma Moon creates a deep inner longing that nothing worldly satisfies — this is the mark of a soul that knows it needs more than the material can provide. Venus dasha is now opening the heart; the path is through beauty, conscious relationship and surrender to love as a divine force. Bhakti — devotion — is the key that unlocks the mystery.",
        "strengths":["Capacity for profound devotional love","Emotional depth as spiritual fuel","Aesthetic sensitivity that sees beauty as sacred"],
        "shadow":"Projecting the divine onto human relationships and collapsing them under that weight; heartbreak as spiritual crisis",
        "practices":["Devotional chanting and kirtan","Love as conscious spiritual practice — each relationship as teaching","Sacred music and poetry as daily offering"],
    },
    "Spirilla Guy": {
        "path":"Mystic",
        "archetype":"The Hidden Dreamer",
        "indicators":["Venus exalted Pisces — Malavya Yoga (beauty as divine channel)","H12 stellium — one foot always in the invisible world","Moon dasha — emotional depths surfacing"],
        "description":"Multiple planets in H12 and Venus exalted in Pisces give this chart one foot perpetually in invisible realms. H12 is the house of liberation, solitude and dissolution — drawn toward mystical states and union with the unseen. The spiritual path involves embracing aloneness as sacred rather than as something to escape.",
        "strengths":["Natural access to subtle and invisible dimensions","Receptivity to inspiration beyond ordinary consciousness","Deep devotional capacity when directed toward the sacred"],
        "shadow":"Escapism — using mystical orientation as avoidance of grounded practical responsibilities",
        "practices":["Solitary silent retreats","Ocean or water meditation and dream work","Mantra japa in private — the hidden path suits this chart"],
    },
    "Gracious George": {
        "path":"Karma",
        "archetype":"The Builder-Priest",
        "indicators":["Mars exalted H1 Capricorn — Yoga Karaka (dharma through building)","Saturn dasha — karma clearing through patience and structure","Cancer Lagna — the home and family are the temple"],
        "description":"Cancer Lagna with Yoga Karaka Mars makes this chart a builder of sanctuaries — homes, communities and safe spaces are the spiritual offering. Saturn dasha is not punishment but a graduation ceremony; every structure built with integrity is an act of worship. Protecting and nurturing the family is the prayer.",
        "strengths":["Protective and nurturing instinct as spiritual expression","Building lasting physical structures as sacred act","Holding space for others through long difficult passages"],
        "shadow":"Over-identifying with home and family as the complete spiritual domain; missing the invitation to wider service",
        "practices":["Family ritual and home altar practice","Seva through building or maintaining community spaces","Saturn/Shani puja for karmic clarity"],
    },
    "Yaqza": {
        "path":"Jnana",
        "archetype":"The Truth Investigator",
        "indicators":["Jupiter + Mercury both in Leo H10 — two Raja Yogas at the dharma peak","Scorpio Lagna — natural occultist and depth researcher","Jupiter/Mercury dasha — dual wisdom activation now"],
        "description":"Scorpio Lagna is one of Jyotish's great mystery signs — drawn to what lies beneath the surface, to hidden truth and transformative knowledge. Jupiter and Mercury together in H10 Leo make the public expression of this wisdom the spiritual calling. The path is research, revelation and making esoteric knowledge accessible to others.",
        "strengths":["Fearless inquiry into deep and uncomfortable truths","Synthesising complex knowledge for practical use","Natural researcher of occult and esoteric domains"],
        "shadow":"Using knowledge to feel superior rather than to serve; obsessive thinking as substitute for embodied experience",
        "practices":["Jyotish or occult science study with depth","Philosophical research and investigative reading","Teaching esoteric knowledge to accessible audiences"],
    },
    "Isolda": {
        "path":"Mystic",
        "archetype":"The Sacred Alchemist",
        "indicators":["Venus exalted H7 Pisces — Malavya Yoga (sacred partnership)","Scorpio Lagna — depth, transformation, occult by nature","Saturn dasha — structure applied to the mystical dimension"],
        "description":"Scorpio Lagna with Venus exalted in H7 Pisces is one of the most potent spiritual configurations — called toward sacred partnership, conscious union and beauty as a pathway to the divine. This is the tantric archetype: finding the eternal through deep, intentional intimacy. Saturn dasha brings discernment to what was previously purely intuitive depth.",
        "strengths":["Understanding of sacred relationship and transformative union","Ability to transmute pain into beauty","Access to hidden power through deep receptivity"],
        "shadow":"Confusing codependency with spiritual depth; using the partner as a substitute for the inner union that is the real goal",
        "practices":["Study of sacred relationship and conscious partnership frameworks","Beauty as devotional practice — art, music, adornment","Shadow work through depth psychology"],
    },
    "Jinx": {
        "path":"Mystic",
        "archetype":"The Dissolution Walker",
        "indicators":["Pisces Lagna — moksha sign, dissolution of self","Ketu bhukti — active spiritual dissolution NOW","Adhi Yoga — three benefics in angular positions (rare grace marker)"],
        "description":"Pisces with Ketu bhukti active is among the most purely spiritual combinations in this pool — the soul is actively dismantling old forms to reveal what is essential. Adhi Yoga (three benefics in angular positions) gives unusual clarity once the dissolution is integrated. This is not a gentle path but it is direct.",
        "strengths":["Direct channel to healing and spiritual dimensions","Capacity for profound surrender — ego is thinner here than elsewhere","Natural healing gifts that surface once the path stabilises"],
        "shadow":"Confusion between spiritual dissolution and mental health challenge — the container must be built before the walls come fully down",
        "practices":["Structured meditation with a teacher (not free-floating)","Energy healing training with proper grounding","Earth contact, bodywork and physical routine as anchors"],
    },
    "Sai": {
        "path":"Karma",
        "archetype":"The Cosmic Builder",
        "indicators":["Saturn exalted — Sasa Yoga (discipline as cosmic dharma)","Jupiter exalted H2 Cancer — Hamsa Yoga (wisdom through values)","Saturn mahadasha — 20-year karmic crystallisation in progress"],
        "description":"Two Pancha Mahapurusha Yogas (Sasa + Hamsa) means the spiritual path operates at cosmic scale — building structures that serve long-term human welfare. Saturn/Saturn dasha is the great forge; every external achievement is simultaneously an inner initiation. The Bhagavad Gita's karma yoga is the exact text for this chart.",
        "strengths":["Extraordinary patience for long-term dharmic work","Natural authority earned through discipline not status","Holding vision across decades without wavering"],
        "shadow":"Equating busyness and achievement with spiritual progress; avoiding the inner silence where the real work happens",
        "practices":["Bhagavad Gita study — karma yoga chapters specifically","Vipassana or structured meditation as counterweight","Building dharmic institutions: learning centres, community structures"],
    },
    "Vi CH": {
        "path":"Mystic",
        "archetype":"The Hidden Investigator",
        "indicators":["Mars (Lagna lord) H12 — drive flows inward","Scorpio Lagna — occult investigator by nature","Triple Leo H10 stellium — public truth-revealing mission"],
        "description":"Scorpio's investigative depth combined with Mars flowing into H12 creates a spiritual detective — drawn to occult research, hidden patterns and the mechanics of transformation. The triple Leo stellium in H10 carries an impulse to bring hidden knowledge into public light as service. The spiritual path is through understanding depth and using it to illuminate others.",
        "strengths":["Fearless depth into what others cannot sustain","Uncovering hidden patterns and bringing them to useful light","Transformative presence — just being present changes something"],
        "shadow":"Power shadow — using penetrating capacity to control rather than illuminate",
        "practices":["Esoteric study with a structured framework and teacher","Shadow work and depth psychology","Mars rituals for conscious channelling of intensity"],
    },
    "Pi CH": {
        "path":"Mystic",
        "archetype":"The Phoenix Forger",
        "indicators":["Two Viparita Raja Yogas — greatest gains come after loss","Venus exalted — Malavya Yoga (beauty through adversity)","Saturn/Ketu coming — major liberatory transition ahead"],
        "description":"Two Viparita Raja Yogas in one chart is a rare signature: deepest breakthroughs come from loss, not success. The spiritual path runs through fire, and the fire is part of the design. Saturn is the forge; Ketu will be the liberation. The task is to stop fighting the losses and start understanding them as initiations.",
        "strengths":["Resilience forged through actual ordeal — not theoretical","Courage to walk through collapse toward what is real","Emergence after dissolution is genuinely new, not just recovery"],
        "shadow":"Spiritual bypass — rushing to the lesson without grieving the loss; intellectualising rather than feeling",
        "practices":["Transformational breathwork or cathartic body practices","Crisis-as-initiation framework: the shamanic view of ordeal","Shadow work: befriending the parts that look like enemies"],
    },
    "Lalu": {
        "path":"Karma",
        "archetype":"The Elder Healer",
        "indicators":["Three major yogas (Raja, DKA, Viparita Raja) — lifetime of earned wisdom","Scorpio Lagna — depth medicine from lived transformation","Ketu bhukti — completing the arc, stripping to essential wisdom"],
        "description":"Decades of transformation through Scorpio Lagna have created a healer's wisdom ready to flow outward. The Ketu bhukti is completing a major arc — stripping what no longer serves, leaving only the essential. This is the elder healer archetype: past wounds metabolised into medicine for others.",
        "strengths":["Experiential wisdom depth no book can provide","Non-judgmental compassion earned through personal transformation","Natural capacity to hold space for others in the depths"],
        "shadow":"Holding the healer identity so tightly it becomes another attachment — the medicine must flow, not accumulate",
        "practices":["Energy healing modalities (transmission stage)","Mentoring younger people through transformative passages","Kali or transformative deity practices — honouring the goddess of endings"],
    },
    "Reddit Girl": {
        "path":"Bhakti",
        "archetype":"The Awakening Swan",
        "indicators":["Jupiter exalted — Hamsa Yoga (wisdom and grace)","Venus exalted — Malavya Yoga (beauty as divine channel)","Venus/Venus dasha — peak heart-opening at age 23"],
        "description":"Two Pancha Mahapurusha Yogas (Hamsa + Malavya) in a 23-year-old's chart is extraordinary — spiritual gifts just beginning to awaken. The path is devotion through beauty: both Jupiter's wisdom and Venus's grace are exalted, suggesting the divine is accessible through art, aesthetics, sacred philosophy and conscious relationship.",
        "strengths":["Natural aesthetic intelligence as genuine spiritual vehicle","Philosophical depth beyond her chronological age","Inspiring others through beauty and devotion combined"],
        "shadow":"Materialism disguised as spirituality — confusing luxury and comfort with sacred beauty",
        "practices":["Sacred art — creating as offering rather than product","Vedanta or bhakti philosophy through relationship lenses","Beauty as conscious practice: adorning the world as an act of love"],
    },
    "Tintu": {
        "path":"Jnana",
        "archetype":"The Contemplative Seeker",
        "indicators":["Jupiter exalted H7 Cancer — wisdom through partnership (partner as guru)","H12 stellium — habitual access to invisible dimensions","Ketu bhukti active NOW — spiritual awakening phase"],
        "description":"Jupiter exalted in H7 means wisdom arrives through relationship — the partner is often a mirror or teacher. H12 stellium means the native operates partly in visible and partly in unseen dimensions. Ketu bhukti is currently active, triggering spiritual dissolution. This is a pivotal moment to go inward — the contemplative path fits this chart precisely.",
        "strengths":["Deep contemplative capacity — internal worlds are rich","Wisdom accessed through reflection and relationship","Access to the mystical through ordinary life"],
        "shadow":"Spiritual seeking as flight from practical responsibilities — the unseen world as escape",
        "practices":["Silent meditation retreats","Non-dual philosophy (Advaita Vedanta, Kashmir Shaivism)","Finding and working closely with a spiritual teacher"],
    },
    "Cini": {
        "path":"Dharmic",
        "archetype":"The Dharma Carrier",
        "indicators":["Sagittarius Lagna — the pure dharma-seeker and teacher sign","Eight yogas with philosophical orientation","Rahu dasha driving cross-cultural expansion and questioning"],
        "description":"Sagittarius is the pure dharma sign — the seeker, the teacher, the arrow pointed at truth. Though the yogas carry less concentrated planetary fuel than they could, the sincere orientation toward dharmic service is genuine. The path is beautifully simple: keep learning, keep teaching, keep pointing others toward truth.",
        "strengths":["Natural philosophical optimism and hope as spiritual gift","Ability to inspire faith and higher vision in others","Cross-cultural openness to diverse spiritual systems"],
        "shadow":"Spiritual restlessness — always seeking the next teacher or system, never arriving and staying long enough to deepen",
        "practices":["Consistent daily practice — same time, same method, for years","Teaching what you already know now (not waiting for more)","Pilgrimage: the journey itself as teaching"],
    },
    "Khayel CH": {
        "path":"Jnana",
        "archetype":"The Precise Healer",
        "indicators":["Budha-Aditya Yoga — Sun + Mercury (discriminating intellect)","Gajakesari — Jupiter trine Moon (wisdom and grace together)","Virgo Lagna — discrimination between pure and impure as dharma"],
        "description":"Virgo Lagna with Budha-Aditya creates a mind that naturally discriminates the pure from the impure — which is a fundamentally spiritual act. The capacity to see clearly what is aligned and what is not is Virgo's core dharma. Gajakesari adds wisdom and social grace. The path is through discerning service to health and healing.",
        "strengths":["Analytical spiritual intelligence — seeing what others cannot","Natural healing orientation and fine discrimination","Integrating spiritual wisdom into practical daily life"],
        "shadow":"Perfectionism in spiritual practice — self-criticism that blocks grace; the path cannot be algorithmically optimised",
        "practices":["Ayurveda study and daily lifestyle practice","Service in healing or health professions as sacred vocation","Discernment practices — learning to hear the inner signal beneath the noise"],
    },
    "Soniya": {
        "path":"Mystic",
        "archetype":"The Transformation Alchemist",
        "indicators":["4-planet H8 stellium (Sun/Mercury/Venus/Rahu) — deepest occult signature in pool","Two Viparita Raja Yogas — crises as catapults","H8 as the house of hidden wealth, death, transformation, occult"],
        "description":"A 4-planet H8 stellium is the strongest possible alchemical, tantric signature. This soul is built to work with the hidden forces of life — money, power, death, sexuality and the unseen. The spiritual path runs through depth, not around it; every crisis is an initiation into a deeper layer. The conventional definition of 'problem' simply does not apply here.",
        "strengths":["Extraordinary access to hidden dimensions and occult knowledge","Ability to transform what others fear into something useful","Alchemical capacity: finding gold in the darkest materials"],
        "shadow":"Addiction to intensity and transformation as the only valid spiritual experience; needing crisis to feel alive",
        "practices":["Tantric study — the yoga of union through depth (not pop tantra)","Shadow work and depth psychology as regular practice","Esoteric traditions: Kabbalah, alchemy, Jyotish's hidden chapters"],
    },
    "Vasudevan": {
        "path":"Bhakti",
        "archetype":"The Radiant Devotee",
        "indicators":["Leo Lagna + Yoga Karaka Mars — creative fire as sacred purpose","Jupiter/Venus dasha — expansion through beauty and devotion now","Kemadruma Moon — emotional longing as engine of spiritual seeking"],
        "description":"Leo's creative fire combined with Jupiter/Venus dasha creates a natural bhakta — one who finds the divine through beauty, music and creative expression. The Kemadruma Moon creates a deep emotional hunger that no worldly success can satisfy, and this longing is precisely the engine of spiritual seeking. Sacred creative expression — art, music, theatre as conscious offering — is the path home.",
        "strengths":["Making the spiritual beautiful and emotionally accessible","Natural devotional performance that opens others' hearts","Heart-centred presence as spiritual transmission"],
        "shadow":"Needing spiritual experiences to be emotionally intense; quiet subtle inner practice feels empty",
        "practices":["Music, dance or art as deliberate devotional offering","Kirtan, bhajan or choral spiritual music","Making creative work a conscious gift rather than performance"],
    },
    "Remya": {
        "path":"Jnana",
        "archetype":"The Swift Mind Oracle",
        "indicators":["Mercury exalted H1 Gemini — Bhadra Yoga (mind as spiritual instrument)","Four planets in H1 — the native embodies the teaching","Mercury/Jupiter dasha — wisdom and intellect simultaneously activated"],
        "description":"Bhadra Yoga — Mercury exalted in its own sign on the Ascendant — is the quintessential Jnana yogi signature. The mind itself is the spiritual instrument; studying, understanding, communicating and writing are not merely work but worship. Mercury/Jupiter dasha is the perfect window for going deep into philosophical and contemplative inquiry.",
        "strengths":["Mind as genuine spiritual vehicle — thinking itself can be meditative","Communicating complex spiritual concepts with precision","Learning and teaching as devotional practice"],
        "shadow":"Spiritual intellectualism — knowing without being; staying in the head to avoid the vulnerability of the heart",
        "practices":["Vedanta study — the philosophical-intellectual path par excellence","Journaling as spiritual practice: making the invisible visible","Teaching and mentoring as the practice of giving what you know"],
    },
    "Ammu CH": {
        "path":"Jnana",
        "archetype":"The Quietly Liberated",
        "indicators":["Jupiter exalted H12 Pisces — liberation marker (moksha yoga)","H1 triple stellium — strong identity being gradually surrendered","Jupiter bhukti active NOW — door to genuine insight is open"],
        "description":"Jupiter exalted in H12 is one of Jyotish's clearest liberation markers — a soul carrying earned grace. The strong H1 triple stellium means the personal identity is vivid and powerful, but the spiritual path is toward its gradual dissolution. The Jupiter bhukti currently running is an open invitation to walk through that door.",
        "strengths":["Access to genuine wisdom beyond mere book knowledge","Capacity for quiet, undramatic transformation","Spiritual grace that flows naturally rather than being performed"],
        "shadow":"Spiritual ambition — wanting to achieve liberation as another accomplishment; the path is surrender, not achievement",
        "practices":["Advaita Vedanta — non-dual philosophy of H12 and liberation","Silent contemplation — sitting with the vastness without agenda","Working closely with a qualified spiritual teacher"],
    },
    "Biju Jacob": {
        "path":"Bhakti",
        "archetype":"The Hidden Devotee",
        "indicators":["Venus (Lagna lord) H12 — devotion hidden from the outer world","Rahu/Moon dasha — outer expansion vs. inner pull in tension","Libra Lagna — harmony and beauty as spiritual language"],
        "description":"Venus hidden in H12 is the mark of a quiet, deeply private devotee — whose spiritual life is intensely real but invisible to others. Rahu/Moon dasha creates tension between outward expansion and inward longing. The spiritual life flourishes in private for this chart; forcing it outward diminishes it.",
        "strengths":["Private devotional depth that is genuine and unperformative","Finding the sacred in hidden, quiet corners","Non-attachment to spiritual recognition or audience"],
        "shadow":"Completely separating spiritual life from the outer world, causing fragmentation — inner gifts remaining forever invisible",
        "practices":["Private devotion — prayer, mantra, sacred reading — without performance","Mystical poetry and devotional music in solitude","Gradually integrating inner and outer life without forcing"],
    },
    "Kiran": {
        "path":"Karma",
        "archetype":"The Dharmic Worker",
        "indicators":["Saturn exalted H10 — Sasa Yoga at the career peak","Sun also in H10 — solar authority through visible structured work","Jupiter/Venus dasha — wisdom and beauty blessing the work"],
        "description":"Saturn exalted in H10 (Sasa Yoga at the career house) is the clearest karma yogi signature — work itself is the spiritual practice. The career and spiritual development are identical, not separate. Every project completed with integrity is a puja; every structure built carefully is an act of worship. Jupiter/Venus dasha is currently gracing the work with wisdom and harmony.",
        "strengths":["Work as worship — complete integration of spiritual and material","Discipline as a form of love and offering","Building what lasts across generations"],
        "shadow":"Using busyness as permanent avoidance of inner work — the spiritual life is always 'later'",
        "practices":["Bhagavad Gita study — karma yoga chapters specifically","Occasional silent retreats as counterweight to the active life","Beginning each workday with conscious intention"],
    },
    "Ann CH": {
        "path":"Mystic",
        "archetype":"The Will-Forged Seeker",
        "indicators":["Mars H1 Scorpio — penetrating investigative intensity in the body","Mars/Saturn dasha — hardest activation period, forging the spiritual will","Scorpio Lagna — inherent depth and occult affinity"],
        "description":"Scorpio with Mars in H1 gives extraordinary capacity for depth and penetrating past surfaces — all genuinely spiritual qualities. Mars/Saturn dasha is intense but is forging the spiritual will through pressure, as a blade is made. The mystical path emerges through understanding power, transformation and karma — not through softness.",
        "strengths":["Natural access to depth that most cannot sustain","Spiritual will forged through actual challenge","Fearless approach to uncomfortable truths in self and others"],
        "shadow":"Premature spiritual intensity — going too deep too fast before a stable container is in place",
        "practices":["Occult sciences studied slowly and with a teacher, not alone","Martial arts or physical discipline as moving spiritual practice","Shadow work with proper guidance and support"],
    },
    "Always CH": {
        "path":"Jnana",
        "archetype":"The Balanced Philosopher",
        "indicators":["Budha-Aditya Yoga in Libra — intellect expressed through balance","Jupiter/Mercury dasha — dual wisdom activation simultaneously","Libra Lagna — dharma manifested through right relationship and harmony"],
        "description":"Budha-Aditya Yoga with Jupiter/Mercury dasha running simultaneously is a rare alignment of philosophical and communicative energy. The spiritual path is through learning and teaching — specifically creating fair, balanced structures of knowledge. Libra's dharma is to model harmony in all domains including the spiritual; every fair act is an offering.",
        "strengths":["Teaching spiritual concepts fairly and accessibly","Balance itself as a form of spiritual mastery","Social wisdom — understanding the ethics of relationship as sacred knowledge"],
        "shadow":"Perpetually seeing all sides as a way to avoid committing to any path; wisdom without commitment leads nowhere",
        "practices":["Studying philosophy and ethical thought","Facilitating spiritual discussion groups — the path is through dialogue","Writing and journaling as integration of insight"],
    },
    "Bodhi CH": {
        "path":"Bhakti",
        "archetype":"The Earth Temple Keeper",
        "indicators":["Taurus Lagna — earth, body, sensory experience as divine manifestation","Venus rules Taurus — beauty and abundance as sacred domain","Jupiter/Mercury dasha — stable philosophical container for embodied living"],
        "description":"Taurus Lagna is the earth-temple archetype — the spiritual path runs through the body, through nature, through taste, touch, sound and the physical world as divine creation. This is not a path of renunciation but of full embodiment. Food we eat, land we tend, things we grow — all are sacred acts when done with awareness.",
        "strengths":["Grounded presence that makes spirituality practical and accessible","Natural connection to earth rhythms and cycles","Body as temple — physical and spiritual health as one"],
        "shadow":"Mistaking sensory comfort and pleasure for spiritual experience; physical abundance becoming the end rather than the means",
        "practices":["Nature practices — gardening, forest bathing, working with the land","Ayurvedic lifestyle — seasonal eating, daily rhythm","Sacred sound and chanting (music through the physical body)"],
    },
    "Kunal": {
        "path":"Mystic",
        "archetype":"The Structured Visionary",
        "indicators":["Pisces Lagna — moksha sign, dissolution into the cosmic","Saturn/Saturn dasha — 20-year discipline on the most fluid Lagna","Bhadra + Gajakesari + 3 Raja Yogas — visionary with structural capacity"],
        "description":"Pisces Lagna is the mystical dreamer — a soul who belongs as much to invisible worlds as visible ones. Saturn mahadasha is the productive paradox: the most structured, disciplined energy working through the most fluid, boundaryless sign. The spiritual path is creative discipline — using Saturn's focused will to channel Piscean visions into forms that serve others.",
        "strengths":["Access to visionary and mystical states that inform original work","Capacity to build structure around the formless (rare and valuable)","Deep empathy as natural spiritual transmission"],
        "shadow":"Dissolving into spiritual longing without ever committing to one specific daily practice",
        "practices":["Structured creative practice — daily writing, art-making, composing","Sacred music and mantra as spiritual anchor","Studying mystical traditions with a teacher who provides the container"],
    },
}

PROFILES = [
    ("Joseph TC",     "1984-08-05","15:30", "Sagittarius","Venus/Venus/Mercury",    "🦅","M","Aluva, Kerala"),
    ("Goldy",         "1985-03-07","07:15", "Pisces",     "Rahu/Venus/Venus",       "🐬","M","Kangazha, Kerala"),
    ("Prakashji",     "1973-11-04","01:22", "Leo",        "Saturn/Moon/Mercury",    "🦁","M","Palakkad, Kerala"),
    ("Gewin",         "1984-12-11","11:55", "Aquarius",   "Ketu/Moon/Saturn",       "🦅","M","Muscat, Oman"),
    ("Mirjam",        "1975-05-27","23:00", "Sagittarius","Rahu/Ketu/Rahu",         "🦢","F","Alkmaar, Netherlands"),
    ("Ruhi CH",       "2002-03-03","02:00", "Sagittarius","Jupiter/Mercury/Saturn", "🦌","F","Alleppey, Kerala"),
    ("Athens CH",     "2000-06-07","20:08", "Sagittarius","Sun/Mars/Jupiter",       "🦅","M","Kanjirapally, Kerala"),
    ("Zerin",         "2000-11-09","09:25", "Sagittarius","Venus/Sun/Mercury",      "🦌","F","Cherpulassery, Kerala"),
    ("Spirilla Guy",  "1996-12-12","10:15", "Capricorn",  "Moon/Venus/Jupiter",     "🐬","M","Chennai, India"),
    ("Gracious George","1985-07-24","07:30","Cancer",     "Saturn/Saturn/Ketu",     "🐘","M","Kattappana, Kerala"),
    ("Yaqza",         "2003-09-19","12:00", "Scorpio",    "Jupiter/Mercury/Sun",    "🦅","M","Kozhikode, Kerala"),
    ("Isolda",        "1985-07-24","14:04", "Scorpio",    "Saturn/Mercury/Mercury", "🦚","F","Cochin, Kerala"),
    ("Jinx",          "2001-07-01","23:30", "Pisces",     "Mercury/Ketu/Mercury",   "🐅","F","Trivandrum, Kerala"),
    ("Sai",           "1991-02-24","04:40", "Capricorn",  "Saturn/Saturn/Rahu",     "🦅","M","Trivandrum, Kerala"),
    ("Vi CH",         "1998-08-23","11:55", "Scorpio",    "Mars/Rahu/Venus",        "🦅","F","Trivandrum, Kerala"),
    ("Pi CH",         "1989-10-01","20:43", "Aries",      "Saturn/Saturn/Ketu",     "🐅","F","Thrissur, Kerala"),
    ("Lalu",          "1958-05-18","19:30", "Scorpio",    "Saturn/Mars/Ketu",       "🐍","F","Aluva, Kerala"),
    ("Reddit Girl",   "2002-11-16","11:25", "Capricorn",  "Venus/Venus/Rahu",       "🦢","F","Jaipur, Rajasthan"),
    ("Tintu",         "1990-12-26","09:30", "Capricorn",  "Venus/Ketu/Mercury",     "🐘","M","Aluva, Kerala"),
    ("Cini",          "1985-10-29","11:30", "Sagittarius","Rahu/Saturn/Saturn",     "🐘","F","Muscat, Oman"),
    ("Khayel CH",     "2001-01-01","00:02", "Virgo",      "Saturn/Mars/Jupiter",    "🦁","F","Dubai, UAE"),
    ("Soniya",        "1984-06-13","16:15", "Libra",      "Moon/Saturn/Venus",      "🦚","F","Palakkad, Kerala"),
    ("Vasudevan",     "1999-06-23","10:30", "Leo",        "Jupiter/Venus/Venus",    "🦁","M","Edappally, Kerala"),
    ("Remya",         "1987-06-18","06:30", "Gemini",     "Mercury/Jupiter/Mercury","🐬","F","Aluva, Kerala"),
    ("Ammu CH",       "1990-09-05","05:30", "Leo",        "Saturn/Jupiter/Jupiter", "🦁","F","Trivandrum, Kerala"),
    ("Biju Jacob",    "1983-11-10","05:30", "Libra",      "Rahu/Moon/Sun",          "🦋","M","Muscat, Oman"),
    ("Kiran",         "1983-11-02","12:58", "Capricorn",  "Jupiter/Venus/Sun",      "🦁","M","Ottapalam, Kerala"),
    ("Ann CH",        "1994-08-09","13:30", "Scorpio",    "Mars/Saturn/Ketu",       "🦋","F","Tripunithura, Kerala"),
    ("Always CH",     "1991-09-21","08:45", "Libra",      "Jupiter/Mercury/Sun",    "🦋","M","Delhi, India"),
    ("Bodhi CH",      "1991-09-05","21:50", "Taurus",     "Jupiter/Mercury/Jupiter","🐘","M","Cherthala, Kerala"),
    ("Kunal",         "1993-09-10","18:50", "Pisces",     "Saturn/Saturn/Rahu",     "🐅","M","Alwar, Rajasthan"),
]

LAGNA_ICON = {
    "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋","Leo":"♌","Virgo":"♍",
    "Libra":"♎","Scorpio":"♏","Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓"
}

all_data = []
for row in PROFILES:
    name, dob, t, lagna, dasha, animal, gender, location = row
    age = (date.today() - datetime.strptime(dob, "%Y-%m-%d").date()).days // 365
    anon_name, anon_emoji = ANON.get(name, (name, animal))
    gender_sym = "♂" if gender == "M" else "♀"
    sp = SPIRITUAL[name]
    pk = PATH_KEYS[sp["path"]]
    all_data.append({
        "name": name, "anon": anon_name, "emoji": anon_emoji,
        "lagna": lagna, "dasha": dasha, "age": age,
        "gender_sym": gender_sym, "location": location,
        "path": sp["path"], "pk": pk,
        "archetype": sp["archetype"],
        "indicators": sp["indicators"],
        "description": sp["description"],
        "strengths": sp["strengths"],
        "shadow": sp["shadow"],
        "practices": sp["practices"],
        "is_me": (name == "Goldy"),
    })

path_counts = Counter(d["path"] for d in all_data)
today_str = datetime.now().strftime("%d %B %Y")

# ---------------------------------------------------------------------------
# HTML GENERATION
# ---------------------------------------------------------------------------
def card_html(d):
    pk = d["pk"]
    ls = LAGNA_ICON.get(d["lagna"], "")
    me_badge = ' <span style="background:rgba(196,158,64,0.2);border:1px solid rgba(196,158,64,0.4);color:#e8c96a;font-size:0.65rem;padding:2px 8px;border-radius:999px;vertical-align:middle;">You</span>' if d["is_me"] else ""
    inds = "".join(
        f'<span style="display:inline-block;background:rgba(255,255,255,0.05);border:1px solid {pk["border"]};border-radius:999px;padding:4px 12px;font-size:0.76rem;color:{pk["color"]};margin:3px 4px 3px 0">{i}</span>'
        for i in d["indicators"]
    )
    strengths = "".join(f'<li>{s}</li>' for s in d["strengths"])
    practices = "".join(f'<li>{p}</li>' for p in d["practices"])
    return f"""
<div class="card" data-path="{d['path']}">
  <div class="card-stripe" style="background:{pk['stripe']}"></div>
  <div class="card-body">
    <div class="card-top">
      <div>
        <div class="card-name">{d['anon']} {d['emoji']}{me_badge}</div>
        <div class="card-sub">{ls} {d['lagna']} · {d['age']}y {d['gender_sym']} · 📍{d['location']}</div>
        <div class="card-dasha" style="color:{pk['color']}">↻ {d['dasha']}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div class="path-badge" style="background:{pk['bg']};border:1px solid {pk['border']};color:{pk['color']}">{pk['icon']} {pk['label']}</div>
        <div class="archetype-label">{d['archetype']}</div>
      </div>
    </div>
    <div class="indicators">{inds}</div>
    <p class="card-desc">{d['description']}</p>
    <div class="card-grid">
      <div>
        <div class="col-label" style="color:{pk['color']}">Spiritual Strengths</div>
        <ul class="bullet-list">{strengths}</ul>
      </div>
      <div>
        <div class="col-label" style="color:#c4607a">Shadow / Block</div>
        <p class="shadow-text">{d['shadow']}</p>
      </div>
    </div>
    <div class="practice-box" style="background:{pk['bg']};border:1px solid {pk['border']}">
      <div class="col-label" style="color:{pk['color']}">Recommended Practices</div>
      <ul class="bullet-list">{practices}</ul>
    </div>
  </div>
</div>"""


PATH_ORDER = ["All", "Jnana", "Bhakti", "Karma", "Mystic", "Dharmic"]
PATH_ALL_LABELS = {
    "All":     ("✦","All Paths","rgba(196,158,64,0.12)","#e8c96a"),
    "Jnana":   ("🧠","Jnana","rgba(91,143,212,0.12)","#5b8fd4"),
    "Bhakti":  ("💗","Bhakti","rgba(196,96,122,0.12)","#c4607a"),
    "Karma":   ("⚙️","Karma","rgba(90,143,114,0.12)","#5a8f72"),
    "Mystic":  ("🔮","Mystic","rgba(124,92,191,0.12)","#7c5cbf"),
    "Dharmic": ("🎓","Dharmic","rgba(196,158,64,0.12)","#c49e40"),
}

tab_html = ""
for p in PATH_ORDER:
    icon, label, bg, col = PATH_ALL_LABELS[p]
    cnt = len(all_data) if p == "All" else path_counts.get(p, 0)
    active = ' tab-active' if p == "All" else ""
    tab_html += f'<button class="tab{active}" onclick="filterPath(\'{p}\')" style="--tab-col:{col}">{icon} {label} <span class="tab-count">{cnt}</span></button>\n'

all_cards = "\n".join(card_html(d) for d in all_data)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow">
<title>Spiritual Paths — Group Reading</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0b0b18;--surface:rgba(255,255,255,0.035);--border:rgba(196,158,64,0.18);
  --gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.55);
  --plum:#7c5cbf;--rose:#c4607a;--sage:#5a8f72;--blue:#5b8fd4;
  --shadow:0 20px 60px rgba(0,0,0,0.45);--r:20px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  font-family:'DM Sans',system-ui,sans-serif;font-size:15px;color:var(--cream);
  background-color:var(--bg);
  background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(124,92,191,0.18),transparent),
    radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.12),transparent);
  background-attachment:fixed;min-height:100vh;
}}
a{{color:inherit;text-decoration:none}}

/* HERO */
.hero{{
  max-width:1100px;margin:0 auto;padding:48px 24px 0;text-align:center;
}}
.hero-eyebrow{{font-size:0.68rem;letter-spacing:0.32em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}}
.hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(2.4rem,5vw,4rem);font-weight:300;color:#fff8f0;line-height:1.15;margin-bottom:10px}}
.hero-sub{{font-size:0.9rem;color:var(--muted);max-width:580px;margin:0 auto 32px}}

/* STAT PILLS */
.stat-row{{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-bottom:32px}}
.stat-pill{{background:var(--surface);border:1px solid var(--border);border-radius:999px;
  padding:8px 18px;font-size:0.82rem;display:flex;align-items:center;gap:8px}}
.stat-pill-num{{font-size:1.1rem;font-weight:600;font-family:'Cormorant Garamond',serif}}

/* TABS */
.tabs{{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;max-width:1100px;margin:0 auto 28px;padding:0 24px}}
.tab{{
  background:var(--surface);border:1px solid rgba(255,255,255,0.08);
  border-radius:999px;padding:9px 18px;font-size:0.82rem;color:var(--muted);
  cursor:pointer;transition:all .2s;font-family:'DM Sans',sans-serif;
}}
.tab:hover{{border-color:var(--tab-col);color:var(--tab-col)}}
.tab-active{{background:rgba(255,255,255,0.06);border-color:var(--tab-col)!important;color:var(--tab-col)!important;font-weight:600}}
.tab-count{{background:rgba(255,255,255,0.08);border-radius:999px;padding:1px 7px;font-size:0.72rem;margin-left:4px}}

/* GRID */
.grid{{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(480px,1fr));
  gap:20px;max-width:1100px;margin:0 auto;padding:0 24px 80px;
}}

/* CARD */
.card{{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  display:flex;overflow:hidden;box-shadow:var(--shadow);transition:transform .2s;
  position:relative;
}}
.card:hover{{transform:translateY(-2px)}}
.card-stripe{{width:4px;flex-shrink:0}}
.card-body{{padding:22px 22px 20px;flex:1;min-width:0}}
.card-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:12px}}
.card-name{{font-family:'Cormorant Garamond',serif;font-size:1.25rem;font-weight:400;color:#fff8f0;margin-bottom:2px}}
.card-sub{{font-size:0.76rem;color:var(--muted);margin-bottom:3px}}
.card-dasha{{font-size:0.72rem;letter-spacing:0.04em}}
.path-badge{{border-radius:999px;padding:5px 12px;font-size:0.72rem;font-weight:600;white-space:nowrap;text-align:center}}
.archetype-label{{font-size:0.68rem;color:var(--muted);text-align:right;margin-top:5px;font-style:italic}}
.indicators{{margin-bottom:12px}}
.card-desc{{font-size:0.87rem;line-height:1.75;color:rgba(240,232,216,0.82);margin-bottom:14px}}
.card-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}}
.col-label{{font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;font-weight:600;margin-bottom:7px}}
.bullet-list{{list-style:none;padding:0;display:flex;flex-direction:column;gap:5px}}
.bullet-list li{{font-size:0.83rem;color:rgba(240,232,216,0.78);line-height:1.55;padding-left:14px;position:relative}}
.bullet-list li::before{{content:"·";position:absolute;left:3px;color:var(--gold)}}
.shadow-text{{font-size:0.83rem;color:rgba(196,96,122,0.85);line-height:1.6}}
.practice-box{{border-radius:12px;padding:12px 14px}}
.practice-box .bullet-list li::before{{content:"→"}}

/* HIDDEN */
.card.hidden{{display:none}}

/* FOOTER */
.footer{{text-align:center;padding:20px 0;font-size:0.72rem;color:rgba(240,232,216,0.3);
  letter-spacing:0.08em;border-top:1px solid var(--border);margin-top:0}}

/* MOBILE */
@media(max-width:600px){{
  .grid{{grid-template-columns:1fr;padding:0 16px 60px}}
  .card-grid{{grid-template-columns:1fr}}
  .card-top{{flex-direction:column;align-items:flex-start}}
  .path-badge,.archetype-label{{text-align:left}}
  .hero{{padding:36px 16px 0}}
}}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-eyebrow">Jyotish Group Reading · 31 Charts</div>
  <h1>Spiritual Paths &amp;<br>Inclinations</h1>
  <p class="hero-sub">The most probable spiritual path for each chart in the pool — derived from Lagna, Ketu placement, H8/H9/H12, Moon nakshatra and current dasha activation.</p>
  <div class="stat-row">
    <div class="stat-pill"><span style="color:#5b8fd4">🧠</span><span class="stat-pill-num" style="color:#5b8fd4">{path_counts['Jnana']}</span><span>Jnana — Wisdom</span></div>
    <div class="stat-pill"><span style="color:#c4607a">💗</span><span class="stat-pill-num" style="color:#c4607a">{path_counts['Bhakti']}</span><span>Bhakti — Devotion</span></div>
    <div class="stat-pill"><span style="color:#5a8f72">⚙️</span><span class="stat-pill-num" style="color:#5a8f72">{path_counts['Karma']}</span><span>Karma Yoga — Service</span></div>
    <div class="stat-pill"><span style="color:#7c5cbf">🔮</span><span class="stat-pill-num" style="color:#7c5cbf">{path_counts['Mystic']}</span><span>Mystic / Tantric</span></div>
    <div class="stat-pill"><span style="color:#c49e40">🎓</span><span class="stat-pill-num" style="color:#c49e40">{path_counts['Dharmic']}</span><span>Dharmic Teacher</span></div>
  </div>
</div>

<div class="tabs">
{tab_html}
</div>

<div class="grid" id="grid">
{all_cards}
</div>

<div class="footer">Generated {today_str} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris</div>

<script>
function filterPath(p) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab-active'));
  event.target.closest('.tab').classList.add('tab-active');
  document.querySelectorAll('.card').forEach(c => {{
    if (p === 'All' || c.dataset.path === p) c.classList.remove('hidden');
    else c.classList.add('hidden');
  }});
}}
</script>
</body>
</html>"""

import os
os.makedirs("docs", exist_ok=True)
with open("docs/spiritual_paths.html", "w") as f:
    f.write(html)

print(f"✓ docs/spiritual_paths.html written ({len(html):,} bytes)")
print(f"  Path distribution: {dict(path_counts)}")
