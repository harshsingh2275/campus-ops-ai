import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from ..models.request import StudentRequestInput, ParsedStudentRequest

# Category definitions with associated keyword rules
CATEGORY_RULES = {
    "Lab Access": [
        r"\blab\b", r"\brobotics\b", r"\bworkbench\b", r"\blab\s*access\b",
        r"\bequipment\s*access\b", r"\bafter[- ]hours\b", r"\blab\s*key\b",
        r"\bhardware\s*lab\b", r"\bchemistry\s*lab\b", r"\bphysics\s*lab\b",
        r"\bcomputer\s*lab\b", r"\baccess\s*card\b", r"\bexperiment\b"
    ],
    "Maintenance & Repairs": [
        r"\bbroken\b", r"\bleak(ing)?\b", r"\bac\b", r"\bair\s*condition(er|ing)?\b",
        r"\bfan\b", r"\blight\b", r"\bplumbing\b", r"\btap\b", r"\bflush\b",
        r"\belectric(ity)?\b", r"\bsocket\b", r"\bpower\s*outlet\b", r"\block\b",
        r"\bwindow\b", r"\bhostel\s*repair\b", r"\bpipe\b", r"\bgeyser\b",
        r"\bwater\s*heater\b", r"\bshort\s*circuit\b", r"\bdrainage\b"
    ],
    "Facility Booking": [
        r"\bauditorium\b", r"\bseminar\s*hall\b", r"\bconference\s*room\b",
        r"\bclassroom\s*booking\b", r"\bbook\s*(the)?\s*(hall|room|ground)\b",
        r"\bfootball\s*ground\b", r"\bsports\s*complex\b", r"\bamphitheat(re|er)\b",
        r"\bvenue\s*reservation\b", r"\breserve\s*(the)?\s*(hall|room)\b"
    ],
    "Academic Request": [
        r"\bassignment\b", r"\bextension\b", r"\bdeadline\b", r"\battendance\b",
        r"\bre[- ]evaluation\b", r"\bgrade(s)?\b", r"\bexam\b", r"\bmedical\s*leave\b",
        r"\bcourse\s*drop\b", r"\btranscript\b", r"\brecommendation\b", r"\blor\b",
        r"\bbonafide\b", r"\bsyllabus\b", r"\bpermission\s*for\s*leave\b"
    ],
    "IT & Equipment Support": [
        r"\bwi[- ]?fi\b", r"\binternet\b", r"\bethernet\b", r"\bprojector\b",
        r"\bhdmi\b", r"\blogin\b", r"\bportal\b", r"\bpassword\s*reset\b",
        r"\bserver\b", r"\bprinter\b", r"\bsoftware\s*license\b", r"\blan\b"
    ],
    "Event Approval": [
        r"\bfest\b", r"\bhackathon\b", r"\bworkshop\b", r"\bclub\s*event\b",
        r"\bguest\s*lecture\b", r"\bcultural\s*fest\b", r"\btech\s*fest\b",
        r"\bsponsorship\b", r"\bbudget\s*approval\b", r"\bposter\s*permission\b"
    ]
}

URGENCY_KEYWORDS_URGENT = [
    r"\burgent(ly)?\b", r"\bemergency\b", r"\basap\b", r"\bcritical\b",
    r"\bimmediat(e|ely)\b", r"\bhazard\b", r"\bdanger\b", r"\bwater\s*leaking\b",
    r"\bshort\s*circuit\b", r"\bmedical\b"
]

URGENCY_KEYWORDS_HIGH = [
    r"\btoday\b", r"\btonight\b", r"\bwithin\s*\d+\s*hours?\b", r"\btomorrow\b",
    r"\bthis\s*evening\b", r"\bhigh\s*priority\b", r"\bsoon\b"
]

EXCLUDED_ID_PREFIXES = {"room", "hall", "block", "date", "time", "need", "door", "gate", "year", "dept", "hostel"}


