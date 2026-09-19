export type Language = "en" | "hi";

export interface TranslationDict {
  // Navigation & General
  nav: {
    brandName: string;
    brandTag: string;
    upload: string;
    myDocuments: string;
    switchDoc: string;
    noDocs: string;
    login: string;
    signup: string;
    logout: string;
    account: string;
    disclaimer: string;
    disclaimerHighlight: string;
  };

  // Home / Landing
  home: {
    heroBadge: string;
    heroTitlePrefix: string;
    heroTitleHighlight: string;
    heroTitleSuffix: string;
    heroSubtitle: string;
    ctaUpload: string;
    ctaSample: string;
    trustTitle: string;
    feat1Title: string;
    feat1Desc: string;
    feat2Title: string;
    feat2Desc: string;
    feat3Title: string;
    feat3Desc: string;
    feat4Title: string;
    feat4Desc: string;
  };

  // Upload
  upload: {
    pageTitle: string;
    pageSubtitle: string;
    dragDropText: string;
    dragDropSubtext: string;
    selectDocType: string;
    typeHealth: string;
    typeLoan: string;
    typeMf: string;
    stageUploading: string;
    stageExtracting: string;
    stageChunking: string;
    stageAnalyzing: string;
    privacyNote: string;
    uploadButton: string;
    analyzingButton: string;
  };

  // Dashboard / Doc Overview
  doc: {
    policyAnalysis: string;
    riskScore: string;
    highRisk: string;
    mediumRisk: string;
    lowRisk: string;
    confidenceScore: string;
    confidenceScoreDesc: string;
    chatCta: string;
    chatCtaDesc: string;
    compareCta: string;
    compareCtaDesc: string;
    redFlagsTitle: string;
    redFlagsCount: string;
    noRedFlagsTitle: string;
    noRedFlagsDesc: string;
    summaryTitle: string;
    tabCoverage: string;
    tabExclusions: string;
    tabFees: string;
    tabWaiting: string;
    tabTerms: string;
    noItemsInTab: string;
    retryButton: string;
    verifiedOnPage: string;
    processing: string;
    uploadedOn: string;
    compareButton: string;
    chatButton: string;
    interactiveAssistant: string;
    assistantDescription: string;
    openChatbot: string;
    viewAlternatives: string;
  };

  // Comparison & Better Policies
  compare: {
    title: string;
    subtitle: string;
    backToDash: string;
    dataFreshness: string;
    betterPoliciesTitle: string;
    betterPoliciesSubtitle: string;
    whyBetter: string;
    keyAdvantages: string;
    potentialSavings: string;
    visitOfficialSite: string;
    featureHeader: string;
    yourPolicyHeader: string;
    competitorBrochure: string;
    roomRent: string;
    waitingPeriod: string;
    coPay: string;
    claimRatio: string;
    ombudsmanGrievances: string;
    sourceTransparency: string;
  };

  // Chat
  chat: {
    pageTitle: string;
    pageSubtitle: string;
    backToDash: string;
    inputPlaceholder: string;
    suggestedHeading: string;
    suggestedQuestions: string[];
    citationsHeader: string;
    policiesRefHeader: string;
    pageLabel: string;
    sendButton: string;
    typingIndicator: string;
    notGroundedNote: string;
  };
}

