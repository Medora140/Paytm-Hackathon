import {
  BenchmarkCompareResponse,
  ChatResponse,
  ConfidenceScoreResponse,
  DocumentDetailResponse,
  DocumentListItem,
  DocumentSummaryResponse,
  RedFlagsResponse,
} from "../types";

export const MOCK_DOCUMENT_ID = "00000000-0000-4000-8000-000000000002";

export const MOCK_DOCUMENTS_LIST: DocumentListItem[] = [
  {
    id: MOCK_DOCUMENT_ID,
    user_id: "usr_0191eb5a-73d8-7910-b9df-20cb558b9190",
    filename: "Star_Health_Optima_Policy.pdf",
    document_type: "health_insurance",
    status: "analyzed",
    issuer_name: "Star Health & Allied Insurance",
    uploaded_at: "2026-09-18T05:30:00.000Z",
    confidence_score: 64,
  },
  {
    id: "17457fcf-87ea-42d4-8fd0-f3197446247d",
    user_id: "usr_0191eb5a-73d8-7910-b9df-20cb558b9190",
    filename: "HDFC_MF_Handbook_2024.pdf",
    document_type: "mutual_fund",
    status: "analyzed",
    issuer_name: "HDFC Asset Management Company Limited",
    uploaded_at: "2026-09-17T12:15:00.000Z",
    confidence_score: 26,
  },
];

export const MOCK_DOCUMENT_DETAIL: DocumentDetailResponse = {
  id: MOCK_DOCUMENT_ID,
  user_id: "usr_0191eb5a-73d8-7910-b9df-20cb558b9190",
  filename: "Star_Health_Optima_Policy.pdf",
  document_type: "health_insurance",
  storage_path: `documents/${MOCK_DOCUMENT_ID}/Star_Health_Optima_Policy.pdf`,
  status: "analyzed",
  pipeline_stage: "Analysis complete - Ready",
  issuer_name: "Star Health & Allied Insurance",
  uploaded_at: "2026-09-18T05:30:00.000Z",
  deleted_at: null,
};

export const MOCK_SUMMARY: DocumentSummaryResponse = {
  id: "sum_4a2c6d8e-1f0b-3e5a-7c9d-8b0e2f4a6c8e",
  document_id: MOCK_DOCUMENT_ID,
  language: "en",
  coverage: [
    "In-patient hospitalisation expenses up to Sum Insured (INR 5,00,000).",
    "Pre-hospitalisation medical expenses up to 60 days prior to admission.",
    "Post-hospitalisation medical expenses up to 90 days after discharge.",
    "Day care procedures covered across all listed standard treatments.",
  ],
  exclusions: [
    "Permanent exclusion on cosmetic, aesthetic treatments, and weight-loss surgeries.",
    "Adventure sports injuries excluded unless specifically endorsed.",
    "Self-inflicted injuries or conditions resulting from breach of law.",
  ],
  key_fees: [
    "Room rent capped at 1% of Sum Insured per day (INR 5,00,000 policy = INR 5,000/day max).",
    "Proportionate deduction clause applies on ICU & surgeon charges if room rent cap is breached.",
    "Mandatory 10% co-pay for treatments in non-network hospitals.",
  ],
  waiting_periods: [
    "Initial waiting period: 30 days for any non-accidental hospitalisation.",
    "Specified disease waiting period: 24 months for joint replacement, hernia, cataract.",
    "Pre-existing conditions (PED) waiting period: 36 months of continuous coverage.",
  ],
  notable_terms: [
    "Grace period: 30 days for policy renewal without loss of continuity benefits.",
    "Free look period: 15 days from receipt of policy document for cancellation with full refund.",
  ],
  model_version: "gemini-1.5-flash-fine-tune-v1",
  generated_at: "2026-09-18T05:31:00.000Z",
};

