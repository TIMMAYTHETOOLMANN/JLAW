# Investigative Language Guide

## Purpose

This guide defines language standards for all investigative outputs produced using the JLAW platform. It applies to forensic dossiers, claim verification reports, regulatory submissions, and any draft narrative prepared from evidence in this repository.

The guide serves four goals:

1. Convert aggressive or conclusory internal draft language into defensible investigative prose.
2. Clearly separate documentary evidence from firsthand testimony, inference, and speculation.
3. Protect the credibility of whistleblower sources and reduce the risk of premature disclosure.
4. Reduce defamation and overstatement risk while preserving the full regulatory utility of the findings.

---

## Core Principle

**Describe what the evidence shows. Do not characterize what it proves.**

Investigative reporting is most powerful — and legally defensible — when it attributes findings precisely to their source and acknowledges their limits. Overstated claims invite legal challenge, damage credibility, and can obscure findings that would otherwise withstand scrutiny.

---

## Prohibited Phrases

Do not use the following phrases in any report, narrative, submission, or public communication unless the finding is supported by:

- An official agency determination (OSHA citation, EPA enforcement action, SEC enforcement order, DOJ indictment or conviction), **or**
- Direct, unambiguous documentary proof from a primary source that eliminates any inferential gap.

| Prohibited | Why It Is Problematic |
|------------|-----------------------|
| "proves fraud" | Legal conclusion. Not appropriate without adjudication or official finding. |
| "criminal conspiracy" | Alleges criminal intent. Requires proof beyond a reasonable doubt and adjudication. |
| "illegal conduct" | Legal conclusion requiring legal determination, not investigative assessment. |
| "guilty" | Verdict language. Cannot be used before adjudication. |
| "confirmed fraud" | Implies verified legal finding. Not available at the investigative stage. |
| "deliberate concealment" | Alleges specific mental state. Not supportable without direct evidence of intent. |
| "knowing misrepresentation" | Same as above. |
| "cover-up" | Implies coordinated intentional misconduct. Not appropriate without documentary proof. |
| "whistleblower proves" | Overstates the evidential weight of firsthand testimony. |
| "smoking gun" | Colloquial. Implies definitive proof. Use specific language describing what the document actually shows. |

---

## Preferred Language

### When Documentary Evidence Appears Inconsistent with a Corporate Claim

> "Records reviewed appear inconsistent with the statement that [claim]."

> "The [document type] dated [date] contains information that appears to contradict the representation made in [filing/statement]."

> "A material discrepancy appears to exist between [corporate claim] and [document reference]."

### When a Claim Requires Further Investigation

> "[Claim] raises questions that warrant independent investigation."

> "The available evidence does not yet establish [conclusion], but warrants further inquiry."

> "Independent verification through [specific records] would be required to assess this claim."

### When Describing Firsthand Testimony

> "According to a firsthand account that has not yet been independently verified, [description]."

> "A source with direct knowledge of [subject] has stated that [description]. This account has not yet been corroborated through documentary evidence."

> "[Account] represents firsthand testimony. Independent verification through [specific records] is recommended before this claim is included in any report."

### When Describing a Pattern

> "The pattern of records reviewed raises questions about [subject] that warrant further inquiry."

> "Taken together, records reviewed indicate a pattern that appears inconsistent with [corporate claim]. Independent verification is recommended."

### When Findings Are Regulatory in Nature

> "Records reviewed indicate conditions that may warrant regulatory review by [OSHA / EPA / SEC]."

> "The discrepancy between [claim] and [evidence] may be material to [agency]'s regulatory oversight of [subject]."

> "These findings have been referred to [agency] for independent assessment."

### When Evidence Is Insufficient

> "The available evidence does not yet establish [conclusion]."

> "This claim has not been independently verified and should not be included in the final report at this time."

> "Insufficient evidence currently exists to assess this claim. It has been placed on the verification hit list pending receipt of [specific records]."

---

## Evidence Type Language

Different types of evidence carry different weights and require different attributions.

### Primary Documentary Evidence (Strength 4–5)

Source documents — filed with a regulator, produced under legal process, or independently obtained — that directly address the subject matter.

> "Records obtained from [source] indicate that..."

> "The [document type] dated [date], filed with [agency], states that..."

> "Pursuant to [document reference], [factual statement]."

### Firsthand Testimony (Strength 3)

Accounts provided by individuals with direct personal knowledge.

> "A person with direct knowledge of [subject] has stated that..."

> "According to firsthand account [reference], which has not yet been independently corroborated..."

> "Firsthand testimony reviewed indicates [description]. Independent verification is recommended."

### Circumstantial Evidence (Strength 2–3)

Documents or records that suggest but do not directly establish a conclusion.

> "Records reviewed are consistent with [description], though this interpretation requires independent verification."

> "The available records are suggestive of [pattern], but do not conclusively establish [conclusion] without additional documentation."

### Inference (Strength 1–2)

Conclusions that go beyond what the evidence directly states.

> "One inference that could be drawn from these records is [description]. This interpretation is not yet supported by direct documentary evidence."

> "This conclusion is inferential and should not be included in any report without corroborating evidence."

Inferences should be clearly labeled as such and should not appear in any section of a report as if they were established facts.

---

## Specific Guidance for Common Scenarios

### Safety Claims vs. Safety Records

When corporate filings represent that a facility meets safety standards, and internal or regulatory records indicate otherwise:

**Do not write:**
> "Nike lied about safety conditions."

**Write instead:**
> "Statements in [filing type and date] representing that [safety claim] appear inconsistent with [document type] records reviewed, which indicate [specific condition]. Independent verification through OSHA inspection records and internal maintenance logs is recommended."

### ESG Disclosures vs. Operational Records

When sustainability disclosures represent environmental compliance and vendor or regulatory records indicate potential inconsistencies:

**Do not write:**
> "Nike's ESG report is fraudulent."

**Write instead:**
> "Certain representations in the [year] sustainability report regarding [subject] appear to warrant verification against underlying operational records. Records reviewed from [source] indicate [specific condition] that may be inconsistent with the disclosed [metric or claim]."

### Whistleblower Account vs. Corporate Statement

When a firsthand account conflicts with a public or regulatory statement:

**Do not write:**
> "The whistleblower proves Nike committed fraud."

**Write instead:**
> "A firsthand account reviewed indicates [description]. This account appears inconsistent with the representation made in [filing/statement]. Independent verification through [specific records] has been identified as a necessary next step before this finding is included in any final report."

---

## Drafting Checklist

Before finalizing any investigative output, confirm:

- [ ] No prohibited phrases appear in the narrative.
- [ ] All claims are attributed to a specific source document or firsthand account.
- [ ] Evidence type (documentary, testimonial, circumstantial, inferential) is clearly identified.
- [ ] Claims scored 1 in the confidence matrix have been excluded from the narrative.
- [ ] All findings requiring further verification are clearly labeled as such.
- [ ] Defamation risk has been assessed for all named individuals and entities.
- [ ] Whistleblower identity is not disclosed without consent.
- [ ] The narrative does not present unverified allegations as established facts.
- [ ] Recommended next steps (records requests, verification targets) are included.

---

## Related Files

| File | Purpose |
|------|---------|
| `agents/investigative_claim_verifier.md` | Agent specification implementing these standards |
| `data/evidence/processed/claim_verification_matrix.schema.json` | Claim record schema with confidence scoring |
| `data/evidence/chain_of_custody/evidence_manifest.schema.json` | Evidence record schema |
| `data/evidence/vendor_subpoena_targets/subpoena_target_index.md` | Records request target categories |
