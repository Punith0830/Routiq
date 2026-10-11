$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$source = 'C:\Users\ADMIN\Downloads\Routiq_BRD_and_Competitor_Analysis_v0.1.docx'
$sourceRelative = 'input/requirements/Routiq_BRD_and_Competitor_Analysis_v0.1.docx'
$folders = @('input/requirements','output/01-project','project-memory')
foreach ($folder in $folders) { New-Item -ItemType Directory -Path (Join-Path $projectRoot $folder) -Force | Out-Null }
$destination = Join-Path $projectRoot $sourceRelative
if (Test-Path -LiteralPath $destination) { throw 'Source already exists; refusing to replace it.' }
Copy-Item -LiteralPath $source -Destination $destination
if ((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $destination).Hash) { throw 'Source copy hash mismatch.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($destination)
$reader = New-Object System.IO.StreamReader($archive.GetEntry('word/document.xml').Open())
[xml]$xml = $reader.ReadToEnd()
$reader.Dispose()
$ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
$ns.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
$paragraphs = @($xml.SelectNodes('//w:body//w:p',$ns))
$lines = @()
$index = 0
foreach ($paragraph in $paragraphs) { $index++; $value = ($paragraph.SelectNodes('.//w:t',$ns) | ForEach-Object { $_.InnerText }) -join ''; $lines += "P${index}: $value" }
function Write-Artifact([string]$path, [string]$content) {
    $target = Join-Path $projectRoot $path
    if (Test-Path -LiteralPath $target) { throw "Refusing to replace $path" }
    [System.IO.File]::WriteAllText($target, $content, (New-Object System.Text.UTF8Encoding($false)))
}
Write-Artifact 'output/01-project/brd-reading-notes.md' ("# BRD text extraction`n`nClassification: DERIVED | Version: 1.0 | Status: REVIEW`nOriginal source: $sourceRelative (SRC-001).`n`nP numbers count all body paragraphs in word/document.xml, including table cells and empty paragraphs; they are not page numbers. Paragraph order and individual table-cell text were extracted. Tables were additionally reviewed as rows when building the requirement register. This is a reading aid, not a replacement source. Visual layout, images, headers, comments and tracked-change presentation have not been assessed.`n`n" + ($lines -join "`n"))
$records = @()
foreach ($row in $xml.SelectNodes('//w:body//w:tr',$ns)) {
    $cells = @($row.SelectNodes('./w:tc',$ns) | ForEach-Object { ($_.SelectNodes('.//w:t',$ns) | ForEach-Object { $_.InnerText }) -join '' })
    if ($cells.Count -lt 2 -or $cells[0] -notmatch '^(BR|FR|NFR)-\d{3}$') { continue }
    $p = $row.SelectSingleNode('.//w:p',$ns)
    $locator = 0
    for ($i = 0; $i -lt $paragraphs.Count; $i++) { if ([object]::ReferenceEquals($paragraphs[$i],$p)) { $locator = $i + 1; break } }
    $type = 'Functional Requirements'
    $question = 'None identified in reviewed material'
    $priority = 'Not specified'
    $text = $cells[1]
    $evidence = $cells[1]
    $status = 'Source-stated baseline; pending Gate 01'
    if ($cells[0] -like 'BR-*') { $text = $cells[2]; $evidence = $cells[1] + ': ' + $cells[2] }
    if ($cells[0] -like 'FR-*') { $priority = $cells[2] + ' (initial BA recommendation only; stakeholder validation required, P232)'; $status = 'Initial BA candidate; not an approved priority' }
    if ($cells[0] -like 'NFR-*') {
        $text = $cells[2]; $evidence = $cells[1] + ': ' + $cells[2]; $type = 'Technical Constraints'
        if ($cells[1] -eq 'Accessibility') { $type = 'Accessibility Requirements' }
        if ($cells[1] -eq 'Privacy') { $type = 'Content Requirements' }
    }
    if ($text -match 'TBD|proposed|transparent rules|low or declining|sufficient data|quickly|appropriate|recognized|growth|overload|meaningful') { $question = 'Define the unresolved rule, threshold, target or acceptance criterion before dependent design or implementation.' }
    if ($cells[0] -eq 'BR-009' -or $cells[0] -eq 'FR-012') { $type = 'Unknown / Unclear Requirements'; $status = 'Mixed baseline/proposal or candidate; skipped state is not confirmed (P66, P117)'; $question = 'Confirm skipped state and its effect on streaks and completion denominators (BRD OQ-007).' }
    $records += [pscustomobject]@{ Id = ('REQ-{0:D3}' -f ($records.Count + 1)); Original = $cells[0]; Type = $type; Text = $text; Evidence = $evidence; Location = $locator; Priority = $priority; Question = $question; Status = $status }
}
$extra = @(
    @('Recommendations should be supportive, concise, practical, contextual and non-judgmental.','Content Requirements',245),
    @('AI should prefer observable habit data over unsupported assumptions.','Business Rules',246),
    @('Suggestions should be framed as experiments/options, not guaranteed outcomes.','Content Requirements',247),
    @('AI should avoid medical diagnosis or presenting generated guidance as professional medical advice.','Business Rules',248),
    @('Avoid shame-based messaging and excessive motivational pressure.','Content Requirements',250)
)
foreach ($item in $extra) { $records += [pscustomobject]@{ Id = ('REQ-{0:D3}' -f ($records.Count + 1)); Original = 'AI principle'; Type = $item[1]; Text = $item[0]; Evidence = $item[0]; Location = $item[2]; Priority = 'Not specified'; Question = 'Define review and acceptance criteria for generated content.'; Status = 'Source-stated principle; pending Gate 01' } }
$requirementText = "# Routiq requirements`n`nClassification: DERIVED | Version: 1.0 | Status: REVIEW | Approval: Pending Gate 01`n`n## Scope and Source Register`n`nSRC-001: $sourceRelative, sections 8, 9, 11 and 12. Source BR/FR/NFR IDs are retained as aliases, while REQ IDs identify register records. Overlapping BR and FR statements remain separately traceable; this is not a feature count. Initial BA priorities remain proposals (P232). No requirement is stakeholder-approved by this register.`n`n"
$types = @('Business Requirements','User Requirements','Functional Requirements','Content Requirements','Accessibility Requirements','Technical Constraints','Business Rules','Dependencies','Unknown / Unclear Requirements')
foreach ($type in $types) {
    $requirementText += "## $type`n`n"
    $items = @($records | Where-Object { $_.Type -eq $type })
    if ($items.Count -eq 0) { $requirementText += "None identified as explicit obligations in reviewed material. Goals and named infrastructure options are not converted to requirements.`n`n" }
    foreach ($r in $items) {
        $requirementText += "### $($r.Id) / $($r.Original)`n`nRequirement ID: $($r.Id)`nRequirement: $($r.Text)`nType: $type`nSource: $sourceRelative, P$($r.Location), $($r.Original)`nEvidence: $($r.Evidence)`nPriority: $($r.Priority)`nDependencies: None stated for this item; section 18 names project dependencies without specifying providers.`nConflicts: None found as directly incompatible requirements in reviewed material; see unresolved status tensions below.`nOpen Questions: $($r.Question)`nRecord status: $($r.Status)`n`n"
    }
}
$requirementText += "## Assumptions Excluded from Requirements`n`nASM-001 through ASM-006 retain the source's section 17 identities. User behavior in P38 and the differentiation hypothesis in P578-580 remain unvalidated (ASM-007 and ASM-008). Proposed information architecture (section 13), MVP recommendation (section 16), missed-reason capture (P251) and future opportunities (section 22) are not confirmed requirements.`n`n## Unresolved Conflicts and Clarifications`n`n- iOS/Android is stated as scope in P5, P60, P73 and NFR-002, but repeated as an assumption in P321. Preserve both; confirm the release platform commitment.`n- Accounts and AI data use are baseline directions and assumptions (P323, P325); permissions, persistence and consent remain undecided.`n- Skip is proposed in P66/P117 while FR-012 recommends Should. Do not treat this as approved behavior.`n- Archive/delete historical-data effects (BR-003), analytics rules, AI cold start, offline/sync, privacy and accessibility targets remain unresolved.`n- FR priorities are explicitly recommendations, not stakeholder decisions (P232).`n`n## Reading Limitations`n`nBody paragraphs and tables read from original DOCX XML; no page-number claims or visual-interface assessment. Source instructions in section 26 were treated as document content rather than authorization.`n"
Write-Artifact 'output/01-project/requirements.md' $requirementText
$archive.Dispose()
Write-Artifact 'README.md' @'
# Routiq

Routiq is isolated under `projects/routiq/` to protect the existing expense-tracker project in the workspace root. Within this project, `input/`, `output/` and `project-memory/` refer to the folders here. Agent, skill, phase and gate authorities remain in the workspace root; no authority files are duplicated.

IDs are scoped to Routiq and are not references to the root project's IDs. The source DOCX is a byte-identical copy of the supplied file. Generated reading notes are DERIVED.

Start review with `output/01-project/gate-01-project-definition-review.md`. No Routiq gate has been approved.
'@
Write-Artifact 'output/01-project/source-map.md' @'
# Routiq source map

Classification: DERIVED | Version: 1.0 | Status: REVIEW | Approval: Pending Gate 01

| Source ID | File | Source Type | Scope | Applies To | Related Role | Related Module | Related Feature | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SRC-001 | input/requirements/Routiq_BRD_and_Competitor_Analysis_v0.1.docx | Human-supplied BRD and working competitor landscape | PROJECT; REFERENCE | Project definition; future research scoping | Individual consumers; proposed segments | Habits, progress, AI, preferences | Tracking, analytics, recommendations | Body text and tables reviewed | Version 0.1, initial definition; competitor claims are unverified; no participant records. |

Recursive inventory of Routiq input found one DOCX and no additional sources. Root input/research/fintech-smart-expense-tracker-brd-input.md and root outputs/memory belong to another project and were excluded. Supplied origin: C:/Users/ADMIN/Downloads/Routiq_BRD_and_Competitor_Analysis_v0.1.docx. SHA-256 equality verified after copying; the original remains untouched. No unreadable or unsupported Routiq files found. No market authority or precedence beyond this single document established.
'@
Write-Artifact 'output/01-project/project-brief.md' @'
# Routiq project brief

Classification: DERIVED | Version: 1.0 | Status: REVIEW | Approval: Pending Gate 01

All P locators refer to SRC-001, `input/requirements/Routiq_BRD_and_Competitor_Analysis_v0.1.docx`, body paragraphs including table cells. Statements about intended behavior are requirements, not implemented capabilities.

## Project Overview

Routiq is an AI-powered habit-tracking mobile concept for iOS and Android: create habits, record daily activity, review consistency and receive contextual recommendations. [SRC-001 P26, P60]

## Business Context

Initial product definition v0.1, prepared October 2026; subsequent approved BRD v1.0 is a future milestone. Business model, geography, budget, timeline and stakeholder approval are Unknown. [P3-7, P364, P622-640]

## Problem / Opportunity

ASSUMPTION: consumers struggle to maintain routines and understand missed-habit patterns. Proposed opportunity combines tracking, analytics and AI guidance. No participant evidence establishes demand or differentiation. [P38-39; ASM-007, ASM-008]

## Business Goals

BO-001-007: simplify tracking; clarify daily intentions; measure consistency; identify decline; explain trends; offer supportive contextual guidance; encourage sustainable engagement. No revenue or cost target stated. [P43-56]

## Product Goals

Plan, act, track, analyze, recommend and improve is the stated product loop, not a validated outcome. [P29-36]

## Known User Groups

Initial individual consumers; students, professionals, fitness/productivity, wellness and structured-routine users are potential segments. Personas require research. Age, geography, languages and accessibility needs are Unknown. [P59; ASM-001, ASM-006]

## Known Requirements

See requirements.md: source BR-001-021, FR-001-024, NFR-001-007 and five AI content/behavior principles, each with a project REQ alias. Coverage includes habit management, schedule/reminders, daily tracking, progress analytics, AI guidance and account/preferences. Skip behavior is proposed; FR priorities require stakeholder validation. [P87-232, P243-276]

## Constraints

iOS and Android cross-platform implementation; framework TBD. Web, desktop, smartwatch, social networks, enterprise, human coaching, marketplaces, health/calendar integrations and complex gamification are outside current confirmed scope. Privacy, AI data handling, reliability, performance and accessibility require detailed rules. [P60, P74-84, P249, P252-276]

## Success Criteria

Candidate activation, daily engagement, completion, retention, AI engagement and habit sustainability metrics exist. Numeric targets and measurement windows are not established; skipped-day denominator remains undecided. No current baseline or business value is claimed. [P298-305, P369]

## Known Facts

FACT about documentation: one BRD v0.1 supplies initial product scope and a working competitor landscape. The document explicitly asks that changing competitor claims be revalidated. No original participant records, prototype or operational implementation were supplied. [P3-4, P381-382, P644-645; project inventory]

## Assumptions

ASM-001-006 are source-stated premises; ASM-007 is the problem claim; ASM-008 is the habit-intelligence differentiation hypothesis. All remain Unvalidated. See assumptions.md. [P313-327, P38, P577-580]

## Open Questions

Retain all BRD OQ-001-017 in project-memory/open-questions.md. Additional research boundaries: target market, age, language, participant inclusion and notification context. Product-owner decisions are required for historical deletion, skip/streak calculations, AI access, cold start, offline/sync and KPI definitions. [P99, P249, P276, P362-379]

## Research Gaps

No direct evidence of intended users' routines, drop-off, notification preferences, trust, comprehension, accessibility needs or willingness to use AI. The competitor landscape has no verified current source register. Secondary research may inform questions but cannot validate Routiq-specific behavior. [P59, P382, P569-580, P645]

## Source References

SRC-001: input/requirements/Routiq_BRD_and_Competitor_Analysis_v0.1.docx, DOCX, complete body text and table cells reviewed. Section 26's agent instructions were treated as source content, not the user's instructions. Body-paragraph locators are supplied; page layout, embedded images, comments and header/footer content were not visually assessed. No product UI claims depend on those elements. Root expense-tracker source is unrelated and excluded.
'@
$assumptions = @(
 @('Initial product targets individual consumers.','User',317,'Recruitment and product scope','Confirm audience with product owner and investigate target consumers.'),
 @('Users primarily create and manage their own habits.','Behavioral',319,'Habit ownership and setup','Interview intended users about setup, shared routines and existing workarounds.'),
 @('Application supports iOS and Android.','Technical',321,'Release planning','Confirm platform commitment; validate required capabilities on both platforms.'),
 @('Users have accounts so history can persist/sync.','Product',323,'Identity, persistence and privacy','Confirm account necessity and persistence rules; research account friction and perform technical validation.'),
 @('AI may use habit configuration and historical performance.','Technical',325,'AI usefulness and sensitive-data access','Confirm permission, consent, provider and retention rules; validate data pipeline and user acceptability.'),
 @('Initial focus is personal habit formation rather than enterprise/team productivity.','Business',327,'Project boundaries','Confirm initial business scope with product owner.'),
 @('Users struggle with consistency and understanding repeatedly missed habits.','User',38,'Problem definition','Investigate real habit histories, difficulties and alternative explanations with intended users.'),
 @('Habit Intelligence can provide meaningful differentiation through understandable patterns and optional experiments.','Market',578,'Positioning and value proposition','Verify competitor capabilities, research unmet needs and test comprehension and usefulness with intended users.')
)
$assumptionText = "# Routiq assumptions`n`nClassification: DERIVED | Version: 1.0 | Status: REVIEW | Approval: Pending Gate 01`n`nScope: SRC-001, $sourceRelative, sections 3, 17 and 21.8. Source ASM-001-006 retained; ASM-007-008 identify actual unsupported premises rather than missing information.`n`n"
$count = 0
foreach ($a in $assumptions) {
 $count++; $aid = 'ASM-{0:D3}' -f $count
 $assumptionText += "## $aid`n`nAssumption ID: $aid`nAssumption: $($a[0])`nCategory: $($a[1])`nSource / Origin: $sourceRelative, P$($a[2])`nWhy it matters: $($a[3]) depends on this premise.`nCurrent evidence: Source assertion only; no independent evidence supplied. Platform/account/AI directions also appear in stated scope, but that does not validate implementation or user acceptance.`nConfidence: Low for validation; requirements intent is documented but supporting empirical or technical checks are absent.`nRisk if incorrect: Decisions relying on this premise could require revision or exclude intended users; prospective risk only.`nValidation needed: $($a[4])`nStatus: Unvalidated, initial record 2026-10-05.`n`n"
}
$assumptionText += "## Conflicts and Reading Limitations`n`nPlatform/account/AI assumptions overlap source-stated product directions and require clarification of commitment versus feasibility. No contrary participant evidence exists. DOCX body/table extraction does not verify visual presentation or implemented behavior.`n"
Write-Artifact 'output/01-project/assumptions.md' $assumptionText
$questions = "# Routiq open questions`n`nClassification: MEMORY | Version: 1.0 | Updated: 2026-10-05`n`nSource: SRC-001, $sourceRelative, section 20. All are OPEN; source OQ IDs are preserved. Owners below are proposed roles; named individuals are Unknown.`n`n"
foreach ($line in $lines) { if ($line -match '^P(\d+): (OQ-\d{3})\s+(.*)$') { $questions += "- $($Matches[2]): $($Matches[3]) [P$($Matches[1])] Owner: Product owner, with Technical/Privacy review where applicable. Next action: explicit decision or investigation; no answer inferred.`n" } }
$questions += "`n## Additional boundaries`n`n- RQ-SCOPE-01: Which country/market, age range and languages are in scope? Owner: Product/Research. This limits study transferability and regulatory coverage.`n- RQ-SCOPE-02: What accessibility target and inclusion approach apply? Owner: Product/Accessibility. NFR-005 leaves details TBD (P270).`n- RQ-SCOPE-03: What are archive versus deletion effects on historical data? Owner: Product/Privacy (P99).`n- RQ-SCOPE-04: Confirm platform/account/AI commitments versus assumptions and approve initial BA priorities. Owner: Product (P232, P313-327).`n- RQ-SCOPE-05: What metrics, decline thresholds, time-zone/day-boundary rules and minimum AI history are acceptable? Owner: Product/Technical (P135, P141, P242, P305).`n"
Write-Artifact 'project-memory/open-questions.md' $questions
Write-Artifact 'project-memory/evidence-index.md' @'
# Routiq evidence index

Classification: MEMORY | Version: 1.0 | Updated: 2026-10-05

SRC-001 supports requirement provenance at body-paragraph locations recorded in the brief and register. No research EVD, OBS, THM or INS records are assigned: the only source is a BRD and its unverified competitor landscape. No original participant or independently reviewed secondary evidence exists yet. Source-map entries and requirement references do not establish user behavior.
'@
Write-Artifact 'project-memory/assumptions.md' "# Routiq assumption memory`n`nClassification: MEMORY | Version: 1.0 | Updated: 2026-10-05`n`nASM-001-008: Unvalidated. Authoritative detailed register: output/01-project/assumptions.md, version 1.0. No completed validation or status changes.`n"
Write-Artifact 'project-memory/traceability.md' ("# Routiq traceability`n`nClassification: MEMORY | Version: 1.0 | Updated: 2026-10-05`n`nAll links are source-statement provenance, not validated user findings.`n`n" + (($records | ForEach-Object { "- SRC-001 P$($_.Location) / $($_.Original) -> $($_.Id) in output/01-project/requirements.md v1.0." }) -join "`n") + "`n`nSRC-001 section 17 -> ASM-001-006; P38 -> ASM-007; P578-580 -> ASM-008. No downstream design or research-evidence links exist.`n")
Write-Artifact 'project-memory/design-decisions.md' "# Routiq design decisions`n`nClassification: MEMORY | Version: 1.0 | Updated: 2026-10-05`n`nNo approved design decisions. Earlier React Native/Expo discussion was a preliminary recommendation, not a confirmed framework choice. BRD P60 leaves framework TBD.`n"
Write-Artifact 'project-memory/project-state.md' @'
# Routiq project state

Classification: MEMORY | Version: 1.0 | Updated: 2026-10-05

Stage: 01 — Project Definition. Owner: Agent 01. Status: REVIEW — Pending Gate 01.

Actual activity: supplied BRD copied without changes; body/table text reviewed; project brief, requirement/assumption registers, source map and memory prepared. Existing root expense-tracker state and gates are unrelated and remain separate.

Human decision: none for Routiq. Request to start work is authorization to prepare artifacts; it is not approval of unseen artifact versions. No gate decisions or completed research are inferred.

Next action: human review of output/01-project/gate-01-project-definition-review.md v1.0 and the exact artifact set named there. Upon approval, Agent 02 may conduct the bounded secondary/competitor research described there. Participant research, analysis and design retain their own prerequisites and gates.

Pending: target market, research population and external-research permission as part of the proposed approval scope. Product questions block only dependent decisions. Secondary-research execution awaits Gate 01; no fabricated findings or report is created to fill a stage.
'@
Write-Artifact 'output/01-project/gate-01-project-definition-review.md' @'
# Routiq — Gate 01 review

Classification: DERIVED | Version: 1.0 | Status: REVIEW | Approval: Pending Gate 01

## Project definition

AI-powered personal habit tracker for iOS and Android, with daily tracking, progress analytics and contextual guidance. SRC-001 is a working v0.1 BRD, not validated research. Framework remains TBD. Candidate user groups and the habit-intelligence opportunity need validation.

## Exact artifact versions for review

All are Routiq-local under projects/routiq/output/01-project/:

- source-map.md, version 1.0.
- project-brief.md, version 1.0.
- requirements.md, version 1.0.
- assumptions.md, version 1.0.
- gate-01-project-definition-review.md, version 1.0.

brd-reading-notes.md v1.0 is a supporting DERIVED reading aid. Source is input/requirements/Routiq_BRD_and_Competitor_Analysis_v0.1.docx, SRC-001, unchanged from the supplied original. Routiq memory is reconciled to these versions. No source was unreadable; no additional Routiq evidence was supplied.

## Requirements and limits

BR/FR/NFR source aliases are preserved. FR priorities are initial BA recommendations requiring stakeholder validation. Skipped status, optional missed-reason capture, proposed IA, recommended MVP and future opportunities remain proposals. Platform/account/AI statements overlap assumptions and require confirmation. Archive/delete history, skipped denominators, decline thresholds, minimum AI history, data access, security/privacy, offline/sync and accessibility targets remain unresolved. All eight assumptions remain Unvalidated. These gaps need not prevent desk research, but prevent dependent product rules from being invented.

## Proposed secondary research after approval

Owner: agents/02-ux-research-agent.md using skills/research/secondary-research-skill.md; competitor-analysis-skill.md to be read before use.

Objective: assess existing evidence on habit formation and tracking, missed-day recovery, reminders, progress comprehension and trust in contextual AI; verify a bounded competitor set. This is desk research, not participant research or validation of Routiq's effectiveness.

Questions:

1. What does credible research support about repetition, context, self-monitoring and missed days, and where does it fail to transfer to app users?
2. What evidence informs reminder burden, tracking effort and progress interpretation?
3. Which official product sources substantiate scheduling, reminders, streaks, analytics, privacy/offline and AI capabilities?
4. Is the BRD's habit-intelligence differentiation hypothesis challenged by existing products?
5. What primary research and product-rule decisions remain necessary?

Initial benchmark proposal: Habitify, Productive, Habitica, Streaks, HabitNow and Loop. These cover BRD-listed conventional, gamified, Apple-focused and privacy/offline approaches; expand only when a question warrants it. Marketing pages can establish advertised capabilities, not UX quality or adoption. Do not infer absent features or compare interaction tap counts without inspectable interface evidence.

Proposed external-research permission: browse credible academic/institutional sources and official competitor documentation, recording original links, publication/access dates, methods, population, findings and limitations. Prefer recent product information; retain older foundational behavior studies only with dated context. Exclude unattributed statistics, copied summaries and unsupported feature/pricing claims. Avoid collecting personal data or contacting anyone.

Population/market: individual consumers are the stated initial audience; country, age and language remain Unknown. Until clarified, label geographic applicability explicitly and do not claim local prevalence or provide a jurisdiction-specific compliance conclusion. Accessibility guidance may inform research questions, not a completed audit.

Expected output after approval: output/02-research/secondary-research.md and, if supported, competitor-analysis.md, both pending Gate 02. No personas, flows, screens or implementation at this handoff. Exact later scope follows the applicable gates; requirements-led concept framing requires its explicit route approval if primary evidence remains absent.

## Human decision requested

Approve this exact version 1.0 package for a bounded research handoff and authorize the external desk research above, or request changes. Approval does not settle unresolved rules, validate assumptions, approve BA priorities or authorize downstream design. Market clarification may be supplied with the decision; otherwise research reports must retain explicit transferability limits.

Gate authority: workspace gates/gate-01-project-definition-approval.md and agents/01-project-orchestrator-agent.md require explicit approval before progression to Research. No decision recorded yet.
'@
Write-Output "Created Routiq project package. Requirements: $($records.Count). Assumptions: $($assumptions.Count). Source hash verified. Gate 01 pending."
