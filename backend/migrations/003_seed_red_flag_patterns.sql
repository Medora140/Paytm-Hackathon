-- ============================================================================
-- Migration: 003_seed_red_flag_patterns.sql
-- Description: Seed Ombudsman & Regulatory Knowledge Base Patterns into red_flag_patterns
-- Sources: SEBI Mutual Fund Regulations, IRDAI Health Insurance Guidelines, RBI Fair Practices Code
-- ============================================================================

-- Ensure pattern_id column exists with unique constraint for deterministic upserts
ALTER TABLE red_flag_patterns ADD COLUMN IF NOT EXISTS pattern_id TEXT UNIQUE;

INSERT INTO red_flag_patterns (
    pattern_id,
    category,
    clause_type,
    trigger_keywords,
    trigger_regex,
    plain_explanation_template,
    severity_default,
    source_reference
)
VALUES
(
    'pat_mf_exit_load_01',
    'mutual_fund',
    'exit_load',
    '["exit load", "redemption charge", "contingent deferred sales charge", "redemption fee", "liquidated before", "allotment of units", "exit load of"]'::jsonb,
    '(?i)\b(?:exit\s*load|redemption\s*(?:fee|charge))\b.*?(?:\d+(?:\.\d+)?\s*%|\b(?:days|months|year|days\s*from\s*allotment)\b)',
    'Exit loads penalize early liquidity by deducting up to 1-3% if units are redeemed or switched out before the specified holding window (commonly 30 to 365 days).',
    'high',
    'SEBI Mutual Fund Regulations (Regulation 49 & Master Circulars on Exit Loads)'
),
(
    'pat_mf_expense_ratio_02',
    'mutual_fund',
    'expense_ratio',
    '["total expense ratio", "ter limit", "management fee", "recurring expense", "scheme expense", "investment management fees", "statutory levy", "goods and services tax on management fees"]'::jsonb,
    '(?i)\b(?:total\s*expense\s*ratio|ter|recurring\s*expenses?|scheme\s*expenses?)\b.*?(?:\d+(?:\.\d+)?\s*%|\blimits?\b)',
    'High ongoing recurring expenses (TER) compound over time, heavily reducing investor net alpha and net realized returns compared to direct low-cost index benchmarks.',
    'medium',
    'SEBI (Mutual Funds) Regulations, 1996 - Regulation 52 (TER Caps)'
),
(
    'pat_mf_lockin_03',
    'mutual_fund',
    'lock_in_period',
    '["lock-in period", "lock in period", "statutory lock-in", "elss lock-in", "cannot be redeemed", "repurchase restriction", "closed ended scheme"]'::jsonb,
    '(?i)\b(?:lock[\s\-]in\s*(?:period)?|statutory\s*lock[\s\-]in)\b.*?(?:\d+\s*(?:years?|months?))?',
    'Mandatory lock-in prevents any early redemption or emergency liquidity until the completion of the statutory timeframe (e.g. 3 years for ELSS).',
    'medium',
    'Income Tax Act, 1961 - Section 80C & SEBI ELSS Guidelines'
),
(
    'pat_mf_nav_cutoff_04',
    'mutual_fund',
    'nav_cutoff',
    '["cut-off time", "cut off timing", "nav applicability", "closing nav of the day", "realisation of funds", "allotment of units"]'::jsonb,
    '(?i)\b(?:cut[\s\-]off\s*tim(?:e|ing)s?|nav\s*applicability)\b',
    'Strict cut-off timings and fund realization clauses delay NAV allotment to subsequent business days, risking market timing variance during volatility.',
    'low',
    'SEBI Circular on Uniformity in Cut-Off Timings for Mutual Fund Transactions'
),
(
    'pat_irda_room_rent_01',
    'insurance',
    'room_rent_cap',
    '["room rent", "room charges", "proportionate deduction", "icu charges limit", "standard room", "sub-limit on room"]'::jsonb,
    '(?i)\b(?:room\s*rent|room\s*charges)\b.*?(?:\d+\s*%|proportionate\s*deduction)',
    'Room rent sub-limits trigger proportionate deduction across your entire hospital bill (surgeon fees, ICU, investigations), frequently causing 30-50% surprise out-of-pocket costs.',
    'high',
    'Insurance Ombudsman Award Analysis / IRDAI Health Regulations'
),
(
    'pat_irda_ped_waiting_02',
    'insurance',
    'pre_existing_exclusion',
    '["waiting period", "pre-existing", "ped", "pre existing disease", "continuous coverage", "declared or undeclared"]'::jsonb,
    '(?i)\b(?:pre[\s\-]existing\s*(?:diseases?|conditions?|ailments?)|ped)\b.*?(?:\d+\s*(?:months?|years?))?',
    'Extended pre-existing disease waiting periods (36-48 months) are the primary driver of early claim repudiations before insurance ombudsman panels.',
    'medium',
    'IRDAI Master Circular on Standardization of Health Insurance Contracts'
),
(
    'pat_irda_copay_03',
    'insurance',
    'co_payment',
    '["co-pay", "copayment", "co-payment", "mandatory co-pay", "non-network hospital", "proportionate share"]'::jsonb,
    '(?i)\b(?:co[\s\-]pay(?:ment)?)\b.*?(?:\d+\s*%)?',
    'Mandatory co-payment mandates that the insured bear 10-20% of every approved claim out-of-pocket, even at network hospitals.',
    'low',
    'IRDAI Guidelines on Co-payment Clauses'
),
(
    'pat_irda_specific_illness_04',
    'insurance',
    'specific_illness_waiting',
    '["cataract", "hernia", "joint replacement", "24 months waiting", "two year exclusion", "specified disease waiting period"]'::jsonb,
    '(?i)\b(?:cataract|hernia|joint\s*replacement|stones?)\b.*?(?:\d+\s*(?:months?|years?)\s*waiting)',
    'Specific common medical conditions are excluded during the initial 12 to 24 months of coverage regardless of pre-existence.',
    'low',
    'IRDAI Standardization Clauses'
),
(
    'pat_rbi_prepayment_01',
    'lending',
    'prepayment_penalty',
    '["prepayment penalty", "foreclosure charges", "early repayment", "pre-payment fee", "foreclosure penalty"]'::jsonb,
    '(?i)\b(?:pre[\s\-]payment\s*(?:penalty|charges?)|foreclosure\s*charges?)\b',
    'Prepayment penalties restrict borrowers from refinancing or repaying debt early, conflicting with RBI consumer protection directives on floating rate loans.',
    'high',
    'RBI Master Direction on Consumer Loans and Prepayment Charges'
),
(
    'pat_rbi_proc_fee_02',
    'lending',
    'processing_fee',
    '["processing fee", "administrative charge", "non-refundable fee", "upfront charges", "loan login fee"]'::jsonb,
    '(?i)\b(?:processing\s*fee|administrative\s*charge)\b.*?(?:non[\s\-]refundable)',
    'Non-refundable processing charges are retained by the lender even if the loan application is rejected or not disbursed.',
    'low',
    'RBI Fair Practices Code for Lenders'
)
ON CONFLICT (pattern_id) DO UPDATE SET
    category = EXCLUDED.category,
    clause_type = EXCLUDED.clause_type,
    trigger_keywords = EXCLUDED.trigger_keywords,
    trigger_regex = EXCLUDED.trigger_regex,
    plain_explanation_template = EXCLUDED.plain_explanation_template,
    severity_default = EXCLUDED.severity_default,
    source_reference = EXCLUDED.source_reference,
    updated_at = NOW();
