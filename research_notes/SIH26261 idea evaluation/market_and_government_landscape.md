# Market and Government Landscape: AI-Enabled Document Validation and Compliance for AICTE Approval Processing

Research date: 26 Oct 2026. Items marked [BACKGROUND] are from prior knowledge and were not re-verified this session; treat them as unconfirmed.

## 1. What the AICTE approval process involves today, and what AICTE (and NAAC) already automate

### Takeaway
AICTE already runs a fully online, self-disclosure-heavy approval process under the Approval Process Handbook (APH) 2024-25 to 2026-27. That process goes from the web portal through the Scrutiny Committee, the Expert Visit Committee (offline or online), the Standing Hearing Committee and the Standing Appellate Committee, with criminal liability for fraudulent documents. I found no official announcement that AICTE uses AI or automated document forensics in scrutiny. NAAC has publicly said it will use AI to check how reliable submitted data is under binary accreditation. The regulatory framework itself may change: a Bill to replace AICTE is pending.

### Cited Findings
- The APH 2024-25 to 2026-27 is a three-year handbook. Institutions with strong performance can get approval for three years at once instead of renewing every year. BBA/BMS/BCA now fall under AICTE. — [IIRF Ranking](https://iirfranking.com/news/aicte-releases-new-approval-process-handbook-for-2024-25-to-2026-27/); [Elets](https://digitallearning.eletsonline.com/2023/12/aicte-launches-approval-process-handbook-for-2024-27/); official copy: [APH PDF (s3waas mirror)](https://cdnbbsr.s3waas.gov.in/s35938b4d054136e5d59ada6ec9c295d7a/uploads/2025/03/2025031399.pdf)
- For 2025-26 and 2026-27, existing institutions apply online on the AICTE web portal, and new institutions apply through the National Single Window System (NSWS). Universities must seek approval for all their technical programmes, and partial approval is not allowed. The 2025-26 window for existing institutions ran from 6 to 20 Nov 2024. — [AICTE Public Notice 2025-26](https://aicte.gov.in/sites/default/files/Public%20Notice%202025-26.pdf); [MAKAUT copy of notice](https://makautwb.ac.in/datas/users/0-noti_aicte_app_exist_25-26.pdf); [TeamLease RegTech, 2026-27 notice](https://www.teamleaseregtech.com/updates/article/50097/aicte-public-notice-for-approval-process-202627/)
- APH definitions: the Expert Visit Committee (EVC) verifies infrastructure "offline or online". The Standing Hearing Committee (SHC) reviews EVC reports and replies to show-cause notices. The Standing Appellate Committee (SAC) can recommend or not recommend a case, or send it back to the Scrutiny Committee or the EVC. The APH has a chapter on affidavits. If a submitted document is found to be fraudulent, a criminal case is filed against the Director/Principal and the Chairman/Secretary of the Trust. — [APH via Scribd (may be a draft)](https://www.scribd.com/document/717022331/APH-Final-1); [Indian Kanoon, AICTE Grant of Approvals guidelines 2024-27](https://indiankanoon.org/doc/163708613/); [APH copy, crescent.education](https://www.crescent.education/wp-content/uploads/2026/03/APH-Final-downloaded-on-23.12.2025.pdf)
- Extension of Approval (EoA) letters for 2025-26 and 2026-27 list "deficiencies based on Self Disclosure" that must be fixed within six months. Approval of existing institutions therefore rests mainly on self-disclosure, and enforcement comes after approval. — [VESIT EoA 2026-27](https://vesit.ves.ac.in/storage/aicte/1775193851EOA%20Report%202026-27%20(2).PDF); [SIES GST EoA 2025-26](https://siesgst.edu.in/images/compliance/EOA%20Report%2025-26.%20Final%20PDF.pdf)
- 2025-26 EoA letters require institutions that ran separate shifts to meet norms for the combined total intake. — [Shobhit University EoA 2025-26](https://www.shobhituniversity.ac.in/pdf/AICTE_2025_26.PDF)
- A parliamentary record says approvals have been given on a self-disclosure basis "with no human intervention". As early as 2013, AICTE e-governance stressed self-declaration over inspection and drew expert committees at random from a national database. — [eparlib.nic.in](https://eparlib.nic.in/bitstream/123456789/974673/1/AS104.pdf); [Rajya Sabha PQ 2013](https://rsdebate.nic.in/bitstream/123456789/621557/2/PQ_228_22032013_U2900_p230_p231.pdf)
- AICTE's own portal data reportedly lists 271 fake technical institutions. — [Shiksha](https://www.shiksha.com/engineering/articles/how-to-check-if-a-college-is-aicte-approved-blogId-242189)
- AI and AICTE: the only AICTE-AI news found was about putting AI into the curriculum, not about approvals. — [Careers360](https://news.careers360.com/aicte-integrate-artificial-intelligence-ai-in-technical-disciplines-engineering-it-management-tg-sitharam)
- NAAC: a 2024 Deccan Herald report says NAAC will use AI under binary accreditation to judge the reliability of data that HEIs submit. AI is used when data looks suspect, by gathering feedback from faculty and students, and physical visits are kept for exceptional cases. — [Deccan Herald](https://deccanherald.com/india/karnataka/naac-adopts-ai-technology-for-accreditation-process-3129355) (page returned 403 on fetch; summary comes from search snippets)
- NAAC announced binary accreditation (Accredited / Not Accredited) in Feb 2025, replacing letter grades. A consultancy says the official Binary or MBGL manuals were still not finalised as of Aug 2026. — [RAYSolute (consultancy, unverified)](https://www.raysolute.com/naac-binary-accreditation-reaccreditation.html)
- DVV (Data Validation and Verification) is NAAC's process for checking the data an HEI submits. The portal allows about 5 MB per metric. — [Digiicampus](https://digiicampus.com/?p=16843)
- The Viksit Bharat Shiksha Adhishthan (VBSA) Bill, 2025, introduced on 15 Dec 2025, would repeal the AICTE Act 1987 (along with the UGC and NCTE Acts). It sets up a commission with Regulatory, Accreditation and Standards councils. As of mid/late 2026 it is with a Joint Parliamentary Committee and has not passed. — [PRS brief](https://prsindia.org/files/bills_acts/bills_parliament/2025/Brief-VBSA_Bill_2025.pdf); [Business Standard](https://www.business-standard.com/education/news/shiksha-adhishthan-bill-single-higher-education-regulator-ugc-aicte-125121500767_1.html); [RAYSolute tracker](https://www.raysolute.com/vbsa-bill-2025-tracker.html)

### Inferences
- The real pain point is not "digitising" approval, which is already online. It is that self-disclosed documents are trusted at entry and checked only afterwards, by sampling or EVC visits. A pre-scrutiny triage tool fits this gap.
- The APH explicitly allows "online" EVC visits, so remote evidence such as geotagged photos, video and document cross-checks has a policy hook.
- If the VBSA Bill passes, approval rules will move to a new Regulatory Council. A platform with a pluggable, versioned rules engine (rather than hard-coded APH rules) carries less risk.
- NAAC's plan to use AI on data reliability gives a precedent that Indian higher-education regulators accept AI-assisted validation, provided humans stay in the loop.

### Gaps
- I could not extract the full APH text (the PDF did not parse), so I could not confirm the exact affidavit list, the document checklist (land, building plan, fire NOC, structural stability) or the scrutiny timelines.
- I found no official AICTE "approval in X days" target or AI-in-scrutiny announcement for 2025-26. Absence of evidence is not proof that nothing exists.
- One TeamLease article dates an APH issue to 6 Feb 2026, which conflicts with the Dec 2023 launch. This may be a corrigendum or addendum; I could not resolve it.
- I could not confirm the official status of NAAC's AI system or how it works.

## 2. Government verification infrastructure and API access

### Takeaway
DigiLocker, NAD/ABC and APAAR have APIs, but access is gated. You must be an approved partner (NeGD, through API Setu) with India-hosted servers, and documents are shared only with the data owner's consent. I found no public APIs for fire NOCs, land records (verified nationally) or AICTE faculty IDs. A hackathon prototype will almost certainly have to use mock connectors.

### Cited Findings
- DigiLocker requester access: the partner registers and NeGD approves at its discretion. Credentials come through the API Setu partner portal. Access needs an Indian mobile number and a server in India. There is no sandbox, so testing happens on production. The API uses OAuth 2.0 with PKCE (code verifier of 43-128 characters), and the redirect URI must match exactly. Rate limits apply. — [DigiLocker Entity Locker onboarding FAQ](https://www.digilocker.gov.in/assets/FAQ%20DL%20EL_onboarding.pdf); [Requester Entity Locker API spec (28-11-24)](https://entity.digilocker.gov.in/assets/img/Requester%20-%20Entity%20Locker%20API%20Specification_28_11_24.pdf); [Sunbird RC DigiLocker integration guide (Pull URI setup)](https://rc.sunbird.org/use/integrations/digilocker-integration)
- A third-party summary of the June 2024 onboarding procedure describes Aadhaar-OTP authentication of a nodal officer, company and tax ID checks, a DSC, multi-level approval, then quarterly usage reports and an STQC audit after go-live. — [Didit blog (secondary, not verified against official text)](https://didit.me/blog/digilocker-api/)
- Commercial KYC vendors already resell DigiLocker flows (HyperVerge DigiLocker APIs, Decentro, AuthBridge "instant checks using DigiLocker"). — [HyperVerge docs](https://documentation.hyperverge.co/api-reference/india_api/Digilocker%20APIs/); [Decentro](https://decentro.tech/resources/digilocker-apis); [AuthBridge](https://authbridge.com/blog/need-for-10th-12th-marksheet-verification-in-india-for-employers)
- NAD: institutions must register and are verified by NAD/UGC. Verifying partners (employers, banks, institutions) can view a student's record only with the student's permission. — [NAD FAQ](https://nad.digilocker.gov.in/faq)
- In 2021 AICTE told all approved institutions to upload academic award data to DigiLocker/NAD. — [AICTE-NAD circular 06/2021](https://cdn.digilocker.gov.in/nad/assets/circulars/4%20Circular_AICTE_NAD_DigiLocker_06_2021.pdf) (dated 2021)
- APAAR is a lifelong, Aadhaar-linked 12-digit learner ID under NEP/NCrF. Institutes can integrate APIs to create and verify APAAR IDs. — [IIEST ABC/APAAR notification](https://www.iiests.ac.in/assets/images/notifications/Notification_ABC_ID_Creation_2024_Admitted_UG_PG_PhD.pdf); [CAG circular](https://cag.gov.in/uploads/ae_circulars_office_orders/CircularsOfficeOrders-067af3e746cad26-61977106.pdf)
- [BACKGROUND, unverified this session] AICTE gives faculty a unique ID through its portal, which is intended to stop the same faculty member being counted at several institutions. AISHE collects institution-level data annually. e-Sign (CCA-licensed ESPs) and DSCs follow the IT Act 2000. PARIVESH handles environmental clearances (relevant for large campuses). Fire NOCs and land records are run by each state on separate portals with no common verification API.

### Inferences
- A credible design is "DigiLocker/NAD-first where consent exists, forensic analysis otherwise". Issuer-verified documents (DigiLocker-issued, QR- or DSC-signed) can be auto-trusted, so AI forensics is needed only for uploaded scans, which is where fraud happens.
- AICTE itself, as a government body, is far better placed than any startup to become a DigiLocker requester. This argues for selling to AICTE rather than to institutions.
- Faculty-ID duplication checks are useful only if AICTE shares its own faculty registry. A hackathon team can only simulate this.

### Gaps
- I could not confirm current API documentation or access rules for the AICTE faculty unique ID, AISHE, state fire NOC portals, Bhulekh/DILRMP land records, or PARIVESH.
- I could not retrieve the official DigiLocker Pull URI specification. The "Meri Pehchaan API Spec v2.4, Sept 2026" seen in one secondary source is unverified.

## 3. Commercial players (Indian KYC/regtech and global document-fraud detection)

### Takeaway
The document-tampering and OCR technology is mature and sold commercially. In India it is built for KYC, BFSI and HR background checks (IDfy, HyperVerge, AuthBridge, Surepass); globally it is built for lending (Resistant AI, Inscribe, Ocrolus). None of these players appears to offer a product for regulator-side approval of institutional dossiers (land deeds, building plans, NOCs, faculty rosters, rule compliance against a handbook). I found no evidence of these vendors being used in AICTE or education regulation.

### Cited Findings
- IDfy: extracts document data, detects tampering on ID documents, checks against databases, matches faces, and does background verification including education. It reports 60M+ verifications a month for 1,300 clients (an older version of the same profile says 25M/600). — [IndiaAI](https://indiaai.gov.in/article/idfy-deploys-ai-to-detect-fraud-and-clear-the-fog-of-deceptiveness); [Provenir marketplace](https://www.provenir.com/idfy/)
- Surepass sells a Document Forgery Detection API that it markets as covering degree certificates and transcripts. — [Surepass](https://surepass.io/?p=16458)
- AuthBridge verifies education through three routes: DigiLocker, its own database of 1B+ records, and physical verification. These are issuer- or database-based checks, not image forensics. It reports employment-verification discrepancies of 14.26% in FY24 (reported second-hand). — [AuthBridge](https://authbridge.com/blog/need-for-10th-12th-marksheet-verification-in-india-for-employers); [HackerNoon](https://hackernoon.com/fake-degrees-are-a-billion-dollar-industry-the-fix-isnt-better-background-checks)
- HyperVerge: AI identity verification, deepfake detection, face authentication, and handling for many document types. Its vendor-authored comparison page lists Signzy as a competitor. — [HyperVerge](https://hyperverge.co/blog/signzy-competitors/)
- Ocrolus integrated Resistant AI's document forensics into Ocrolus Detect (bank statements, pay stubs, W-2s). Ocrolus says about 12% of loan applications contain suspicious activity. — [The Paypers](https://thepaypers.com/fraud-and-fincrime/news/ocrolus-adds-resistant-ai-forensics-to-detect-fraud-tool)
- Inscribe uses forensic, network, semantic and perceptual models across structure, metadata and visuals, and reasons across all documents in an application. It claims 99% precision (self-reported). Resistant AI claims 500+ detectors (self-reported). — [Inscribe vs Resistant AI (vendor-biased)](https://www.inscribe.ai/fraud-detection/inscribe-vs-resistant-ai)
- Verisk Digital Media Forensics added a PDF "Version History" check that shows what changed between incremental saves. — [Verisk release notes](https://www.verisk.com/resources/release-notes/anti-fraud/version-history-for-dmf/)
- [BACKGROUND, unverified] Karza (acquired by Perfios), Bureau, Klippa and Signzy offer OCR, KYC and document-fraud APIs mainly aimed at BFSI.

### Inferences
- Novelty does not come from the forensic primitives (ELA, metadata, PDF revisions, OCR), which vendors already sell. It comes from applying them to the regulatory domain: checking a whole dossier for consistency (declared area vs building plan vs fire NOC), applying APH rules with clause citations, checking year over year, and detecting duplicates across institutions.
- A government buyer would probably prefer an on-prem, open or GoI-owned system to a foreign SaaS such as Inscribe or Resistant AI, because of data-location and procurement constraints (see section 5).

### Gaps
- I found no independent accuracy benchmarks for any vendor. All accuracy figures are self-reported.
- I could not confirm any vendor contract with AICTE, UGC, NAAC or any state technical education board.

## 4. Academic and open-source work, including prior SIH projects

### Takeaway
The research on image forgery (copy-move, splicing, ELA, CNN-based detection) and PDF structural forensics is well developed. Several open-source prototypes built specifically for SIH 2026 PS 26261 already exist, and they implement nearly the same feature set. This significantly reduces the novelty of a generic version of the idea.

### Cited Findings
- SIH 2026 PS 26261 is titled "AI-Powered Application Validation, Document Authentication and Regulatory Compliance Verification" for AICTE scrutiny. — [Nirikshan-SIH26261 repo](https://github.com/amanray10/Nirikshan-SIH26261)
- Nirikshan already implements: a checklist of required documents per application type; comparison of portal declarations with documents; 14 versioned APH rules (faculty ratio, built-up area, lease duration, fire NOC validity) with clause citations; four-level document authentication (metadata, visual forensics, DSC/QR, mock issuer registry); OCR, clause retrieval and an optional local LLM, with deterministic rules making the decisions; hashed cross-institution faculty IDs; pHash detection of recycled photos; year-over-year drift checks; evidence highlighting; an institution self-check; English/Hindi rectification notices; and fully on-prem operation. — [Nirikshan repo](https://github.com/amanray10/Nirikshan-SIH26261)
- Other public PS-26261-style repos: Drishti-AI (multi-agent, human-in-the-loop), SAKSHYA (OCR, forensics, rule-conflict detection, evidence graph, explainable audit reports), AICTE_Fraud_Detection_SIH (an earlier fraud-detection project), and SIH26262 (a workflow from SUBMITTED to SCRUTINY to EVC to SHC to LOA). At least one says all its data and registry connectors are mock. — [Drishti-AI](https://github.com/devrajpoot2903-del/Drishti-AI); [SAKSHYA](https://github.com/AKTHARHUSSAIN09/SAKSHYA-Aicte-Regulatory-Compliance-Document-Verification); [AICTE_Fraud_Detection_SIH](https://github.com/anvithspatil/AICTE_Fraud_Detection_SIH); [SIH26262](https://github.com/Tharun-Kumaran/SIH26262)
- PDF forensics: a 2025 arXiv preprint (University of Pretoria) detects tampering using PDF page objects and argues that hashes and watermarks miss non-visual and metadata changes. Practitioner signals include metadata timestamp mismatch, the number of incremental xref updates, Creator/Producer fields and signature status. — [arXiv 2507.00827](https://arxiv.org/abs/2507.00827); [Help Net Security](https://www.helpnetsecurity.com/2025/07/07/detect-pdf-tampering-forgery/); [dev.to guide](https://dev.to/iurii_rogulia/detect-pdf-tampering-programmatically-developer-guide-2ohb)
- Image forgery: recent reviews cover deep-learning copy-move detection and suggest combining classic image processing with pre-trained CNNs. — [IJSSE 2024 review](https://www.iieta.org/journals/ijsse/paper/10.18280/ijsse.140518); [MDPI Appl. Sci. 2025](https://www.mdpi.com/2076-3417/15/21/11774); [Bilad Alrafidain 2025 survey](https://bajest.bauc14.edu.iq/index.php/bajest/article/view/124)
- [BACKGROUND, unverified] Blockcerts (MIT Media Lab / Learning Machine) is an open standard for blockchain-anchored certificates. In India, DigiLocker/NAD plus issuer DSCs/QR codes do the same job without a blockchain. Perceptual hashing (pHash/dHash) is the standard method for near-duplicate image detection.

### Inferences
- For a hackathon, the baseline expectation for PS 26261 is now high: forensics, a rules engine, cross-institution duplicate checks and explainability are already common. A team needs a sharper angle to stand out, for example:
  - measured accuracy on a realistic synthetic forged-document benchmark;
  - a demonstrated DigiLocker/NAD consent flow, even using a mock built to the real spec;
  - geospatial checks on land and building, such as matching satellite or geotagged photos to survey numbers;
  - EVC remote-verification tooling;
  - a reviewer-workload or triage-scoring model;
  - a rules DSL that AICTE staff can edit when the APH changes.
- ELA is known to be noisy on recompressed scans. Claims that rely on it alone are weak, and judges with forensics knowledge may object.

### Gaps
- I did not check how many PS 26261 submissions exist in total or which ones were shortlisted.
- I found no public dataset of forged Indian institutional documents (land deeds, NOCs, building plans). Any evaluation will need synthetic data.

## 5. Law and policy: DPDP, IT Act, AI governance, data localisation

### Takeaway
The DPDP Rules 2025 were notified in Nov 2025, and most obligations take effect 18 months later (about May 2027). The MeitY AI Governance Guidelines (Nov 2025) are non-statutory and principle-based, stressing human-centricity, accountability and being "understandable by design". For a government buyer handling faculty Aadhaar, PAN and personal data, on-prem or India-hosted deployment, consent, minimisation, audit trails and human final decisions are, in practice, required to be considered at all.

### Cited Findings
- The DPDP Rules 2025 were notified on 13/14 Nov 2025 (G.S.R. 846(E)). Rules 1, 2 and 17-21 (definitions, Data Protection Board) apply immediately. Rule 4 (consent managers) applies after one year. The main fiduciary obligations (notice, consent, security safeguards, rights, children's data, cross-border transfers) apply after 18 months, about 13 May 2027. Cross-border transfer is allowed subject to government restrictions, which moves away from earlier strict localisation drafts. — [PIB document](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf); [Khaitan & Co ERGO](https://www.khaitanco.com/sites/default/files/2025-11/ERGO%20-%20Digital%20Personal%20%20Data%20Protection%20Rules%20-%2015%20November%202025.pdf); [Deccan Herald](https://www.deccanherald.com/amp/story/india%2Fcentre-notifies-dpdp-rules-implementation-planned-in-phases-spread-over-12-18-months-3798465); [S.S. Rana](https://ssrana.in/articles/meity-notifies-final-digital-personal-data-protection-rules-2025/)
- MeitY's India AI Governance Guidelines (5 Nov 2025, IndiaAI Mission) create no new AI law and rely on the IT Act, the DPDP Act, the BNS and sectoral regulators. The seven sutras are: Trust, People First (human oversight), Innovation over Restraint, Fairness and Equity, Accountability, Understandable by Design, and Safety/Resilience/Sustainability. The guidelines also set out six governance pillars and an action plan. — [Vikaspedia](https://en.vikaspedia.in/viewcontent/e-governance/digital-india/india-ai-governance-guidelines?lgn=en); [AZB & Partners](https://www.azbpartners.com/bank/meity-releases-guidelines-on-ai-governance-the-way-ahead-and-roadmap-for-ai-use-in-india/); [Mondaq](https://www.mondaq.com/india's-ai-governance-guidelines/1746072)
- DigiLocker API access already requires India-hosted servers and STQC audits, according to a secondary source. — [DigiLocker FAQ](https://www.digilocker.gov.in/assets/FAQ%20DL%20EL_onboarding.pdf); [Didit](https://didit.me/blog/digilocker-api/)
- [BACKGROUND, unverified] MeitY's cloud empanelment and GI Cloud (MeghRaj) rules and the CERT-In directions of April 2022 (6-hour incident reporting, log retention) apply to government IT systems. The IT Act 2000 recognises DSC and e-Sign signatures, which supports automated signature validation.

### Inferences
- Security and privacy are threshold requirements for a government buyer, not differentiators. A pitch should show: on-prem or India-region deployment, no external LLM APIs (or only India-hosted ones), role-based access, hashing of personal identifiers in cross-institution checks, immutable audit logs, and AI as advisory with human sign-off. These match the "People First", "Accountability" and "Understandable by Design" sutras.
- Because the DPDP obligations apply from about May 2027, a system built in 2026-27 should be designed to comply from the start.

### Gaps
- I did not verify how DPDP exemptions for State instrumentalities (Section 17) would apply to AICTE processing faculty data.
- I could not confirm any AICTE-specific data-hosting policy.

## 6. Where the real gaps are for a credible hackathon solution

### Takeaway
The gap is not "AI document verification" in general, which is commoditised commercially and already appears in multiple PS 26261 prototypes. It lies in regulator-specific integration and evidence. Specifically:
- linking documents to declarations to rules, across institutions and across years, against the current APH;
- trust levels that put issuer-verified documents first, using DigiLocker/NAD/DSC;
- remote EVC verification support;
- measured, honest accuracy with human-in-the-loop decisions.

The biggest feasibility constraint is that real registries (faculty IDs, land, fire NOCs) are not openly accessible, so prototypes rely on mocks.

### Cited Findings
- Approval relies on self-disclosure, with deficiencies fixed after approval. — [VESIT EoA 2026-27](https://vesit.ves.ac.in/storage/aicte/1775193851EOA%20Report%202026-27%20(2).PDF)
- The EVC can verify "offline or online". — [Indian Kanoon APH guidelines](https://indiankanoon.org/doc/163708613/)
- Commercial tools target KYC and lending, not regulatory dossiers. — [The Paypers](https://thepaypers.com/fraud-and-fincrime/news/ocrolus-adds-resistant-ai-forensics-to-detect-fraud-tool); [IndiaAI on IDfy](https://indiaai.gov.in/article/idfy-deploys-ai-to-detect-fraud-and-clear-the-fog-of-deceptiveness)
- Existing PS 26261 prototypes use mock registry connectors. — [Nirikshan](https://github.com/amanray10/Nirikshan-SIH26261); [search summary of the Authentiq/other repos](https://github.com/AKTHARHUSSAIN09/SAKSHYA-Aicte-Regulatory-Compliance-Document-Verification)
- NAAC is using AI for data-reliability checks, which is a regulatory precedent. — [Deccan Herald](https://deccanherald.com/india/karnataka/naac-adopts-ai-technology-for-accreditation-process-3129355)

### Inferences
- Gaps that still look credible, from most to least defensible:
  1. A cross-document consistency graph for the domain. For example, the land deed survey number should match the building plan, which should match the fire NOC address and occupancy, which should match the declared built-up area. Commercial KYC tools do not do this.
  2. Cross-institution and cross-year reuse detection: the same faculty, photos or building plans appearing at different colleges or in different years. This is valuable, but it needs AICTE-side data.
  3. Remote EVC tooling: a geotagged, timestamped capture app plus matching against declared infrastructure and satellite imagery. I saw little of this in the existing repos.
  4. A versioned rules engine that tracks APH addenda and possible VBSA-era rules.
  5. Honest evaluation: a synthetic forged-document benchmark with reported precision and recall, and a measured false-positive burden on reviewers.
- Weak or commoditised claims: "AI OCR", "ELA tamper detection", "blockchain certificates" (DigiLocker/NAD already fills this role in India), and "LLM approves applications" (this conflicts with MeitY's human-oversight principles and the APH committee structure).
- Feasibility: a working prototype is easy to build with mocks. Real deployment depends on AICTE sharing data, DigiLocker requester onboarding by AICTE, and state portal integrations. None of these are within a team's control.

### Gaps
- I could not check whether AICTE's portal vendor already includes internal validation logic, such as automated checks on intake versus faculty ratio. Such logic is likely but unconfirmed.
- I have no data on how many applications AICTE processes a year, reviewer workload, or fraud rates found in approvals. These would be needed to quantify impact.