class RequestParser:
    """Intelligent rule-based and NLP parser for unstructured campus operational requests."""

    @classmethod
    def parse(cls, input_data: StudentRequestInput) -> ParsedStudentRequest:
        text = input_data.raw_text.strip()
        
        # 1. Extract Email
        email = input_data.email or cls._extract_email(text)
        
        # 2. Extract Student ID / Roll Number
        student_id = input_data.student_id or cls._extract_student_id(text)
        
        # 3. Extract Student Name
        student_name = input_data.student_name or cls._extract_student_name(text) or "Student"
        
        # 4. Extract Category
        category = cls._extract_category(text)
        
        # 5. Extract Priority & Urgency
        priority, urgency = cls._extract_priority_and_urgency(text)
        
        # 6. Extract Location
        location = cls._extract_location(text)
        
        # 7. Extract Date/Time Needed
        date_needed = cls._extract_date_time(text)
        
        # 8. Generate Summary & Title
        summary = cls._generate_summary(text, category, location)
        title = cls._generate_title(category, summary, location, student_name, student_id)
        
        metadata = {
            "source": input_data.source or "web_portal",
            "extracted_category": category,
            "extracted_urgency": urgency,
            "detected_keywords": cls._detect_key_phrases(text),
            "character_count": len(text),
            "parser_version": "2.0.0-heuristic-nlp"
        }
        
        return ParsedStudentRequest(
            title=title,
            student_name=student_name,
            student_id=student_id,
            email=email,
            category=category,
            priority=priority,
            status="Pending",
            location=location,
            summary=summary,
            urgency=urgency,
            date_needed=date_needed,
            raw_text=text,
            extracted_metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )

    @staticmethod
    def _extract_email(text: str) -> Optional[str]:
        match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        if match:
            # Strip trailing punctuation such as . or ,
            return match.group(0).rstrip('.,;:')
        return None

    @staticmethod
    def _extract_student_id(text: str) -> Optional[str]:
        # Priority 1: Explicit labels like "Student ID: CS2024-042" or "Student ID is CS2024-042" or "Roll No: 21BCE049"
        explicit_patterns = [
            r'(?:student\s*id|roll\s*(?:no|number)|id\s*code|reg\s*(?:no|number)|enrollment\s*no)(?:\s+is|\s*:|\s*#)?\s+([A-Za-z0-9\-_/]+)'
        ]
        for pat in explicit_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip().rstrip('.,;:')
                first_word = candidate.split()[0].lower() if candidate else ""
                if len(candidate) >= 3 and first_word not in EXCLUDED_ID_PREFIXES and first_word not in ["is", "the", "a", "my"]:
                    return candidate

        # Priority 2: Standard roll / student ID codes like CS2024-042, 21BCE049, EC-9948, CS2024
        code_patterns = [
            r'\b([A-Z]{2,4}\d{2,4}[-_]\d{2,6}[A-Za-z]?)\b',
            r'\b([A-Z]{2,4}[-_]\d{2,8}[A-Za-z]?)\b',
            r'\b([A-Z]{2,4}\d{4,8}[A-Za-z]?)\b',
            r'\b(\d{2,4}[A-Z]{2,4}\d{2,6})\b'
        ]
        for pat in code_patterns:
            matches = re.finditer(pat, text)
            for m in matches:
                candidate = m.group(1).strip().rstrip('.,;:')
                first_word = candidate.split()[0].lower() if candidate else ""
                if first_word not in EXCLUDED_ID_PREFIXES and len(candidate) >= 4:
                    return candidate
        return None

    @staticmethod
    def _extract_student_name(text: str) -> Optional[str]:
        patterns = [
            r'(?:my\s+name\s+is|i\s+am|name\s*:\s*|from\s*:\s*|regards,?\s*|thanks,?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+))\s+here\b'
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                name = match.group(1).strip().rstrip('.,;:')
                if name.lower() not in ["student id", "robotics lab", "hostel block", "seminar hall", "dear team"]:
                    return name
        return None

    @staticmethod
    def _extract_category(text: str) -> str:
        text_lower = text.lower()
        scored_categories = {}
        
        for category, patterns in CATEGORY_RULES.items():
            score = 0
            for pat in patterns:
                matches = len(re.findall(pat, text_lower))
                score += matches
            if score > 0:
                scored_categories[category] = score
                
        if scored_categories:
            return max(scored_categories.items(), key=lambda x: x[1])[0]
            
        return "General Inquiry"

    @staticmethod
    def _extract_priority_and_urgency(text: str) -> tuple[str, str]:
        text_lower = text.lower()
        
        for pat in URGENCY_KEYWORDS_URGENT:
            if re.search(pat, text_lower):
                return "Urgent", "Urgent"
                
        for pat in URGENCY_KEYWORDS_HIGH:
            if re.search(pat, text_lower):
                return "High", "High"
                
        if any(w in text_lower for w in ["when possible", "whenever", "no rush", "general inquiry"]):
            return "Low", "Normal"
            
        return "Medium", "Normal"

    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        patterns = [
            r'((?:Hostel\s+)?Block\s+[A-Za-z0-9\-]+(?:,\s*(?:Room|Rm)\s+[A-Za-z0-9\-]+)?)',
            r'((?:Robotics|Computer|Physics|Chemistry|Hardware|AI|IoT)\s+Lab(?:\s*\([^)]+\))?)',
            r'((?:Room|Rm|Cabin|Hall|Auditorium|Block)\s*(?:No\.?|#)?\s*[A-Za-z0-9\-]+(?:\s*,\s*Block\s*[A-Za-z0-9\-]+)?)',
            r'((?:Main|Central|Old|New)\s+(?:Auditorium|Library|Seminar Hall|Sports Ground|Cafeteria))'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().rstrip('.,;:')
        return None

    @staticmethod
    def _extract_date_time(text: str) -> Optional[str]:
        patterns = [
            r'(this\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+from\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*to\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?)',
            r'(\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s*,\s*\d{4})?(?:\s+from\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*to\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?)',
            r'((?:from|at)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:to|-)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            r'\b(today|tomorrow|this\s+weekend|asap)\b'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().rstrip('.,;:')
        return None

    @staticmethod
    def _generate_summary(text: str, category: str, location: Optional[str]) -> str:
        sentences = [s.strip() for s in re.split(r'[.\n]+', text) if len(s.strip()) > 5]
        if sentences:
            first_sentence = sentences[0]
            if len(first_sentence) > 160:
                return first_sentence[:157] + "..."
            return first_sentence
        return f"{category} request for {location or 'campus operations'}."

    @staticmethod
    def _generate_title(category: str, summary: str, location: Optional[str], student_name: str, student_id: Optional[str]) -> str:
        descriptor = location or (summary[:40] if len(summary) > 5 else category)
        descriptor = re.sub(r'^(I need|Please|Requesting for|Request for)\s+', '', descriptor, flags=re.IGNORECASE).strip()
        
        identifier = student_id or (student_name if student_name != "Student" else "")
        if identifier:
            return f"[{category}] {descriptor} ({identifier})"
        return f"[{category}] {descriptor}"

    @staticmethod
    def _detect_key_phrases(text: str) -> list[str]:
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        stopwords = {"this", "that", "with", "from", "have", "need", "please", "could", "would", "about", "there", "their", "student"}
        return list(dict.fromkeys([w for w in words if w not in stopwords]))[:8]