export const MOCK_SUMMARY_HI: DocumentSummaryResponse = {
  id: "sum_4a2c6d8e-1f0b-3e5a-7c9d-8b0e2f4a6c8e_hi",
  document_id: MOCK_DOCUMENT_ID,
  language: "hi",
  coverage: [
    "अस्पताल में भर्ती होने का खर्च बीमा राशि (INR 5,00,000) तक कवर्ड है।",
    "अस्पताल में भर्ती होने से 60 दिन पहले तक के चिकित्सा खर्च।",
    "डिस्चार्ज होने के बाद 90 दिनों तक का चिकित्सा खर्च।",
    "सभी मानक डे-केयर प्रक्रियाएं शामिल हैं।",
  ],
  exclusions: [
    "कॉस्मेटिक और सौंदर्य उपचार पर स्थायी बहिष्करण।",
    "साहसिक खेलों की चोटें तब तक शामिल नहीं हैं जब तक विशेष रूप से समर्थित न हों।",
    "कानून के उल्लंघन के कारण होने वाली चोटें शामिल नहीं हैं।",
  ],
  key_fees: [
    "कमरे का किराया प्रति दिन बीमा राशि का 1% (अधिकतम INR 5,000/दिन)।",
    "कमरे के किराए की सीमा पार होने पर आनुपातिक कटौती लागू होगी।",
    "गैर-नेटवर्क अस्पतालों में उपचार के लिए अनिवार्य 10% सह-भुगतान (co-pay)।",
  ],
  waiting_periods: [
    "प्रारंभिक प्रतीक्षा अवधि: किसी भी गैर-आकस्मिक बीमारी के लिए 30 दिन।",
    "विशिष्ट बीमारियों (हर्निया, मोतियाबिंद आदि) के लिए 24 महीने।",
    "पहले से मौजूद बीमारियों (PED) के लिए 36 महीने की निरंतर पॉलिसी।",
  ],
  notable_terms: [
    "नवीनीकरण छूट अवधि (Grace Period): निरंतरता लाभ खोए बिना 30 दिन।",
    "फ्री-लुक अवधि: पूरा रिफंड पाने के लिए पॉलिसी प्राप्ति के 15 दिन।",
  ],
  model_version: "gemini-1.5-flash-fine-tune-v1",
  generated_at: "2026-09-18T05:31:00.000Z",
};

export const MOCK_RED_FLAGS: RedFlagsResponse = {
  document_id: MOCK_DOCUMENT_ID,
  count: 3,
  red_flags: [
    {
      id: "rf_001_room_rent",
      document_id: MOCK_DOCUMENT_ID,
      pattern_id: "pat_irda_room_rent_01",
      chunk_id: "chk_page14_sec4",
      page_number: 14,
      clause_label: "Clause 4.2 - Room Rent Sub-limits",
      source_text:
        "The company's liability for room charges is restricted to 1% of Sum Insured per day. If the insured occupies a room with a higher rent, all associated medical expenses will be proportionately reduced.",
      severity: "high",
      plain_explanation:
        "This strict room-rent cap triggers proportionate deduction across your entire hospital bill (surgeon fees, nursing, medicines), frequently resulting in unexpected out-of-pocket deductions of 30-50%.",
      confirmed_by_llm: true,
      created_at: "2026-09-18T05:31:30.000Z",
    },
    {
      id: "rf_002_ped_waiting",
      document_id: MOCK_DOCUMENT_ID,
      pattern_id: "pat_irda_ped_waiting_02",
      chunk_id: "chk_page18_sec9",
      page_number: 18,
      clause_label: "Clause 9.1 - Pre-Existing Diseases Exclusion",
      source_text:
        "Any condition declared or undeclared for which symptoms occurred within 36 months prior to inception is excluded from coverage until 36 months of continuous renewals have elapsed.",
      severity: "medium",
      plain_explanation:
        "A 36-month waiting period for pre-existing ailments is longer than the industry median benchmark (24 months), which is a common basis for early claim repudiations in ombudsman records.",
      confirmed_by_llm: true,
      created_at: "2026-09-18T05:31:30.000Z",
    },
    {
      id: "rf_003_copay_nonnetwork",
      document_id: MOCK_DOCUMENT_ID,
      pattern_id: "pat_irda_copay_03",
      chunk_id: "chk_page22_sec12",
      page_number: 22,
      clause_label: "Clause 12.4 - Non-Network Hospital Co-payment",
      source_text:
        "An additional co-pay of 10% shall be borne by the insured person for each and every admissible claim treated at a non-network hospital.",
      severity: "low",
      plain_explanation:
        "Emergency admissions to nearby non-network hospitals incur an automatic 10% out-of-pocket cost deduction even if within your overall sum insured limit.",
      confirmed_by_llm: true,
      created_at: "2026-09-18T05:31:30.000Z",
    },
  ],
};

