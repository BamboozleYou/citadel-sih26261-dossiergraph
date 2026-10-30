# How past SIH idea-submission decks were built (SIH 2023–2025)

Compiled 2026-10-26 for SIH26261 (AICTE: AI-powered application validation, document authentication, regulatory compliance verification).

Method: I downloaded every deck listed below and extracted its text with pypdf or python-pptx. PDFs that were only images were rendered and inspected visually. Word counts per slide were computed from the extracted text. They undercount slides whose text sits inside images.

**Read this first: outcome evidence is weak.** Searches of GitHub, the web, LinkedIn/Medium, YouTube and SlideShare turned up no deck whose shortlist or win is confirmed by an official SIH results list. The finalist lists on sih.gov.in returned HTTP 403, and SIH does not publish idea decks. Each example below carries an evidence grade:

- **A**: the team itself says it was a finalist or winner, the deck comes from the team's own post or repo, and there is some corroboration such as photos or a narrative. Not officially verified.
- **B**: a third-party "winners" collection labels the deck a winner. The team, institution and source are unknown. Unverified, and the collection is a lead-in to a paid "SIH Winners Vault".
- **C**: a real SIH 2025 idea deck that follows the official template. Its outcome is unknown, so it is useful only for format and density.

---

## 1. Official template: structure and rules

### 1.1 Template text (confirmed for 2024 and 2025)

