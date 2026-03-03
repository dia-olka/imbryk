import type { WorldLedger } from './world-ledger.types.js';

export const INITIAL_WORLD_LEDGER: WorldLedger = {
  epoch: 'March 2026 — The World as It Is',

  synopsis: `The world enters 2026 under compounding pressures. The United States, under Donald Trump's second term, has imposed a 10% global import tariff and withdrawn from the WHO, reshaping the multilateral order. A fragile US-China tariff truce holds at 30%/10% baseline rates, but tensions over Taiwan remain elevated. Russia and Ukraine are locked in a grinding stalemate across the Donbas front, with no peace talks in sight. The most acute crisis erupted on 28 February 2026: US and Israeli strikes killed Iranian Supreme Leader Ali Khamenei; Iran is retaliating across the Middle East, and the region is on the edge of full-scale war.

AI has crossed into the agentic era — autonomous systems are acting on behalf of users and institutions without step-by-step human instruction. DeepSeek R1 narrowed the US-China AI capability gap dramatically. Renewable energy met 109% of new global electricity demand in 2025 — the first year solar and wind outpaced all new demand. Global temperature anomaly reached 1.47°C above pre-industrial levels in 2025. The morning papers have never mattered more.`,

  geopolitics: {
    nations: [
      {
        name: 'United States',
        governmentType: 'Federal presidential republic',
        leader: 'Donald Trump',
        stability: 62,
        description:
          'The world\'s largest economy and military superpower, now in Trump\'s second term. Pursuing aggressive tariff policy, energy dominance, and strategic confrontation with China. Domestically divided but institutionally functional. Engaged militarily in the Middle East following strikes on Iran.',
      },
      {
        name: 'China',
        governmentType: 'One-party state',
        leader: 'Xi Jinping',
        stability: 76,
        description:
          'The world\'s second-largest economy and primary US strategic rival. Pursuing technological self-sufficiency following US chip export controls. DeepSeek R1 closed the AI gap with US frontier labs. Military pressure on Taiwan is intensifying. Navigating a fragile trade truce with Washington.',
      },
      {
        name: 'Russia',
        governmentType: 'Presidential federation',
        leader: 'Vladimir Putin',
        stability: 58,
        description:
          'Engaged in a costly war of attrition in Ukraine. Economy under severe Western sanctions but propped up by energy exports to China and India. Military capacity degraded but intact. Increasingly dependent on North Korean ammunition and Iranian drones.',
      },
      {
        name: 'United Kingdom',
        governmentType: 'Parliamentary constitutional monarchy',
        leader: 'Keir Starmer',
        stability: 72,
        description:
          'Post-Brexit Britain under a Labour government. Pursuing closer EU ties without rejoining the single market. Committed to NATO and Ukrainian support. Facing domestic economic pressures and a resurgent Reform Party.',
      },
      {
        name: 'Germany',
        governmentType: 'Federal parliamentary republic',
        leader: 'Friedrich Merz',
        stability: 70,
        description:
          'Europe\'s largest economy, growing at a sluggish 0.9%. New CDU-led coalition under Friedrich Merz following the February 2025 snap election. Facing deindustrialisation pressures, energy costs, and the rise of the AfD. Central to European defence rearming.',
      },
      {
        name: 'France',
        governmentType: 'Semi-presidential republic',
        leader: 'Emmanuel Macron',
        stability: 65,
        description:
          'Navigating political fragmentation after 2024 snap elections produced a hung parliament. Macron serves as president with reduced authority. France is pushing for greater European strategic autonomy and remains a nuclear power.',
      },
      {
        name: 'Japan',
        governmentType: 'Parliamentary constitutional monarchy',
        leader: 'Sanae Takaichi',
        stability: 74,
        description:
          'Japan\'s LDP returned a majority, with Sanae Takaichi confirmed as Prime Minister — Japan\'s first female PM. Increasing defence spending toward 2% of GDP. Deeply engaged in QUAD and AUKUS-adjacent security arrangements. Watching Taiwan closely.',
      },
      {
        name: 'India',
        governmentType: 'Federal parliamentary republic',
        leader: 'Narendra Modi',
        stability: 74,
        description:
          'World\'s most populous nation and fastest-growing major economy. Modi\'s BJP government balancing ties with the West, Russia, and China. A key QUAD partner. Emerging as a global manufacturing hub as companies diversify away from China.',
      },
      {
        name: 'Brazil',
        governmentType: 'Federal presidential republic',
        leader: 'Luiz Inácio Lula da Silva',
        stability: 60,
        description:
          'Latin America\'s largest economy, under Lula\'s third term. Navigating fiscal pressures and climate leadership ambitions simultaneously. Active in BRICS+ and pushing for Global South interests in multilateral forums.',
      },
      {
        name: 'Ukraine',
        governmentType: 'Presidential republic (wartime)',
        leader: 'Volodymyr Zelenskyy',
        stability: 44,
        description:
          'In its fourth year of full-scale war with Russia. Stalemate persists on the Donbas front. Sustained by Western military and financial aid, though US support has become less reliable under Trump. Martial law in effect; civilian resilience remains high.',
      },
      {
        name: 'Israel',
        governmentType: 'Parliamentary democracy',
        leader: 'Benjamin Netanyahu',
        stability: 52,
        description:
          'Engaged in simultaneous conflicts in Gaza and Lebanon, and now directly at war with Iran following the February 2026 strikes on Tehran. Domestic coalition is fragile. October 2026 elections loom. International isolation deepening despite US backing.',
      },
      {
        name: 'Iran',
        governmentType: 'Theocratic republic (in succession crisis)',
        leader: 'Interim Leadership Council',
        stability: 28,
        description:
          'In acute crisis following the assassination of Supreme Leader Ali Khamenei on 28 February 2026 in a US-Israeli strike. An interim council is directing the state. Revolutionary Guards are conducting retaliatory strikes across the region. The succession struggle threatens regime cohesion.',
      },
      {
        name: 'Turkey',
        governmentType: 'Presidential republic',
        leader: 'Recep Tayyip Erdoğan',
        stability: 60,
        description:
          'Pivotal NATO member playing both sides — maintaining ties with Russia while hosting Ukrainian peace talks. Erdoğan leverages Turkey\'s geographic position for economic and political gains. Inflation remains a domestic pressure.',
      },
      {
        name: 'Saudi Arabia',
        governmentType: 'Absolute monarchy',
        leader: 'Mohammed bin Salman (de facto)',
        stability: 68,
        description:
          'Crown Prince MBS is the effective ruler. Pursuing Vision 2030 economic diversification. Navigating the Iran crisis carefully — member of BRICS+ but aligned with the US on security. Major oil producer facing long-term demand uncertainty as clean energy accelerates.',
      },
      {
        name: 'South Korea',
        governmentType: 'Presidential republic',
        leader: 'Lee Jae-Myung',
        stability: 56,
        description:
          'Emerging from a constitutional crisis: President Yoon Suk-yeol was convicted and sentenced to life imprisonment on 19 February 2026. Opposition leader Lee Jae-Myung won the subsequent presidential election. North Korean provocations and close US alliance ties define foreign policy.',
      },
    ],
    alliances: [
      {
        name: 'NATO',
        members: [
          'United States', 'United Kingdom', 'France', 'Germany', 'Canada',
          'Italy', 'Poland', 'Turkey', 'Spain', 'Netherlands', 'Belgium',
          'Norway', 'Denmark', 'Sweden', 'Finland', 'Greece', 'Portugal',
          'Czech Republic', 'Hungary', 'Romania', 'Bulgaria', 'Slovakia',
          'Slovenia', 'Estonia', 'Latvia', 'Lithuania', 'Albania', 'Croatia',
          'Montenegro', 'North Macedonia', 'Luxembourg', 'Iceland',
        ],
        purpose:
          'Collective defence pact (Article 5). 32 member states. Largest peacetime military alliance in history. Currently supporting Ukraine and monitoring Middle East escalation.',
      },
      {
        name: 'G7',
        members: ['United States', 'United Kingdom', 'France', 'Germany', 'Italy', 'Japan', 'Canada'],
        purpose:
          'Forum of the world\'s seven largest advanced economies plus the EU. Coordinates sanctions on Russia, AI governance standards, clean energy transition, and economic policy among Western democracies.',
      },
      {
        name: 'BRICS+',
        members: ['Brazil', 'Russia', 'India', 'China', 'South Africa', 'Egypt', 'Ethiopia', 'Iran', 'UAE', 'Saudi Arabia'],
        purpose:
          'Expanded bloc of major emerging and developing economies. Promotes a multipolar world order, dollar-alternative payment systems, and South-South cooperation. Tensions between members (India-China, Saudi-Iran) limit cohesion.',
      },
      {
        name: 'QUAD',
        members: ['United States', 'Australia', 'India', 'Japan'],
        purpose:
          'Indo-Pacific security dialogue. Focused on countering Chinese military expansion, securing supply chains, and maintaining freedom of navigation in the South China Sea and Taiwan Strait.',
      },
      {
        name: 'AUKUS',
        members: ['Australia', 'United Kingdom', 'United States'],
        purpose:
          'Defence technology partnership providing Australia with nuclear-powered submarines and advanced military capabilities. Designed to strengthen Indo-Pacific deterrence against Chinese power projection.',
      },
      {
        name: 'European Union',
        members: [
          'France', 'Germany', 'Italy', 'Spain', 'Poland', 'Netherlands',
          'Belgium', 'Sweden', 'Austria', 'Denmark', 'Finland', 'Portugal',
          'Greece', 'Czech Republic', 'Romania', 'Hungary', 'Bulgaria',
          'Slovakia', 'Croatia', 'Slovenia', 'Estonia', 'Latvia', 'Lithuania',
          'Luxembourg', 'Malta', 'Cyprus', 'Ireland',
        ],
        purpose:
          'Political and economic union of 27 member states. Single market, common currency (euro — now used by 21 members including Bulgaria from January 2026). Pursuing strategic autonomy in defence and AI regulation.',
      },
    ],
    conflicts: [
      {
        name: 'Russia-Ukraine War',
        parties: ['Russia', 'Ukraine'],
        status: 'active',
        description:
          'Now in its fourth year following Russia\'s February 2022 full-scale invasion. The front line has stabilised across the Donbas, with neither side able to achieve a breakthrough. Russia has adapted to Western sanctions through oil exports to China and India. Ukraine remains dependent on Western military aid.',
      },
      {
        name: 'US-Iran-Israel Military Escalation',
        parties: ['United States', 'Israel', 'Iran'],
        status: 'active',
        description:
          'The most acute current flashpoint. US and Israeli strikes on 28 February 2026 killed Supreme Leader Ali Khamenei. Iran\'s Interim Leadership Council is directing retaliatory strikes on US bases in the Gulf region and on Israeli territory. The conflict risks drawing in Hezbollah, Houthis, and regional proxies.',
      },
      {
        name: 'Israel-Gaza War',
        parties: ['Israel', 'Hamas'],
        status: 'active',
        description:
          'Ongoing since October 2023. Gaza faces a severe humanitarian crisis. Ceasefire negotiations have repeatedly collapsed. International pressure on Israel is intensifying. October 2026 Israeli elections are adding domestic political pressure on Netanyahu\'s coalition.',
      },
      {
        name: 'Sudan Civil War',
        parties: ['Sudanese Armed Forces (SAF)', 'Rapid Support Forces (RSF)'],
        status: 'active',
        description:
          'Conflict between the SAF and the paramilitary RSF has caused one of the world\'s worst humanitarian disasters. Millions displaced, widespread famine conditions. Regional powers (Egypt, UAE, Ethiopia) back different sides.',
      },
      {
        name: 'Taiwan Strait Tensions',
        parties: ['China', 'Taiwan', 'United States'],
        status: 'active',
        description:
          'China has increased military incursions into Taiwan\'s air defence identification zone to near-daily frequency. QUAD and AUKUS partners have intensified naval presence. No kinetic conflict, but crisis risk is at its highest since 1996. The Middle East war is diverting US attention and resources.',
      },
    ],
  },

  economics: {
    currencies: [
      {
        name: 'US Dollar (USD)',
        issuingEntity: 'US Federal Reserve',
        strength: 86,
        description:
          'Dominant global reserve currency, comprising ~58% of central bank reserves. Strengthened by Trump tariff policy and safe-haven demand during Middle East escalation. BRICS+ nations are actively developing alternatives, but the dollar\'s structural dominance persists.',
      },
      {
        name: 'Euro (EUR)',
        issuingEntity: 'European Central Bank',
        strength: 72,
        description:
          'Second most-held reserve currency. Used by 21 EU member states including Bulgaria (joined Jan 2026). Eurozone growth is sluggish: Germany at 0.9%, Italy at 0.4%. The ECB is navigating between stimulating growth and controlling residual inflation.',
      },
      {
        name: 'Chinese Yuan (CNY)',
        issuingEntity: 'People\'s Bank of China',
        strength: 65,
        description:
          'Growing in bilateral trade settlements, especially with Russia, Iran, and BRICS+ members. Capital controls and limited convertibility constrain its reserve currency role. China is promoting a BRICS+ payment system to bypass dollar dependency.',
      },
      {
        name: 'British Pound (GBP)',
        issuingEntity: 'Bank of England',
        strength: 68,
        description:
          'A major reserve currency, though diminished post-Brexit. UK economy stabilising under the Labour government but growth remains modest. Sterling benefits from London\'s role as a global financial centre.',
      },
      {
        name: 'Japanese Yen (JPY)',
        issuingEntity: 'Bank of Japan',
        strength: 60,
        description:
          'The Bank of Japan has cautiously raised interest rates as it exits decades of ultra-loose monetary policy. The yen had weakened sharply in 2024-25; modest recovery underway. Japan remains a major creditor nation.',
      },
      {
        name: 'Bitcoin (BTC)',
        issuingEntity: 'Decentralised (Bitcoin network)',
        strength: 42,
        description:
          'Bitcoin has established itself as a digital asset class. US spot Bitcoin ETFs now hold significant institutional assets. Trump administration is crypto-friendly. Volatility remains high; not yet functioning as a stable reserve, but growing as a hedge against dollar risk in sanctioned economies.',
      },
    ],
    tradingBlocs: [
      {
        name: 'US Tariff Regime (2025-)',
        members: ['United States'],
        focus:
          'Trump\'s 10% baseline global import tariff, in effect from early 2025. Sector-specific tariffs on China (30%+), steel, aluminium, and EVs. Designed to re-shore manufacturing and leverage trade as diplomatic tool. Trading partners are seeking bilateral deals to reduce exposure.',
      },
      {
        name: 'US-China Trade Truce',
        members: ['United States', 'China'],
        focus:
          'Fragile baseline truce: US maintains 30% tariffs on Chinese goods; China maintains 10% on US goods. Both sides have agreed not to escalate for 90 days (as of Jan 2026). Technology and semiconductor restrictions remain in full force outside the truce.',
      },
      {
        name: 'European Single Market',
        members: ['European Union member states'],
        focus:
          'Tariff-free trade in goods and services among 27 EU members. The EU is negotiating updated trade frameworks with the US and pursuing strategic autonomy in semiconductors and AI. EU Carbon Border Adjustment Mechanism (CBAM) now operational.',
      },
    ],
    scarcities: [
      {
        resource: 'Semiconductors (advanced chips)',
        severity: 'critical',
        affectedRegions: ['United States', 'European Union', 'Japan', 'South Korea'],
        description:
          'US export controls on advanced AI chips and semiconductor equipment to China have intensified a global tech supply chain bifurcation. TSMC\'s Arizona fabs are ramping but at higher cost. China is investing heavily in domestic chip production.',
      },
      {
        resource: 'Critical minerals (lithium, cobalt, rare earths)',
        severity: 'moderate',
        affectedRegions: ['United States', 'European Union', 'Japan'],
        description:
          'Clean energy transition is driving demand for critical minerals. China dominates rare earth processing (~60% global share). The IRA and EU Critical Raw Materials Act are funding diversified supply chains, but results are years away.',
      },
      {
        resource: 'Fresh water (MENA and sub-Saharan Africa)',
        severity: 'moderate',
        affectedRegions: ['Saudi Arabia', 'Iran', 'Sudan'],
        description:
          'Aquifer depletion and climate-driven drought are creating severe water stress across the Middle East and North Africa. The ongoing wars in Sudan and the Israel-Gaza-Iran theatre are worsening water infrastructure. Desalination capacity is expanding but is energy-intensive.',
      },
    ],
    globalGdpTrend:
      'Global GDP growth is 3.3% (IMF, January 2026 projection). India leads major economies at ~6.5%. The US grows at ~2.7% amid tariff uncertainty. The eurozone is sluggish at ~1.2%. Russia is in a war economy, growing nominally via defence spending but facing long-term structural decline. China is targeting ~4.5% amid property sector weakness and US tech restrictions.',
  },

  technology: {
    ai: {
      name: 'Artificial Intelligence',
      maturityLevel: 'growth',
      keyPlayers: [
        'United States (OpenAI, Anthropic, Google DeepMind, Meta AI)',
        'China (DeepSeek, Baidu, Alibaba)',
        'European Union (AI Act regulatory framework)',
      ],
      description:
        'AI has shifted from powerful LLM tools to autonomous agents — systems that plan, act, and iterate without step-by-step human instruction. DeepSeek R1 (released Jan 2025) demonstrated that frontier-level reasoning could be achieved at a fraction of US training cost, closing the perceived US-China capability gap. IBM announced a quantum computing milestone. Trump signed an executive order limiting state AI laws to preserve federal pre-emption. The EU AI Act is entering enforcement phase.',
    },
    energy: {
      name: 'Energy',
      maturityLevel: 'growth',
      keyPlayers: [
        'China (world\'s largest solar and wind installer)',
        'United States (LNG exports, shale, growing renewables)',
        'European Union (green energy transition, REPowerEU)',
      ],
      description:
        'Solar and wind met 109% of new global electricity demand in 2025 — the first time renewables have exceeded all incremental demand growth. A record 600 GW of solar was added globally in 2025. The US is pursuing both fossil fuel expansion ("drill, baby, drill") and clean energy deployment, while the EU is accelerating decarbonisation. Battery storage costs continue to fall.',
    },
    biotech: {
      name: 'Biotechnology',
      maturityLevel: 'emerging',
      keyPlayers: [
        'United States (pharma industry, CRISPR pioneers)',
        'European Union (EMA regulatory framework)',
        'China (genomics, synthetic biology)',
      ],
      description:
        'The first bespoke CRISPR gene-editing treatment was administered to baby KJ Muldoon, marking a milestone in personalised medicine. Over 150 active gene-editing clinical trials are underway globally. GLP-1 weight-loss and diabetes drugs (Ozempic, Wegovy) are reshaping healthcare economics. Bioethics frameworks are struggling to keep pace with capability.',
    },
    other: [],
  },

  culture: {
    dominantNarratives: [
      '"America First" is reshaping global multilateralism — tariffs, WHO withdrawal, and reduced US engagement in international institutions are forcing other nations to build resilience without Washington.',
      'The "agentic AI" moment — the shift from AI as a tool to AI as an autonomous actor is creating both opportunity and anxiety across every sector of the economy and society.',
      'Democratic backsliding anxiety — from Hungary to South Korea to the United States, the resilience of democratic institutions is being tested and debated globally.',
    ],
    movements: [
      {
        name: 'Anti-AI Labour Movement',
        reach: 'global',
        description:
          'Workers in creative industries, law, finance, and journalism are organising against AI displacement. Hollywood writers\' precedents are being cited globally. Demands range from AI use disclosure to per-use royalty funds for displaced workers.',
      },
      {
        name: 'Pro-Palestine Solidarity Movement',
        reach: 'global',
        description:
          'University campuses and city centres across the West have seen sustained demonstrations demanding ceasefires, arms embargoes on Israel, and sanctions. The movement has intensified following the Iran strikes of February 2026.',
      },
    ],
    mediaLandscape:
      'Legacy media is under existential financial pressure from AI-generated content and social media. Trust in mainstream outlets is at historic lows across Western democracies. X (formerly Twitter) under Elon Musk has become a primary news source for millions while also being a vector for state-sponsored disinformation. AI-generated deepfakes are increasingly indistinguishable from authentic video. A new generation of subscription-funded, AI-augmented newsrooms is emerging — small, opinionated, and audience-funded.',
  },

  military: {
    forces: [
      {
        entity: 'United States',
        conventionalStrength: 97,
        nuclearCapable: true,
        specialCapabilities: [
          'Global force projection (11 carrier strike groups)',
          'Cyber Command (USCYBERCOM)',
          'Space-based ISR and GPS dominance',
          'AI-directed autonomous drone swarms',
          'Special Operations Forces globally deployed',
        ],
      },
      {
        entity: 'China',
        conventionalStrength: 85,
        nuclearCapable: true,
        specialCapabilities: [
          'Anti-access/area denial (A2/AD) — South China Sea and Taiwan Strait',
          'Hypersonic glide vehicle (DF-17, DF-41)',
          'Cyber warfare (APT groups)',
          'Satellite and anti-satellite capabilities',
          'World\'s largest navy by hull count',
        ],
      },
      {
        entity: 'Russia',
        conventionalStrength: 68,
        nuclearCapable: true,
        specialCapabilities: [
          'Large nuclear arsenal (largest warhead stockpile globally)',
          'Electronic warfare and GPS jamming',
          'Hypersonic missiles (Kinzhal, Zircon)',
          'Hybrid warfare and information operations',
        ],
      },
      {
        entity: 'NATO (collective)',
        conventionalStrength: 82,
        nuclearCapable: true,
        specialCapabilities: [
          'Interoperable combined arms across 32 nations',
          'Article 5 collective defence guarantee',
          'Advanced air defence systems (Patriot, THAAD, NASAMS)',
          'Intelligence sharing (Five Eyes + partners)',
        ],
      },
      {
        entity: 'Israel',
        conventionalStrength: 68,
        nuclearCapable: true,
        specialCapabilities: [
          'Iron Dome and multi-layer air defence',
          'Long-range precision strike capability (demonstrated vs Iran)',
          'Signals intelligence (Unit 8200)',
          'Autonomous loitering munitions',
        ],
      },
    ],
    armsRaces: [
      'AI-directed autonomous weapons — the US and China are racing to deploy AI-directed combat platforms, creating pressure on allied nations to relax human-in-the-loop requirements.',
      'Hypersonic missiles — Russia, China, and the US all have operational hypersonic systems; NATO allies are accelerating counter-hypersonic defences.',
      'Drone warfare — Ukraine-Russia has become the world\'s largest real-world laboratory for drone combat, with lessons being rapidly absorbed by all major militaries.',
    ],
    doctrineShifts: [
      'Mass autonomous strike — the use of drone swarms and loitering munitions is replacing traditional artillery-centric warfare, as demonstrated in Ukraine and the Israel-Iran conflict.',
      'Grey zone operations — cyber attacks, disinformation, economic coercion, and proxy warfare are the primary tools of great power competition below the threshold of open war.',
    ],
  },

  environment: {
    globalTemperatureAnomaly: 1.47,
    crises: [
      {
        name: 'Global Warming Milestone',
        severity: 'severe',
        affectedRegions: ['Global'],
        description:
          '2025 was confirmed as the hottest year on record, with a global average temperature anomaly of +1.47°C above pre-industrial levels — approaching the 1.5°C Paris Agreement threshold. Extreme weather events (floods, heatwaves, wildfires) intensified globally.',
      },
      {
        name: 'Middle East Humanitarian Crisis',
        severity: 'catastrophic',
        affectedRegions: ['Gaza', 'Lebanon', 'Sudan', 'Yemen'],
        description:
          'The intersecting conflicts in Gaza, Lebanon, Sudan, and Yemen have created simultaneous humanitarian disasters affecting tens of millions. Aid delivery is blocked or insufficient. The Iran escalation risks further destabilising food and fuel supply chains across the region.',
      },
    ],
    mitigationEfforts: [
      'Record global renewable energy deployment — 600 GW of solar added in 2025; wind and solar now meet 109% of new global electricity demand growth.',
      'EU Green Deal and REPowerEU — accelerating clean energy and reducing dependence on Russian fossil fuels across 27 member states.',
      'US Inflation Reduction Act clean energy investment continues — despite Trump administration pressure, IRA subsidies are flowing to red-state manufacturing, creating bipartisan political resilience.',
    ],
  },

  history: [
    {
      date: '1 January 2026',
      headline: 'Bulgaria adopts the euro',
      description:
        'Bulgaria became the 21st member of the eurozone on 1 January 2026, replacing the lev with the euro after years of preparation and meeting Maastricht convergence criteria.',
      impact:
        'Deepened EU economic integration and provided currency stability to one of the EU\'s poorest member states.',
      sectors: ['finance-and-markets', 'trade-and-commerce', 'domestic-politics'],
    },
    {
      date: 'January 2026',
      headline: 'Davos 2026 — record attendance of world leaders',
      description:
        'The World Economic Forum in Davos attracted a record 60+ heads of state and government, reflecting acute demand for global coordination amid trade wars, AI disruption, and Middle East escalation.',
      impact:
        'Produced no binding agreements but signalled elite consensus around AI governance frameworks and tariff de-escalation talks.',
      sectors: ['geopolitics', 'trade-and-commerce', 'artificial-intelligence'],
    },
    {
      date: 'February 2026',
      headline: 'United States withdraws from the World Health Organisation',
      description:
        'The Trump administration formally withdrew the US from the WHO, citing cost and alleged political bias. The withdrawal takes effect after 12 months under WHO rules.',
      impact:
        'Reduced WHO funding by ~18%. Triggered emergency fundraising from EU and philanthropic donors. Weakened global pandemic preparedness coordination.',
      sectors: ['domestic-politics', 'public-health', 'geopolitics'],
    },
    {
      date: '19 February 2026',
      headline: 'South Korea: President Yoon convicted, sentenced to life imprisonment',
      description:
        'Former President Yoon Suk-yeol was convicted of insurrection following his short-lived imposition of martial law in December 2024, and sentenced to life imprisonment.',
      impact:
        'Affirmed South Korean democratic institutions. Opposition leader Lee Jae-Myung won the subsequent presidential election.',
      sectors: ['domestic-politics', 'law-and-justice'],
    },
    {
      date: 'February 2026',
      headline: 'Japan election — LDP majority restored, Takaichi confirmed as PM',
      description:
        'Japan\'s ruling Liberal Democratic Party secured a parliamentary majority in snap elections. Sanae Takaichi was confirmed as Prime Minister — Japan\'s first female head of government.',
      impact:
        'Ended a period of coalition instability. Takaichi has committed to continuing defence spending increases and close US alignment.',
      sectors: ['domestic-politics', 'geopolitics', 'military-and-defence'],
    },
    {
      date: '28 February 2026',
      headline: 'US and Israel strike Iran — Supreme Leader Khamenei killed',
      description:
        'In a coordinated strike, US and Israeli forces targeted Iranian military and leadership sites. Supreme Leader Ali Khamenei was killed. Iran\'s Interim Leadership Council immediately took control of state functions.',
      impact:
        'The most significant Middle East escalation in decades. Iran immediately began retaliatory strikes on US Gulf bases and Israeli territory. Global oil prices surged. The UN Security Council held emergency sessions.',
      sectors: ['geopolitics', 'military-and-defence', 'energy', 'finance-and-markets'],
    },
    {
      date: 'March 2026',
      headline: 'Iran retaliates — Middle East war escalates',
      description:
        'Iran\'s Interim Leadership Council directed ballistic missile and drone strikes against US bases in Bahrain, Qatar, and Iraq, and against Israeli cities. Hezbollah launched simultaneous rocket barrages from Lebanon.',
      impact:
        'The Middle East is in its most dangerous state since 1973. Oil prices at multi-year highs. Shipping through the Strait of Hormuz is under threat. The US has deployed additional carrier strike groups to the region.',
      sectors: ['geopolitics', 'military-and-defence', 'energy', 'trade-and-commerce', 'finance-and-markets'],
    },
  ],
};
