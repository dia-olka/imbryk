"""Initial WorldLedger state — Python port of world-ledger.initial.ts."""

from .types import (
    Alliance,
    Conflict,
    CulturalMovement,
    CultureState,
    Currency,
    EconomicsState,
    EnvironmentalCrisis,
    EnvironmentState,
    GeopoliticsState,
    HistoricalEvent,
    MilitaryForce,
    MilitaryState,
    Nation,
    Scarcity,
    TechDomain,
    TechnologyState,
    TradingBloc,
    WorldLedger,
)

INITIAL_WORLD_LEDGER = WorldLedger(
    epoch="Year Zero \u2014 The Morning After",
    synopsis=(
        "The old order collapsed not with a bang but with a cascade of defaults,"
        " sanctions, and walked-out summits. What remains is a world of six major"
        " power blocs circling each other warily, none strong enough to dominate,"
        " all too proud to cooperate. The Atlantic Republic and the Eastern Compact"
        " stare across a digital iron curtain while the European Commonwealth tries"
        " to hold the centre. The Southern Union demands a seat at every table it"
        " was once excluded from, the Pacific Rim Alliance hedges all bets, and the"
        " Northern Shield quietly builds the infrastructure everyone else will"
        " need.\n\n"
        "A new digital reserve currency \u2014 the Meridian \u2014 threatens to unseat"
        " the Atlantic Dollar, fusion energy is tantalisingly close to commercial"
        " viability, and AI systems have crossed into autonomous decision-making"
        " territory. Meanwhile, the Caspian Basin is a frozen conflict zone, water"
        " scarcity is redrawing maps in North Africa, and a generation raised on"
        " algorithmic feeds is demanding something real. The morning papers have"
        " never mattered more."
    ),
    geopolitics=GeopoliticsState(
        nations=[
            Nation(
                name="Atlantic Republic",
                government_type="Federal presidential republic",
                leader="President Elena Marsh",
                stability=72,
                description=(
                    "The successor state to American hegemony. Still the largest"
                    " economy and military, but its soft power is fraying."
                    " Domestically polarised between techno-optimists and"
                    " neo-protectionists."
                ),
            ),
            Nation(
                name="European Commonwealth",
                government_type="Parliamentary confederation",
                leader="Chancellor Theodor Brandt",
                stability=68,
                description=(
                    "A tighter political union forged from the EU after the"
                    " Fracture Accords. Strong on regulation, green energy, and"
                    " diplomacy. Weak on military autonomy and demographic decline."
                ),
            ),
            Nation(
                name="Eastern Compact",
                government_type="One-party technocratic state",
                leader="Chairman Wei Longji",
                stability=78,
                description=(
                    "The merged strategic interests of continental East Asia and"
                    " northern Eurasia. Controls critical mineral supply chains and"
                    " leads in manufacturing automation. Internally cohesive but"
                    " diplomatically isolated."
                ),
            ),
            Nation(
                name="Pacific Rim Alliance",
                government_type="Multilateral defence and trade pact",
                leader="Rotating presidency (current: PM Haruki Tanabe)",
                stability=65,
                description=(
                    "A loose coalition of island and coastal nations bound by trade"
                    " routes and maritime security. Pragmatic, commercially driven,"
                    " and officially non-aligned but quietly Atlantic-leaning."
                ),
            ),
            Nation(
                name="Southern Union",
                government_type="Federal council of member states",
                leader="Council Chair Amara Diallo",
                stability=58,
                description=(
                    "The Global South's collective bargaining bloc. Rich in natural"
                    " resources and youth demographics but burdened by"
                    " infrastructure deficits and internal disagreements. Champions"
                    " the Meridian digital currency."
                ),
            ),
            Nation(
                name="Northern Shield",
                government_type="Nordic-model social democracy",
                leader="Prime Minister Astrid Holm",
                stability=85,
                description=(
                    "A compact alliance of Nordic nations and Canada. Small"
                    " population, outsized influence in green tech, Arctic"
                    " governance, and AI ethics. Quietly building the"
                    " infrastructure other blocs will depend on."
                ),
            ),
        ],
        alliances=[
            Alliance(
                name="Atlantic Shield",
                members=[
                    "Atlantic Republic",
                    "European Commonwealth",
                    "Northern Shield",
                ],
                purpose=(
                    "Collective defence and intelligence sharing. The successor to"
                    " NATO, reconfigured around hybrid warfare and cyber defence."
                ),
            ),
            Alliance(
                name="Eastern Compact Pact",
                members=["Eastern Compact"],
                purpose=(
                    "Military and economic mutual defence among Compact member"
                    " states. Closed to outside observers."
                ),
            ),
            Alliance(
                name="Non-Aligned Movement",
                members=["Southern Union", "Pacific Rim Alliance"],
                purpose=(
                    "Trade cooperation and diplomatic coordination without military"
                    " entanglement. Advocates for Meridian adoption and reformed"
                    " international institutions."
                ),
            ),
        ],
        conflicts=[
            Conflict(
                name="Caspian Basin Standoff",
                parties=["Eastern Compact", "European Commonwealth"],
                status="frozen",
                description=(
                    "A territorial and pipeline dispute over the energy-rich"
                    " Caspian corridor. Both sides maintain forward-deployed"
                    " forces. Ceasefire holds but no peace talks are scheduled."
                ),
            ),
            Conflict(
                name="Strait of Malacca Proxy Tensions",
                parties=[
                    "Atlantic Republic",
                    "Eastern Compact",
                    "Pacific Rim Alliance",
                ],
                status="active",
                description=(
                    "Competing naval patrols and commercial shipping disputes in"
                    " the world's busiest trade chokepoint. No shots fired, but"
                    " electronic warfare incidents are escalating."
                ),
            ),
        ],
    ),
    economics=EconomicsState(
        currencies=[
            Currency(
                name="Atlantic Dollar",
                issuing_entity="Atlantic Republic Federal Reserve",
                strength=82,
                description=(
                    "Still the dominant reserve currency but losing ground."
                    " Underpinned by military reach and legacy trade agreements."
                ),
            ),
            Currency(
                name="Commonwealth Euro",
                issuing_entity="European Commonwealth Central Bank",
                strength=74,
                description=(
                    "Stable and trusted within the Commonwealth but lacks global"
                    " reach. Strong green bond market."
                ),
            ),
            Currency(
                name="Eastern Yuan",
                issuing_entity="Eastern Compact Monetary Authority",
                strength=70,
                description=(
                    "Growing in bilateral trade settlements. Capital controls"
                    " limit its reserve currency ambitions."
                ),
            ),
            Currency(
                name="Meridian",
                issuing_entity="Meridian Foundation (Southern Union-backed)",
                strength=45,
                description=(
                    "A blockchain-based digital reserve currency designed to"
                    " bypass Atlantic Dollar hegemony. Volatile but gaining"
                    " adoption in the Southern Union and parts of the Pacific Rim."
                ),
            ),
        ],
        trading_blocs=[
            TradingBloc(
                name="Atlantic-Commonwealth Free Trade Zone",
                members=[
                    "Atlantic Republic",
                    "European Commonwealth",
                    "Northern Shield",
                ],
                focus=(
                    "Zero-tariff goods, harmonised tech standards, mutual"
                    " recognition of AI safety certifications."
                ),
            ),
            TradingBloc(
                name="Southern Corridor",
                members=["Southern Union", "Pacific Rim Alliance"],
                focus=(
                    "Raw materials for manufactured goods. Meridian-denominated"
                    " contracts. Infrastructure-for-resources swaps with the"
                    " Eastern Compact."
                ),
            ),
        ],
        scarcities=[
            Scarcity(
                resource="Rare earth elements",
                severity="critical",
                affected_regions=[
                    "Atlantic Republic",
                    "European Commonwealth",
                    "Pacific Rim Alliance",
                ],
                description=(
                    "The Eastern Compact controls 78% of global rare earth"
                    " processing. Export quotas are weaponised during diplomatic"
                    " disputes, choking electronics and defence supply chains."
                ),
            ),
            Scarcity(
                resource="Fresh water",
                severity="moderate",
                affected_regions=["Southern Union", "Pacific Rim Alliance"],
                description=(
                    "Aquifer depletion and shifting rainfall patterns are creating"
                    " water stress across equatorial regions. Desalination capacity"
                    " is growing but energy-intensive."
                ),
            ),
        ],
        global_gdp_trend=(
            "Global GDP growth is 2.1%, down from 3.4% pre-Fracture. The Atlantic"
            " Republic and Eastern Compact are near-stagnant; the Southern Union"
            " is the fastest-growing bloc at 4.8% but from a low base."
        ),
    ),
    technology=TechnologyState(
        ai=TechDomain(
            name="Artificial Intelligence",
            maturity_level="growth",
            key_players=[
                "Atlantic Republic (frontier labs)",
                "Eastern Compact (state-directed AI)",
                "Northern Shield (AI safety and ethics frameworks)",
            ],
            description=(
                "AI systems have crossed into autonomous decision-making in"
                " logistics, medical diagnostics, and financial trading. Frontier"
                " models are capable of multi-step reasoning but alignment remains"
                " unsolved. The Atlantic Republic leads in model capability; the"
                " Northern Shield leads in governance."
            ),
        ),
        energy=TechDomain(
            name="Energy",
            maturity_level="emerging",
            key_players=[
                "Northern Shield (fusion research)",
                "European Commonwealth (green grid)",
                "Eastern Compact (nuclear expansion)",
            ],
            description=(
                "Fusion energy achieved net-positive output in Northern Shield"
                " labs but commercial deployment is 5-8 years away. Solar and wind"
                " dominate new capacity. The Eastern Compact is building"
                " fourth-generation nuclear at scale."
            ),
        ),
        biotech=TechDomain(
            name="Biotechnology",
            maturity_level="emerging",
            key_players=[
                "European Commonwealth (gene therapy regulation)",
                "Atlantic Republic (pharma industry)",
                "Southern Union (tropical disease research)",
            ],
            description=(
                "CRISPR-derived gene therapies are entering clinical use for"
                " hereditary diseases. Synthetic biology startups are engineering"
                " drought-resistant crops. Bioethics frameworks lag behind"
                " capability."
            ),
        ),
        other=[],
    ),
    culture=CultureState(
        dominant_narratives=[
            (
                'The "Managed Decline" thesis \u2014 the idea that the old powers'
                " are gracefully (or not) ceding ground to new ones, and ordinary"
                " people must adapt."
            ),
            (
                'The "Digital Sovereignty" movement \u2014 citizens demanding'
                " control over their data, algorithmic feeds, and digital identity"
                " from both corporations and governments."
            ),
            (
                'The "Year Zero Reset" \u2014 a pervasive cultural sense that the'
                " old rules no longer apply and everything is up for"
                " renegotiation."
            ),
        ],
        movements=[
            CulturalMovement(
                name="Analog Revival",
                reach="global",
                description=(
                    "A counter-movement rejecting algorithmic curation. Print"
                    " newspapers, vinyl, handwritten letters, and in-person"
                    " gatherings are status symbols among the young."
                ),
            ),
            CulturalMovement(
                name="Meridian Populism",
                reach="regional",
                description=(
                    "A grassroots movement in the Southern Union demanding faster"
                    " adoption of the Meridian currency and debt cancellation for"
                    " post-colonial economies."
                ),
            ),
        ],
        media_landscape=(
            "Legacy media has splintered into ideological silos. Algorithmic feeds"
            " dominate attention but trust is at historic lows. A new generation of"
            " subscription-funded, AI-augmented newsrooms is emerging \u2014 small,"
            " opinionated, and unapologetically biased."
        ),
    ),
    military=MilitaryState(
        forces=[
            MilitaryForce(
                entity="Atlantic Republic",
                conventional_strength=95,
                nuclear_capable=True,
                special_capabilities=[
                    "Global force projection",
                    "Cyber Command",
                    "Space-based ISR",
                    "Autonomous drone swarms",
                ],
            ),
            MilitaryForce(
                entity="Eastern Compact",
                conventional_strength=88,
                nuclear_capable=True,
                special_capabilities=[
                    "Anti-access/area denial (A2/AD)",
                    "Hypersonic missiles",
                    "Cyber warfare divisions",
                    "Satellite disruption capability",
                ],
            ),
            MilitaryForce(
                entity="European Commonwealth",
                conventional_strength=65,
                nuclear_capable=True,
                special_capabilities=[
                    "Combined arms expeditionary force",
                    "Cyber defence consortium",
                    "Maritime patrol",
                ],
            ),
            MilitaryForce(
                entity="Northern Shield",
                conventional_strength=40,
                nuclear_capable=False,
                special_capabilities=[
                    "Arctic operations",
                    "Cyber security excellence",
                    "Submarine fleet",
                    "AI-integrated command systems",
                ],
            ),
        ],
        arms_races=[
            (
                "Autonomous weapons systems \u2014 the Atlantic Republic and"
                " Eastern Compact are racing to deploy AI-directed combat"
                " platforms while the Northern Shield pushes for a global treaty"
                " ban."
            ),
        ],
        doctrine_shifts=[
            (
                "Shift from mass mobilisation to precision autonomous operations."
                " Human-in-the-loop requirements are being quietly relaxed in both"
                " the Atlantic Republic and Eastern Compact."
            ),
        ],
    ),
    environment=EnvironmentState(
        global_temperature_anomaly=1.8,
        crises=[
            EnvironmentalCrisis(
                name="North African Water Crisis",
                severity="severe",
                affected_regions=["Southern Union"],
                description=(
                    "Accelerating desertification and aquifer collapse across the"
                    " Sahel and Maghreb. Triggering mass displacement toward the"
                    " European Commonwealth and coastal Southern Union cities."
                ),
            ),
            EnvironmentalCrisis(
                name="Pacific Coral Collapse",
                severity="catastrophic",
                affected_regions=["Pacific Rim Alliance"],
                description=(
                    "Over 60% of Pacific reef systems have bleached beyond"
                    " recovery. Fisheries collapse threatens food security for 200"
                    " million people."
                ),
            ),
        ],
        mitigation_efforts=[
            (
                "The European Commonwealth Green Grid \u2014 a continent-spanning"
                " renewable energy network aiming for 90% clean electricity by"
                " Year Five."
            ),
            (
                "The Northern Shield Fusion Initiative \u2014 public-private"
                " partnership targeting commercial fusion by Year Eight."
            ),
        ],
    ),
    history=[
        HistoricalEvent(
            date="Year Zero, Day 1",
            headline="The Fracture Accords signed",
            description=(
                "After two years of cascading diplomatic failures, the six major"
                " blocs formally acknowledged the end of the multilateral order"
                " and signed the Fracture Accords \u2014 a mutual non-aggression"
                " framework replacing the defunct UN Security Council."
            ),
            impact=(
                "Established the current six-bloc world order. Created the"
                " framework for bilateral dispute resolution but no collective"
                " security mechanism."
            ),
            sectors=["geopolitics", "military-and-defence", "law-and-justice"],
        ),
        HistoricalEvent(
            date="Year Zero, Day 1",
            headline="Meridian currency launched",
            description=(
                "The Southern Union launched the Meridian digital currency on the"
                " same day as the Fracture Accords, positioning it as an"
                " alternative to Atlantic Dollar hegemony."
            ),
            impact=(
                "Introduced a viable digital reserve currency. The Atlantic"
                ' Republic condemned it as "financial destabilisation."'
            ),
            sectors=[
                "finance-and-markets",
                "cryptocurrency",
                "trade-and-commerce",
            ],
        ),
        HistoricalEvent(
            date="Year Zero, Day 1",
            headline="Caspian Ceasefire declared",
            description=(
                "The European Commonwealth and Eastern Compact agreed to a"
                " ceasefire along the Caspian corridor after a six-month border"
                " escalation. No peace terms \u2014 just a freeze."
            ),
            impact=(
                "Prevented open war but left a permanent flashpoint. Energy"
                " transit through the corridor remains disrupted."
            ),
            sectors=["geopolitics", "energy", "military-and-defence"],
        ),
        HistoricalEvent(
            date="Year Zero, Day 1",
            headline="Northern Shield Fusion Breakthrough",
            description=(
                "The Northern Shield announced sustained net-positive fusion"
                " output at the Troms\u00f8 Energy Research Centre \u2014 a scientific"
                " milestone, though commercial deployment remains years away."
            ),
            impact=(
                "Shifted global energy investment calculus. Fusion futures"
                " contracts appeared on commodity exchanges within hours."
            ),
            sectors=[
                "energy",
                "science-and-research",
                "finance-and-markets",
                "technology-and-innovation",
            ],
        ),
        HistoricalEvent(
            date="Year Zero, Day 1",
            headline="Atlantic AI Autonomy Directive",
            description=(
                "President Marsh signed the AI Autonomy Directive, permitting AI"
                " systems to make binding decisions in financial regulation,"
                " medical triage, and military logistics without human approval."
            ),
            impact=(
                'Crossed a governance Rubicon. The Northern Shield called it'
                ' "reckless." The Eastern Compact quietly expanded its own'
                " autonomous systems programme."
            ),
            sectors=[
                "artificial-intelligence",
                "technology-and-innovation",
                "domestic-politics",
            ],
        ),
    ],
)