Sources:
- 2024: blank official-format file `SIH2024_IDEA_Presentation_Format.pptx` in https://github.com/mohitjoping/SIH-ppt-references (repo created 2024-09-08, during the 2024 cycle).
- 2025: `SIH2025-IDEA-Presentation-Format (2) (1).pptx` in https://github.com/edusatyaki/SIH-Winners-PPT/tree/main/PPT. Slide 7 still has the instruction slide.
- 2026: the copies are unofficial. SlideShare "Innovative Smart India Hackathon 2026 Idea Submission Template" (https://www.slideshare.net/slideshow/innovative-smart-india-hackathon-2026-idea-submission-template-for-software-hardware-solutions/289256695) and a Google Slides copy (https://docs.google.com/presentation/d/1gPowH1jbmcuv3vksVzNv9dee5pHujWWc/htmlpresent) have the same six sections and the same instruction slide. **I could not open the template on sih.gov.in (HTTP 403).** Check the downloaded template against the portal or your SPOC.

The placeholder guidance printed on each slide, verbatim from the 2024 file (2025 is identical):

| # | Slide header | Guidance printed on the slide |
|---|---|---|
| 1 | TITLE PAGE / "SMART INDIA HACKATHON 2024" | Problem Statement ID –, Problem Statement Title-, Theme-, PS Category- Software/Hardware, Team ID-, Team Name (Registered on portal) |
| 2 | IDEA TITLE | "Proposed Solution (Describe your Idea/Solution/Prototype)"; "Detailed explanation of the proposed solution"; "How it addresses the problem"; "Innovation and uniqueness of the solution" |
| 3 | TECHNICAL APPROACH | "Technologies to be used (e.g. programming languages, frameworks, hardware)"; "Methodology and process for implementation (Flow Charts/Images/ working prototype)" |
| 4 | FEASIBILITY AND VIABILITY | "Analysis of the feasibility of the idea"; "Potential challenges and risks"; "Strategies for overcoming these challenges" |
| 5 | IMPACT AND BENEFITS | "Potential impact on the target audience"; "Benefits of the solution (social, economic, environmental, etc.)" |
| 6 | RESEARCH AND REFERENCES | "Details / Links of the reference and research work" |
| 7 | IMPORTANT INSTRUCTIONS (to be deleted before upload) | see below |

The instruction slide, verbatim from the 2024 and 2025 files:
> Please ensure below pointers are met while submitting the Idea PPT:
> - Kindly keep the maximum slides limit up to six (6). ( Including the title slide)
> - Try to avoid paragraphs and post your idea in points /diagrams / Infographics /pictures
> - Keep your explanation precise and easy to understand
> - Idea should be unique and novel.
> - You can only use provided template for making the PPT without changing the idea details pointers (mentioned in previous slides).
> - You need to save the file in PDF and upload the same on portal. No PPT, Word Doc or any other format will be supported.
>
> Note - You can delete this slide (Important Pointers) when you upload the details of your idea on SIH portal.

Template visuals, seen in every 2024 and 2025 deck examined:
- **Title slide:** large "SMART INDIA HACKATHON 202X" heading, the bulleted fields, and the SIH brain-lightbulb inside a grey hexagon graphic on the right.
- **Content slides:**
  - SIH logo and "SMART INDIA HACKATHON 202X" wordmark at top-right.
  - An oval at top-left holding the team name ("Your Team Name" placeholder).
  - Slide title centred in a serif caps font (e.g. "TECHNICAL APPROACH").
  - A **solid blue footer bar** reading "@SIH Idea submission- Template", with the slide number at bottom-right.
- **Correction to the brief:** the coloured bar is a footer, not a header. Many teams keep the "@SIH Idea submission- Template" footer text. Some replace it with their team name, e.g. NeXora: "@SIH Idea submission - NeXora".

### 1.2 The 2023 template was different

Evidence:
- the "SIH 2023" deck in the Aadiii00 collection (Nyay Sathi, SIH1283);
- the SIH 2023 deck "SIH ppt (applications added).pptx" in the mohitjoping repo (Team TECH NATIVES, NTRO, SIH1456).

The 2023 format had these slides:
- "Team Details & Problem Statement": a table with Ministry/Organization, PS Code, PS Title, Team Name, Team Leader, Institute Code (AISHE), Institute Name and Theme.
- "Idea/Approach Details", spread over 2–3 slides with tech stack, use-case diagram and process flow, plus "Show stoppers".
- "Team Member Details": name, branch, stream and year for each member.

The six-section Title / Idea / Technical / Feasibility / Impact / References template appears from **2024**. Do not use 2023 decks as a model for the 2026 layout. They are still useful for content ideas.

### 1.3 How strictly the six-slide rule is applied (inference)

The self-reported 2024 finalist deck (Blue Screen of Death, Example 1) has **7 pages**, because its Technical Approach runs over two slides. It is also missing the Team ID field. It was still shortlisted according to the team. One example cannot show how strictly the rule is applied. Keep to six slides: it costs you nothing.

### 1.4 Third-party "2026 template" claims to ignore

Reskilll (https://blogs.reskilll.com/sih-2026-ppt-template-exact-format-slides-evaluators-score/) offers:
- a **10-slide** structure;
- scoring weights: Problem understanding 20%, Innovation 25%, Feasibility 20%, Impact 20%, Presentation 15%;
- "2–3 minutes per submission".

The post cites no sources and contradicts the official six-slide rule. The TechDoodles "SIH 2026 Playbook" in the Aadiii00 repo also proposes 9 slides. Treat both as unofficial.

---

## 2. Example decks (14)

Per-slide word counts below are for slides 1–6.

### Grade A: outcome claimed by the team, deck from the team

**Example 1: Team "Blue Screen of Death" (28002), SIH 2024, SIH1672 "Develop a ML Model based solution to refine CAPTCHA" (Smart Automation, Software)**
- **Outcome:** finalist ("selected for SIH 2024 finals"), self-reported. The team did not attend because of exams. Source: dev.to post https://dev.to/macroandmicro/behind-the-scenes-key-takeaways-from-our-smart-india-hackathon-2024-experience-5glc
- **Deck:** https://drive.google.com/file/d/1mSeNQ9RN582e8nKPD3-QyeqRfEo-VnTY/view (7 pages).
- **Words per page:** 37 / 180 / 42 / 25 / 231 / 55 / 47.
- **Slide-by-slide:**
  - **Title:** fields filled; team ID shown in brackets after the team name.
  - **Idea (180 words):** two columns. Left, "Detailed explanation" with 4 bullets of 20–30 words. Right, "How it addresses the problem" (2 bullets) and "Innovation and uniqueness" (2 bullets, including "No existing open-source solution offers similar CAPTCHA refinement"). The bottom third is a **horizontal tree diagram** of the four detection channels (behaviour analysis, device fingerprinting, IP/GeoLoc, request header), each leading to a method and an outcome.
  - **Technical Approach, part 1:** tech stack as a **categorised text list** (Frontend / Backend / Model Building / Additionals, 4–8 one-word items each) next to a detailed **methodology flowchart** (UIDAI frontend → JS script → bot-detector backend → ML model → cache/DB, with data sources such as Project Honey Pot).
  - **Technical Approach, part 2:** a full-slide **icon architecture diagram** (Frontend, Load Balancer, Backend, Cookies, User, Request Header, IP Tracking, ML/AI, BOT Detector, Cache/DB).
  - **Feasibility (231 words, the densest slide):** two columns. Left, "Analysis of feasibility": 1. Technical (2 bullets), 2. Practical (4 bullets, which honestly admit "accuracy depends on the quality and quantity of training data"). Right, "Potential challenges and risks" (3 bullets), then "Strategies for overcoming" (4 bold-labelled bullets of about 25 words, each mapped to a risk).
  - **Impact:** two short lists (4 + 6 bullets of 2–5 words). No numbers and no named stakeholders. This is the weakest slide.
  - **References:** 7 hyperlinked items, all **datasets and tools** (Project Honey Pot, BeCAPTCHA Mouse Benchmark, HuMIdb, CSIC Kaggle, CreepJS, Brotector) plus one named paper.
- **Prototype screenshot:** none. Diagrams only.
- **Takeaway:** the strong parts are the specific technical design and the risk-to-mitigation mapping. A finalist got through with a thin Impact slide.

**Example 2: Team "Ourobonics" (Galgotias University), SIH 2025, PS 25117 "Student Innovation: Swadeshi for Atmanirbhar Bharat – Robotics and Drones" (Hardware)**
- **Outcome:** winner of the Hardware Edition (₹75,000), self-reported in the repo README with photos of the trophy and cheque. Repo: https://github.com/Naveenmehta121/TEAM-OUROBONICS---SIH2025-WINNERS. The deck is `ourobonics_SIH2025.pptx`.
- **Caveat:** this is a hardware deck, and the repo was created in Sept 2026, after the event.
- **Words per slide (text inside image groups is missed):** title / 230 / 95 / ~0 / 220 / 45.
- **Slide-by-slide:**
  - **Idea:** a problem block of 3 bullets with a cost number ("Existing humanoids are too expensive (₹20–60 lakh)"), "We propose Kritrim – Modular Snap-and-Fit Humanoid", target environments, and a closing uniqueness paragraph that ties in Digital India / Atmanirbhar Bharat.
  - **Technical Approach:** 4 capability bullets, "Technologies used" (hardware list with specific servo models, software, APIs), and a **YouTube preview link** to a working prototype.
  - **Feasibility:** entirely graphical (grouped shapes and images), so no text could be extracted.
  - **Impact:** 5 bold headers with a 1–2 sentence explanation each, a quantified claim ("70–80% cheaper than global humanoids"), and a list of 6 deployment sectors.
  - **References:** 4 paper or market-report titles, without links.
- **Takeaway:** the winning hardware deck carried a **prototype video link**, a cost comparison in rupees and a modularity "unique angle". It is not dense with text.

**Example 3: Team "404:FOUND", SIH 2023, PS1415 (Ministry of Defence, video motion amplification)**
- **Outcome:** winner, self-reported in the README. Repo: https://github.com/Ashwin-Baduni/video-based-motion-amplification-and-vibration-analysis-SIH-2023, file `SampleOutputs/Final PPT.pdf`.
- **This is a finale/demo deck (15 slides), not the idea submission.** Its structure is Objective, End product (web-app screenshot), Tech stack, Solution description (paragraph), Approach (4 steps), 5 output screenshots (FFT, heatmap, magnified, time series, 3D plot), Future directions, Novelty, Conclusion.
- Included only to show that, by the finale, decks lean on **output screenshots**. It does not show the idea-round format.

### Grade B: labelled "winner" by a third-party collection, unverified

Source: https://github.com/Aadiii00/SIH-Winners-PPt-and-Sources (261 stars, created 2026-08-25; copied into https://github.com/edusatyaki/SIH-Winners-PPT and https://github.com/dheeraj0204/SIH-Winners-PPt-and-Sources).
- The README links to a paid "SIH Winners Vault" (superprofile.bio). It names no teams or institutions and gives no outcome evidence.
- All 7 PDFs are image-only, and several are screenshots taken in a document viewer (download and AI buttons are visible).
- The file names say "Winner". Nothing confirms it, and two 2025 decks are for the **same PS** (SIH25071), which cannot both have won.

**Example 4: Nyay Sathi (team unnamed), SIH 2023, SIH1283 "Digital Assistant for Legal Awareness and Designing a KYC framework" (Ministry of Law and Justice), file `SIH_2023_Presentation_Clean.pdf`**
- Uses the 2023 format.
- **Idea & Approach:** 2 justified paragraphs (about 130 words) beside a **phone mockup screenshot** of the app.
- **Use-case diagram:** UML-style, with actors (User / Admin / Lawyer / Authorities), modules, an encryption layer, the web server, the DB and IPFS.
- **Technology Stack:** logos with captions (Next.js, WebAuthn biometric, OpenAI, Indian Kanoon / e-courts APIs, Blockchain-IPFS, MySQL) next to a **6-box icon process flow**.
- **Additional Features:** a 7-icon grid, each with one sentence (biometric auth, multilingual, blockchain document storage, case summariser and so on).
- **Team members:** a blank table.
- **Relevance:** close to your domain (legal documents, KYC, blockchain document integrity).

**Example 5: AKY "greenSort AI", SIH 2024, SIH1592 Student Innovation (Clean & Green), file `SIH_2024_AKY_GreenSort_AI.pdf`**
- **Idea:** title and tagline; a 5-bullet ">" list of about 30 words each, with key terms in bold (CNN with transfer learning, "2000+ pre-trained images", cashback, path optimisation). A right-hand sidebar has "Problem Resolution" (1 bullet) and "Unique Value Propositions" (3 bold bullets).
- **Technical Approach:** three **logo strips on black bars** (MERN + Tailwind; PyTorch/TF/Keras/Python/OpenCV; Maps/AWS/Django) and a **box-and-arrow workflow** of 15 nodes.
- **Feasibility:** two columns. Technical / Operational / Economic feasibility (3 bullets of about 30 words), and "Potential Challenges, Risks and its overcomings" as Challenge → **Solution** pairs (technical, operational, economic).
- Slides 5–6 were not legible at render resolution. The pattern matches the other decks.

**Example 6: "Cannon Crew" (Team ID 27113), SIH 2024, SIH1686 "Automating GPO Customization and Deployment Based on CIS Guidelines" (Smart Education theme), file `SIH_2024_Cannon_Crew_High_Quality.pdf`**
- **Idea:** three blue "tab" columns: "Detailed Explanation", "How It Addresses the Problem", "Innovation and Uniqueness". Each has 5–6 bullets with a bold lead-in and 10–20 words, some lead-ins hyperlinked (CIS guidelines, RAG pipeline). Dense, at roughly 300 words.
- **Technical Approach:** a large **tree flowchart** of the agent pipeline (PDF upload → Ollama local LLM → FAISS → PowerShell script generator → executor → audit), a boxed architecture/components list (7 bullets), and a row of **8 tech logos** (FastAPI, Windows, Mistral, MongoDB, Electron, Ollama, Chroma, PowerShell).
- **Feasibility:** three rounded bands. "Analysis of the feasibility" (2 bold-label bullets), "Potential challenges" (2), "Strategies to overcome" (2), plus decorative icons.
- **Impact:** two columns. Impact (3 bullets) and Benefits (5 bullets), plus a **"For instance: User story"** box (a scenario at a government agency, with impact and benefits). That box is a nice device.
- **References:** 8 **hyperlinked keywords** only (RAG, Ollama, Mistral, CIS Benchmark, PowerShell module, Air-gapped systems, SSH Tunneling, GPO Overview), with no titles. Weak.
- **Relevance:** **government compliance automation**, which is closest in spirit to "regulatory compliance verification".

**Example 7: "Innovators", SIH 2024, SIH1605 "Women Safety Analytics" (Miscellaneous), file `SIH_2024_Innovators_High_Quality.pdf`**
- **Idea:** one long underlined paragraph and three coloured boxes ("#Detailed problem proposed", "#How it addresses problem", "#Innovation and uniqueness"), each with 3–4 fragments, above a strip of 3 stock illustrations.
- **Technical:** 3 coloured category boxes (language, framework, hardware) and a mind-map from APP to emergency features.
- **Feasibility:** three coloured label blocks (Feasibility / Challenges and Risks / Strategies), each with 3 **2–4-word** bullets, plus a large stock image.
- **Impact:** a 3-column stakeholder table (For women / For law enforcement / For urban communities) and a chevron graphic (social, economic, environmental).
- **References:** 3 raw URLs (India Today, Scribd, a project-report site).
- **Assessment:** visually busy and thin on content. If this really won, the bar for slides is lower than the bar for the idea. I would not copy it.

**Example 8: "Techbyte", SIH 2024, SIH1587 Student Innovation, Disaster Management, "AlertMe", file `SIH_2024_Techbyte_High_Quality.pdf`**
- **Idea:** objective, "Our Solution", and 5 bold-italic feature bullets of about 15 words, beside a **hub-and-spoke diagram**.
- **Technical:** a 5-bullet stack list and a **4-step numbered chevron** (stack → DB/maps → prototype design → MVP testing).
- **Feasibility:** two boxed columns, Feasibility (Technical / Operational) and **Viability** (Market / Social / Partnerships & Funding). There is no explicit risk/mitigation section.
- **Impact:** 3 arrow banners on each side (Impact vs Benefits).
- **References:** 7 URLs including chatgpt.com, github.com and figma.com, plus a Figma prototype link. This is weak, except for NDMA Sachet and FEMA.

**Example 9: "GeoGuards", SIH 2025, SIH25071 "AI-Based Rockfall Prediction and Alert System for Open-Pit Mines" (Disaster Management), file `SIH_2025_GeoGuards_High_Quality.pdf`**
- **Idea:** a 1-sentence proposed solution; "Addressing the problem" (2 bullets) in a rounded box; a central **open-pit mine diagram**; "Solution overview" as 3 pill boxes.
- **Technical:** a **5-step coloured pipeline** (simulate data → preprocess → train → backend → SMS/email alerts) that branches into **Low / Medium / High risk** with mock sensor charts.
- **Feasibility:** 4 pill boxes (time-feasible, scalable, low cost, modular), and a **pie chart of rockfall causes**, each with a mitigation callout.
- **Impact:** an "Impacts" box of 5 short bullets; Social / Economic / Environmental bubbles; 2 figures borrowed from papers (3D geological model).
- **References:** 2 research notes, 1 MDPI link, and "Kaggle/GitHub datasets" and "SIH PS documents". Weak.

**Example 10: "Tech Pioneers" / RockVision AI, SIH 2025, SIH25071 (same PS as GeoGuards), file `SIH_2025_Tech_Pioneers_High_Quality.pdf`**
- **Idea:** 7 bold-labelled ">" features of 15–30 words, beside an architecture sketch.
- **Technical:** 5 category lines (Frontend / Backend / AI-ML / API services / Cloud) listing about 40 technologies, with a **20-logo grid**. This over-lists technologies.
- **Feasibility:** 12 numbered points over Feasibility (Technical / Economic / Operational), Viability, Business potential (subscription and tiered pricing), Challenges, Solutions and Use cases, in about 8pt text, plus a green "supporting facts" panel. Very dense.
- **Impact:** a benefits tree (Social / Technological / Economic / Environmental); stakeholder bullets (mining executives, miners and engineers, regulators, local communities); **numbers** ("70–90% reduction in rockfall-related incidents", "15–60 minutes advance notice", "$2–5 million annually").
- **References:** generic domain links (sciencedirect.com, researchgate.net and so on), plus a **comparison table with competitors** (RockVision vs MineGUARD, RockWatch Pro, SafeMine 360, GeoAlert, 9 features with ✓/✗).

### Grade C: real SIH 2025 idea decks in the official template, outcome unknown

From https://github.com/edusatyaki/SIH-Winners-PPT/tree/main/PPT. The repo title says "Winners", but these files carry no outcome claim at all. They were picked for how close their domain is to SIH26261.

**Example 11: "Health Hacker" / Sehat Sathi (AI medical report analyser), SIH25131 Student Innovation (MedTech), file `Sehat Sathi.pdf`**
- **Domain:** OCR and document understanding, so closest technically to SIH26261.
- **Words per slide:** 41 / 171 / 62 / 205 / 116 / 145.
- **Idea:** a 2×2 grid of bordered boxes (Problem Definition, Idea/Solution, Problem Resolution, Unique Value Proposition), each with 3 "❖" bullets of 12–20 words, plus a horizontal **7-icon system flow** (Upload → OCR → Parameter Extraction → Range Comparison → Explanation → Voice Narration → Chatbot).
- **Technical:** "Technology used" as 7 "Layer: tool (reason)" lines, and a **vertical icon workflow** that names the tool used at each step.
- **Feasibility:** a full-width "Feasibility assessment" box (Technical / Operational / Economic / Social, one line each), then **two columns: "Potential challenges" (5) → arrow → "Mitigation strategies" (5)**, matched one to one. This is the clearest example of the two-column convention.
- **Impact:** an Impacts column (5 dimension boxes) and a Benefits 2×2 grid. No numbers.
- **References:** a **table** with S.No, Title, Publisher, Year and Key insight (MedlinePlus, AACC, ICMR-NIN, Tesseract, OpenCV, Flutter docs).

**Example 12: "Automation Coders", SIH25185 "AI-Powered DPR Quality Assessment and Risk Prediction System for MDoNER" (Smart Automation), file `SIH25185.pptx`**
- **Domain:** a government document-assessment AI, the most similar PS.
- **Idea:** 1 paragraph, plus "Why do we need it?" as 5 "problem → consequence" arrow lines.
- **Technical:** 4 numbered layers (Data extraction: PyPDF2/pdfplumber, Camelot, Tesseract, OpenCV; NLP: spaCy NER, BERT/RoBERTa; Dashboard; Backend), with 13 logos.
- **Slide 4:** a "Work Flow" diagram, which pushes Feasibility to slide 5 and **Impact to slide 6**. There is no References slide. This **breaks the template order** (weak).
- **Feasibility:** 2 points of feasibility, 2 challenges and 3 strategies.

**Example 13: "Niyati" / TransitMind, SIH25081 "AI-Driven Train Induction Planning & Scheduling for KMRL" (Smart Automation), file `Team Niyati Presentation.pdf`**
- **Words per slide:** 40 / 114 / 67 / 100 / 74 / 61. This is a clean, mid-density model deck.
- **Idea:** Proposed Solution (3 bullets), Detailed Explanation (3), Innovation & Uniqueness (3), each 10–25 words, beside a **data sources → central engine → outputs** diagram.
- **Technical:** a 5-step numbered methodology (Ingestion → Rule engine → Optimisation → Decision-support UI → Learning loop), a **full-width layered architecture diagram** (Data ingestion | Processing & intelligence | Frontend), and a **vertical logo column** (8 logos).
- **Feasibility:** Feasibility (3), Challenges & Risks (3) and Strategies (3), each strategy answering a specific risk ("Phase-wise integration (start with CSV/JSON → later APIs)", "manual override panel", "Explainable AI → builds operator trust").
- **Impact:** target impact (2) and Benefits by dimension (Operational / Economic / Social / Environmental / Scalability), with one number (">99.5% punctuality") and a flow graphic.
- **References:** 5 items with URLs (KMRL annual reports, IBM Maximo API docs, OR-Tools, a Nature paper, the Singapore MRT case).

**Further Grade C decks examined (same repo), noted briefly:**
- **Veritas / Aegis-AI, SIH25159 phishing detection** (`SIH 2025 Idea Presentation Format.pdf`):
  - Feasibility is a **two-column table**, "Potential Challenges | Our Mitigation Strategy", with 4 rows.
  - References list 5 **titled papers with venue and year** (arXiv 2024, IEEE 2021, MDPI 2024, USENIX Security 2022). This is the best academic citation style seen.
- **HerbariumX, SIH25027 blockchain herb traceability** (`HerbariumX-SIH2025.pptx`):
  - Idea has 6 "Component: function" bullets.
  - Feasibility (231 words) covers Technical / Operational / Economic, then 5 risks and 5 grouped strategies.
  - Impact uses stakeholder sub-heads (Consumers, Farmers, Manufacturers, Regulators).
  - References are grouped by topic, each with a URL.
- **Ednext / "Vidya" AI-agentic ERP, SIH25103** (`SIH2025-IDEA-Presentation-Format (2) (1).pptx`): education domain, with blockchain-secured marksheets. Uses "Label: sentence" bullets throughout, and cites Samarth ERP documentation.
  - **They uploaded 7 slides, including the instruction slide, which they forgot to delete. Do not do this.**
- **COMET / FloatChat, SIH25040** (`COMET_SIH25.pdf`):
  - At about 160–200 words per slide, it is the heaviest deck.
  - Many unsupported superlatives ("Zero Competition", "Fortune-500 Architecture", "95% users excluded").
  - References are well formatted (Lewis et al. 2020 RAG NeurIPS, Roemmich et al. 2019).
- **PashuVision, SIH25004** (`SIH presentation.pptx.pdf`):
  - Feasibility is a **two-column "Challenges & Risks | Strategies" table** with 4 rows.
  - References are IEEE-style [1]–[7] with government portals and access dates. However, refs [1], [2] and [6] look like **fabricated** entries ("J. A. Doe, M. B. Smith…", "L. E. Brown and F. G. Johnson"), which look like AI hallucinations. This is a risk to avoid.
- **Weak decks for contrast:**
  - Techbirds, SIH25048 (`SIH2025 Idea PPT.pptx`): one 193-word paragraph slide; Technical and Feasibility slides have no text; references say "Mostly research-work is done by using Perplexity and Chatgpt".
  - BUG-0, SIH25033 (`SIH2025-IDEA-Presentation-Format.pptx`): Feasibility and Impact slides are empty apart from images.
  - Neural Ninjas, SIH25033: references are a Google Form, a YouTube channel and a Python bootcamp.
  - NeuralNexus, SIH25012: lists "ChatGPT", "Copilot" and "Replit" as references.

**Domain note:** I found no idea deck for a document-verification or credential-authentication PS (for example SIH25029, "Authenticity Validator for Academia") with any outcome evidence. GitHub has code-only repos for SIH25029 (Krishna945-crtl/certicheck-sih25029, Shreeyoga/certauth, Kumarutkarsh9470/SIH25029_LastMinute), with no decks. "KrupaliGadhavi/smart-india-hackathon-dashboard" claims to be an "SIH 2024 Winner" for a DRDO document-verification system, but it holds only a Power BI dashboard PDF. Searches for SIH1729 and SIH1730 found nothing.

---

## 3. Patterns across the decks

### 3.1 Text density (measured)

Words per slide across 24 SIH 2025 template decks and the 2024 finalist:

| Slide | Typical range | Median-ish | Strong examples |
|---|---|---|---|
| 1 Title | 30–60 | ~40 | Fields only, plus a product name in the title bar (e.g. "Float Chat – …", "KRISHAK SETU") |
| 2 Idea | 80–200 | ~120 | Niyati 114, Sehat Sathi 171, finalist 180 |
| 3 Technical | 40–170 (low because diagrams dominate) | ~70 | Niyati 67 plus a large diagram |
| 4 Feasibility | 90–230 | ~110 | **The densest slide.** Finalist 231, HerbariumX 231, Sehat Sathi 205 |
| 5 Impact | 50–180 | ~100 | |
| 6 References | 30–180 | ~70 | |

- **Bullets:** 3–7 per block, usually with a **bold "Label:" lead-in** followed by 8–25 words.
- **Paragraphs:** rare in the better decks. The template asks for points.
- **Font size:** body text is often 10–12pt on the Feasibility slide in dense decks. The Tech Pioneers deck goes to about 8pt, which is too small.

### 3.2 Slide-by-slide pattern of the better decks

1. **Title.** Every field filled, with the PS title copied exactly. Many teams add a product name as the slide headline (e.g. "TransitMind", "Sehat Sathi"). The team name sits in the top-left oval on every slide.
2. **Idea.** The slide header is replaced with **product name + one-line tagline**. Then come 3–4 labelled blocks that mirror the template prompts exactly:
   - Proposed solution (1–2 sentences);
   - Detailed explanation / key components (3–6 bullets);
   - How it addresses the problem (2–4 bullets, often "pain → fix");
   - Innovation & uniqueness (2–4 bullets).
   
   About 60% of the better decks also put a **small concept diagram** here (a pipeline strip, hub-and-spoke, or data sources → engine → outputs). Some add a 1–3-bullet "Problem" block first.
3. **Technical approach.** Two components appear almost every time:
   - **(a) the tech stack**, either as a categorised list (Frontend / Backend / AI-ML / DB / Cloud) or as a **logo grid/strip** (6–20 logos);
   - **(b) a methodology flowchart or architecture diagram**, usually the largest visual in the deck.
   
   The better decks also add a **numbered 4–6-step methodology** ("1. Ingest → 2. Rule engine → …"). Few show a prototype screenshot at idea stage. When they do, it is a phone mockup or UI frame (Nyay Sathi 2023; BusKr 2025 app screens), or a prototype or demo link (Ourobonics YouTube, TACHYON Vercel link, Techbyte Figma).
4. **Feasibility & viability.** The near-universal layout is:
   - a top "Feasibility analysis" block split into **Technical / Operational / Economic** (sometimes Social, Legal-Ethical or Market), one line each;
   - then **"Potential Challenges & Risks" and "Strategies to Overcome"** side by side or as a two-column table, with **3–5 rows mapped one to one**.
   
   Viability (market, business model, funding) appears in about a third of the decks, usually as a separate small block.
5. **Impact & benefits.** Usually two parts:
   - "Potential impact on the target audience", with **stakeholder sub-heads** (users, officials/regulators, institutions, society);
   - "Benefits", by **Social / Economic / Environmental / Technological** (sometimes Operational).
   
   Numbers appear in roughly a third of the decks, and they are mostly unsourced ("95% time reduction", "20–40% higher profit"). A **Before vs After table** (TACHYON, TechTrek) and a **user-story scenario box** (Cannon Crew) are effective devices.
6. **Research & references.** 4–8 items. The better decks name a title, a source or venue, a year and a URL, and group items by topic (research papers / government data or portals / tools and standards). Several decks put a **competitor comparison table** (✓/✗ matrix) here or on Impact (Tech Pioneers, Neocoders, AttenAI). That uses the slide to show novelty.

### 3.3 Visual conventions (confirmed from the decks)

- Template chrome is kept: SIH logo top-right, team-name oval top-left, **blue footer bar** with "@SIH Idea submission- Template" and the page number.
- **Logo rows or grids** on the Technical slide (AKY, Cannon Crew, Tech Pioneers, Niyati, SIH25185).
- **Flowcharts**: horizontal icon pipelines on the Idea slide, and box-and-arrow or layered architecture diagrams on the Technical slide.
- **Coloured label tabs or bands** for the template sub-prompts (Cannon Crew's blue tabs, Innovators' coloured blocks, Sehat Sathi's bordered boxes).
- **Two-column Challenges → Strategies**, often with an arrow between the columns (Sehat Sathi, PashuVision, Veritas, the finalist deck).
- Benefit trees or chevrons by dimension; stakeholder columns.
- Hyperlinks shown underlined in blue.

### 3.4 What weak decks get wrong (observed)

1. Slides left empty or image-only where the template asks for content (Techbirds, BUG-0, Ourobonics feasibility as text).
2. Instruction slide not deleted, giving 7 slides (Ednext). The template slide order also gets broken (SIH25185: no References slide, Impact moved to slide 6).
3. References that are not references: ChatGPT, Perplexity, Copilot, github.com, figma.com, YouTube channels, Google Forms, or bare keywords without titles.
4. **Made-up citations** (PashuVision's "J. A. Doe…" entries). An evaluator who checks one will discount the whole deck.
5. Superlatives and unsupported numbers ("Zero Competition", "Fortune-500 architecture", "99% accuracy", "6-month ROI") with no source or method.
6. Tech-stack overload: 40 technologies and 20 logos with no explanation of why each is there (Tech Pioneers).
7. Feasibility written as categories without content ("Technical feasibility / Financial feasibility / Social feasibility" as 2-word bullets: Innovators), or risks listed with no mitigation (NeuralNexus).
8. Long paragraphs on the Idea slide despite "avoid paragraphs".
9. Stock or clip-art imagery in place of a system diagram (Innovators).
10. Impact as generic adjectives ("Better UX", "Improved efficiency") with no named stakeholder and no metric. This shows up even in the 2024 finalist, so it is common but not disqualifying.

### 3.5 Inference: what drives selection

These points are my inference, not confirmed scoring criteria:
- The idea-to-PS fit and how specific the technical design is (the finalist's detection channels, Cannon Crew's air-gapped local-LLM angle) seem to matter more than polish. The decks labelled winners range from polished (Cannon Crew) to amateur (Innovators).
- No official SIH rubric for the idea round was found. The Reskilll weights are unsourced.

---

## 4. Recommended level of detail per slide for SIH26261

**Slide 1, Title (about 40 words).**
- Fill every template field: PS ID SIH26261, the exact PS title, Theme, "Software", Team ID, and team name as registered.
- Add the product name and a one-line tagline in the headline.
- Keep the hexagon graphic and the template chrome.

**Slide 2, Idea Title (110–170 words plus one small diagram).**
- Header: product name and an 8–12-word tagline.
- Use 4 labelled blocks that mirror the template prompts:
  - Proposed solution: 1–2 sentences.
  - Detailed explanation: 4–5 bullets of the form "**Module:** what it does", 10–20 words each. For example: application intake and validation; document authenticity (OCR, tamper/forgery checks, QR/DigiLocker cross-verification); regulatory compliance rule engine against AICTE norms; reviewer dashboard with explainability.
  - How it addresses the problem: 3 "pain → fix" bullets.
  - Innovation & uniqueness: 3 bullets, each naming a specific mechanism, not an adjective.
- Bottom strip: a 5–7-icon horizontal pipeline (Upload → Extract → Verify → Check compliance → Score/flag → Human review).

**Slide 3, Technical Approach (60–110 words; diagrams take about 60% of the area).**
- Left: a categorised stack (Frontend / Backend / AI-ML / OCR & document forensics / Data & integration / Security / Deployment), 2–4 named tools per line, each with a short reason where it isn't obvious. Optionally a strip of 8–12 logos. Do not go over 12 logos.
- Right or full width: a **layered architecture diagram** (Data sources: applicant uploads, DigiLocker/issuer APIs, AICTE norms database → processing and AI services → decision layer with human-in-the-loop → dashboards and audit log).
- A numbered 5-step methodology.
- If a working prototype exists, add one UI screenshot or a demo link. The template prompt explicitly allows "working prototype".

**Slide 4, Feasibility & Viability (130–200 words, the densest slide; keep body text at 11pt or larger).**
- Top band: Technical / Operational / Economic (plus Legal/Privacy, which matters for document data). Write one specific line each, naming the tools, datasets and integrations that make it feasible.
- Two columns, "Challenges & Risks" → "Mitigation Strategies", with **4–5 rows mapped one to one**. Use a bold risk label and 10–20 words per cell. Likely rows for this PS:
  - OCR on poor scans or regional languages;
  - forged or tampered documents that defeat simple checks;
  - false rejections of genuine applicants;
  - data privacy (DPDP Act 2023);
  - integration with legacy AICTE portals;
  - explainability for reviewers.
- Optional small Viability line: who adopts it, rollout phases, cost basis.

**Slide 5, Impact & Benefits (90–140 words).**
- Impact by **named stakeholders**: AICTE reviewers and approval committees; institutions and applicants; students and regulators.
- Benefits by Social / Economic / Operational / Governance.
- Include 2–4 **quantified claims with a stated basis** (e.g. "review time per application from X days to Y", sourced or labelled "estimate"). A small Before vs After table works well.

**Slide 6, Research & References (6–10 items, about 60–120 words).**
- Group as: (a) government and regulatory sources (AICTE Approval Process Handbook, DigiLocker, DPDP Act 2023); (b) papers with authors, venue, year and URL (document forgery detection, OCR, explainable AI); (c) datasets and tools.
- Every citation must be real and checked. Never cite ChatGPT or bare homepages.
- Optionally add a small comparison table against existing systems to show novelty.

**General rules.**
- Exactly 6 slides. Delete the instruction slide. Export as PDF.
- Keep the template headers and sub-prompts as labels.
- Use bold "Label:" bullets throughout. One strong diagram on slides 2, 3 and 4.
- No unsourced superlatives.

---

## 5. Source URLs

- Official-format templates: https://github.com/mohitjoping/SIH-ppt-references (2024 template, 2024 filled sample "Final[1]" from team CODESTRIX, SIH 2023 sample from TECH NATIVES / SIH1456).
- 2025 decks: https://github.com/edusatyaki/SIH-Winners-PPT/tree/main/PPT
- "Winners" collection, unverified: https://github.com/Aadiii00/SIH-Winners-PPt-and-Sources
- Finalist deck and story: https://dev.to/macroandmicro/behind-the-scenes-key-takeaways-from-our-smart-india-hackathon-2024-experience-5glc and https://drive.google.com/file/d/1mSeNQ9RN582e8nKPD3-QyeqRfEo-VnTY/view
- Ourobonics winner deck: https://github.com/Naveenmehta121/TEAM-OUROBONICS---SIH2025-WINNERS
- 2023 winner finale deck: https://github.com/Ashwin-Baduni/video-based-motion-amplification-and-vibration-analysis-SIH-2023
- Unofficial 2026 template copies: https://www.slideshare.net/slideshow/innovative-smart-india-hackathon-2026-idea-submission-template-for-software-hardware-solutions/289256695 and https://docs.google.com/presentation/d/1gPowH1jbmcuv3vksVzNv9dee5pHujWWc/htmlpresent
- Unofficial guidance, low trust: https://blogs.reskilll.com/sih-2026-ppt-template-exact-format-slides-evaluators-score/
- Context on the selection process (5–7 teams per PS shortlisted from idea PPTs, 2024): https://srec.ac.in/coin/hackathonproject/smart-india-hackathon ; 2024 finale scale: https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/dec/doc20241211470201.pdf
- Not reachable: https://sih.gov.in (HTTP 403 to automated fetch). Confirm the 2026 template there or through your SPOC.
