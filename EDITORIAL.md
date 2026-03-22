# Editorial Excellence Plan

Upgrade newspaper prompts with real-world few-shot examples, named editorial teams, and Gemini 2.5 Pro/Flash prompt best practices.

> **Goal**: Each of the 6 newspapers should read as if written by a world-class editorial team steeped in the tradition of a real iconic publication. Readers should feel the difference in every headline, every lede, every paragraph break.

---

## Table of Contents

1. [Phase 1 — Few-Shot Exemplar Library](#phase-1--few-shot-exemplar-library)
2. [Phase 2 — Editorial Teams](#phase-2--editorial-teams)
3. [Phase 3 — Gemini 3.1 Prompt Restructuring](#phase-3--gemini-31-prompt-restructuring)
4. [Phase 4 — Implementation Plan](#phase-4--implementation-plan)
5. [Phase 5 — Evaluation & Iteration](#phase-5--evaluation--iteration)

---

## Phase 1 — Few-Shot Exemplar Library

Each newspaper gets 2–3 real-world article excerpts baked into its `promptSuffix`. These are **not full articles** — they are carefully trimmed exemplars (lede + 2 paragraphs + headline) that demonstrate the target voice, structure, and rhythm. The model learns by imitation, not by instruction alone.

### 1.1 The Sovereign — *modelled on The Economist*

**Why The Economist**: Authoritative, detached, witty-but-never-frivolous broadsheet prose. The gold standard for geopolitical analysis written for decision-makers. No bylines — the institutional voice is the brand.

**Exemplar style markers to extract:**
- The unsigned institutional "we" and "this newspaper"
- Dry wit in parenthetical asides
- Lede that drops you mid-action, then zooms out to structural analysis
- Paragraph 2 always gives the "why it matters" pivot
- Subheadings as complete declarative sentences

**Few-shot examples to source (3 articles):**

| # | Source | Why this article |
|---|--------|-----------------|
| 1 | *The Economist* — a leader (editorial) on a geopolitical crisis | Shows the classic Economist structure: bold thesis in lede, concession to counterargument, data pivot, policy recommendation |
| 2 | *Foreign Affairs* — an analytical essay on great-power competition | Demonstrates the measured, evidence-heavy register The Sovereign should use for long-form pieces |
| 3 | *The Economist* — a Briefing section piece | Shows data integration mid-narrative, chart-referencing prose, and the signature "And yet…" pivot |

**Exemplar template (to include in promptSuffix):**

```
WRITING EXEMPLARS — study these for voice, structure, and rhythm:

EXEMPLAR 1 (Leader / Editorial):
Headline: [Real Economist headline, ≤10 words]
---
[Lede paragraph — 40-60 words, drops reader into the situation]
[Pivot paragraph — "why it matters" structural analysis, 50-70 words]
[Closing paragraph — policy implication or forward-looking statement]
---
NOTE: Observe the institutional voice, the absence of first person, the dry pivot from fact to implication.

EXEMPLAR 2 (Analysis):
[Similar structure]
```

---

### 1.2 The Aspirant — *modelled on The Guardian*

**Why The Guardian**: The world's leading progressive broadsheet. Investigative rigour paired with moral urgency. Long tradition of holding power to account while centring affected communities.

**Exemplar style markers to extract:**
- Lede that starts with a person — a worker, a refugee, a community member
- Second paragraph widens to the systemic issue
- Direct quotes from affected people woven into analysis
- Headlines that name the human cost, not the policy abstraction
- "Comment is Free" opinion pieces as model for editors_note voice

**Few-shot examples to source (3 articles):**

| # | Source | Why this article |
|---|--------|-----------------|
| 1 | *The Guardian* — a long-read investigative piece on labour/environmental justice | Shows the human-first structure: open on a person, widen to the system, return to the person |
| 2 | *The Guardian* — a front-page news report on a protest or workers' action | Demonstrates solidarity framing without losing journalistic distance |
| 3 | *Jacobin* or *The Nation* — a sharp structural analysis piece | Shows the academic-progressive register: class analysis, historical context, systemic critique |

---

### 1.3 The Owner — *modelled on the Financial Times*

**Why the Financial Times**: The global newspaper of record for markets and capital. Salmon-pink authority. Data-first, unsentimental, but never crude — the FT respects the reader's intelligence.

**Exemplar style markers to extract:**
- Lede opens with the number — a price move, a deal size, a percentage shift
- Attribution to named analysts/economists in paragraph 2
- "said [Name], [title] at [institution]" pattern for authority
- Charts described in prose ("as the chart below shows" → translate to narrative)
- Closing paragraph is always forward-looking: "investors will be watching for…"

**Few-shot examples to source (3 articles):**

| # | Source | Why this article |
|---|--------|-----------------|
| 1 | *Financial Times* — a markets report (Lex column style) | The Lex column is the purest expression of FT voice: 300–500 words, one thesis, data-driven, concludes with an investment implication |
| 2 | *Wall Street Journal* — a front-page business story | Shows the "anecdotal lede → data pivot → industry analysis" structure |
| 3 | *Bloomberg Opinion* (Matt Levine's "Money Stuff") | Demonstrates the rare ability to make financial complexity entertaining and accessible without dumbing it down |

---

### 1.4 The Moralist — *modelled on The Daily Telegraph*

**Why The Daily Telegraph**: Britain's paper of record for traditional conservatism. Measured but morally clear. Respects institutions, tradition, and community. Not angry tabloid populism — dignified conviction.

**Exemplar style markers to extract:**
- Lede states the moral stakes plainly: "Families across Britain face…"
- Second paragraph provides the policy/event trigger
- Appeals to shared values, not ideology ("common sense", "decency", "fairness to taxpayers")
- Direct, clear sentences — no academic jargon
- Closing paragraph often invokes what "ordinary people" expect or deserve

**Few-shot examples to source (3 articles):**

| # | Source | Why this article |
|---|--------|-----------------|
| 1 | *The Daily Telegraph* — a leader column on a social/cultural issue | Shows the signature Telegraph blend: moral clarity + policy pragmatism |
| 2 | *The Spectator* — a column by a traditionalist voice | Demonstrates the witty, erudite conservative essay form |
| 3 | *National Review* — an American conservative editorial | Provides the transatlantic conservative register for US-focused stories |

---

### 1.5 The Radical — *modelled on The Intercept*

**Why The Intercept**: Adversarial journalism that follows the money and the power. Documents what institutions would rather keep hidden. The spiritual heir to I.F. Stone's Weekly.

**Exemplar style markers to extract:**
- Lede drops a revelation: a document, a data point, a contradiction
- Second paragraph names who benefits and who is harmed
- "Follow the money" structure: trace funding, contracts, revolving doors
- Short, punchy paragraphs — often one sentence each
- Rhetorical questions deployed sparingly but effectively

**Few-shot examples to source (3 articles):**

| # | Source | Why this article |
|---|--------|-----------------|
| 1 | *The Intercept* — an investigative exposé on government/corporate malfeasance | Shows the document-first, revelation-driven structure |
| 2 | *Rolling Stone* (Matt Taibbi era) — a financial/political investigation | Demonstrates the gonzo-meets-rigour voice: accessible rage backed by receipts |
| 3 | *Private Eye* — a brief from the "In the Back" section | Shows how to compress a power-accountability story into 150 brutal words |

---

### 1.6 The Hedonist — *modelled on the Daily Mail / New York Post*

**Why Daily Mail + New York Post**: The two most-read English-language tabloids. Masters of the irresistible headline, the scandalous lede, the "you won't believe" energy. Entertainment-first, politics-as-soap-opera.

**Exemplar style markers to extract:**
- Headline is the story — if the headline doesn't make you click, nothing will
- Lede is one sentence, max 20 words, and contains the shock/drama
- Short paragraphs (1–3 sentences max)
- Celebrity names, ages, and relationship status in first mention
- Loaded adjectives: "stunning", "embattled", "disgraced", "bombshell"
- Photo captions do heavy narrative lifting

**Few-shot examples to source (3 articles):**

| # | Source | Why this article |
|---|--------|-----------------|
| 1 | *New York Post* — a front-page splash (political scandal as entertainment) | The Post's wood (front page headline) is an art form — study the compression |
| 2 | *Daily Mail* — a celebrity/society story | Shows the Mail's signature structure: headline → subheadline bullets → punchy lede → photo-driven narrative |
| 3 | *Vanity Fair* — a profile/scandal longform piece | Demonstrates how to give tabloid energy literary polish for the longer articles |

---

### 1.7 Few-Shot Integration Rules

- Each exemplar must be **real, published text** (trimmed to ~150 words) — not AI-generated imitations
- Include source attribution in the prompt as a comment (the model won't output it)
- Place exemplars in a dedicated `WRITING EXEMPLARS` section within each `promptSuffix`, after VOICE and before BIASES
- Mark exemplars clearly: `EXEMPLAR 1 (Type: Leader)`, `EXEMPLAR 2 (Type: Investigation)`
- Add a closing instruction: `"Study these exemplars for voice, rhythm, and structure. Do not copy them — absorb their style and apply it to the clusters below."`

---

## Phase 2 — Editorial Teams

Each newspaper gets a named **editorial board** — real writers and journalists whose distinctive styles the model should channel. These are not impersonations; they are **style anchors**. The prompt says: *"Write as if your editorial team includes writers in the tradition of…"*

### 2.1 The Sovereign — Editorial Board

| Role | Style Anchor | Domain | Why |
|------|-------------|--------|-----|
| **Editor-in-Chief** | Walter Lippmann | Political columnist | Father of modern political commentary. *Public Opinion* (1922) defined how elites think about the world. His columns set the register for serious geopolitical analysis: measured, evidence-based, institutional. |
| **Senior Correspondent** | Anne Applebaum | Geopolitical essayist | Pulitzer winner (*Gulag*, *Iron Curtain*, *Twilight of Democracy*). Writes about geopolitics with data-grounded, historically sweeping, institutionally authoritative prose. Her Atlantic and Washington Post columns are morally serious without being preachy — the exact Sovereign register. |
| **Prose Clarity** | George Orwell | Novelist & essayist | Not 1984-Orwell — essay-Orwell. "Politics and the English Language" Orwell. Clear prose, no jargon, every word earns its place. The antidote to bloated institutional writing. |
| **Gravitas & Rhythm** | John le Carré | Novelist | *Tinker Tailor Soldier Spy*, *The Constant Gardener*. Le Carré wrote about geopolitics the way a great broadsheet should: morally serious, structurally intricate, every sentence loaded with implication. His prose has the weight of institutional knowledge. |
| **Historical Sweep** | Barbara Tuchman | Historian | *The Guns of August*, *A Distant Mirror*. Pulitzer winner who wrote history as riveting narrative. Her ability to compress decades of geopolitical context into a paragraph is exactly what The Sovereign's analysis pieces need. |
| **Rhetorical Authority** | Ted Sorensen | Speechwriter & counsel | "Ask not what your country can do for you — ask what you can do for your country." JFK's speechwriter and closest adviser. Sorensen's institutional eloquence — centrist, aspirational, measured — is the exact register The Sovereign needs for its biggest editorials. Unlike partisan speechwriting, Sorensen wrote for the office, not the ideology. |

**Prompt instruction:**
```
EDITORIAL TEAM TRADITION:
Your editorial voice draws from these traditions:
- The measured institutional analysis of Walter Lippmann — weigh evidence, resist hysteria, write for decision-makers
- The geopolitical prose of Anne Applebaum — historically sweeping, institutionally authoritative, morally serious without being preachy
- The prose clarity of George Orwell's essays — never use a long word where a short one will do; never use the passive where you can use the active
- The morally serious intrigue of John le Carré's novels — every sentence loaded with implication, every paragraph a world in miniature
- The sweeping historical narrative of Barbara Tuchman — compress decades of context into a paragraph that reads like a thriller
- The institutional eloquence of Ted Sorensen — write for the office, not the ideology; make the reader feel the weight of the decision
```

---

### 2.2 The Aspirant — Editorial Board

| Role | Style Anchor | Domain | Why |
|------|-------------|--------|-----|
| **Editor-in-Chief** | George Monbiot | Columnist & activist | The Guardian's most influential columnist. Combines scientific rigour with moral outrage. His environment and power-structures writing is the template for progressive journalism that respects evidence. |
| **Structural Narrative** | Naomi Klein | Author & journalist | *The Shock Doctrine*, *No Logo*. Master of connecting corporate power to human suffering through narrative. Her structural analysis is accessible without being simplistic. |
| **Literary Fire** | James Baldwin | Novelist & essayist | America's greatest essayist on power, identity, and justice. *The Fire Next Time* showed how to write about systemic oppression with beauty, fury, and precision. His prose lifts progressive journalism from polemic to literature. |
| **Poetic Witness** | Eduardo Galeano | Author & poet | *Open Veins of Latin America*, *Memory of Fire* trilogy. Galeano wrote about exploitation and resistance with the compression of poetry and the fury of a pamphleteer. His voice gives The Aspirant its Global South register. |
| **Moral Philosophy** | Ursula K. Le Guin | Novelist & essayist | "The Ones Who Walk Away from Omelas" is the finest parable about systemic injustice ever written. Le Guin's essays and speeches (her National Book Award speech on capitalism and art) model how to challenge power structures with calm, devastating clarity. |
| **Investigative Compassion** | Svetlana Alexievich | Oral historian | Nobel laureate. *Voices from Chernobyl*, *The Unwomanly Face of War*. Alexievich lets the affected speak — her method of centring victims' voices in their own words is exactly how The Aspirant should handle human-impact stories. |

**Prompt instruction:**
```
EDITORIAL TEAM TRADITION:
Your editorial voice draws from these traditions:
- The evidence-based moral urgency of George Monbiot — name the system, show the data, demand accountability
- The structural narrative of Naomi Klein — connect corporate power to human impact through storytelling
- The literary fire of James Baldwin — write about injustice with beauty and precision, not just anger
- The poetic compression of Eduardo Galeano — the history of exploitation told in sentences that cut like glass
- The calm devastating clarity of Ursula K. Le Guin's essays — challenge power without raising your voice
- The witness-centred method of Svetlana Alexievich — let the affected speak; your job is to hold the microphone steady
```

---

### 2.3 The Owner — Editorial Board

| Role | Style Anchor | Domain | Why |
|------|-------------|--------|-----|
| **Editor-in-Chief** | Martin Wolf | Economics columnist | FT's chief economics commentator for 25+ years. The most respected economics columnist alive. His writing is the gold standard: data-dense, intellectually honest, globally authoritative. |
| **Markets Voice** | Matt Levine | Financial newsletter | Bloomberg's "Money Stuff" is the most-read financial newsletter in the world. Levine makes complex financial instruments entertaining without dumbing them down. His voice proves finance writing doesn't have to be dry. |
| **Narrative Craft** | Michael Lewis | Non-fiction author | *The Big Short*, *Flash Boys*, *Liar's Poker*. Lewis turns financial stories into page-turners by finding the human character inside the trade. For The Owner's feature articles. |
| **Intellectual Rigour** | Nassim Nicholas Taleb | Essayist & trader | *The Black Swan*, *Antifragile*. Taleb writes about risk, probability, and markets with the authority of a practitioner and the flair of a philosopher. His irreverent, contrarian style gives The Owner permission to challenge consensus — something financial journalism desperately needs. |
| **Elegant Authority** | John Kenneth Galbraith | Economist & essayist | *The Great Crash, 1929*, *The Affluent Society*. Galbraith was that rarest thing — an economist who could actually write. His prose is urbane, witty, and devastatingly clear. He proved that writing about markets and economic systems doesn't require sacrificing elegance for precision. The Owner's longer analysis pieces need this register. |
| **Analytical Depth** | Gillian Tett | Journalist & anthropologist | FT's chair of the editorial board. Uniquely, Tett has a PhD in social anthropology — she applies ethnographic thinking to financial systems. Her coverage of CDOs before the 2008 crisis showed how to explain complex instruments through the culture that creates them. |

**Prompt instruction:**
```
EDITORIAL TEAM TRADITION:
Your editorial voice draws from these traditions:
- The intellectual authority of Martin Wolf — data-first, globally scoped, never partisan but always opinionated
- The accessible brilliance of Matt Levine — make complex financial mechanics entertaining; if it's boring, you haven't understood it well enough
- The narrative craft of Michael Lewis — every market move has a human character driving it; find that person
- The contrarian rigour of Nassim Taleb — challenge consensus, respect uncertainty, think in probabilities not predictions
- The elegant clarity of John Kenneth Galbraith — markets and economic systems rendered in urbane, witty, devastating prose
- The anthropological lens of Gillian Tett — financial systems are cultures; explain the tribe, not just the numbers
```

---

### 2.4 The Moralist — Editorial Board

| Role | Style Anchor | Domain | Why |
|------|-------------|--------|-----|
| **Editor-in-Chief** | Peggy Noonan | Speechwriter & columnist | WSJ columnist, former Reagan speechwriter. The finest prose stylist in American conservatism. Her writing is warm, patriotic, morally grounded, and never mean-spirited. She writes about values without hectoring. |
| **Philosophical Depth** | Roger Scruton | Philosopher & essayist | *The Meaning of Conservatism* articulated traditionalism as love of inherited beauty, not fear of change. His essays model the erudite, humane conservative voice. |
| **Logical Rigour** | Charles Krauthammer | Columnist | Pulitzer Prize-winning columnist. Clear, logical, persuasive. His columns demonstrated that conservative argument can be rigorous and evidence-based, not just emotional. The template for The Moralist's harder news coverage. |
| **Moral Storytelling** | C.S. Lewis | Novelist & theologian | *Mere Christianity*, *The Screwtape Letters*. Lewis is the master of making moral arguments through accessible, warm, conversational prose. No writer in English has ever been better at explaining traditional values to a sceptical modern audience without condescension. |
| **Homespun Wisdom** | Wendell Berry | Poet, novelist & farmer | *The Unsettling of America*, the Port William novels. Berry writes about community, land, stewardship, and the costs of rootlessness. His voice is the antidote to abstract conservatism — it grounds tradition in the soil, the family table, the local economy. |
| **Civic Eloquence** | Abraham Lincoln (Gettysburg, Second Inaugural) | Statecraft & rhetoric | Not a writer by trade, but the greatest prose stylist ever to hold power. Lincoln's brevity, moral weight, and biblical cadence ("with malice toward none, with charity for all") set the ceiling for what The Moralist's editorial voice should aspire to on the biggest stories. |

**Prompt instruction:**
```
EDITORIAL TEAM TRADITION:
Your editorial voice draws from these traditions:
- The warm moral clarity of Peggy Noonan — write about values with conviction and grace, never with contempt
- The philosophical depth of Roger Scruton — conservatism as love of inherited good, not fear of the new
- The logical rigour of Charles Krauthammer — argue from evidence and principle, not emotion alone
- The accessible moral reasoning of C.S. Lewis — explain traditional values to a sceptical audience without condescension or jargon
- The rooted, earthy conviction of Wendell Berry — ground abstract values in community, land, and the family table
- The brevity and moral weight of Lincoln's prose — on the biggest stories, every word must earn its place; biblical cadence, not partisan noise
```

---

### 2.5 The Radical — Editorial Board

| Role | Style Anchor | Domain | Why |
|------|-------------|--------|-----|
| **Editor-in-Chief** | I.F. Stone | Independent journalist | *I.F. Stone's Weekly* (1953–1971) was one-man investigative journalism. He read every government document, cross-referenced every claim, and exposed lies through public records alone. The patron saint of accountability journalism. |
| **Adversarial Stylist** | Christopher Hitchens | Essayist & polemicist | The finest adversarial prose stylist of the last 50 years. His *Vanity Fair* and *Nation* essays are masterclasses in following power, naming names, and building a devastating argument with wit and fury. Declares bias, then makes it a source of authority — The Radical's exact register. |
| **Gonzo Energy** | Hunter S. Thompson | Novelist & journalist | *Fear and Loathing on the Campaign Trail '72* proved that subjective, angry, vivid reporting can be more truthful than "objective" both-sides-ism. Thompson gives The Radical its fire and irreverence. |
| **Satirical Blade** | Jonathan Swift | Satirist & essayist | *A Modest Proposal* is the greatest piece of political satire ever written. Swift demonstrated that the most devastating way to expose cruelty is to adopt its logic and follow it to absurd conclusions. The Radical's editors_note should channel this energy. |
| **Investigative Writer** | Matt Taibbi | Journalist | Rolling Stone's financial and political investigative voice. Direct descendant of Thompson's energy but as a prose writer, not a performer. His Goldman Sachs "vampire squid" piece is a template for The Radical's investigative lede: revelation, then mechanism, then named beneficiary. |
| **Narrative Exposé** | Roberto Saviano | Author & journalist | *Gomorrah* — Saviano embedded himself inside the Camorra and wrote a book that reads like a novel but is forensic journalism. His method of narrating systemic corruption from the inside is the model for The Radical's long-form investigative pieces. |

**Prompt instruction:**
```
EDITORIAL TEAM TRADITION:
Your editorial voice draws from these traditions:
- The documentary rigour of I.F. Stone — read every document, cross-reference every claim, expose lies through their own words
- The adversarial brilliance of Christopher Hitchens — declare your bias, then make it a source of authority; name names, follow power, build the argument with wit and fury
- The gonzo energy of Hunter S. Thompson — be vivid, be furious, be funny; "objective" journalism is a myth when the powerful control the narrative
- The satirical devastation of Jonathan Swift — adopt power's own logic and follow it to its absurd, cruel conclusion
- The investigative prose of Matt Taibbi — revelation, then mechanism, then named beneficiary; accessible rage backed by receipts
- The embedded narrative of Roberto Saviano — tell the story of corruption from the inside, with the pacing of a novel and the evidence of a court filing
```

---

### 2.6 The Hedonist — Editorial Board

| Role | Style Anchor | Domain | Why |
|------|-------------|--------|-----|
| **Editor-in-Chief** | Tom Wolfe | Novelist & journalist | Father of New Journalism. *The Bonfire of the Vanities*, *The Electric Kool-Aid Acid Test*. Wolfe proved you could write about society, scandal, and spectacle with literary ambition. His status-obsessed eye is perfect for The Hedonist's lens. |
| **Tabloid Craft** | Jimmy Breslin | Columnist | Legendary *New York Daily News* and *Newsday* columnist. Covered the Kennedy assassination by interviewing the gravedigger. Short paragraphs, killer details, the working-class perspective — tabloid energy with genuine literary craft. His columns are the bridge between tabloid instinct and sourceable prose. |
| **Profile & Glamour** | Gay Talese | Literary journalist | "Frank Sinatra Has a Cold" is the greatest celebrity profile ever written. Talese showed how to write about fame with literary depth. The Hedonist's longer pieces should aspire to this: gossip elevated to art. |
| **Wicked Wit** | Oscar Wilde | Playwright & essayist | "I can resist everything except temptation." Wilde's aphoristic brilliance, his obsession with surfaces and the truths they conceal, and his ability to make the reader feel simultaneously delighted and implicated — this is The Hedonist's editorial DNA. The editor's note should feel like a Wilde epigram. |
| **Pop Culture Electricity** | Nora Ephron | Screenwriter, novelist & essayist | *When Harry Met Sally*, *Heartburn*, her New Yorker essays. Ephron turned the personal, the romantic, and the trivial into literature. She proved that writing about food, relationships, and celebrity isn't shallow — it's the texture of how people actually live. The Hedonist's "soft" stories need Ephron's voice. |
| **High-Society Scandal** | Dominick Dunne | Journalist & novelist | *Vanity Fair*'s legendary crime-and-society writer. Dunne covered the O.J. Simpson trial, the Menendez brothers, and every major high-society scandal of the 80s and 90s. His gift was writing about wealth, crime, and celebrity with tabloid compulsion and literary poise — short paragraphs, devastating details, a gossip's instinct for the killer quote. The Hedonist's scandal coverage at its best. |

**Prompt instruction:**
```
EDITORIAL TEAM TRADITION:
Your editorial voice draws from these traditions:
- The social X-ray vision of Tom Wolfe — status, spectacle, and scandal rendered in vivid, status-conscious prose
- The tabloid craft of Jimmy Breslin — short paragraphs, killer details, the working-class perspective; find the gravedigger, not the eulogy
- The literary celebrity profile of Gay Talese — gossip elevated to art; every famous person is a character in a novel they don't know they're in
- The wicked aphoristic wit of Oscar Wilde — delight the reader, then make them realise you just said something devastating
- The personal-is-universal voice of Nora Ephron — food, love, scandal, celebrity; the "trivial" is where people actually live
- The high-society scandal craft of Dominick Dunne — wealth, crime, celebrity; short paragraphs, devastating details, a gossip's instinct for the killer quote
```

---

### 2.7 Sourcing Guide — Best Text Per Team Member

One best sourceable text per person. Each passage gives the model a genuinely distinct voice — no two sound remotely alike.

#### The Sovereign

| Person | Source Text | Passage & Notes |
|--------|-----------|-----------------|
| **Walter Lippmann** | *"Today and Tomorrow"* column, Herald Tribune, October 1947 | His first column after the Truman Doctrine speech. Opens cold with a geopolitical thesis, no throat-clearing. Library of Congress Lippmann archive. |
| **Anne Applebaum** | *"History Will Judge the Complicit"*, The Atlantic, June 2020 | Trim the opening three paragraphs — two men confronted with the same circumstances who took dramatically different paths. Historical parallel as lede is pure Sovereign register. |
| **George Orwell** | *"Politics and the English Language"* (1946) | The six rules section at the end: *"Never use a long word where a short one will do…"* Public domain. The most teachable prose-clarity specimen in the English language. |
| **John le Carré** | *"The United States of America Has Gone Mad"*, The Times (London), January 15, 2003 | His only major newspaper essay — a geopolitical broadside against the Iraq War. Pure prose, no fiction scaffolding. Trim paragraphs 2–4. |
| **Barbara Tuchman** | *The Guns of August* (1962), Chapter 1 "A Funeral" | Opening describing the nine kings riding behind Edward VII's coffin. Three paragraphs, ~150 words, an entire geopolitical era compressed into a procession. |
| **Ted Sorensen** | JFK's Inaugural Address, January 20, 1961 | Middle section from *"Let every nation know…"* to *"ask what you can do for your country."* Public domain. ~200 words. Every sentence is a lesson in institutional cadence. |

#### The Aspirant

| Person | Source Text | Passage & Notes |
|--------|-----------|-----------------|
| **George Monbiot** | *"The Age of Loneliness Is Killing Us"*, The Guardian, October 14, 2014 | Opens with a human, widens to a systemic argument, closes with a demand. Freely available on theguardian.com. Trim the first four paragraphs. |
| **Naomi Klein** | *The Shock Doctrine* (2007), Introduction "Blank Is Beautiful" | Opening three paragraphs. Sets up a structural argument through a single concrete case study. Captures her method better than any column. |
| **James Baldwin** | *The Fire Next Time* (1963), letter to his nephew | Opening two paragraphs beginning *"I have begun this letter five times…"* Fourteen sentences, devastatingly controlled fury. |
| **Eduardo Galeano** | *Open Veins of Latin America* (1971), prologue | The full prologue — only ~180 words. Every sentence is a compression of centuries. The whole prologue is the exemplar. |
| **Ursula K. Le Guin** | National Book Award acceptance speech, November 19, 2014 | Under 400 words total. The passage beginning *"I think hard times are coming…"* is 90 words and contains her entire worldview. Transcript widely reprinted. |
| **Svetlana Alexievich** | *Voices from Chernobyl* (1997), opening monologue | "Monologue about What Can Be Heard" — the firefighter's wife. Trim to first three paragraphs. The voice-centred method is fully on display in ~150 words. |

#### The Owner

| Person | Source Text | Passage & Notes |
|--------|-----------|-----------------|
| **Martin Wolf** | *"Why I Am Now a Keynesian"*, Financial Times, October 23, 2008 | Written at the peak of the financial crisis. Opens with a personal intellectual admission, pivots to global structural analysis. FT archive (may require subscription). |
| **Matt Levine** | *"Money Stuff"* newsletter, Bloomberg, January 27, 2021 | The GameStop issue. Opening section explaining the short squeeze through participant logic rather than moral outrage — purest specimen of his voice. |
| **Michael Lewis** | *The Big Short* (2010), prologue "Poltergeist" | First three paragraphs. Find the contrarian who saw it coming, tell the story through them. ~120 words. Perfect structural model for The Owner's features. |
| **Nassim Taleb** | *The Black Swan* (2007), prologue | The "Triplet of Opacity" section. Three named cognitive failures, presented with aphoristic precision. Makes a structural argument feel inevitable. |
| **John Kenneth Galbraith** | *The Great Crash, 1929* (1954), Chapter 1 opening | First three paragraphs. The most elegant understatement in economic writing. Dry wit immediately apparent. |
| **Gillian Tett** | *Fool's Gold* (2009), prologue | The JP Morgan derivatives team at their 1994 Boca Raton offsite. Opens like a novel, lands like a warning. The anthropological lens: describe the tribe before analysing the numbers. |

#### The Moralist

| Person | Source Text | Passage & Notes |
|--------|-----------|-----------------|
| **Peggy Noonan** | *"Welcome Back, Duke"*, Wall Street Journal, October 12, 2001 | Post-9/11 meditation on the return of masculine civic virtue. Warm, patriotic, never preachy. WSJ archive or collection *A Heart, A Cross, and a Flag.* |
| **Roger Scruton** | *"Why Beauty Matters"* (BBC, 2009), opening monologue | Widely transcribed. Or his essay *"Conservatism Means Conservation"* from *The Meaning of Conservatism*. Both show erudite, non-angry traditionalism. |
| **Charles Krauthammer** | *Things That Matter* (2013), introduction | Two-page essay arguing politics matters because without ordered society, nothing else is possible. Clean, logical, evidence-first. |
| **C.S. Lewis** | *Mere Christianity* (1952), Book 1, Ch. 1 "The Law of Human Nature" | Opening three paragraphs, beginning with the quarrelling men. Demonstrates how to make a moral argument feel like common sense. |
| **Wendell Berry** | *"It All Turns on Affection"* (2012 Jefferson Lecture, NEH) | Opening section. Full text freely available on NEH website. The passage about his uncle's farm and what "local knowledge" means — purest Berry in ~150 words. |
| **Abraham Lincoln** | Second Inaugural Address, March 4, 1865 | Final paragraph in full: *"With malice toward none, with charity for all…"* 75 words. Public domain. The ceiling for what The Moralist should aspire to. |

#### The Radical

| Person | Source Text | Passage & Notes |
|--------|-----------|-----------------|
| **I.F. Stone** | *"In a Time of Torment"* (1967), title essay | Opening section. Or *"The Killings at Kent State"* (1971). Both at ifstone.org. Trim opening four paragraphs — his method: start with the official record, expose the contradiction buried in it. |
| **Christopher Hitchens** | *"The Case Against Henry Kissinger, Part One"*, Harper's Magazine, February 2001 | Opening three paragraphs. "It will become clear… that this is written by a political opponent of Henry Kissinger. Nonetheless, I have found myself continually amazed at how much hostile and discreditable material I have felt compelled to omit." Self-positioning move: declaring bias as authority. |
| **Matt Taibbi** | *"The Great American Bubble Machine"*, Rolling Stone, July 2009 | Opening paragraph with the "vampire squid" metaphor. Beyond the famous line, the structure of the opening ~200 words — revelation, then mechanism, then named beneficiary — is the template for The Radical's investigative lede. |
| **Jonathan Swift** | *A Modest Proposal* (1729) | Opening three paragraphs in full. Public domain. The deadpan adoption of the oppressor's logic is the move. ~150 words demonstrates the full satirical method. |
| **Hunter S. Thompson** | *"He Was a Crook"*, Rolling Stone, June 16, 1994 | Obituary of Nixon. Focused, furious, funny, and surprisingly precise. Better than *Fear and Loathing* for The Radical because the anger has a clear political target. Freely available online. |
| **Roberto Saviano** | *Gomorrah* (2006), Chapter 1 "The Port" | Opening page — containers falling into the harbour and bodies spilling out. English translation (Farrar, Straus & Giroux). ~150 words is an instant exemplar of embedded, revelatory journalism. |

#### The Hedonist

| Person | Source Text | Passage & Notes |
|--------|-----------|-----------------|
| **Tom Wolfe** | *"Radical Chic: That Party at Lenny's"*, New York Magazine, June 8, 1970 | Opening three paragraphs describing Bernstein's penthouse party for the Black Panthers. Status-obsessed, vivid, devastating, and funny in the same breath. NY Magazine archive or *Radical Chic & Mau-Mauing the Flak Catchers.* |
| **Jimmy Breslin** | *"It's An Honor"*, New York Herald Tribune, November 26, 1963 | While the press corps covered the funeral choreography, Breslin interviewed the gravedigger. Opening: "Clifton Pollard was pretty sure he was going to be working on Sunday…" The entire column is ~600 words — use the first four paragraphs. Library of America website. |
| **Gay Talese** | *"Frank Sinatra Has a Cold"*, Esquire, April 1966 | Opening three paragraphs. The most famous magazine opening in American journalism. Establishes the subject's power through his absence and its effect on everyone around him. Esquire archive. |
| **Oscar Wilde** | *"The Soul of Man Under Socialism"* (1891), opening paragraph | Or the first exchange from *The Importance of Being Earnest* (1895), Act I. Both public domain. The former shows his aphoristic essay voice; the latter shows wit as dialogue — more useful for The Hedonist's editorial note register. |
| **Nora Ephron** | *Heartburn* (1983), Chapter 1 | The entire first chapter is ~180 words and stands alone: personal, funny, self-aware, hiding something devastating behind every quip. Or *"A Few Words About Breasts"* from *Crazy Salad* (1975) — same register, non-fiction. |
| **Dominick Dunne** | *"The Verdict"*, Vanity Fair, February 1995 | Account of the O.J. Simpson acquittal. Opening section — sitting in the courtroom, watching the room's reaction to the verdict. Tabloid energy with literary control. Vanity Fair archive. |

---

## Phase 3 — Gemini 3.1 + Imagen 4 Prompt Restructuring

Restructure all prompts to follow Google's official best practices. Every change below cites the specific doc it comes from.

### 3.1 Critical Parameter Fixes

These are **bugs in our current setup** based on official docs:

| Issue | Current | Fix | Source |
|-------|---------|-----|--------|
| **Temperature** | Not explicitly set (likely defaults) | **Must be 1.0 for Gemini 3.x models.** Sub-1.0 values cause looping and degraded performance. | [Prompting Strategies: Gemini 3 specific] |
| **Thinking config** | `thinking_budget=-1` (Gemini 2.5 API) | **Switch to `thinkingLevel` parameter.** Using `thinkingBudget` with Gemini 3 Pro "may result in unexpected performance." Use `high` for Pro newspapers, `medium` for Flash. | [Thinking docs: Gemini 3 section] |
| **Thought signatures** | Not explicitly handled | **Pass all signatures back in multi-turn.** Gemini 3 returns thought signatures for all part types. "Required even when set to `minimal` for Gemini Flash 3." SDK handles this automatically, but verify. | [Thinking docs: Thought Signatures] |

### 3.2 System Instruction Restructuring

**Official Gemini 3 recommendation** (from Prompting Strategies):
> "Place essential behavioral constraints, role definitions (persona), and output format requirements in the System Instruction or at the very beginning of the user prompt."

> "When providing large amounts of context, supply all the context first. Place your specific instructions or questions at the very end of the prompt."

**Current state**: Preamble (~2,400 words) + promptSuffix (~1,800 words) concatenated into system prompt. Context (WorldLedger, cluster digests) injected via template variables.

**Required changes:**

| Change | Rationale (from docs) |
|--------|----------------------|
| **Split into XML-tagged sections** | "Employ clear delimiters to separate different parts of your prompt. XML-style tags (e.g., `<context>`, `<task>`) or Markdown headings are effective." — Prompting Strategies |
| **Role statement as first line** | "Place essential behavioral constraints, personas, and output format requirements in System Instruction or at prompt beginning." — Prompting Strategies |
| **Output schema at end of system instruction** | Context first, instructions/questions at end. The JSON schema defines what we *want* — it's the "question." — Long Context docs |
| **WorldLedger synopsis stays at prefix** | "Cached content is a prefix to the prompt." / "Try putting large and common contents at the beginning." — Caching docs. Our current placement is correct for implicit caching. |
| **Add self-critique instruction** | "Before returning your final response, review your generated output against the user's original constraints." — Prompting Strategies |
| **Separate do/avoid lists** | "State your goal clearly and concisely." Positive instructions first, then avoidances. — Prompting Strategies |
| **Be precise and direct** | "Avoid unnecessary or overly persuasive language." Tighten the preamble prose. — Prompting Strategies |

**New prompt architecture:**

```
SYSTEM INSTRUCTION (passed via system_instruction config field — cached across calls):
┌─────────────────────────────────────────────────────┐
│ <role>                                               │  ← 2 sentences: who you are, modelled on what
│ <editorial_team>                                     │  ← Style anchor traditions (Phase 2)
│ <voice>                                              │  ← Persona voice rules
│ <exemplars>                                          │  ← 3 real-world article excerpts (Phase 1)
│ <lens>                                               │  ← Lens + biases + blindspots (combined)
│ <image_style>                                        │  ← Imagen prompt rules (see 3.5)
│ <rules>                                              │
│   <do> ... </do>                                     │
│   <avoid> ... </avoid>                               │
│ </rules>                                             │
│ <thinking_guidance>                                  │  ← NEW: editorial reasoning steps
│ <self_review>                                        │  ← NEW: self-critique checklist
│ <output_schema>                                      │  ← END-ANCHORED: JSON schema + field names
└─────────────────────────────────────────────────────┘

USER PROMPT (passed via contents):
┌─────────────────────────────────────────────────────┐
│ {{WORLD_LEDGER_SYNOPSIS}}                            │  ← FIRST: 90% cache discount (identical
│                                                      │    across all 6 calls — prefix-matched)
│ ─ ─ ─ ─ ─ cache boundary ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│ {{EDITORIAL_JOURNAL}}                                │  ← Per-newspaper (optional, varies)
│ {{CLUSTER_DIGESTS}}                                  │  ← Per-newspaper (different clusters)
│                                                      │
│ <task>                                               │  ← LAST: the actual instruction
│   Based on the context and clusters above, produce   │
│   today's edition. Follow all rules in your system   │
│   instruction.                                       │
│ </task>                                              │
└─────────────────────────────────────────────────────┘
```

**Key structural changes:**

1. **System instruction vs user turn split**: Currently we concatenate rules + context + data into one block. The official docs say: behavioural rules go in `system_instruction` config, context data (WorldLedger, clusters) goes in the user turn. This gives us two cache layers.

2. **WorldLedger prefix caching (90% discount)**: The WorldLedger synopsis is the first content in the user turn and is identical across all 6 newspaper calls. Vertex AI implicit caching matches shared prefixes — this gives us a 90% cost reduction on the entire WorldLedger block. Everything after it (editorial journal, cluster digests) varies per newspaper and is not cached.

3. **System instruction caching**: If passed via the `system_instruction` config field (not embedded in `contents`), the shared preamble rules are also cached. The per-newspaper promptSuffix varies, but the shared preamble does not.

### 3.3 Self-Review Block (new)

The official Gemini 3 docs recommend adding explicit self-critique. Add this to every newspaper's system instruction:

```xml
<self_review>
Before returning your final JSON, verify:
1. Every headline is ≤10 words, active voice, concrete subject
2. Every article uses field names "headline" and "body" (not "title"/"content")
3. Every in_brief item uses "headline" and "summary"
4. Article length is proportional to cluster aggregate_weight
5. No two articles cover the same story from the same angle
6. Image prompts follow the Subject + Setting + Style + Quality structure
7. All text is in English
8. The editor's note reflects your editorial persona, not a generic summary
</self_review>
```

### 3.4 Thinking Configuration

**Official guidance** (Thinking docs):

| Task complexity | Recommended level | Our mapping |
|----------------|-------------------|-------------|
| Easy (fact retrieval, classification) | `minimal` | — |
| Medium (step-by-step processing) | `medium` (default) | Flash newspapers (Aspirant, Moralist, Radical, Hedonist) |
| Hard (complex reasoning, planning) | `high` | Pro newspapers (Sovereign, Owner) + Curator |

**Changes to `generation.py`:**

```python
# BEFORE (Gemini 2.5 style):
thinking_config=types.ThinkingConfig(thinking_budget=-1)

# AFTER (Gemini 3.x style):
# Pro tier newspapers:
thinking_config=types.ThinkingConfig(thinking_level="high")
# Flash tier newspapers:
thinking_config=types.ThinkingConfig(thinking_level="medium")
```

**Add thinking guidance in system prompt** to steer what the model reasons about:

```xml
<thinking_guidance>
During your editorial reasoning, work through these steps:
1. SCAN all clusters — identify the 3-5 dominant stories by aggregate_weight
2. CHECK for cross-cluster narratives (same event, different angles → merge into one article)
3. DECIDE article count: [3-6] full articles + [4-8] In Brief items
4. ALLOCATE length proportional to weight: top clusters → 400-600 words; lower → In Brief
5. PLAN each article's angle through your editorial lens before writing
6. VERIFY every headline against the ≤10-word rule
</thinking_guidance>
```

### 3.5 Imagen Prompt Rules (official best practices)

Our current image prompts are generated by Gemini and passed to Imagen. The official Imagen docs specify a precise structure we should enforce.

**Official Imagen prompt structure** (from Imagen docs + Prompt Guide):

> Three pillars: **Subject** + **Context/Background** + **Style**

**Current issues vs official guidance:**

| Issue | Current state | Official recommendation | Fix |
|-------|--------------|------------------------|-----|
| **Max prompt length** | No limit enforced | **480 tokens max** | Add validation in generation pipeline; instruct Gemini to keep image prompts under 60 words |
| **Negative prompts** | Not used | Official feature: state unwanted elements as **plain nouns** ("wall, frame"). **Never** use "no" or "don't" — these are anti-patterns | Add `negativePrompt` field to image generation calls |
| **Quality modifiers** | Partially present in persona prompts | Always include: `"4K"`, `"HDR"`, `"professional photography"` or `"editorial illustration"` | Already in preamble — verify all personas include them |
| **Lens specificity** | Per-persona (e.g., "50mm prime") | Official table: Portraits=24-35mm, Macro=60-105mm, Sports=100-400mm, Landscapes=10-24mm | Cross-reference persona lens choices against official recommendations |
| **Text in images** | Preamble says "no text or lettering" | Official: max 25 chars, 2-3 phrases. But our "no text" rule is actually **better** for newspaper images — keep it | No change needed |
| **Prompt enhancement** | Unknown if enabled | `enhancePrompt: true` is default — LLM rewrites your prompt. For complex prompts on fast model, **disable it** | Check our Imagen API calls; if using fast model, set `enhancePrompt: false` |
| **Aspect ratio** | Not specified per article type | Official options: 1:1, 3:4, 4:3, 16:9, 9:16. Hero images should be 16:9, article images 4:3 | Add aspect ratio selection logic |
| **Person generation** | Unknown setting | `allow_adult` (default) allows adults + celebrities. Appropriate for newspaper images | Verify setting in our API calls |

**Updated Imagen prompt instruction for preamble:**

```xml
<image_style>
IMAGE PROMPT RULES (for Google Imagen):
Structure: Subject + Setting/Context + Style + Quality modifiers
- ALWAYS include: "4K", "HDR", and either "professional photography" or "editorial illustration"
- For photorealistic: specify lens type, focal length, lighting, camera angle
- For artistic: specify art movement/technique
- Keep prompts UNDER 60 words (480 token Imagen limit)
- NO text, letters, words, or watermarks in images
- Be concrete: name specific objects, materials, colours, light sources
- [Persona-specific style vocabulary follows below]
</image_style>
```

**New: Negative prompt per persona** (passed as separate API parameter, not in the image prompt itself):

| Newspaper | Negative prompt (plain nouns) |
|-----------|------------------------------|
| The Sovereign | cartoon, illustration, bright colours, casual clothing, clutter |
| The Aspirant | studio lighting, corporate setting, luxury, suits, sterile |
| The Owner | warm tones, nature, casual, rustic, handmade |
| The Moralist | neon, urban decay, abstract, cold lighting, brutalism |
| The Radical | soft focus, glamour, studio portrait, pastel, luxury |
| The Hedonist | muted colours, grey, institutional, formal, boring |

### 3.6 Few-Shot Example Rules (official best practices)

From Prompting Strategies:
> "We recommend to always include few-shot examples in your prompts. Prompts without few-shot examples are likely to be less effective."

> "Make sure that the structure and formatting of few-shot examples are the same to avoid responses with undesired formats." It is "essential to ensure consistent format across all examples, especially paying attention to XML tags, white spaces, newlines, and example splitters."

**Implementation rules:**

| Rule | Source | Implementation |
|------|--------|---------------|
| **Always include few-shot** | Prompting Strategies | 3 exemplars per newspaper in `<exemplars>` block |
| **Consistent formatting** | Prompting Strategies | All exemplars use identical XML structure with `<example>` tags and consistent whitespace |
| **Match output format** | Prompting Strategies | Exemplars must show the exact JSON field names (`"headline"`, `"body"`) |
| **Don't overfit** | Prompting Strategies | 3 exemplars max — "too many examples causes overfitting" |
| **Place after instructions, before data** | Long Context docs | `<exemplars>` block in system instruction, cluster data in user turn |

**Exemplar format (must be identical across all newspapers):**

```xml
<exemplars>
Study these for voice, rhythm, and structure. Absorb the style — do not copy.

<example type="news_report">
  <headline>Three Nations Seize River Dams in Water Wars</headline>
  <lede>Ethiopian forces secured the Blue Nile's last uncontrolled tributary on Tuesday, completing a three-month campaign that has redrawn the hydro-politics of East Africa.</lede>
  <body_excerpt>The seizure places Addis Ababa in control of 84% of Nile headwaters, a strategic position that Cairo has long warned would constitute an act of war. Downstream, Egyptian farmers report irrigation canals running at half capacity for the third consecutive month.</body_excerpt>
  <note>Observe: institutional voice, no first person, data woven into narrative, geopolitical framing.</note>
</example>

<example type="analysis">
  [Same XML structure, different content]
</example>

<example type="editorial">
  [Same XML structure, different content]
</example>
</exemplars>
```

### 3.7 Structured Output Improvements

From Structured Output docs:
> "Use the `description` field in your schema to provide clear instructions to the model about what each property represents. This is crucial for guiding the model's output."

**Current state**: We use `response_schema` for controlled JSON output, but our schema likely lacks descriptive `description` fields.

**Fix — add descriptions to every schema field:**

```python
# BEFORE:
class ArticleOutput:
    headline: str
    body: str
    clusters: list[int] | None = None
    imagePrompt: str | None = None

# AFTER (Pydantic with descriptions):
class ArticleOutput(BaseModel):
    headline: str = Field(description="Article headline. Max 10 words. Active voice, concrete subject, strong verb. No colons or semicolons.")
    body: str = Field(description="Full article text. Length proportional to cluster aggregate_weight. 400-600 words for top-weight stories, 100-200 for lower.")
    clusters: list[int] | None = Field(default=None, description="Cluster IDs this article covers. Multiple IDs if article synthesises cross-cluster themes.")
    imagePrompt: str | None = Field(default=None, description="Imagen prompt. Structure: Subject + Setting + Style + Quality. Under 60 words. No text/letters in image.")

class InBriefOutput(BaseModel):
    headline: str = Field(description="Brief item headline. Max 10 words.")
    summary: str = Field(description="2-3 sentence summary of a lower-weight story.")
    clusters: list[int] | None = Field(default=None, description="Cluster IDs covered by this brief.")

class NewspaperOutput(BaseModel):
    newspaper_name: str = Field(description="Name of this newspaper persona.")
    articles: list[ArticleOutput] = Field(description="Full articles, ordered by editorial importance (highest-weight clusters first).")
    in_brief: list[InBriefOutput] | None = Field(default=None, description="Short digest items for lower-weight clusters.")
    editors_note: str | None = Field(default=None, description="Editor's note in the newspaper's editorial voice. 2-4 sentences reflecting on today's edition.")
    frontPageImagePrompt: str | None = Field(default=None, description="Hero image prompt for the front page. Captures the dominant story's visual essence.")
```

### 3.8 Context Caching Optimisation

From Caching docs:
> "Cached content is a prefix to the prompt."
> "Try putting large and common contents at the beginning of your prompt."
> "Try to send requests with similar prefix in a short amount of time."

**Why WorldLedger is first in every prompt**: The WorldLedger synopsis is the single largest reusable block (~tens of thousands of tokens of world state). It is placed at the **start** of every user turn specifically because Vertex AI implicit caching matches on shared prefixes — all 6 newspaper calls share the same WorldLedger, so placing it first gives us a **90% token cost discount** on that entire block across all calls. This is an existing architectural decision that must be preserved. Any restructuring must keep WorldLedger as the literal first content in the user turn.

**Current state**: WorldLedger synopsis is placed at the start of every prompt. This is correct and must not change.

**Improvements:**

| Change | Rationale |
|--------|-----------|
| **Move system instruction to `system_instruction` config field** | System instructions passed via the config `system_instruction` parameter (not in `contents`) are automatically cached when identical across requests. This creates a second cache layer: system instruction cached + WorldLedger prefix cached. |
| **Ensure all 6 newspaper calls fire in rapid succession** | Implicit caching works when "similar prefix" requests arrive close together. Our pipeline already does this (parallel generation), but verify timing is tight enough. |
| **Consider explicit caching for WorldLedger** | WorldLedger exceeds the 1,024-token minimum for Flash and 4,096 minimum for Pro. Explicit caching with 1h TTL would **guarantee** the 90% discount rather than relying on implicit cache hits. |
| **WorldLedger must be literal first bytes** | No template boilerplate (`"WORLD HISTORY:\n"` header) before the synopsis content. The prefix match is byte-for-byte — any per-newspaper variation before the synopsis breaks the cache. |
| **Prompt ordering after WorldLedger** | After the cached WorldLedger prefix: Editorial Journal (optional, varies), then Cluster Digests (per-newspaper, varies), then `<task>` instruction (identical). Only the WorldLedger prefix portion is cached; the rest is per-newspaper. |

### 3.9 Token Budget Considerations

| Component | Current tokens (est.) | After changes (est.) | Delta |
|-----------|----------------------|---------------------|-------|
| System instruction (shared preamble) | ~2,400 | ~2,200 (tightened, precise) | -200 |
| System instruction (per-newspaper) | ~1,800 | ~2,800 (+ exemplars + editorial team + self-review) | +1,000 |
| Few-shot exemplars | 0 | ~450 (3 × 150 words) | +450 |
| Editorial team block | 0 | ~150 (6 anchors) | +150 |
| Self-review checklist | 0 | ~100 | +100 |
| Thinking guidance | 0 | ~100 | +100 |
| Schema descriptions | ~200 | ~400 (added Field descriptions) | +200 |
| **Total per newspaper** | **~4,400** | **~6,200** | **+1,800** |

**Impact**: +1,800 tokens per newspaper. Against the ~800K total token budget this is 0.2% per newspaper, 1.4% total across all 6. The shared system instruction is cached (implicit or explicit), so the real per-call cost increase is only the per-newspaper delta (~1,000 tokens).

### 3.10 Anti-Patterns to Fix (from official docs)

| Anti-pattern | Where we might have it | Fix |
|-------------|----------------------|-----|
| **Temperature < 1.0** | generation.py config | Set `temperature=1.0` explicitly |
| **`thinkingBudget` with Gemini 3** | generation.py thinking config | Switch to `thinkingLevel` |
| **Putting instructions before context in long prompts** | Current prompt template mixes rules and data | Move all data (WorldLedger, clusters) to user turn; rules stay in system instruction |
| **Inconsistent few-shot formatting** | N/A (we don't have few-shots yet) | Use identical XML structure for all exemplars |
| **No `description` fields in response schema** | output_schemas.py | Add Pydantic `Field(description=...)` to every field |
| **Imagen: no negative prompts** | Image generation calls | Add per-persona negative prompts |
| **Imagen: no prompt length limit** | Preamble image rules | Add 60-word / 480-token instruction |
| **Imagen: no aspect ratio selection** | Image generation calls | 16:9 for hero images, 4:3 for article images |
| **Vague/persuasive language in prompts** | Some preamble sections | Tighten to precise, direct instructions |

---

## Phase 4 — Implementation Plan

### Step 1: Source exemplar articles (manual curation)
- [ ] For each of the 6 newspapers, find 3 real published articles that match the target voice
- [ ] Trim each article to ~150 words: headline + lede + 1-2 body paragraphs
- [ ] Verify copyright/fair-use compliance (short excerpts for style reference in non-public prompts = fair use)
- [ ] Store raw exemplars in `data/exemplars/` as individual `.md` files (one per newspaper)

### Step 2: Update `personas.json` structure
- [ ] Add new fields to persona schema:
  - `editorialTeam`: array of `{ role, styleAnchor, tradition }` objects
  - `exemplars`: array of `{ type, headline, excerpt, sourceNote }` objects
  - `thinkingGuidance`: string (tier-specific thinking instructions)
  - `realWorldModel`: string (e.g., "The Economist", "The Guardian")
- [ ] Update TypeScript types in `packages/ai-personas/src/lib/personas.ts`
- [ ] Run `scripts/generate-data.mjs` to regenerate `_generated_data.ts` and `_generated_data.py`

### Step 3: Restructure prompt templates
- [ ] Refactor `promptSuffix` in `personas.json` to use the new XML-tagged structure
- [ ] Move output schema to end-anchor position in preamble
- [ ] Add `<role>`, `<editorial_team>`, `<exemplars>`, `<thinking_guidance>` sections
- [ ] Split mixed instruction lists into `<do>` / `<avoid>` blocks
- [ ] Update `packages/prompt-engine/src/lib/prompt-builder.ts` to assemble the new structure

### Step 4: Update prompt-builder
- [ ] Modify `buildNewspaperPrompt()` to interpolate new fields:
  - `{{EDITORIAL_TEAM}}` → serialized editorial team tradition block
  - `{{EXEMPLARS}}` → serialized exemplar block with study instruction
  - `{{THINKING_GUIDANCE}}` → tier-specific thinking instructions
- [ ] Add new template variables to `interpolateTemplate()` if needed
- [ ] Update `buildCuratorPrompt()` — Curator doesn't need exemplars but benefits from the XML structure

### Step 5: Test & compare
- [ ] Run a test generation with 1 newspaper (The Sovereign) using old vs new prompts
- [ ] Blind comparison: evaluate 3 articles from each version for voice consistency, headline quality, structure
- [ ] Iterate on exemplar selection and editorial team instructions based on results
- [ ] Roll out to all 6 newspapers once The Sovereign's quality is validated

### Step 6: Full rollout
- [ ] Update all 6 newspaper promptSuffixes with new structure
- [ ] Run full pipeline test (all newspapers + Curator)
- [ ] Verify output schema compliance (field names, JSON structure)
- [ ] Verify image prompt quality hasn't regressed
- [ ] Deploy to production

---

## Phase 5 — Evaluation & Iteration

### Quality metrics (manual review)

| Metric | How to evaluate | Target |
|--------|----------------|--------|
| **Voice consistency** | Does every article in a newspaper sound like it came from the same editorial team? | 9/10 articles clearly "on-brand" |
| **Headline quality** | Do headlines follow the persona's style? (Tabloid punch for Hedonist, institutional gravitas for Sovereign) | All headlines ≤10 words, stylistically distinct |
| **Lede structure** | Does the opening paragraph follow the persona's pattern? (Number-first for Owner, human-first for Aspirant) | Pattern visible in 80%+ of articles |
| **Exemplar absorption** | Does the output echo the exemplar style without copying it verbatim? | Style match without plagiarism |
| **Cross-newspaper distinction** | Can a reader tell which newspaper they're reading without seeing the name? | Blind test: 5/6 correctly identified |

### Iteration protocol
1. After each production run, sample 2 articles per newspaper (12 total)
2. Score against the metrics above
3. If a newspaper consistently underperforms on voice, swap one of its 3 exemplars for a stronger one
4. If a newspaper's editorial team tradition isn't coming through, adjust the tradition prompt wording
5. Log all changes in a `data/exemplars/CHANGELOG.md`

---

## Appendix A — Exemplar Sourcing Guide

When selecting real article excerpts, follow these criteria:

1. **Iconic, not obscure** — choose articles that define the publication's voice. Awards, high-traffic, widely-cited.
2. **Timeless, not dated** — avoid articles tied to specific ephemeral events. Choose pieces whose style transcends the news cycle.
3. **Diverse story types** — each newspaper's 3 exemplars should cover: (a) a hard news report, (b) an analysis/editorial, (c) a feature or column.
4. **Trim ruthlessly** — the model needs voice cues, not full articles. Headline + lede + 1-2 key paragraphs. ~150 words max.
5. **Annotate** — after each exemplar, add a 1-sentence note: "Observe the [specific technique] in this excerpt."

## Appendix B — Editorial Team Quick Reference

| Newspaper | Model Publication | Style Anchors (6 each) |
|-----------|------------------|----------------------|
| **The Sovereign** | The Economist | Walter Lippmann (political analysis) · Christiane Amanpour (frontline authority) · George Orwell (prose clarity) · John le Carré (geopolitical intrigue) · Barbara Tuchman (historical sweep) · Ted Sorensen (institutional eloquence) |
| **The Aspirant** | The Guardian | George Monbiot (moral urgency) · Naomi Klein (structural narrative) · James Baldwin (literary fire) · Eduardo Galeano (poetic compression) · Ursula K. Le Guin (devastating clarity) · Svetlana Alexievich (witness-centred voice) |
| **The Owner** | Financial Times | Martin Wolf (intellectual authority) · Matt Levine (accessible brilliance) · Michael Lewis (narrative craft) · Nassim Taleb (contrarian rigour) · J.K. Galbraith (elegant authority) · Gillian Tett (anthropological lens) |
| **The Moralist** | Daily Telegraph | Peggy Noonan (warm conviction) · Roger Scruton (philosophical depth) · Charles Krauthammer (logical rigour) · C.S. Lewis (accessible moral reasoning) · Wendell Berry (rooted wisdom) · Abraham Lincoln (civic eloquence) |
| **The Radical** | The Intercept | I.F. Stone (documentary rigour) · Seymour Hersh (fearless sourcing) · Hunter S. Thompson (gonzo energy) · Jonathan Swift (satirical blade) · George Carlin (systemic clarity) · Roberto Saviano (embedded exposé) |
| **The Hedonist** | Daily Mail / NY Post | Tom Wolfe (social X-ray) · Kelvin MacKenzie (tabloid instinct) · Gay Talese (literary profile) · Oscar Wilde (wicked wit) · Nora Ephron (personal-is-universal) · Dominick Dunne (high-society scandal) |

## Appendix C — Official Docs Compliance Checklist

### Gemini 3.1 Prompting (from ai.google.dev)

- [ ] Temperature explicitly set to 1.0 (mandatory for Gemini 3.x — sub-1.0 causes looping)
- [ ] `thinkingLevel` parameter used instead of `thinkingBudget` (2.5-era API)
- [ ] `thinkingLevel: "high"` for Pro newspapers, `"medium"` for Flash
- [ ] Thought signatures passed back correctly in any multi-turn calls
- [ ] XML-tagged sections (`<role>`, `<voice>`, `<exemplars>`, `<rules>`, `<output_schema>`)
- [ ] Role statement as first line of system instruction
- [ ] Output schema end-anchored in system instruction (context first, instructions last)
- [ ] All large context (WorldLedger, clusters) in user turn, not system instruction
- [ ] WorldLedger synopsis is literal first content in user turn (cache-prefix requirement)
- [ ] Self-review checklist added (`<self_review>` block)
- [ ] 3 few-shot exemplars per newspaper with identical XML formatting
- [ ] Do/avoid rules separated into `<do>` and `<avoid>` subsections
- [ ] `description` fields on every property in response JSON schema
- [ ] Preamble prose tightened — precise and direct, no persuasive language
- [ ] Explicit caching considered for shared system instruction (TTL 24h)

### Imagen 4 Image Generation (from cloud.google.com/vertex-ai)

- [ ] Prompt structure: Subject + Context/Background + Style + Quality modifiers
- [ ] Prompt length enforced: under 60 words / 480 tokens
- [ ] Quality modifiers always present: "4K", "HDR", "professional photography"
- [ ] Per-persona negative prompts added as plain nouns (no "no"/"don't")
- [ ] Aspect ratio selection: 16:9 for hero images, 4:3 for article images
- [ ] `enhancePrompt` setting verified (disable for fast model + complex prompts)
- [ ] `personGeneration: "allow_adult"` verified
- [ ] Lens/focal length cross-referenced against official table per subject type
- [ ] No text/letters in image prompts (our existing rule — confirmed correct)
- [ ] SynthID watermarking enabled (default `addWatermark: true`)
