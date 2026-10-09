"""
SwasthyaConnect — Dynamic UI Localization System
Provides instant multilingual labels across all dashboard components,
buttons, cards, headers, tables, and settings.
"""

from typing import Dict, Any

UI_STRINGS: Dict[str, Dict[str, str]] = {
    # --- Sidebar Menu Items ---
    "Dashboard": {
        "en": "Dashboard",
        "hi": "डैशबोर्ड",
        "mr": "डॅशबोर्ड",
        "ta": "டாஷ்போர்டு",
        "bn": "ড্যাশবোর্ড",
        "te": "డాష్‌బోర్డ్",
        "kn": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "gu": "ડેશબોર્ડ",
    },
    "AI Assistant": {
        "en": "AI Assistant",
        "hi": "एआई सहायक",
        "mr": "एआय सहाय्यक",
        "ta": "AI உதவியாளர்",
        "bn": "এআই সহকারী",
        "te": "AI అసిస్టెంట్",
        "kn": "AI ಸಹಾಯಕ",
        "gu": "AI સહાયક",
    },
    "Find Doctor": {
        "en": "Find Doctor",
        "hi": "डॉक्टर खोजें",
        "mr": "डॉक्टर शोधा",
        "ta": "மருத்துவரை தேடுங்கள்",
        "bn": "ডাক্তার খুঁজুন",
        "te": "వైద్యుడిని కనుగొనండి",
        "kn": "ವೈದ್ಯರನ್ನು ಹುಡುಕಿ",
        "gu": "ડૉક્ટર શોધો",
    },
    "My Records": {
        "en": "My Records",
        "hi": "मेरे रिकॉर्ड्स",
        "mr": "माझे रेकॉर्ड्स",
        "ta": "என் பதிவுகள்",
        "bn": "আমার রেকর্ড",
        "te": "నా రికార్డులు",
        "kn": "ನನ್ನ ದಾಖಲೆಗಳು",
        "gu": "મારા રેકોર્ડ્સ",
    },
    "Appointments": {
        "en": "Appointments",
        "hi": "अपॉइंटमेंट्स",
        "mr": "अपॉइंटमेंट्स",
        "ta": "நியமனங்கள்",
        "bn": "অ্যাপয়েন্টমেন্ট",
        "te": "అపాయింట్‌మెంట్లు",
        "kn": "ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್‌ಗಳು",
        "gu": "મુલાકાતો",
    },
    "Prescriptions": {
        "en": "Prescriptions",
        "hi": "नुस्खे (प्रिस्क्रिप्शन)",
        "mr": "प्रिस्क्रिप्शन्स",
        "ta": "மருந்துச் சீட்டுகள்",
        "bn": "প্রেসক্রিপশন",
        "te": "ప్రిస్క్రిప్షన్లు",
        "kn": "ಔಷಧಿ ಚೀಟಿಗಳು",
        "gu": "પ્રિસ્ક્રિપ્શનો",
    },
    "Treatment Status": {
        "en": "Treatment Status",
        "hi": "उपचार स्थिति",
        "mr": "उपचार स्थिती",
        "ta": "சிகிச்சை நிலை",
        "bn": "চিকিৎসার স্থিতি",
        "te": "చికిత్స స్థితి",
        "kn": "ಚಿಕಿತ್ಸೆಯ ಸ್ಥಿತಿ",
        "gu": "સારવારની સ્થિતિ",
    },
    "Medicine Verification": {
        "en": "Medicine Verification",
        "hi": "दवा सत्यापन",
        "mr": "औषध पडताळणी",
        "ta": "மருந்து சரிபார்ப்பு",
        "bn": "ওষুধ যাচাইকরণ",
        "te": "మందుల ధృవీకరణ",
        "kn": "ಔಷಧಿ ಪರಿಶೀಲನೆ",
        "gu": "દવા ચકાસણી",
    },
    "🔗 Health Integrity": {
        "en": "🔗 Health Integrity",
        "hi": "🔗 स्वास्थ्य अखंडता",
        "mr": "🔗 आरोग्य अखंडता",
        "ta": "🔗 சுகாதார ஒருமைப்பாடு",
        "bn": "🔗 স্বাস্থ্য অখণ্ডতা",
        "te": "🔗 ఆరోగ్య సమగ్రత",
        "kn": "🔗 ಆರೋಗ್ಯ ಸಮಗ್ರತೆ",
        "gu": "🔗 આરોગ્ય અખંડિતતા",
    },
    "Settings": {
        "en": "Settings",
        "hi": "सेटिंग्स",
        "mr": "सेटिंग्ज",
        "ta": "அமைப்புகள்",
        "bn": "সেটিংস",
        "te": "సెట్టింగ్‌లు",
        "kn": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "gu": "સેટિંગ્સ",
    },
    "Logout": {
        "en": "Logout",
        "hi": "लॉग आउट",
        "mr": "लॉग आउट",
        "ta": "வெளியேறு",
        "bn": "লগ আউট",
        "te": "లాగ్ అవుట్",
        "kn": "ಲಾಗ್ ಔಟ್",
        "gu": "લૉગ આઉટ",
    },

    # --- Home Page Greetings & Subtitle ---
    "Good morning": {
        "en": "Good morning",
        "hi": "सुप्रभात",
        "mr": "शुभ सकाळ",
        "ta": "காலை வணக்கம்",
        "bn": "সুপ্রভাত",
        "te": "శుభోదయం",
        "kn": "ಶುಭೋದಯ",
        "gu": "શુભ સવાર",
    },
    "Good afternoon": {
        "en": "Good afternoon",
        "hi": "शुभ दोपहर",
        "mr": "शुभ दुपार",
        "ta": "மதிய வணக்கம்",
        "bn": "শুভ দুপুর",
        "te": "శుభ మధ్యాహ్నం",
        "kn": "ಶುಭ ಮಧ್ಯಾಹ್ನ",
        "gu": "શુભ બપોર",
    },
    "Good evening": {
        "en": "Good evening",
        "hi": "शुभ संध्या",
        "mr": "शुभ संध्याकाळ",
        "ta": "மாலை வணக்கம்",
        "bn": "শুভ সন্ধ্যা",
        "te": "శుభ సాయంత్రం",
        "kn": "ಶುಭ ಸಂಜೆ",
        "gu": "શુભ સાંજ",
    },
    "subtitle": {
        "en": "Your AI Health Control Center — All your medical history in one place.",
        "hi": "आपका एआई स्वास्थ्य नियंत्रण केंद्र — आपका संपूर्ण चिकित्सा इतिहास एक ही स्थान पर।",
        "mr": "तुमचे एआय आरोग्य नियंत्रण केंद्र — तुमचा सर्व वैद्यकीय इतिहास एकाच ठिकाणी.",
        "ta": "உங்கள் AI சுகாதார கட்டுப்பாட்டு மையம் — உங்கள் முழு மருத்துவ வரலாறும் ஓரிடத்தில்.",
        "bn": "আপনার এআই স্বাস্থ্য নিয়ন্ত্রণ কেন্দ্র — সমস্ত চিকিৎসার ইতিহাস এক জায়গায়।",
        "te": "మీ AI ఆరోగ్య నియంత్రణ కేంద్రం — మీ వైద్య చరిత్ర మొత్తం ఒకే చోట.",
        "kn": "ನಿಮ್ಮ AI ಆರೋಗ್ಯ ನಿಯಂತ್ರಣ ಕೇಂದ್ರ — ನಿಮ್ಮ ಸಂಪೂರ್ಣ ವೈದ್ಯಕೀಯ ಇತಿಹಾಸ ಒಂದೇ ಸ್ಥಳದಲ್ಲಿ.",
        "gu": "તમારું AI આરોગ્ય નિયંત્રણ કેન્દ્ર — તમારો તમામ તબીબી ઇતિહાસ એક જ જગ્યાએ.",
    },

    # --- Top Stats Cards ---
    "Health Stability": {
        "en": "Health Stability",
        "hi": "स्वास्थ्य स्थिरता",
        "mr": "आरोग्य स्थिरता",
    },
    "AI assessment": {
        "en": "AI assessment",
        "hi": "एआई मूल्यांकन",
        "mr": "एआय मूल्यांकन",
    },
    "Active Conditions": {
        "en": "Active Conditions",
        "hi": "सक्रिय स्थितियां",
        "mr": "सक्रिय आजार",
    },
    "Currently tracked": {
        "en": "Currently tracked",
        "hi": "वर्तमान में ट्रैक किए गए",
        "mr": "सध्या ट्रॅक केलेले",
    },
    "Active Medications": {
        "en": "Active Medications",
        "hi": "सक्रिय दवाएं",
        "mr": "सक्रिय औषधे",
    },
    "From prescriptions": {
        "en": "From prescriptions",
        "hi": "प्रिस्क्रिप्शन से",
        "mr": "प्रिस्क्रिप्शनवरून",
    },
    "Reports Uploaded": {
        "en": "Reports Uploaded",
        "hi": "अपलोड की गई रिपोर्टें",
        "mr": "अपलोड केलेले अहवाल",
    },
    "Analyzer status": {
        "en": "Analyzer status",
        "hi": "विश्लेषक स्थिति",
        "mr": "विश्लेषक स्थिती",
    },
    "Total visits": {
        "en": "Total visits",
        "hi": "कुल मुलाक़ातें",
        "mr": "एकूण भेटी",
    },
    "Emergency Risk": {
        "en": "Emergency Risk",
        "hi": "आपातकालीन जोखिम",
        "mr": "तातडीचा धोका",
    },
    "Based on vitals": {
        "en": "Based on vitals",
        "hi": "महत्वपूर्ण संकेतों पर आधारित",
        "mr": "महत्त्वाच्या लक्षणांवर आधारित",
    },
    "Low": {
        "en": "Low",
        "hi": "कम",
        "mr": "कमी",
    },
    "Elevated": {
        "en": "Elevated",
        "hi": "बढ़ा हुआ",
        "mr": "वाढलेला",
    },

    # --- Timeline Section ---
    "Medical History Timeline": {
        "en": "📅 Medical History Timeline",
        "hi": "📅 चिकित्सा इतिहास टाइमलाइन",
        "mr": "📅 वैद्यकीय इतिहास टाइमलाइन",
    },
    "No medical history found. Upload reports or book appointments to see your timeline here.": {
        "en": "No medical history found. Upload reports or book appointments to see your timeline here.",
        "hi": "कोई चिकित्सा इतिहास नहीं मिला। अपनी टाइमलाइन देखने के लिए रिपोर्ट अपलोड करें या अपॉइंटमेंट बुक करें।",
        "mr": "कोणताही वैद्यकीय इतिहास आढळला नाही. आपली टाइमलाइन पाहण्यासाठी अहवाल अपलोड करा किंवा अपॉइंटमेंट बुक करा.",
    },
    "more_events_template": {
        "en": "... and {count} more events. View full history in My Records.",
        "hi": "... और {count} अधिक घटनाएं। मेरे रिकॉर्ड्स में पूरा इतिहास देखें।",
        "mr": "... आणि आणखी {count} नोंदी. माझे रेकॉर्ड्स मध्ये पूर्ण इतिहास पहा.",
    },

    # --- Analytics & Charts ---
    "Disease / Diagnosis Trend": {
        "en": "📊 Disease / Diagnosis Trend",
        "hi": "📊 रोग / निदान प्रवृत्ति",
        "mr": "📊 रोग / निदान ट्रेंड",
    },
    "Upload reports to see disease trends.": {
        "en": "Upload reports to see disease trends.",
        "hi": "रोग के रुझान देखने के लिए रिपोर्ट अपलोड करें।",
        "mr": "रोगांचे ट्रेंड पाहण्यासाठी अहवाल अपलोड करा.",
    },
    "Vitals Timeline": {
        "en": "🩺 Vitals Timeline",
        "hi": "🩺 वाइटल्स टाइमलाइन",
        "mr": "🩺 वाइटल्स टाइमलाइन",
    },
    "No vitals extracted yet.\nUpload reports to populate.": {
        "en": "No vitals extracted yet.\nUpload reports to populate.",
        "hi": "अभी तक कोई महत्वपूर्ण संकेत नहीं निकाले गए।\nभरने के लिए रिपोर्ट अपलोड करें।",
        "mr": "अद्याप कोणतीही महत्त्वपूर्ण लक्षणे नोंदवली नाहीत.\nनोंदवण्यासाठी अहवाल अपलोड करा.",
    },
    "Heart Rate (bpm)": {
        "en": "Heart Rate (bpm)",
        "hi": "हृदय गति (bpm)",
        "mr": "हृदय गती (bpm)",
    },
    "No HR data extracted yet.": {
        "en": "No HR data extracted yet.",
        "hi": "अभी तक हृदय गति का कोई डेटा उपलब्ध नहीं है।",
        "mr": "अद्याप हृदय गतीचा कोणताही डेटा उपलब्ध नाही.",
    },

    # --- Bottom Cards ---
    "Recent Reports": {
        "en": "📝 Recent Reports",
        "hi": "📝 हाल की रिपोर्टें",
        "mr": "📝 अलीकडील अहवाल",
    },
    "No reports uploaded yet.": {
        "en": "No reports uploaded yet.",
        "hi": "अभी तक कोई रिपोर्ट अपलोड नहीं की गई।",
        "mr": "अद्याप कोणताही अहवाल अपलोड केलेला नाही.",
    },
    "Key Findings & Vital Signs": {
        "en": "🔬 Key Findings & Vital Signs",
        "hi": "🔬 मुख्य निष्कर्ष और महत्वपूर्ण संकेत",
        "mr": "🔬 प्रमुख निष्कर्ष आणि महत्त्वपूर्ण लक्षणे",
    },
    "No detailed findings available.\nUpload a report to extract vitals and findings.": {
        "en": "No detailed findings available.\nUpload a report to extract vitals and findings.",
        "hi": "कोई विस्तृत निष्कर्ष उपलब्ध नहीं है।\nवाइटल्स और निष्कर्ष निकालने के लिए एक रिपोर्ट अपलोड करें।",
        "mr": "कोणतेही तपशीलवार निष्कर्ष उपलब्ध नाहीत.\nनिष्कर्ष काढण्यासाठी अहवाल अपलोड करा.",
    },
    "AI Health Summary": {
        "en": "⚕️ AI Health Summary",
        "hi": "⚕️ एआई स्वास्थ्य सारांश",
        "mr": "⚕️ एआय आरोग्य सारांश",
    },
    "No recent summaries available. Please upload reports to generate AI insights.": {
        "en": "No recent summaries available. Please upload reports to generate AI insights.",
        "hi": "कोई हालिया सारांश उपलब्ध नहीं है। कृपया एआई अंतर्दृष्टि उत्पन्न करने के लिए रिपोर्ट अपलोड करें।",
        "mr": "कोणताही अलीकडील सारांश उपलब्ध नाही. कृपया एआय माहितीसाठी अहवाल अपलोड करा.",
    },

    # --- Records Tab ---
    "My Medical Records": {
        "en": "My Medical Records",
        "hi": "मेरे मेडिकल रिकॉर्ड्स",
        "mr": "माझे वैद्यकीय रेकॉर्ड्स",
    },
    "Upload Medical Report (Smart Analyzer)": {
        "en": "Upload Medical Report (Smart Analyzer)",
        "hi": "मेडिकल रिपोर्ट अपलोड करें (स्मार्ट एनालाइज़र)",
        "mr": "वैद्यकीय अहवाल अपलोड करा (स्मार्ट विश्लेषक)",
    },
    "Date": {"en": "Date", "hi": "तारीख", "mr": "तारीख"},
    "Title": {"en": "Title", "hi": "शीर्षक", "mr": "शीर्षक"},
    "Description": {"en": "Description", "hi": "विवरण", "mr": "तपशील"},
    "View": {"en": "View", "hi": "देखें", "mr": "पहा"},

    # --- Appointments Tab ---
    "My Appointments": {
        "en": "My Appointments",
        "hi": "मेरी अपॉइंटमेंट्स",
        "mr": "माझ्या अपॉइंटमेंट्स",
    },
    "Time": {"en": "Time", "hi": "समय", "mr": "वेळ"},
    "Doctor": {"en": "Doctor", "hi": "डॉक्टर", "mr": "डॉक्टर"},
    "Status": {"en": "Status", "hi": "स्थिति", "mr": "स्थिती"},

    # --- Prescriptions Tab ---
    "My Prescriptions": {
        "en": "My Prescriptions",
        "hi": "मेरे नुस्खे (प्रिस्क्रिप्शन)",
        "mr": "माझे प्रिस्क्रिप्शन्स",
    },
    "Upload Prescription (Smart Analyzer)": {
        "en": "Upload Prescription (Smart Analyzer)",
        "hi": "प्रिस्क्रिप्शन अपलोड करें (स्मार्ट एनालाइज़र)",
        "mr": "प्रिस्क्रिप्शन अपलोड करा (स्मार्ट विश्लेषक)",
    },
    "Medicine": {"en": "Medicine", "hi": "दवा", "mr": "औषध"},
    "Dosage": {"en": "Dosage", "hi": "खुराक", "mr": "डोस"},
    "Frequency": {"en": "Frequency", "hi": "आवृत्ति", "mr": "वारंवारता"},
    "Duration": {"en": "Duration", "hi": "अवधि", "mr": "कालावधी"},

    # --- Treatment Tracking Tab ---
    "My Treatment Tracking": {
        "en": "My Treatment Tracking",
        "hi": "मेरी उपचार ट्रैकिंग",
        "mr": "माझे उपचार ट्रॅकिंग",
    },
    "Treatment History": {
        "en": "Treatment History",
        "hi": "उपचार इतिहास",
        "mr": "उपचार इतिहास",
    },
    "Current Status: None": {
        "en": "Current Status: None",
        "hi": "वर्तमान स्थिति: कोई नहीं",
        "mr": "सध्याची स्थिती: काहीही नाही",
    },
    "Notes": {"en": "Notes", "hi": "टिप्पणियां", "mr": "नोंदी"},
    "Updated By": {"en": "Updated By", "hi": "अपडेटकर्ता", "mr": "अपडेट करणारे"},
    "Role": {"en": "Role", "hi": "भूमिका", "mr": "भूमिका"},

    # --- Medicine Verification Tab ---
    "Medicine Search & AI Verification System": {
        "en": "Medicine Search & AI Verification System",
        "hi": "दवा खोज और एआई सत्यापन प्रणाली",
        "mr": "औषध शोध आणि एआय पडताळणी प्रणाली",
    },
    "Enter Medicine Name (e.g. Paracetamol)": {
        "en": "Enter Medicine Name (e.g. Paracetamol)",
        "hi": "दवा का नाम दर्ज करें (उदा. Paracetamol)",
        "mr": "औषधाचे नाव प्रविष्ट करा (उदा. Paracetamol)",
    },
    "Search Database": {
        "en": "Search Database",
        "hi": "डेटाबेस खोजें",
        "mr": "डेटाबेस शोधा",
    },
    "AI Medicine Explanation (Double-click a row to explain):": {
        "en": "AI Medicine Explanation (Double-click a row to explain):",
        "hi": "एआई दवा स्पष्टीकरण (स्पष्टीकरण के लिए पंक्ति पर डबल क्लिक करें):",
        "mr": "एआय औषध स्पष्टीकरण (माहितीसाठी पंक्तीवर डबल क्लिक करा):",
    },
    "Name": {"en": "Name", "hi": "नाम", "mr": "नाव"},
    "Manufacturer": {"en": "Manufacturer", "hi": "निर्माता", "mr": "उत्पादक"},
    "Composition": {"en": "Composition", "hi": "संयोजन", "mr": "घटक"},
    "Price": {"en": "Price", "hi": "मूल्य", "mr": "किंमत"},

    # --- Settings Tab ---
    "Profile Settings": {
        "en": "Profile Settings",
        "hi": "प्रोफ़ाइल सेटिंग्स",
        "mr": "प्रोफाइल सेटिंग्ज",
    },
    "Full Name": {"en": "Full Name", "hi": "पूरा नाम", "mr": "पूर्ण नाव"},
    "Phone Number": {"en": "Phone Number", "hi": "फ़ोन नंबर", "mr": "फोन नंबर"},
    "Email Address": {"en": "Email Address", "hi": "ईमेल पता", "mr": "ईमेल पत्ता"},
    "Save Changes": {"en": "Save Changes", "hi": "बदलाव सहेजें", "mr": "बदल जतन करा"},

    # --- Find Doctor Tab ---
    "Find a Specialist": {
        "en": "Find a Specialist",
        "hi": "विशेषज्ञ डॉक्टर खोजें",
        "mr": "तज्ज्ञ डॉक्टर शोधा",
    },
    "All States": {"en": "All States", "hi": "सभी राज्य", "mr": "सर्व राज्ये"},
    "All Specializations": {"en": "All Specializations", "hi": "सभी विशेषज्ञताएं", "mr": "सर्व विशेषीकरणे"},

    # --- Chatbot Tab ---
    "🤖 AI Health Assistant": {
        "en": "🤖 AI Health Assistant",
        "hi": "🤖 एआई स्वास्थ्य सहायक",
        "mr": "🤖 एआय आरोग्य सहाय्यक",
    },
    "Type your health question here...": {
        "en": "Type your health question here...",
        "hi": "अपना स्वास्थ्य संबंधी प्रश्न यहां लिखें...",
        "mr": "तुमचा आरोग्यासंबंधी प्रश्न येथे टाइप करा...",
    },
    "Send": {"en": "Send", "hi": "भेजें", "mr": "पाठवा"},
}


def get_localized_ui_string(key: str, lang_code: str = "en", default: str = None) -> str:
    """Return the localized UI string for the given key and language code."""
    if not lang_code:
        lang_code = "en"
    lang_code = lang_code.lower().strip()
    
    entry = UI_STRINGS.get(key)
    if entry:
        if lang_code in entry:
            return entry[lang_code]
        # Fallback to English
        if "en" in entry:
            return entry["en"]
    
    return default if default is not None else key