export const MOCK_CONFIDENCE_SCORE: ConfidenceScoreResponse = {
  id: "cs_91b7c3d5-2e4f-6a8b-0c2d-4e6f8a0b2c4d",
  document_id: MOCK_DOCUMENT_ID,
  score: 68,
  breakdown: [
    { reason: "Base transparency score", points: 100 },
    {
      reason: "High-severity penalty: Strict room rent sub-limit with proportionate deduction",
      points: -15,
    },
    {
      reason: "Medium-severity penalty: 36-month pre-existing condition waiting period",
      points: -8,
    },
    {
      reason: "Low-severity penalty: 10% non-network co-pay requirement",
      points: -3,
    },
    {
      reason: "Benchmark penalty: Room rent terms stricter than 75% of scraped market peers",
      points: -8,
    },
    {
      reason: "Transparency bonus: Clear disclosure of grievance redressal officer details",
      points: 2,
    },
  ],
  kb_version: "kb_v2026.09_irda_ombudsman",
  computed_at: "2026-09-18T05:31:45.000Z",
};

export const MOCK_CHAT_ANSWERS: Record<string, ChatResponse> = {
  room_rent: {
    id: "msg_room_rent_answer",
    document_id: MOCK_DOCUMENT_ID,
    role: "assistant",
    content:
      "Yes, your policy has a strict room rent cap. Under Clause 4.2 (Page 14), daily room rent is limited to 1% of the Sum Insured (INR 5,000/day). If you choose a room exceeding this limit, proportionate deduction will be applied across your entire hospital bill, including doctor fees and surgery costs.",
    cited_chunk_ids: ["chk_page14_sec4"],
    citations: [
      {
        chunk_id: "chk_page14_sec4",
        page_number: 14,
        clause_label: "Clause 4.2 - Room Rent Sub-limits",
        quote:
          "The company's liability for room charges is restricted to 1% of Sum Insured per day. If the insured occupies a room with a higher rent, all associated medical expenses will be proportionately reduced.",
      },
    ],
    created_at: "2026-09-18T05:32:00.000Z",
  },
  waiting_period: {
    id: "msg_ped_answer",
    document_id: MOCK_DOCUMENT_ID,
    role: "assistant",
    content:
      "According to Clause 9.1 (Page 18), pre-existing conditions have a waiting period of 36 months (3 years) of continuous coverage before any claims related to them will be admissible.",
    cited_chunk_ids: ["chk_page18_sec9"],
    citations: [
      {
        chunk_id: "chk_page18_sec9",
        page_number: 18,
        clause_label: "Clause 9.1 - Pre-Existing Diseases Exclusion",
        quote:
          "Any condition declared or undeclared for which symptoms occurred within 36 months prior to inception is excluded from coverage until 36 months of continuous renewals have elapsed.",
      },
    ],
    created_at: "2026-09-18T05:32:15.000Z",
  },
  default: {
    id: "msg_default_answer",
    document_id: MOCK_DOCUMENT_ID,
    role: "assistant",
    content:
      "Based on Clause 4.2 (Page 14) and Clause 9.1 (Page 18) of your policy, your coverage includes standard inpatient care up to INR 5,00,000, subject to a 1% room rent limit and a 36-month pre-existing condition exclusion period.",
    cited_chunk_ids: ["chk_page14_sec4", "chk_page18_sec9"],
    citations: [
      {
        chunk_id: "chk_page14_sec4",
        page_number: 14,
        clause_label: "Clause 4.2 - Room Rent Sub-limits",
        quote:
          "The company's liability for room charges is restricted to 1% of Sum Insured per day.",
      },
      {
        chunk_id: "chk_page18_sec9",
        page_number: 18,
        clause_label: "Clause 9.1 - Pre-Existing Diseases Exclusion",
        quote:
          "Any condition declared or undeclared for which symptoms occurred within 36 months prior to inception is excluded...",
      },
    ],
    created_at: "2026-09-18T05:32:30.000Z",
  },
};

