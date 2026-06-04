"""Compiled regex patterns and redaction placeholders for PII detection."""

from __future__ import annotations

import re

PII_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    # -------------------------------------------------------------------------
    # CONTACT & IDENTITY
    # -------------------------------------------------------------------------
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        "phone",
        re.compile(r"\b(?:\+44\s?|0)(?:\d\s?){9,10}\b"),
        "[REDACTED_PHONE]",
    ),
    (
        "uk_postcode",
        re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.IGNORECASE),
        "[REDACTED_POSTCODE]",
    ),
    (
        "gps_coordinates",
        # Decimal degrees: e.g. 51.5074, -0.1278
        re.compile(
            r"\b-?(?:[1-8]?\d(?:\.\d+)?|90(?:\.0+)?),\s*-?(?:1[0-7]\d(?:\.\d+)?|[1-9]?\d(?:\.\d+)?|180(?:\.0+)?)\b"
        ),
        "[REDACTED_COORDS]",
    ),
    # -------------------------------------------------------------------------
    # UK GOVERNMENT & TAX IDENTIFIERS
    # -------------------------------------------------------------------------
    (
        "nino",
        # National Insurance Number: two letters, six digits, one letter (A-D)
        re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b", re.IGNORECASE),
        "[REDACTED_NINO]",
    ),
    (
        "nhs_number",
        # NHS Number: 10 digits, often grouped as 3-3-4
        re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b"),
        "[REDACTED_NHS]",
    ),
    (
        "utr",
        # Unique Taxpayer Reference: 10 digits, optionally prefixed with 'UTR'
        re.compile(r"\b(?:UTR[\s:]*)?[1-9]\d{9}\b", re.IGNORECASE),
        "[REDACTED_UTR]",
    ),
    (
        "vat_number",
        # UK VAT: GB followed by 9 or 12 digits
        re.compile(r"\bGB\d{9}(?:\d{3})?\b", re.IGNORECASE),
        "[REDACTED_VAT]",
    ),
    (
        "companies_house",
        # Companies House: 8 digits, or 2 letters + 6 digits (e.g. SC123456)
        re.compile(r"\b(?:[A-Z]{2}\d{6}|\d{8})\b"),
        "[REDACTED_COMPNO]",
    ),
    (
        "eori_number",
        # Economic Operators Registration: GB + 12 digits (post-Brexit)
        re.compile(r"\bGB\d{12}\b", re.IGNORECASE),
        "[REDACTED_EORI]",
    ),
    (
        "upn",
        # Unique Pupil Number: 1 letter + 12 digits
        re.compile(r"\b[A-Z]\d{12}\b", re.IGNORECASE),
        "[REDACTED_UPN]",
    ),
    (
        "charity_number",
        # England/Wales: 6–7 digits; Scotland: SC + 6 digits
        re.compile(r"\b(?:SC\d{6}|\d{6,7})\b", re.IGNORECASE),
        "[REDACTED_CHARITY]",
    ),
    (
        "land_registry",
        # Title number: 2–3 letters + up to 6 digits
        re.compile(r"\b[A-Z]{2,3}\d{1,6}\b", re.IGNORECASE),
        "[REDACTED_TITLENO]",
    ),
    # -------------------------------------------------------------------------
    # TRAVEL & VEHICLE DOCUMENTS
    # -------------------------------------------------------------------------
    (
        "passport",
        # UK passport: 9 alphanumeric characters
        re.compile(r"\b[0-9]{9}\b"),
        "[REDACTED_PASSPORT]",
    ),
    (
        "uk_driving_licence",
        # DVLA format: 5 letters + 6 digits + 2 letters + 1 digit + 2 alphanumeric
        re.compile(r"\b[A-Z]{5}\d{6}[A-Z]{2}\d[A-Z0-9]{2}\b", re.IGNORECASE),
        "[REDACTED_DRVLIC]",
    ),
    (
        "uk_vrm",
        # Current format: AB12 ABC
        re.compile(r"\b[A-Z]{2}\d{2}[\s]?[A-Z]{3}\b", re.IGNORECASE),
        "[REDACTED_VRM]",
    ),
    # -------------------------------------------------------------------------
    # FINANCIAL IDENTIFIERS
    # -------------------------------------------------------------------------
    (
        "credit_card",
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "[REDACTED_CARD]",
    ),
    (
        "uk_sort_code_account",
        # Sort code (XX-XX-XX) + 8-digit account number
        re.compile(r"\b\d{2}-\d{2}-\d{2}[\s,/]*\d{8}\b"),
        "[REDACTED_BANK]",
    ),
    (
        "iban",
        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b"),
        "[REDACTED_IBAN]",
    ),
    (
        "salary_or_income",
        # Matches GBP amounts likely representing salary/income figures
        re.compile(
            r"£\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\s?(?:GBP|gbp)"
        ),
        "[REDACTED_FINANCIAL]",
    ),
    (
        "loyalty_membership_number",
        # Generic membership/loyalty card: 8–20 alphanumeric digits
        re.compile(
            r"\b(?:membership|member|loyalty|card)[\s#:no.]*([A-Z0-9]{8,20})\b", re.IGNORECASE
        ),
        "[REDACTED_MEMBERID]",
    ),
    # -------------------------------------------------------------------------
    # PROFESSIONAL REGISTRATION NUMBERS
    # -------------------------------------------------------------------------
    (
        "gmc_number",
        # General Medical Council: 7 digits
        re.compile(r"\b(?:GMC[\s:]*)?[1-9]\d{6}\b", re.IGNORECASE),
        "[REDACTED_GMC]",
    ),
    (
        "nmc_number",
        # Nursing & Midwifery Council: 2 letters + 6 digits + 1 letter
        re.compile(r"\b[A-Z]{2}\d{6}[A-Z]\b", re.IGNORECASE),
        "[REDACTED_NMC]",
    ),
    (
        "sra_number",
        # Solicitors Regulation Authority: 6–8 digits
        re.compile(r"\b(?:SRA[\s:]*)?[1-9]\d{5,7}\b", re.IGNORECASE),
        "[REDACTED_SRA]",
    ),
    # -------------------------------------------------------------------------
    # NETWORK / DEVICE IDENTIFIERS
    # -------------------------------------------------------------------------
    (
        "ip_address",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[REDACTED_IP]",
    ),
    (
        "ipv6_address",
        re.compile(
            r"\b(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}\b"
            r"|\b(?:[0-9A-Fa-f]{1,4}:){1,7}:\b"
            r"|\b::(?:[0-9A-Fa-f]{1,4}:){0,6}[0-9A-Fa-f]{1,4}\b"
        ),
        "[REDACTED_IPv6]",
    ),
    (
        "mac_address",
        re.compile(r"\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b"),
        "[REDACTED_MAC]",
    ),
    (
        "imei",
        # IMEI: exactly 15 digits
        re.compile(r"\b\d{15}\b"),
        "[REDACTED_IMEI]",
    ),
    (
        "device_serial",
        # Generic serial: alphanumeric, 10–20 chars, often labelled S/N or Serial
        re.compile(r"\b(?:S/?N|Serial[\s:No.]*)([A-Z0-9]{10,20})\b", re.IGNORECASE),
        "[REDACTED_SERIAL]",
    ),
    (
        "cookie_session_token",
        # Short session tokens/cookie values: 16–31 chars (below API key threshold)
        re.compile(r"\b[A-Za-z0-9_\-]{16,31}\b"),
        "[REDACTED_SESSION]",
    ),
    (
        "guid_uuid",
        # Standard UUID/GUID format
        re.compile(
            r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b"
        ),
        "[REDACTED_UUID]",
    ),
    (
        "api_key_or_token",
        # High-entropy bearer tokens / API keys: 32–512 chars
        re.compile(r"\b[A-Za-z0-9_\-]{32,512}\b"),
        "[REDACTED_TOKEN]",
    ),
    # -------------------------------------------------------------------------
    # CREDENTIALS
    # -------------------------------------------------------------------------
    (
        "plaintext_password",
        # Matches labelled plaintext passwords; cannot catch unlabelled free-text
        re.compile(r"(?:password|passwd|pwd)[\s:=]+\S+", re.IGNORECASE),
        "[REDACTED_PASSWORD]",
    ),
    (
        "security_answer",
        # Matches labelled security question answers
        re.compile(r"(?:security[\s_-]?answer|secret[\s_-]?answer)[\s:=]+.+", re.IGNORECASE),
        "[REDACTED_SECANSWER]",
    ),
    (
        "username",
        # Matches labelled usernames / handles
        re.compile(
            r"(?:username|user[\s_-]?name|handle|screen[\s_-]?name)[\s:=]+\S+", re.IGNORECASE
        ),
        "[REDACTED_USERNAME]",
    ),
    # -------------------------------------------------------------------------
    # DATES OF BIRTH
    # -------------------------------------------------------------------------
    (
        "date_of_birth",
        # DD/MM/YYYY and DD Month YYYY — pair with context keywords where precision matters
        re.compile(
            r"\b(?:0?[1-9]|[12]\d|3[01])[/\-.](?:0?[1-9]|1[0-2])[/\-.]\d{4}\b"
            r"|"
            r"\b(?:0?[1-9]|[12]\d|3[01])\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
            r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
            r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
            re.IGNORECASE,
        ),
        "[REDACTED_DOB]",
    ),
    # -------------------------------------------------------------------------
    # SPECIAL CATEGORY DATA (UK GDPR Article 9) — context-labelled only
    # Full coverage requires NER; these catch explicitly labelled disclosures
    # -------------------------------------------------------------------------
    (
        "health_condition",
        re.compile(
            r"(?:diagnosis|condition|disorder|disease|illness|medical[\s_-]?history)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_HEALTH]",
    ),
    (
        "disability_status",
        re.compile(r"(?:disability|disabled|impairment)[\s:=]+.+", re.IGNORECASE),
        "[REDACTED_DISABILITY]",
    ),
    (
        "medication",
        re.compile(r"(?:medication|prescription|drug|dosage)[\s:=]+.+", re.IGNORECASE),
        "[REDACTED_MEDICATION]",
    ),
    (
        "mental_health",
        re.compile(
            r"(?:mental[\s_-]?health|psychiatric|psychological[\s_-]?condition|therapy|counselling)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_MENTALHEALTH]",
    ),
    (
        "ethnicity",
        re.compile(
            r"(?:ethnicity|ethnic[\s_-]?origin|race|nationality[\s_-]?background)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_ETHNICITY]",
    ),
    (
        "religion",
        re.compile(
            r"(?:religion|religious[\s_-]?belief|faith|denomination)[\s:=]+.+", re.IGNORECASE
        ),
        "[REDACTED_RELIGION]",
    ),
    (
        "sexual_orientation",
        re.compile(r"(?:sexual[\s_-]?orientation|sexuality)[\s:=]+.+", re.IGNORECASE),
        "[REDACTED_SEXORIENT]",
    ),
    (
        "political_opinion",
        re.compile(
            r"(?:political[\s_-]?(?:opinion|view|affiliation|belief))[\s:=]+.+", re.IGNORECASE
        ),
        "[REDACTED_POLITICS]",
    ),
    (
        "trade_union",
        re.compile(
            r"(?:trade[\s_-]?union|union[\s_-]?membership|TUC[\s_-]?member)[\s:=]+.+", re.IGNORECASE
        ),
        "[REDACTED_UNION]",
    ),
    (
        "criminal_record",
        # Covers DBS-style disclosures; spent/unspent conviction references
        re.compile(
            r"(?:conviction|offence|criminal[\s_-]?record|DBS[\s_-]?check|caution|sentence)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_CRIMINAL]",
    ),
    (
        "immigration_status",
        re.compile(
            r"(?:immigration[\s_-]?status|visa[\s_-]?(?:type|number|status)|leave[\s_-]?to[\s_-]?remain|BRP[\s_-]?number)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_IMMIGRATION]",
    ),
    (
        "gender",
        re.compile(
            r"(?:gender|sex)[\s:=]+(?:male|female|non[\s_-]?binary|transgender|prefer[\s_-]?not[\s_-]?to[\s_-]?say|\S+)",
            re.IGNORECASE,
        ),
        "[REDACTED_GENDER]",
    ),
    (
        "marital_status",
        re.compile(r"(?:marital[\s_-]?status|relationship[\s_-]?status)[\s:=]+.+", re.IGNORECASE),
        "[REDACTED_MARITAL]",
    ),
    # -------------------------------------------------------------------------
    # SOCIAL CARE / BENEFITS / EDUCATION REFERENCES
    # -------------------------------------------------------------------------
    (
        "social_care_ref",
        re.compile(
            r"(?:case[\s_-]?(?:ref(?:erence)?|no|number)|social[\s_-]?care[\s_-]?id)[\s:=]+([A-Z0-9\-]{4,20})",
            re.IGNORECASE,
        ),
        "[REDACTED_CASEREF]",
    ),
    (
        "benefits_ref",
        # Universal Credit / Housing Benefit / DWP references
        re.compile(
            r"(?:UC[\s_-]?ref(?:erence)?|claim[\s_-]?(?:ref(?:erence)?|number)|DWP[\s_-]?ref)[\s:=]+([A-Z0-9\-]{4,20})",
            re.IGNORECASE,
        ),
        "[REDACTED_BENEFITSREF]",
    ),
    (
        "student_id",
        re.compile(
            r"(?:student[\s_-]?(?:id|number|ref(?:erence)?))[\s:=]+([A-Z0-9\-]{4,20})",
            re.IGNORECASE,
        ),
        "[REDACTED_STUDENTID]",
    ),
    (
        "prison_offender_number",
        # NOMIS-style: letter + 4–5 digits + 2 letters
        re.compile(r"\b[A-Z]\d{4,5}[A-Z]{2}\b", re.IGNORECASE),
        "[REDACTED_PRISONNO]",
    ),
    (
        "cqc_registration",
        # CQC provider/location ID: alphanumeric 1–3 chars + 6 digits
        re.compile(r"\b[A-Z]{1,3}\d{6}\b", re.IGNORECASE),
        "[REDACTED_CQCID]",
    ),
    # -------------------------------------------------------------------------
    # NEXT OF KIN / DEPENDENT INFORMATION — context-labelled only
    # -------------------------------------------------------------------------
    (
        "next_of_kin",
        re.compile(
            r"(?:next[\s_-]?of[\s_-]?kin|emergency[\s_-]?contact|nok)[\s:=]+.+", re.IGNORECASE
        ),
        "[REDACTED_NOK]",
    ),
    (
        "dependent_info",
        re.compile(
            r"(?:dependent(?:s)?|child(?:ren)?[\s_-]?(?:name|dob|details))[\s:=]+.+", re.IGNORECASE
        ),
        "[REDACTED_DEPENDENT]",
    ),
    # =========================================================================
    # UK-SPECIFIC ADDITIONS
    # =========================================================================
    # -------------------------------------------------------------------------
    # UK GOVERNMENT IDENTITY DOCUMENTS
    # -------------------------------------------------------------------------
    (
        "uk_national_identity_card",
        # UK National Identity Card (biometric): 9 alphanumeric (IDGBR format prefix optional)
        re.compile(r"\b(?:IDGBR)?[A-Z0-9]{9}\b", re.IGNORECASE),
        "[REDACTED_UKNIC]",
    ),
    (
        "brp_number",
        # Biometric Residence Permit: 2 letters + 7 digits (standalone format)
        re.compile(r"\b[A-Z]{2}\d{7}\b", re.IGNORECASE),
        "[REDACTED_BRP]",
    ),
    (
        "armed_forces_number",
        # Service number: up to 3 letters + 5–8 digits (varies by service)
        re.compile(
            r"\b(?:armed[\s_-]?forces[\s_-]?(?:no|number|id)|service[\s_-]?no(?:\.)?|svc[\s_-]?no)[\s:=]*([A-Z]{0,3}\d{5,8})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_ARMEDFORCES]",
    ),
    (
        "pnc_id",
        # Police National Computer ID: typically labelled; format varies by force
        re.compile(
            r"\b(?:PNC[\s_-]?(?:id|no|number|ref(?:erence)?))[\s:=]+([A-Z0-9/\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_PNCID]",
    ),
    (
        "blue_badge_ref",
        # Blue Badge (disability parking): typically 8–10 alphanumeric, labelled
        re.compile(
            r"\b(?:blue[\s_-]?badge[\s_-]?(?:no|number|ref(?:erence)?))[\s:=]+([A-Z0-9]{6,12})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_BLUEBADGE]",
    ),
    # -------------------------------------------------------------------------
    # HEALTHCARE / NHS
    # -------------------------------------------------------------------------
    (
        "ods_code",
        # ODS (Organisation Data Service) / GP practice code: 1 letter + 5 alphanumeric
        re.compile(r"\b[A-Z]\d{5}\b", re.IGNORECASE),
        "[REDACTED_ODSCODE]",
    ),
    # -------------------------------------------------------------------------
    # EDUCATION
    # -------------------------------------------------------------------------
    (
        "ofsted_urn",
        # Ofsted Unique Reference Number for schools/providers: 6 digits
        re.compile(r"\b(?:URN[\s:]*)?(?:1[0-9]{5}|[2-9]\d{5})\b", re.IGNORECASE),
        "[REDACTED_OFSTEDURN]",
    ),
    # -------------------------------------------------------------------------
    # LOCAL GOVERNMENT / HOUSING / COURTS
    # -------------------------------------------------------------------------
    (
        "council_tax_account",
        # Council Tax account number: labelled, typically 8–12 digits
        re.compile(
            r"\b(?:council[\s_-]?tax[\s_-]?(?:account|ref(?:erence)?|no|number))[\s:=]+(\d{8,12})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_COUNCILTAX]",
    ),
    (
        "electoral_roll_number",
        # Electoral roll / register number: labelled reference
        re.compile(
            r"\b(?:electoral[\s_-]?(?:roll|register|ref(?:erence)?|no|number))[\s:=]+([A-Z0-9\-]{4,16})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_ELECTORALREF]",
    ),
    (
        "legal_aid_ref",
        # Legal Aid Agency reference: typically 5 digits + letter, or labelled
        re.compile(
            r"\b(?:legal[\s_-]?aid[\s_-]?(?:ref(?:erence)?|no|number))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_LEGALAID]",
    ),
    (
        "hmcts_case_number",
        # HMCTS court case number: varies by court; common formats include digits/letters
        re.compile(
            r"\b(?:case[\s_-]?(?:no|number|ref(?:erence)?))[\s:=]+([A-Z0-9]{2,6}[\-/][A-Z0-9]{2,10})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_CASENUM]",
    ),
    (
        "coroner_case_ref",
        # Coroner's case reference: labelled
        re.compile(
            r"\b(?:coroner[\s_-]?(?:case|ref(?:erence)?|no|number))[\s:=]+([A-Z0-9\-/]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_CORONERREF]",
    ),
    (
        "probate_registry_number",
        # Probate registry / grant number: labelled
        re.compile(
            r"\b(?:probate[\s_-]?(?:no|number|ref(?:erence)?|grant))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_PROBATEREF]",
    ),
    (
        "warrant_number",
        # Arrest / distress warrant number: labelled
        re.compile(
            r"\b(?:warrant[\s_-]?(?:no|number|ref(?:erence)?))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_WARRANTNO]",
    ),
    # =========================================================================
    # CROSS-JURISDICTION ADDITIONS
    # =========================================================================
    # -------------------------------------------------------------------------
    # GEOLOCATION — SUPPLEMENTARY FORMATS
    # -------------------------------------------------------------------------
    (
        "what3words_address",
        # what3words: three lowercase words separated by dots
        re.compile(r"\b[a-z]+\.[a-z]+\.[a-z]+\b"),
        "[REDACTED_W3W]",
    ),
    (
        "os_grid_reference",
        # Ordnance Survey National Grid: 2 letters + even number of digits (2–10)
        re.compile(r"\b[A-Z]{2}\s?\d{2,5}\s?\d{2,5}\b", re.IGNORECASE),
        "[REDACTED_OSGRID]",
    ),
    # -------------------------------------------------------------------------
    # SOCIAL MEDIA & ONLINE IDENTIFIERS
    # -------------------------------------------------------------------------
    (
        "social_media_profile_url",
        # Profile URLs for major platforms
        re.compile(
            r"https?://(?:www\.)?(?:twitter\.com|x\.com|linkedin\.com/in|facebook\.com|instagram\.com|tiktok\.com/@?|threads\.net/@?)"
            r"/[A-Za-z0-9._%-]{1,64}",
            re.IGNORECASE,
        ),
        "[REDACTED_SOCIALURL]",
    ),
    (
        "social_media_numeric_id",
        # Platform numeric user/post IDs when labelled (Twitter/X, Facebook, etc.)
        re.compile(
            r"\b(?:user[\s_-]?id|profile[\s_-]?id|account[\s_-]?id|twitter[\s_-]?id|facebook[\s_-]?id)[\s:=]+(\d{6,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_SOCIALID]",
    ),
    # -------------------------------------------------------------------------
    # BROWSER / DEVICE FINGERPRINTING
    # -------------------------------------------------------------------------
    (
        "browser_fingerprint",
        # Browser/canvas fingerprint hashes: typically 32-char hex (MD5-length) when labelled
        re.compile(
            r"\b(?:fingerprint|canvas[\s_-]?hash|browser[\s_-]?id|device[\s_-]?fingerprint)[\s:=]+([A-Fa-f0-9]{32,64})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_FINGERPRINT]",
    ),
    # -------------------------------------------------------------------------
    # DIGITAL SIGNATURES / CERTIFICATE HASHES
    # -------------------------------------------------------------------------
    (
        "certificate_hash",
        # X.509 / TLS certificate thumbprint: 40-char SHA-1 or 64-char SHA-256 hex,
        # often colon-delimited (AA:BB:CC:...)
        re.compile(
            r"\b(?:[A-Fa-f0-9]{2}:){19}[A-Fa-f0-9]{2}\b"  # SHA-1 colon-delimited
            r"|\b(?:[A-Fa-f0-9]{2}:){31}[A-Fa-f0-9]{2}\b"  # SHA-256 colon-delimited
            r"|\b[A-Fa-f0-9]{40}\b"  # SHA-1 plain hex
            r"|\b[A-Fa-f0-9]{64}\b",  # SHA-256 plain hex
        ),
        "[REDACTED_CERTHASH]",
    ),
    # -------------------------------------------------------------------------
    # CRYPTOCURRENCY WALLET ADDRESSES
    # -------------------------------------------------------------------------
    (
        "bitcoin_address",
        # Legacy P2PKH (1...), P2SH (3...), Bech32 (bc1...)
        re.compile(
            r"\b(?:1[A-HJ-NP-Za-km-z1-9]{25,34}|3[A-HJ-NP-Za-km-z1-9]{25,34}|bc1[ac-hj-np-z02-9]{6,87})\b",
        ),
        "[REDACTED_BTCADDR]",
    ),
    (
        "ethereum_address",
        # EIP-55 checksummed or lowercase: 0x + 40 hex chars
        re.compile(r"\b0x[A-Fa-f0-9]{40}\b"),
        "[REDACTED_ETHADDR]",
    ),
    # =========================================================================
    # UK-SPECIFIC ADDITIONS — ROUND 2
    # =========================================================================
    # -------------------------------------------------------------------------
    # NAMED PERSONS IN PROFESSIONAL / INSTITUTIONAL CONTEXT
    # Context-label approach: catches explicitly labelled name fields.
    # Full NER is required for unlabelled free-text name recognition.
    # -------------------------------------------------------------------------
    (
        "full_name_labelled",
        # Catches "Name: John Smith", "Patient name: ...", "Full name: ..." etc.
        re.compile(
            r"(?:(?:full|first|last|sur|fore|given|family|middle|preferred|legal)[\s_-]?name"
            r"|patient[\s_-]?name|client[\s_-]?name|pupil[\s_-]?name|resident[\s_-]?name"
            r"|name[\s_-]?of[\s_-]?(?:applicant|claimant|defendant|offender|tenant|child|patient))[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_NAME]",
    ),
    # -------------------------------------------------------------------------
    # FREE-TEXT POSTAL ADDRESS — STRUCTURED FRAGMENTS
    # Catches house-number + street-name patterns and PO Box references.
    # Full address parsing requires NER or a dedicated address library.
    # -------------------------------------------------------------------------
    (
        "street_address_fragment",
        # Matches "12 High Street", "Flat 3B, Church Road", "Unit 7 Industrial Estate"
        re.compile(
            r"\b(?:flat|apartment|apt|unit|suite|floor|house|no\.?|number)[\s.]*\d{1,4}[A-Z]?"
            r"[\s,]+[A-Za-z][A-Za-z\s]{3,40}"
            r"|"
            r"\b\d{1,4}[A-Z]?[\s,]+[A-Za-z][A-Za-z\s]{3,40}"
            r"(?:\s+(?:road|rd|street|st|avenue|ave|lane|ln|drive|dr|close|cl|way|place|pl|crescent|cres|court|ct|grove|terrace|terr|row|walk|mews|gardens|gate|hill|park|view|rise|square|sq))\b",
            re.IGNORECASE,
        ),
        "[REDACTED_ADDRESS]",
    ),
    (
        "po_box",
        # Royal Mail PO Box: "PO Box 1234" or "P.O. Box 56"
        re.compile(r"\bP\.?O\.?\s*Box\s+\d{1,6}\b", re.IGNORECASE),
        "[REDACTED_POBOX]",
    ),
    # -------------------------------------------------------------------------
    # HEALTHCARE — NAMED ENTITIES (CONTEXT-LABELLED)
    # -------------------------------------------------------------------------
    (
        "nhs_trust_name",
        # NHS Trust or hospital linked to a patient record — labelled
        re.compile(
            r"(?:nhs[\s_-]?trust|hospital|healthcare[\s_-]?trust|foundation[\s_-]?trust"
            r"|mental[\s_-]?health[\s_-]?trust|community[\s_-]?trust)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_NHSTRUST]",
    ),
    (
        "gp_name_or_surgery",
        # GP name or surgery name linked to a patient record — labelled
        re.compile(
            r"(?:gp[\s_-]?(?:name|surgery|practice|clinic)|doctor[\s_-]?name"
            r"|registered[\s_-]?(?:gp|doctor|practice)|surgery[\s_-]?name)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_GPNAME]",
    ),
    # -------------------------------------------------------------------------
    # LEGAL / JUDICIAL NAMED ENTITIES (CONTEXT-LABELLED)
    # -------------------------------------------------------------------------
    (
        "coroner_name",
        # Coroner's name when labelled in a document
        re.compile(
            r"(?:coroner[\s_-]?(?:name|:)|his[\s_-]?her[\s_-]?majesty[\s_-]?s[\s_-]?coroner)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_CORONERNAME]",
    ),
    (
        "solicitor_barrister_name",
        # Solicitor or barrister name when labelled
        re.compile(
            r"(?:solicitor|barrister|counsel|legal[\s_-]?representative|instructed[\s_-]?by"
            r"|acting[\s_-]?for|represented[\s_-]?by)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_LEGALREP]",
    ),
    # -------------------------------------------------------------------------
    # EDUCATION — NAMED ENTITIES (CONTEXT-LABELLED)
    # -------------------------------------------------------------------------
    (
        "school_staff_name",
        # Teacher or school staff name linked to a pupil record — labelled
        re.compile(
            r"(?:teacher[\s_-]?name|class[\s_-]?teacher|form[\s_-]?tutor|head[\s_-]?of[\s_-]?year"
            r"|senco|teaching[\s_-]?assistant[\s_-]?name|staff[\s_-]?name)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_STAFFNAME]",
    ),
    # -------------------------------------------------------------------------
    # DBS CERTIFICATE NUMBER
    # -------------------------------------------------------------------------
    (
        "dbs_certificate_number",
        # DBS (Disclosure and Barring Service) certificate: exactly 12 digits
        re.compile(
            r"\b(?:DBS[\s_-]?(?:cert(?:ificate)?[\s_-]?)?(?:no|number)[\s:=]*)?(\d{12})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_DBSCERT]",
    ),
    # -------------------------------------------------------------------------
    # ARMED FORCES PENSION NUMBER
    # -------------------------------------------------------------------------
    (
        "armed_forces_pension_number",
        # Armed Forces Pension Scheme reference — labelled; format: letters + digits
        re.compile(
            r"\b(?:armed[\s_-]?forces[\s_-]?pension|afps[\s_-]?(?:no|number|ref(?:erence)?)"
            r"|military[\s_-]?pension[\s_-]?(?:no|number|ref(?:erence)?))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_AFPENSION]",
    ),
    # -------------------------------------------------------------------------
    # BORDER FORCE / IMMIGRATION
    # -------------------------------------------------------------------------
    (
        "uk_border_force_ref",
        # UK Border Force case or seizure reference — labelled
        re.compile(
            r"\b(?:border[\s_-]?force[\s_-]?(?:ref(?:erence)?|no|number|case)"
            r"|ukbf[\s_-]?(?:ref(?:erence)?|no|number))[\s:=]+([A-Z0-9\-/]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_BORDERFORCE]",
    ),
    # -------------------------------------------------------------------------
    # TRIBUNAL CASE NUMBERS
    # -------------------------------------------------------------------------
    (
        "tribunal_case_number",
        # Employment, Immigration, First-tier, Upper Tribunal references
        # Employment: NNNN/YYYY or NNNNNN/YYYY; Immigration: e.g. IA/12345/2023; FTT: e.g. TC/2023/01234
        re.compile(
            r"\b(?:(?:employment|immigration|first[\s_-]?tier|upper|property|tax|social[\s_-]?security)"
            r"[\s_-]?tribunal[\s_-]?(?:case[\s_-]?)?(?:no|number|ref(?:erence)?)[\s:=]+([A-Z0-9/\-]{4,25})"
            r"|(?:ET|IA|EA|UKUT|TC|FTT|UT)[/\-]\d{4,7}[/\-]\d{2,4})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_TRIBUNALREF]",
    ),
    # -------------------------------------------------------------------------
    # CHILDREN'S SERVICES — CARE & PROTECTION REFERENCES
    # -------------------------------------------------------------------------
    (
        "adoption_order_ref",
        # Adoption order reference number — labelled
        re.compile(
            r"\b(?:adoption[\s_-]?(?:order[\s_-]?)?(?:ref(?:erence)?|no|number))[\s:=]+([A-Z0-9\-/]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_ADOPTIONREF]",
    ),
    (
        "foster_care_ref",
        # Foster care reference number — labelled
        re.compile(
            r"\b(?:foster(?:ing)?[\s_-]?(?:ref(?:erence)?|no|number|id)|foster[\s_-]?care[\s_-]?(?:ref(?:erence)?|no|number))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_FOSTERREF]",
    ),
    (
        "looked_after_child_number",
        # Looked-after child (LAC) number — labelled
        re.compile(
            r"\b(?:lac[\s_-]?(?:no|number|id|ref(?:erence)?)"
            r"|looked[\s_-]?after[\s_-]?child[\s_-]?(?:no|number|id|ref(?:erence)?)"
            r"|child[\s_-]?in[\s_-]?care[\s_-]?(?:no|number|id))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_LACNUM]",
    ),
    # -------------------------------------------------------------------------
    # PROPERTY / HOUSING / PLANNING
    # -------------------------------------------------------------------------
    (
        "mortgage_property_address",
        # Property address explicitly linked to a mortgage account — labelled
        re.compile(
            r"(?:mortgage[\s_-]?(?:property|address)|secured[\s_-]?(?:property|address)"
            r"|property[\s_-]?(?:address|details)[\s_-]?(?:for[\s_-]?mortgage)?)[\s:=]+.+",
            re.IGNORECASE,
        ),
        "[REDACTED_MORTGAGEPROP]",
    ),
    (
        "leasehold_freehold_title_ref",
        # Extended land registry title reference (longer leasehold/freehold formats)
        # Covers: AGL123456, GM-123456, SYK123456, etc.
        re.compile(r"\b[A-Z]{2,4}[\-]?\d{4,8}\b", re.IGNORECASE),
        "[REDACTED_TITLEREF]",
    ),
    (
        "housing_association_tenant_ref",
        # Housing association / registered provider tenant reference — labelled
        re.compile(
            r"\b(?:tenant[\s_-]?(?:ref(?:erence)?|no|number|id)"
            r"|housing[\s_-]?(?:association[\s_-]?)?(?:ref(?:erence)?|no|number|account)"
            r"|registered[\s_-]?provider[\s_-]?(?:ref(?:erence)?|no))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_TENANTREF]",
    ),
    (
        "rent_account_number",
        # Rent account number — labelled
        re.compile(
            r"\b(?:rent[\s_-]?(?:account[\s_-]?)?(?:no|number|ref(?:erence)?|id))[\s:=]+([A-Z0-9\-]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_RENTACCT]",
    ),
    (
        "planning_application_number",
        # Local authority planning application reference
        # Common formats: YYYY/NNNNN/FUL, NN/NNNN/N, PP-NNNN-NNNN
        re.compile(
            r"\b(?:planning[\s_-]?(?:application[\s_-]?)?(?:no|number|ref(?:erence)?)[\s:=]+([A-Z0-9/\-]{4,25})"
            r"|\d{2,4}[/\-]\d{3,6}[/\-][A-Z]{2,8})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_PLANNINGREF]",
    ),
    (
        "building_regulations_cert",
        # Building regulations completion certificate number — labelled
        re.compile(
            r"\b(?:building[\s_-]?reg(?:ulation)?s?[\s_-]?(?:cert(?:ificate)?[\s_-]?)?(?:no|number|ref(?:erence)?))"
            r"[\s:=]+([A-Z0-9\-/]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_BUILDREGSREF]",
    ),
    (
        "cqc_inspection_ref",
        # CQC care home inspection report reference or narrative reference — labelled
        re.compile(
            r"\b(?:cqc[\s_-]?(?:inspection[\s_-]?)?(?:ref(?:erence)?|no|number|report[\s_-]?id)"
            r"|care[\s_-]?quality[\s_-]?commission[\s_-]?(?:ref(?:erence)?|inspection[\s_-]?no))[\s:=]+([A-Z0-9\-/]{4,20})\b",
            re.IGNORECASE,
        ),
        "[REDACTED_CQCINSPREF]",
    ),
    # -------------------------------------------------------------------------
    # NOTE: The following require NER (e.g. spaCy en_core_web_trf) — not regex:
    #   - Full names in unlabelled free text (first/last/full)
    #   - Full free-text postal addresses (unlabelled)
    #   - Biometric / genetic data in unstructured text
    #   - Photographic / voice / CCTV references in free text
    #   - NHS Trust, GP, coroner, solicitor, teacher names in unlabelled prose
    # -------------------------------------------------------------------------
)