export const translations: Record<Language, TranslationDict> = {
  en: {
    nav: {
      brandName: "Docs",
      brandTag: "Decoded",
      upload: "Upload",
      myDocuments: "My Documents",
      switchDoc: "Select Policy",
      noDocs: "No documents uploaded yet",
      login: "Log In",
      signup: "Sign Up",
      logout: "Log Out",
      account: "Account",
      disclaimer: "Informational analysis only. Not financial or legal advice. Always verify with official policy terms.",
      disclaimerHighlight: "IRDAI / DPDP Compliant",
    },
    home: {
      heroBadge: "AI Financial Policy Intelligence",
      heroTitlePrefix: "Decode Fine Print.",
      heroTitleHighlight: "Uncover Hidden Risks.",
      heroTitleSuffix: "Find Better Policies.",
      heroSubtitle: "Upload your health insurance, loan contract, or mutual fund handbook in English or Hindi. Our AI identifies trap clauses, evaluates your risk score, and scrapes online market benchmarks to suggest superior alternatives.",
      ctaUpload: "Analyze My Document Free",
      ctaSample: "View Sample Star Health Analysis",
      trustTitle: "Trusted by Indian Policyholders Across 15+ Insurers",
      feat1Title: "Trap Clause & Red Flag Detection",
      feat1Desc: "Instantly flags room-rent sub-limits, proportionate deductions, pre-existing disease exclusions, and co-pay traps with exact page citations.",
      feat2Title: "Online Market Benchmark & Scraper",
      feat2Desc: "Automated n8n and web scraping workflows compare your terms against top competitor policies (Care, HDFC ERGO, Niva Bupa) to recommend better options.",
      feat3Title: "Dual-Context Conversational Chat",
      feat3Desc: "Ask any detailed question about your uploaded document or explore why recommended competitor policies offer higher savings and broader coverage.",
      feat4Title: "Full Multilingual English & Hindi",
      feat4Desc: "Upload documents written in Hindi or English and switch the entire platform into pure Hindi at any moment.",
    },
    upload: {
      pageTitle: "Upload Your Financial Policy or Agreement",
      pageSubtitle: "Supports PDF documents in English and Hindi (Text-native and Scanned with OCR)",
      dragDropText: "Click to upload or drag and drop your document",
      dragDropSubtext: "Health Insurance Policy, Loan Agreement, or Mutual Fund Factsheet (Max 25MB)",
      selectDocType: "Document Category",
      typeHealth: "Health Insurance",
      typeLoan: "Loan Agreement",
      typeMf: "Mutual Fund",
      stageUploading: "Securely uploading file...",
      stageExtracting: "Extracting text and running multilingual OCR...",
      stageChunking: "Parsing clauses and section boundaries...",
      stageAnalyzing: "LLM detecting red flags and scoring risk...",
      privacyNote: "Your data is processed in strict compliance with the Digital Personal Data Protection (DPDP) Act. All Personally Identifiable Information (PII) is masked.",
      uploadButton: "Start AI Analysis",
      analyzingButton: "Analyzing Policy...",
    },
    doc: {
      policyAnalysis: "Policy Analysis",
      riskScore: "Risk Assessment",
      highRisk: "High Risk Detected",
      mediumRisk: "Moderate Risk",
      lowRisk: "Low Risk (Favorable Terms)",
      confidenceScore: "Transparency Score",
      confidenceScoreDesc: "Based on clause fairness, room rent caps, co-pay, and market benchmarking.",
      chatCta: "Ask Policy AI Chat",
      chatCtaDesc: "Ask questions about this policy and compare with suggested alternatives.",
      compareCta: "Market Comparison & Better Policies",
      compareCtaDesc: "See how your policy compares to Care, HDFC ERGO, and Niva Bupa with official links.",
      redFlagsTitle: "Red Flags & Trap Clauses Detected",
      redFlagsCount: "flags identified",
      noRedFlagsTitle: "No Critical Red Flags Detected",
      noRedFlagsDesc: "Your policy does not contain severe room-rent caps or restrictive proportionate deduction clauses.",
      summaryTitle: "Plain-Language Policy Summary",
      tabCoverage: "Coverage & Benefits",
      tabExclusions: "Exclusions",
      tabFees: "Fees & Deductions",
      tabWaiting: "Waiting Periods",
      tabTerms: "Notable Terms",
      noItemsInTab: "No specific items specified in this section.",
      retryButton: "Retry Analysis",
      verifiedOnPage: "Verified on Page",
      processing: "Analyzing Document Clauses...",
      uploadedOn: "Uploaded on",
      compareButton: "Compare Alternatives",
      chatButton: "Ask Policy AI",
      interactiveAssistant: "Interactive Policy Assistant",
      assistantDescription: "Have questions about clauses, deductions, or whether an alternative policy is better for you? Chat with our AI grounded directly in your document.",
      openChatbot: "Open Policy AI Chat",
      viewAlternatives: "View Market Benchmarks",
    },
    compare: {
      title: "Market Intelligence & Better Policy Recommendations",
      subtitle: "How your uploaded policy compares against leading market benchmarks scraped online",
      backToDash: "Back to Dashboard",
      dataFreshness: "Verified live market intelligence (Updated weekly)",
      betterPoliciesTitle: "Recommended Better Policies Online",
      betterPoliciesSubtitle: "Top-rated alternative contracts that eliminate your policy's red flags with direct official links",
      whyBetter: "Why It's Better:",
      keyAdvantages: "Key Advantages:",
      potentialSavings: "Potential Out-of-Pocket Savings:",
      visitOfficialSite: "Visit Official Website",
      featureHeader: "Feature / Clause",
      yourPolicyHeader: "Your Policy (Uploaded)",
      competitorBrochure: "Official Brochure",
      roomRent: "Room Rent Sub-Limit",
      waitingPeriod: "Pre-Existing Disease Waiting Period",
      coPay: "Co-Payment Requirement",
      claimRatio: "Claim Settlement Ratio",
      ombudsmanGrievances: "Ombudsman Grievances (per 10k)",
      sourceTransparency: "Source Transparency",
    },
    chat: {
      pageTitle: "Policy AI Assistant",
      pageSubtitle: "Ask anything about your uploaded document or explore suggested better policies",
      backToDash: "Back to Dashboard",
      inputPlaceholder: "Ask about room rent limits, exclusions, or compare with Care Supreme...",
      suggestedHeading: "Suggested Questions:",
      suggestedQuestions: [
        "What is my room rent limit and does it have proportionate deductions?",
        "What is the waiting period for pre-existing diseases?",
        "Why is Care Supreme recommended over my current policy?",
        "How does HDFC ERGO Optima Secure differ in claim settlement?",
      ],
      citationsHeader: "Sources from your document:",
      policiesRefHeader: "Suggested Policies Referenced:",
      pageLabel: "Page",
      sendButton: "Send",
      typingIndicator: "AI is analyzing clauses and market benchmarks...",
      notGroundedNote: "Answers are grounded strictly in your document clauses and verified competitor benchmarks.",
    },
  },

  hi: {
    nav: {
      brandName: "डॉक्स",
      brandTag: "डिकोडेड",
      upload: "अपलोड करें",
      myDocuments: "मेरे दस्तावेज़",
      switchDoc: "पॉलिसी चुनें",
      noDocs: "अभी कोई दस्तावेज़ अपलोड नहीं है",
      login: "लॉग इन",
      signup: "साइन अप",
      logout: "लॉग आउट",
      account: "खाता",
      disclaimer: "यह केवल सूचनात्मक विश्लेषण है, वित्तीय या कानूनी सलाह नहीं। आधिकारिक पॉलिसी शर्तों की पुष्टि करें।",
      disclaimerHighlight: "IRDAI / DPDP अनुपालन",
    },
    home: {
      heroBadge: "एआई वित्तीय पॉलिसी विश्लेषण",
      heroTitlePrefix: "बारीक शर्तों को समझें।",
      heroTitleHighlight: "छिपे जोखिम पहचानें।",
      heroTitleSuffix: "बेहतर पॉलिसी पाएं।",
      heroSubtitle: "अपनी स्वास्थ्य बीमा, ऋण अनुबंध या म्यूचुअल फंड दस्तावेज़ हिंदी या अंग्रेजी में अपलोड करें। हमारा एआई जोखिम भरे क्लॉज की पहचान करता है, रिस्क स्कोर की गणना करता है और बेहतर पॉलिसी का सुझाव देता है।",
      ctaUpload: "दस्तावेज़ का मुफ्त विश्लेषण करें",
      ctaSample: "स्टार हेल्थ का नमूना विश्लेषण देखें",
      trustTitle: "15+ से अधिक प्रमुख बीमा कंपनियों के पॉलिसीधारकों द्वारा विश्वसनीय",
      feat1Title: "छिपे क्लॉज और रेड फ्लैग पहचान",
      feat1Desc: "रूम-रेंट सब-लिमिट, आनुपातिक कटौती, पूर्व-मौजूदा बीमारियों की प्रतीक्षा अवधि और को-पेमेंट जैसे जोखिमों को तुरंत पृष्ठ संदर्भ के साथ दर्शाता है।",
      feat2Title: "ऑनलाइन बाजार तुलना और स्क्रैपर",
      feat2Desc: "स्वचालित वेब स्क्रैपर और n8n पाइपलाइन आपकी पॉलिसी की तुलना केयर, एचडीएफसी एर्गो, निवा बूपा से करके बेहतर विकल्प सुझाते हैं।",
      feat3Title: "इंटरैक्टिव एआई चैटबॉट",
      feat3Desc: "अपनी अपलोड की गई पॉलिसी या सुझाई गई वैकल्पिक पॉलिसियों के बारे में कोई भी प्रश्न विस्तार से पूछें।",
      feat4Title: "पूर्ण हिंदी और अंग्रेजी भाषा समर्थन",
      feat4Desc: "हिंदी या अंग्रेजी में दस्तावेज़ अपलोड करें और कभी भी पूरी वेबसाइट को शुद्ध हिंदी में बदलें।",
    },
    upload: {
      pageTitle: "अपनी पॉलिसी या अनुबंध अपलोड करें",
      pageSubtitle: "हिंदी और अंग्रेजी में पीडीएफ का पूर्ण समर्थन (डिजिटल और ओसीआर स्कैन)",
      dragDropText: "फ़ाइल अपलोड करने के लिए क्लिक करें या यहाँ खींचें",
      dragDropSubtext: "स्वास्थ्य बीमा, ऋण अनुबंध, या म्यूचुअल फंड फैक्टशीट (अधिकतम 25MB)",
      selectDocType: "दस्तावेज़ का प्रकार",
      typeHealth: "स्वास्थ्य बीमा (Health Insurance)",
      typeLoan: "ऋण अनुबंध (Loan Agreement)",
      typeMf: "म्यूचुअल फंड (Mutual Fund)",
      stageUploading: "फ़ाइल सुरक्षित रूप से अपलोड हो रही है...",
      stageExtracting: "टेक्स्ट निकाला जा रहा है और ओसीआर चल रहा है...",
      stageChunking: "क्लॉज और अनुभाग अलग किए जा रहे हैं...",
      stageAnalyzing: "एआई जोखिम और रेड फ्लैग्स का विश्लेषण कर रहा है...",
      privacyNote: "आपका डेटा डिजिटल पर्सनल डेटा प्रोटेक्शन (DPDP) अधिनियम के तहत सुरक्षित है। सभी व्यक्तिगत पहचान (PII) छिपाई जाती है।",
      uploadButton: "एआई विश्लेषण शुरू करें",
      analyzingButton: "विश्लेषण जारी है...",
    },
    doc: {
      policyAnalysis: "पॉलिसी विश्लेषण",
      riskScore: "जोखिम मूल्यांकन",
      highRisk: "उच्च जोखिम पाया गया",
      mediumRisk: "मध्यम जोखिम",
      lowRisk: "कम जोखिम (सुरक्षित शर्तें)",
      confidenceScore: "पारदर्शिता स्कोर",
      confidenceScoreDesc: "क्लॉज निष्पक्षता, रूम रेंट सीमा, को-पे और बाजार तुलना के आधार पर।",
      chatCta: "पॉलिसी एआई चैट",
      chatCtaDesc: "इस पॉलिसी के बारे में पूछें और वैकल्पिक पॉलिसियों से तुलना करें।",
      compareCta: "बाजार तुलना और बेहतर पॉलिसियाँ",
      compareCtaDesc: "देखें कि आपकी पॉलिसी केयर, एचडीएफसी एर्गो से कैसे बेहतर या कमजोर है।",
      redFlagsTitle: "पहचाने गए रेड फ्लैग्स और जोखिम",
      redFlagsCount: "जोखिम क्लॉज पाए गए",
      noRedFlagsTitle: "कोई गंभीर रेड फ्लैग नहीं मिला",
      noRedFlagsDesc: "आपकी पॉलिसी में कोई हानिकारक रूम रेंट सब-लिमिट या अनुचित कटौती क्लॉज नहीं है।",
      summaryTitle: "सरल भाषा में पॉलिसी सारांश",
      tabCoverage: "कवर किए गए लाभ",
      tabExclusions: "शामिल नहीं (अपवाद)",
      tabFees: "शुल्क व कटौती",
      tabWaiting: "प्रतीक्षा अवधि",
      tabTerms: "महत्वपूर्ण शर्तें",
      noItemsInTab: "इस अनुभाग में कोई विशिष्ट विवरण नहीं है।",
      retryButton: "पुनः विश्लेषण करें",
      verifiedOnPage: "पृष्ठ पर सत्यापित",
      processing: "दस्तावेज़ का विश्लेषण हो रहा है...",
      uploadedOn: "अपलोड किया गया",
      compareButton: "विकल्पों की तुलना करें",
      chatButton: "पॉलिसी AI से पूछें",
      interactiveAssistant: "इंटरैक्टिव पॉलिसी सहायक",
      assistantDescription: "क्या आपके पास क्लॉज, कटौतियों या बेहतर पॉलिसी विकल्पों के बारे में सवाल हैं? सीधे अपने दस्तावेज़ पर आधारित AI से पूछें।",
      openChatbot: "पॉलिसी AI चैट खोलें",
      viewAlternatives: "बाजार मानक देखें",
    },
    compare: {
      title: "बाजार तुलना और बेहतर पॉलिसी सुझाव",
      subtitle: "आपकी पॉलिसी बनाम ऑनलाइन स्क्रैप की गई अग्रणी बाजार पॉलिसियों की सीधी तुलना",
      backToDash: "डैशबोर्ड पर वापस जाएं",
      dataFreshness: "सत्यापित लाइव बाजार डेटा (साप्ताहिक अपडेट)",
      betterPoliciesTitle: "ऑनलाइन अनुशंसित बेहतर पॉलिसियाँ",
      betterPoliciesSubtitle: "शीर्ष रेटेड पॉलिसियाँ जो आपकी पॉलिसी के जोखिमों को समाप्त करती हैं (सीधे आधिकारिक लिंक सहित)",
      whyBetter: "यह बेहतर क्यों है:",
      keyAdvantages: "मुख्य लाभ:",
      potentialSavings: "संभावित बचत:",
      visitOfficialSite: "आधिकारिक वेबसाइट पर जाएं",
      featureHeader: "विशेषता / क्लॉज",
      yourPolicyHeader: "आपकी पॉलिसी (अपलोड की गई)",
      competitorBrochure: "आधिकारिक विवरणिका",
      roomRent: "रूम रेंट सब-लिमिट",
      waitingPeriod: "पूर्व-मौजूदा बीमारी प्रतीक्षा अवधि",
      coPay: "को-पेमेंट की शर्त",
      claimRatio: "क्लेम सेटलमेंट अनुपात",
      ombudsmanGrievances: "ओम्बड्समैन शिकायतें (प्रति 10 हज़ार)",
      sourceTransparency: "स्रोत पारदर्शिता",
    },
    chat: {
      pageTitle: "पॉलिसी एआई सहायक",
      pageSubtitle: "अपनी पॉलिसी या सुझाई गई बेहतर पॉलिसियों के बारे में विस्तार से पूछें",
      backToDash: "डैशबोर्ड पर वापस जाएं",
      inputPlaceholder: "रूम रेंट सीमा, अपवादों या केयर सुप्रीम से तुलना के बारे में पूछें...",
      suggestedHeading: "सुझाए गए प्रश्न:",
      suggestedQuestions: [
        "मेरी पॉलिसी में रूम रेंट की क्या सीमा है और क्या इसमें आनुपातिक कटौती है?",
        "पहले से मौजूद बीमारियों के लिए प्रतीक्षा अवधि क्या है?",
        "केयर सुप्रीम मेरी वर्तमान पॉलिसी से बेहतर क्यों है?",
        "एचडीएफसी एर्गो ऑप्टिमा सिक्योर में क्लेम सेटलमेंट कैसे बेहतर है?",
      ],
      citationsHeader: "आपके दस्तावेज़ से उद्धरण:",
      policiesRefHeader: "संदर्भित अनुशंसित पॉलिसियाँ:",
      pageLabel: "पृष्ठ",
      sendButton: "भेजें",
      typingIndicator: "एआई क्लॉज और बाजार डेटा का विश्लेषण कर रहा है...",
      notGroundedNote: "उत्तर केवल आपके दस्तावेज़ और सत्यापित प्रतिस्पर्धी बाजार डेटा पर आधारित हैं।",
    },
  },
};