export const MOCK_BENCHMARK_COMPARE: BenchmarkCompareResponse = {
  document_id: MOCK_DOCUMENT_ID,
  product_category: "health_insurance",
  issuer_name: "Star Health & Allied Insurance",
  target_attributes: {
    room_rent_cap: "1% of Sum Insured (max INR 5,000/day)",
    waiting_period_pre_existing: "36 months",
    co_pay_percent: "10% co-pay for non-network hospitals",
    claim_settlement_ratio: "89.9%",
  },
  comparables: [
    {
      id: "bp_001_care_supreme",
      product_category: "health_insurance",
      issuer_name: "Care Health Insurance",
      product_name: "Care Supreme",
      source_url: "https://www.careinsurance.com/product/care-supreme",
      attributes: {
        room_rent_cap: "No room rent sub-limit (Any room category allowed)",
        waiting_period_pre_existing: "24 months (optional 12 months buyback)",
        co_pay_percent: "0% co-pay across network & non-network",
        claim_settlement_ratio: "95.2%",
        annual_bonus: "50% cumulative bonus up to 100%",
      },
      complaint_signal: {
        source: "IRDAI Ombudsman Annual Report 2024",
        complaints_per_10k_policies: 14.2,
      },
      last_scraped_at: "2026-09-17T18:00:00.000Z",
    },
    {
      id: "bp_002_hdfc_ergo_optima",
      product_category: "health_insurance",
      issuer_name: "HDFC ERGO General Insurance",
      product_name: "Optima Secure",
      source_url: "https://www.hdfcergo.com/health-insurance/optima-secure",
      attributes: {
        room_rent_cap: "No room rent capping",
        waiting_period_pre_existing: "36 months",
        co_pay_percent: "0% co-pay standard",
        claim_settlement_ratio: "97.5%",
        annual_bonus: "100% instant sum insured restoration",
      },
      complaint_signal: {
        source: "IRDAI Ombudsman Annual Report 2024",
        complaints_per_10k_policies: 9.8,
      },
      last_scraped_at: "2026-09-17T18:00:00.000Z",
    },
    {
      id: "bp_003_niva_bupa_reassure",
      product_category: "health_insurance",
      issuer_name: "Niva Bupa Health Insurance",
      product_name: "ReAssure 2.0",
      source_url: "https://www.nivabupa.com/health-insurance-plans/reassure-2-0.html",
      attributes: {
        room_rent_cap: "Single private room without capping",
        waiting_period_pre_existing: "24 months",
        co_pay_percent: "0% co-pay",
        claim_settlement_ratio: "91.6%",
        annual_bonus: "Lock the clock age-based premium discount",
      },
      complaint_signal: {
        source: "IRDAI Ombudsman Annual Report 2024",
        complaints_per_10k_policies: 18.5,
      },
      last_scraped_at: "2026-09-17T18:00:00.000Z",
    },
  ],
  last_scraped_at: "2026-09-17T18:00:00.000Z",
  data_freshness_label: "Benchmark data refreshed within the last 3 days",
};
