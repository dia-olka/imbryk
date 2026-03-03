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
    epoch="March 2026 \u2014 The World as It Is",
    synopsis=(
        "The world enters 2026 under compounding pressures. The United States,"
        " under Donald Trump\u2019s second term, has imposed a 10% global import"
        " tariff and withdrawn from the WHO, reshaping the multilateral order."
        " A fragile US-China tariff truce holds at 30%/10% baseline rates, but"
        " tensions over Taiwan remain elevated. Russia and Ukraine are locked in"
        " a grinding stalemate across the Donbas front, with no peace talks in"
        " sight. The most acute crisis erupted on 28 February 2026: US and"
        " Israeli strikes killed Iranian Supreme Leader Ali Khamenei; Iran is"
        " retaliating across the Middle East, and the region is on the edge of"
        " full-scale war.\n\n"
        "AI has crossed into the agentic era \u2014 autonomous systems are acting"
        " on behalf of users and institutions without step-by-step human"
        " instruction. DeepSeek R1 narrowed the US-China AI capability gap"
        " dramatically. Renewable energy met 109% of new global electricity"
        " demand in 2025 \u2014 the first year solar and wind outpaced all new"
        " demand. Global temperature anomaly reached 1.47\u00b0C above"
        " pre-industrial levels in 2025. The morning papers have never"
        " mattered more."
    ),
    geopolitics=GeopoliticsState(
        nations=[
            Nation(
                name="United States",
                government_type="Federal presidential republic",
                leader="Donald Trump",
                stability=62,
                description=(
                    "The world\u2019s largest economy and military superpower, now in"
                    " Trump\u2019s second term. Pursuing aggressive tariff policy,"
                    " energy dominance, and strategic confrontation with China."
                    " Domestically divided but institutionally functional. Engaged"
                    " militarily in the Middle East following strikes on Iran."
                ),
            ),
            Nation(
                name="China",
                government_type="One-party state",
                leader="Xi Jinping",
                stability=76,
                description=(
                    "The world\u2019s second-largest economy and primary US strategic"
                    " rival. Pursuing technological self-sufficiency following US"
                    " chip export controls. DeepSeek R1 closed the AI gap with US"
                    " frontier labs. Military pressure on Taiwan is intensifying."
                    " Navigating a fragile trade truce with Washington."
                ),
            ),
            Nation(
                name="Russia",
                government_type="Presidential federation",
                leader="Vladimir Putin",
                stability=58,
                description=(
                    "Engaged in a costly war of attrition in Ukraine. Economy under"
                    " severe Western sanctions but propped up by energy exports to"
                    " China and India. Military capacity degraded but intact."
                    " Increasingly dependent on North Korean ammunition and Iranian"
                    " drones."
                ),
            ),
            Nation(
                name="United Kingdom",
                government_type="Parliamentary constitutional monarchy",
                leader="Keir Starmer",
                stability=72,
                description=(
                    "Post-Brexit Britain under a Labour government. Pursuing closer"
                    " EU ties without rejoining the single market. Committed to NATO"
                    " and Ukrainian support. Facing domestic economic pressures and"
                    " a resurgent Reform Party."
                ),
            ),
            Nation(
                name="Germany",
                government_type="Federal parliamentary republic",
                leader="Friedrich Merz",
                stability=70,
                description=(
                    "Europe\u2019s largest economy, growing at a sluggish 0.9%. New"
                    " CDU-led coalition under Friedrich Merz following the February"
                    " 2025 snap election. Facing deindustrialisation pressures,"
                    " energy costs, and the rise of the AfD. Central to European"
                    " defence rearming."
                ),
            ),
            Nation(
                name="France",
                government_type="Semi-presidential republic",
                leader="Emmanuel Macron",
                stability=65,
                description=(
                    "Navigating political fragmentation after 2024 snap elections"
                    " produced a hung parliament. Macron serves as president with"
                    " reduced authority. France is pushing for greater European"
                    " strategic autonomy and remains a nuclear power."
                ),
            ),
            Nation(
                name="Japan",
                government_type="Parliamentary constitutional monarchy",
                leader="Sanae Takaichi",
                stability=74,
                description=(
                    "Japan\u2019s LDP returned a majority, with Sanae Takaichi"
                    " confirmed as Prime Minister \u2014 Japan\u2019s first female PM."
                    " Increasing defence spending toward 2% of GDP. Deeply engaged"
                    " in QUAD and AUKUS-adjacent security arrangements. Watching"
                    " Taiwan closely."
                ),
            ),
            Nation(
                name="India",
                government_type="Federal parliamentary republic",
                leader="Narendra Modi",
                stability=74,
                description=(
                    "World\u2019s most populous nation and fastest-growing major"
                    " economy. Modi\u2019s BJP government balancing ties with the"
                    " West, Russia, and China. A key QUAD partner. Emerging as a"
                    " global manufacturing hub as companies diversify away from"
                    " China."
                ),
            ),
            Nation(
                name="Brazil",
                government_type="Federal presidential republic",
                leader="Luiz In\u00e1cio Lula da Silva",
                stability=60,
                description=(
                    "Latin America\u2019s largest economy, under Lula\u2019s third"
                    " term. Navigating fiscal pressures and climate leadership"
                    " ambitions simultaneously. Active in BRICS+ and pushing for"
                    " Global South interests in multilateral forums."
                ),
            ),
            Nation(
                name="Ukraine",
                government_type="Presidential republic (wartime)",
                leader="Volodymyr Zelenskyy",
                stability=44,
                description=(
                    "In its fourth year of full-scale war with Russia. Stalemate"
                    " persists on the Donbas front. Sustained by Western military"
                    " and financial aid, though US support has become less reliable"
                    " under Trump. Martial law in effect; civilian resilience"
                    " remains high."
                ),
            ),
            Nation(
                name="Israel",
                government_type="Parliamentary democracy",
                leader="Benjamin Netanyahu",
                stability=52,
                description=(
                    "Engaged in simultaneous conflicts in Gaza and Lebanon, and now"
                    " directly at war with Iran following the February 2026 strikes"
                    " on Tehran. Domestic coalition is fragile. October 2026"
                    " elections loom. International isolation deepening despite US"
                    " backing."
                ),
            ),
            Nation(
                name="Iran",
                government_type="Theocratic republic (in succession crisis)",
                leader="Interim Leadership Council",
                stability=28,
                description=(
                    "In acute crisis following the assassination of Supreme Leader"
                    " Ali Khamenei on 28 February 2026 in a US-Israeli strike. An"
                    " interim council is directing the state. Revolutionary Guards"
                    " are conducting retaliatory strikes across the region. The"
                    " succession struggle threatens regime cohesion."
                ),
            ),
            Nation(
                name="Turkey",
                government_type="Presidential republic",
                leader="Recep Tayyip Erdo\u011fan",
                stability=60,
                description=(
                    "Pivotal NATO member playing both sides \u2014 maintaining ties"
                    " with Russia while hosting Ukrainian peace talks. Erdo\u011fan"
                    " leverages Turkey\u2019s geographic position for economic and"
                    " political gains. Inflation remains a domestic pressure."
                ),
            ),
            Nation(
                name="Saudi Arabia",
                government_type="Absolute monarchy",
                leader="Mohammed bin Salman (de facto)",
                stability=68,
                description=(
                    "Crown Prince MBS is the effective ruler. Pursuing Vision 2030"
                    " economic diversification. Navigating the Iran crisis carefully"
                    " \u2014 member of BRICS+ but aligned with the US on security."
                    " Major oil producer facing long-term demand uncertainty as"
                    " clean energy accelerates."
                ),
            ),
            Nation(
                name="South Korea",
                government_type="Presidential republic",
                leader="Lee Jae-Myung",
                stability=56,
                description=(
                    "Emerging from a constitutional crisis: President Yoon Suk-yeol"
                    " was convicted and sentenced to life imprisonment on 19"
                    " February 2026. Opposition leader Lee Jae-Myung won the"
                    " subsequent presidential election. North Korean provocations"
                    " and close US alliance ties define foreign policy."
                ),
            ),
        ],
        alliances=[
            Alliance(
                name="NATO",
                members=[
                    "United States", "United Kingdom", "France", "Germany",
                    "Canada", "Italy", "Poland", "Turkey", "Spain",
                    "Netherlands", "Belgium", "Norway", "Denmark", "Sweden",
                    "Finland", "Greece", "Portugal", "Czech Republic",
                    "Hungary", "Romania", "Bulgaria", "Slovakia", "Slovenia",
                    "Estonia", "Latvia", "Lithuania", "Albania", "Croatia",
                    "Montenegro", "North Macedonia", "Luxembourg", "Iceland",
                ],
                purpose=(
                    "Collective defence pact (Article 5). 32 member states."
                    " Largest peacetime military alliance in history. Currently"
                    " supporting Ukraine and monitoring Middle East escalation."
                ),
            ),
            Alliance(
                name="G7",
                members=[
                    "United States", "United Kingdom", "France", "Germany",
                    "Italy", "Japan", "Canada",
                ],
                purpose=(
                    "Forum of the world\u2019s seven largest advanced economies plus"
                    " the EU. Coordinates sanctions on Russia, AI governance"
                    " standards, clean energy transition, and economic policy"
                    " among Western democracies."
                ),
            ),
            Alliance(
                name="BRICS+",
                members=[
                    "Brazil", "Russia", "India", "China", "South Africa",
                    "Egypt", "Ethiopia", "Iran", "UAE", "Saudi Arabia",
                ],
                purpose=(
                    "Expanded bloc of major emerging and developing economies."
                    " Promotes a multipolar world order, dollar-alternative"
                    " payment systems, and South-South cooperation. Tensions"
                    " between members (India-China, Saudi-Iran) limit cohesion."
                ),
            ),
            Alliance(
                name="QUAD",
                members=["United States", "Australia", "India", "Japan"],
                purpose=(
                    "Indo-Pacific security dialogue. Focused on countering Chinese"
                    " military expansion, securing supply chains, and maintaining"
                    " freedom of navigation in the South China Sea and Taiwan"
                    " Strait."
                ),
            ),
            Alliance(
                name="AUKUS",
                members=["Australia", "United Kingdom", "United States"],
                purpose=(
                    "Defence technology partnership providing Australia with"
                    " nuclear-powered submarines and advanced military capabilities."
                    " Designed to strengthen Indo-Pacific deterrence against"
                    " Chinese power projection."
                ),
            ),
            Alliance(
                name="European Union",
                members=[
                    "France", "Germany", "Italy", "Spain", "Poland",
                    "Netherlands", "Belgium", "Sweden", "Austria", "Denmark",
                    "Finland", "Portugal", "Greece", "Czech Republic",
                    "Romania", "Hungary", "Bulgaria", "Slovakia", "Croatia",
                    "Slovenia", "Estonia", "Latvia", "Lithuania", "Luxembourg",
                    "Malta", "Cyprus", "Ireland",
                ],
                purpose=(
                    "Political and economic union of 27 member states. Single"
                    " market, common currency (euro \u2014 now used by 21 members"
                    " including Bulgaria from January 2026). Pursuing strategic"
                    " autonomy in defence and AI regulation."
                ),
            ),
        ],
        conflicts=[
            Conflict(
                name="Russia-Ukraine War",
                parties=["Russia", "Ukraine"],
                status="active",
                description=(
                    "Now in its fourth year following Russia\u2019s February 2022"
                    " full-scale invasion. The front line has stabilised across the"
                    " Donbas, with neither side able to achieve a breakthrough."
                    " Russia has adapted to Western sanctions through oil exports to"
                    " China and India. Ukraine remains dependent on Western military"
                    " aid."
                ),
            ),
            Conflict(
                name="US-Iran-Israel Military Escalation",
                parties=["United States", "Israel", "Iran"],
                status="active",
                description=(
                    "The most acute current flashpoint. US and Israeli strikes on"
                    " 28 February 2026 killed Supreme Leader Ali Khamenei. Iran\u2019s"
                    " Interim Leadership Council is directing retaliatory strikes on"
                    " US bases in the Gulf region and on Israeli territory. The"
                    " conflict risks drawing in Hezbollah, Houthis, and regional"
                    " proxies."
                ),
            ),
            Conflict(
                name="Israel-Gaza War",
                parties=["Israel", "Hamas"],
                status="active",
                description=(
                    "Ongoing since October 2023. Gaza faces a severe humanitarian"
                    " crisis. Ceasefire negotiations have repeatedly collapsed."
                    " International pressure on Israel is intensifying. October"
                    " 2026 Israeli elections are adding domestic political pressure"
                    " on Netanyahu\u2019s coalition."
                ),
            ),
            Conflict(
                name="Sudan Civil War",
                parties=["Sudanese Armed Forces (SAF)", "Rapid Support Forces (RSF)"],
                status="active",
                description=(
                    "Conflict between the SAF and the paramilitary RSF has caused"
                    " one of the world\u2019s worst humanitarian disasters. Millions"
                    " displaced, widespread famine conditions. Regional powers"
                    " (Egypt, UAE, Ethiopia) back different sides."
                ),
            ),
            Conflict(
                name="Taiwan Strait Tensions",
                parties=["China", "Taiwan", "United States"],
                status="active",
                description=(
                    "China has increased military incursions into Taiwan\u2019s air"
                    " defence identification zone to near-daily frequency. QUAD and"
                    " AUKUS partners have intensified naval presence. No kinetic"
                    " conflict, but crisis risk is at its highest since 1996. The"
                    " Middle East war is diverting US attention and resources."
                ),
            ),
        ],
    ),
    economics=EconomicsState(
        currencies=[
            Currency(
                name="US Dollar (USD)",
                issuing_entity="US Federal Reserve",
                strength=86,
                description=(
                    "Dominant global reserve currency, comprising ~58% of central"
                    " bank reserves. Strengthened by Trump tariff policy and"
                    " safe-haven demand during Middle East escalation. BRICS+"
                    " nations are actively developing alternatives, but the"
                    " dollar\u2019s structural dominance persists."
                ),
            ),
            Currency(
                name="Euro (EUR)",
                issuing_entity="European Central Bank",
                strength=72,
                description=(
                    "Second most-held reserve currency. Used by 21 EU member states"
                    " including Bulgaria (joined Jan 2026). Eurozone growth is"
                    " sluggish: Germany at 0.9%, Italy at 0.4%. The ECB is"
                    " navigating between stimulating growth and controlling"
                    " residual inflation."
                ),
            ),
            Currency(
                name="Chinese Yuan (CNY)",
                issuing_entity="People\u2019s Bank of China",
                strength=65,
                description=(
                    "Growing in bilateral trade settlements, especially with Russia,"
                    " Iran, and BRICS+ members. Capital controls and limited"
                    " convertibility constrain its reserve currency role. China is"
                    " promoting a BRICS+ payment system to bypass dollar dependency."
                ),
            ),
            Currency(
                name="British Pound (GBP)",
                issuing_entity="Bank of England",
                strength=68,
                description=(
                    "A major reserve currency, though diminished post-Brexit. UK"
                    " economy stabilising under the Labour government but growth"
                    " remains modest. Sterling benefits from London\u2019s role as a"
                    " global financial centre."
                ),
            ),
            Currency(
                name="Japanese Yen (JPY)",
                issuing_entity="Bank of Japan",
                strength=60,
                description=(
                    "The Bank of Japan has cautiously raised interest rates as it"
                    " exits decades of ultra-loose monetary policy. The yen had"
                    " weakened sharply in 2024-25; modest recovery underway. Japan"
                    " remains a major creditor nation."
                ),
            ),
            Currency(
                name="Bitcoin (BTC)",
                issuing_entity="Decentralised (Bitcoin network)",
                strength=42,
                description=(
                    "Bitcoin has established itself as a digital asset class. US"
                    " spot Bitcoin ETFs now hold significant institutional assets."
                    " Trump administration is crypto-friendly. Volatility remains"
                    " high; not yet functioning as a stable reserve, but growing as"
                    " a hedge against dollar risk in sanctioned economies."
                ),
            ),
        ],
        trading_blocs=[
            TradingBloc(
                name="US Tariff Regime (2025-)",
                members=["United States"],
                focus=(
                    "Trump\u2019s 10% baseline global import tariff, in effect from"
                    " early 2025. Sector-specific tariffs on China (30%+), steel,"
                    " aluminium, and EVs. Designed to re-shore manufacturing and"
                    " leverage trade as a diplomatic tool. Trading partners are"
                    " seeking bilateral deals to reduce exposure."
                ),
            ),
            TradingBloc(
                name="US-China Trade Truce",
                members=["United States", "China"],
                focus=(
                    "Fragile baseline truce: US maintains 30% tariffs on Chinese"
                    " goods; China maintains 10% on US goods. Both sides have agreed"
                    " not to escalate for 90 days (as of Jan 2026). Technology and"
                    " semiconductor restrictions remain in full force outside the"
                    " truce."
                ),
            ),
            TradingBloc(
                name="European Single Market",
                members=["European Union member states"],
                focus=(
                    "Tariff-free trade in goods and services among 27 EU members."
                    " The EU is negotiating updated trade frameworks with the US and"
                    " pursuing strategic autonomy in semiconductors and AI. EU"
                    " Carbon Border Adjustment Mechanism (CBAM) now operational."
                ),
            ),
        ],
        scarcities=[
            Scarcity(
                resource="Semiconductors (advanced chips)",
                severity="critical",
                affected_regions=[
                    "United States", "European Union", "Japan", "South Korea",
                ],
                description=(
                    "US export controls on advanced AI chips and semiconductor"
                    " equipment to China have intensified a global tech supply chain"
                    " bifurcation. TSMC\u2019s Arizona fabs are ramping but at higher"
                    " cost. China is investing heavily in domestic chip production."
                ),
            ),
            Scarcity(
                resource="Critical minerals (lithium, cobalt, rare earths)",
                severity="moderate",
                affected_regions=[
                    "United States", "European Union", "Japan",
                ],
                description=(
                    "Clean energy transition is driving demand for critical minerals."
                    " China dominates rare earth processing (~60% global share). The"
                    " IRA and EU Critical Raw Materials Act are funding diversified"
                    " supply chains, but results are years away."
                ),
            ),
            Scarcity(
                resource="Fresh water (MENA and sub-Saharan Africa)",
                severity="moderate",
                affected_regions=["Saudi Arabia", "Iran", "Sudan"],
                description=(
                    "Aquifer depletion and climate-driven drought are creating"
                    " severe water stress across the Middle East and North Africa."
                    " The ongoing wars in Sudan and the Israel-Gaza-Iran theatre are"
                    " worsening water infrastructure. Desalination capacity is"
                    " expanding but is energy-intensive."
                ),
            ),
        ],
        global_gdp_trend=(
            "Global GDP growth is 3.3% (IMF, January 2026 projection). India leads"
            " major economies at ~6.5%. The US grows at ~2.7% amid tariff"
            " uncertainty. The eurozone is sluggish at ~1.2%. Russia is in a war"
            " economy, growing nominally via defence spending but facing long-term"
            " structural decline. China is targeting ~4.5% amid property sector"
            " weakness and US tech restrictions."
        ),
    ),
    technology=TechnologyState(
        ai=TechDomain(
            name="Artificial Intelligence",
            maturity_level="growth",
            key_players=[
                "United States (OpenAI, Anthropic, Google DeepMind, Meta AI)",
                "China (DeepSeek, Baidu, Alibaba)",
                "European Union (AI Act regulatory framework)",
            ],
            description=(
                "AI has shifted from powerful LLM tools to autonomous agents"
                " \u2014 systems that plan, act, and iterate without step-by-step"
                " human instruction. DeepSeek R1 (released Jan 2025) demonstrated"
                " that frontier-level reasoning could be achieved at a fraction of"
                " US training cost, closing the perceived US-China capability gap."
                " IBM announced a quantum computing milestone. Trump signed an"
                " executive order limiting state AI laws to preserve federal"
                " pre-emption. The EU AI Act is entering enforcement phase."
            ),
        ),
        energy=TechDomain(
            name="Energy",
            maturity_level="growth",
            key_players=[
                "China (world\u2019s largest solar and wind installer)",
                "United States (LNG exports, shale, growing renewables)",
                "European Union (green energy transition, REPowerEU)",
            ],
            description=(
                "Solar and wind met 109% of new global electricity demand in 2025"
                " \u2014 the first time renewables have exceeded all incremental"
                " demand growth. A record 600 GW of solar was added globally in"
                " 2025. The US is pursuing both fossil fuel expansion and clean"
                " energy deployment, while the EU is accelerating decarbonisation."
                " Battery storage costs continue to fall."
            ),
        ),
        biotech=TechDomain(
            name="Biotechnology",
            maturity_level="emerging",
            key_players=[
                "United States (pharma industry, CRISPR pioneers)",
                "European Union (EMA regulatory framework)",
                "China (genomics, synthetic biology)",
            ],
            description=(
                "The first bespoke CRISPR gene-editing treatment was administered"
                " to baby KJ Muldoon, marking a milestone in personalised medicine."
                " Over 150 active gene-editing clinical trials are underway"
                " globally. GLP-1 weight-loss and diabetes drugs (Ozempic, Wegovy)"
                " are reshaping healthcare economics. Bioethics frameworks are"
                " struggling to keep pace with capability."
            ),
        ),
        other=[],
    ),
    culture=CultureState(
        dominant_narratives=[
            (
                "\u201cAmerica First\u201d is reshaping global multilateralism"
                " \u2014 tariffs, WHO withdrawal, and reduced US engagement in"
                " international institutions are forcing other nations to build"
                " resilience without Washington."
            ),
            (
                "The \u201cagentic AI\u201d moment \u2014 the shift from AI as a"
                " tool to AI as an autonomous actor is creating both opportunity"
                " and anxiety across every sector of the economy and society."
            ),
            (
                "Democratic backsliding anxiety \u2014 from Hungary to South Korea"
                " to the United States, the resilience of democratic institutions"
                " is being tested and debated globally."
            ),
        ],
        movements=[
            CulturalMovement(
                name="Anti-AI Labour Movement",
                reach="global",
                description=(
                    "Workers in creative industries, law, finance, and journalism"
                    " are organising against AI displacement. Hollywood writers\u2019"
                    " precedents are being cited globally. Demands range from AI use"
                    " disclosure to per-use royalty funds for displaced workers."
                ),
            ),
            CulturalMovement(
                name="Pro-Palestine Solidarity Movement",
                reach="global",
                description=(
                    "University campuses and city centres across the West have seen"
                    " sustained demonstrations demanding ceasefires, arms embargoes"
                    " on Israel, and sanctions. The movement has intensified"
                    " following the Iran strikes of February 2026."
                ),
            ),
        ],
        media_landscape=(
            "Legacy media is under existential financial pressure from AI-generated"
            " content and social media. Trust in mainstream outlets is at historic"
            " lows across Western democracies. X (formerly Twitter) under Elon Musk"
            " has become a primary news source for millions while also being a"
            " vector for state-sponsored disinformation. AI-generated deepfakes are"
            " increasingly indistinguishable from authentic video. A new generation"
            " of subscription-funded, AI-augmented newsrooms is emerging \u2014"
            " small, opinionated, and audience-funded."
        ),
    ),
    military=MilitaryState(
        forces=[
            MilitaryForce(
                entity="United States",
                conventional_strength=97,
                nuclear_capable=True,
                special_capabilities=[
                    "Global force projection (11 carrier strike groups)",
                    "Cyber Command (USCYBERCOM)",
                    "Space-based ISR and GPS dominance",
                    "AI-directed autonomous drone swarms",
                    "Special Operations Forces globally deployed",
                ],
            ),
            MilitaryForce(
                entity="China",
                conventional_strength=85,
                nuclear_capable=True,
                special_capabilities=[
                    "Anti-access/area denial (A2/AD) \u2014 South China Sea and Taiwan Strait",
                    "Hypersonic glide vehicle (DF-17, DF-41)",
                    "Cyber warfare (APT groups)",
                    "Satellite and anti-satellite capabilities",
                    "World\u2019s largest navy by hull count",
                ],
            ),
            MilitaryForce(
                entity="Russia",
                conventional_strength=68,
                nuclear_capable=True,
                special_capabilities=[
                    "Large nuclear arsenal (largest warhead stockpile globally)",
                    "Electronic warfare and GPS jamming",
                    "Hypersonic missiles (Kinzhal, Zircon)",
                    "Hybrid warfare and information operations",
                ],
            ),
            MilitaryForce(
                entity="NATO (collective)",
                conventional_strength=82,
                nuclear_capable=True,
                special_capabilities=[
                    "Interoperable combined arms across 32 nations",
                    "Article 5 collective defence guarantee",
                    "Advanced air defence systems (Patriot, THAAD, NASAMS)",
                    "Intelligence sharing (Five Eyes + partners)",
                ],
            ),
            MilitaryForce(
                entity="Israel",
                conventional_strength=68,
                nuclear_capable=True,
                special_capabilities=[
                    "Iron Dome and multi-layer air defence",
                    "Long-range precision strike capability (demonstrated vs Iran)",
                    "Signals intelligence (Unit 8200)",
                    "Autonomous loitering munitions",
                ],
            ),
        ],
        arms_races=[
            (
                "AI-directed autonomous weapons \u2014 the US and China are racing"
                " to deploy AI-directed combat platforms, creating pressure on"
                " allied nations to relax human-in-the-loop requirements."
            ),
            (
                "Hypersonic missiles \u2014 Russia, China, and the US all have"
                " operational hypersonic systems; NATO allies are accelerating"
                " counter-hypersonic defences."
            ),
            (
                "Drone warfare \u2014 Ukraine-Russia has become the world\u2019s"
                " largest real-world laboratory for drone combat, with lessons being"
                " rapidly absorbed by all major militaries."
            ),
        ],
        doctrine_shifts=[
            (
                "Mass autonomous strike \u2014 the use of drone swarms and loitering"
                " munitions is replacing traditional artillery-centric warfare, as"
                " demonstrated in Ukraine and the Israel-Iran conflict."
            ),
            (
                "Grey zone operations \u2014 cyber attacks, disinformation, economic"
                " coercion, and proxy warfare are the primary tools of great power"
                " competition below the threshold of open war."
            ),
        ],
    ),
    environment=EnvironmentState(
        global_temperature_anomaly=1.47,
        crises=[
            EnvironmentalCrisis(
                name="Global Warming Milestone",
                severity="severe",
                affected_regions=["Global"],
                description=(
                    "2025 was confirmed as the hottest year on record, with a global"
                    " average temperature anomaly of +1.47\u00b0C above pre-industrial"
                    " levels \u2014 approaching the 1.5\u00b0C Paris Agreement"
                    " threshold. Extreme weather events (floods, heatwaves,"
                    " wildfires) intensified globally."
                ),
            ),
            EnvironmentalCrisis(
                name="Middle East Humanitarian Crisis",
                severity="catastrophic",
                affected_regions=["Gaza", "Lebanon", "Sudan", "Yemen"],
                description=(
                    "The intersecting conflicts in Gaza, Lebanon, Sudan, and Yemen"
                    " have created simultaneous humanitarian disasters affecting tens"
                    " of millions. Aid delivery is blocked or insufficient. The Iran"
                    " escalation risks further destabilising food and fuel supply"
                    " chains across the region."
                ),
            ),
        ],
        mitigation_efforts=[
            (
                "Record global renewable energy deployment \u2014 600 GW of solar"
                " added in 2025; wind and solar now meet 109% of new global"
                " electricity demand growth."
            ),
            (
                "EU Green Deal and REPowerEU \u2014 accelerating clean energy and"
                " reducing dependence on Russian fossil fuels across 27 member"
                " states."
            ),
            (
                "US Inflation Reduction Act clean energy investment continues"
                " \u2014 despite Trump administration pressure, IRA subsidies are"
                " flowing to red-state manufacturing, creating bipartisan political"
                " resilience."
            ),
        ],
    ),
    history=[
        HistoricalEvent(
            date="1 January 2026",
            headline="Bulgaria adopts the euro",
            description=(
                "Bulgaria became the 21st member of the eurozone on 1 January 2026,"
                " replacing the lev with the euro after years of preparation and"
                " meeting Maastricht convergence criteria."
            ),
            impact=(
                "Deepened EU economic integration and provided currency stability"
                " to one of the EU\u2019s poorest member states."
            ),
            sectors=[
                "finance-and-markets",
                "trade-and-commerce",
                "domestic-politics",
            ],
        ),
        HistoricalEvent(
            date="January 2026",
            headline="Davos 2026 \u2014 record attendance of world leaders",
            description=(
                "The World Economic Forum in Davos attracted a record 60+ heads of"
                " state and government, reflecting acute demand for global"
                " coordination amid trade wars, AI disruption, and Middle East"
                " escalation."
            ),
            impact=(
                "Produced no binding agreements but signalled elite consensus around"
                " AI governance frameworks and tariff de-escalation talks."
            ),
            sectors=[
                "geopolitics",
                "trade-and-commerce",
                "artificial-intelligence",
            ],
        ),
        HistoricalEvent(
            date="February 2026",
            headline="United States withdraws from the World Health Organisation",
            description=(
                "The Trump administration formally withdrew the US from the WHO,"
                " citing cost and alleged political bias. The withdrawal takes effect"
                " after 12 months under WHO rules."
            ),
            impact=(
                "Reduced WHO funding by ~18%. Triggered emergency fundraising from"
                " EU and philanthropic donors. Weakened global pandemic preparedness"
                " coordination."
            ),
            sectors=["domestic-politics", "public-health", "geopolitics"],
        ),
        HistoricalEvent(
            date="19 February 2026",
            headline="South Korea: President Yoon convicted, sentenced to life imprisonment",
            description=(
                "Former President Yoon Suk-yeol was convicted of insurrection"
                " following his short-lived imposition of martial law in December"
                " 2024, and sentenced to life imprisonment."
            ),
            impact=(
                "Affirmed South Korean democratic institutions. Opposition leader"
                " Lee Jae-Myung won the subsequent presidential election."
            ),
            sectors=["domestic-politics", "law-and-justice"],
        ),
        HistoricalEvent(
            date="February 2026",
            headline="Japan election \u2014 LDP majority restored, Takaichi confirmed as PM",
            description=(
                "Japan\u2019s ruling Liberal Democratic Party secured a parliamentary"
                " majority in snap elections. Sanae Takaichi was confirmed as Prime"
                " Minister \u2014 Japan\u2019s first female head of government."
            ),
            impact=(
                "Ended a period of coalition instability. Takaichi has committed to"
                " continuing defence spending increases and close US alignment."
            ),
            sectors=[
                "domestic-politics",
                "geopolitics",
                "military-and-defence",
            ],
        ),
        HistoricalEvent(
            date="28 February 2026",
            headline="US and Israel strike Iran \u2014 Supreme Leader Khamenei killed",
            description=(
                "In a coordinated strike, US and Israeli forces targeted Iranian"
                " military and leadership sites. Supreme Leader Ali Khamenei was"
                " killed. Iran\u2019s Interim Leadership Council immediately took"
                " control of state functions."
            ),
            impact=(
                "The most significant Middle East escalation in decades. Iran"
                " immediately began retaliatory strikes on US Gulf bases and Israeli"
                " territory. Global oil prices surged. The UN Security Council held"
                " emergency sessions."
            ),
            sectors=[
                "geopolitics",
                "military-and-defence",
                "energy",
                "finance-and-markets",
            ],
        ),
        HistoricalEvent(
            date="March 2026",
            headline="Iran retaliates \u2014 Middle East war escalates",
            description=(
                "Iran\u2019s Interim Leadership Council directed ballistic missile and"
                " drone strikes against US bases in Bahrain, Qatar, and Iraq, and"
                " against Israeli cities. Hezbollah launched simultaneous rocket"
                " barrages from Lebanon."
            ),
            impact=(
                "The Middle East is in its most dangerous state since 1973. Oil"
                " prices at multi-year highs. Shipping through the Strait of Hormuz"
                " is under threat. The US has deployed additional carrier strike"
                " groups to the region."
            ),
            sectors=[
                "geopolitics",
                "military-and-defence",
                "energy",
                "trade-and-commerce",
                "finance-and-markets",
            ],
        ),
    ],
)
