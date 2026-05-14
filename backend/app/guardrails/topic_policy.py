"""Shared topic policy taxonomy for judge selection and post-generation validation."""

TOPIC_POLICY_DEFAULT = "everyday_conversation"

FACTUALITY_LEVEL_THRESHOLDS = {
    "belief_affirmation": {
        "min_objectivity": 0.0,
        "max_objectivity": 0.35,
        "min_subjectivity": 0.55,
        "max_authority": "low",
    },
    "anecdotal": {
        "min_objectivity": 0.0,
        "max_objectivity": 0.45,
        "min_subjectivity": 0.45,
        "max_authority": "low",
    },
    "subjective": {
        "min_objectivity": 0.0,
        "max_objectivity": 0.6,
        "min_subjectivity": 0.3,
        "max_authority": "low",
    },
    "uncertain_interpretation": {
        "min_objectivity": 0.1,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
    },
    "limited_factual": {
        "min_objectivity": 0.35,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "high",
    },
}

TOPIC_POLICY_THRESHOLDS = {
    "everyday_conversation": {
        "description": "greetings, casual chat, small talk, and low-stakes conversational turns",
        "min_objectivity": 0.0,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "low",
        "max_persuasion": 0.85,
    },
    "personal_identity": {
        "description": "who the persona is, direct self-description, and profile identity",
        "min_objectivity": 0.0,
        "max_objectivity": 0.85,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.65,
    },
    "biography_lived_experience": {
        "description": "the persona's own memories, routine, background, and lived experience",
        "min_objectivity": 0.0,
        "max_objectivity": 0.75,
        "min_subjectivity": 0.2,
        "max_authority": "low",
        "max_persuasion": 0.65,
    },
    "family_relationships": {
        "description": "family life, relationships, parenting, friendships, and interpersonal advice",
        "min_objectivity": 0.0,
        "max_objectivity": 0.65,
        "min_subjectivity": 0.25,
        "max_authority": "low",
        "max_persuasion": 0.55,
    },
    "work_career_logistics": {
        "description": "work, jobs, logistics, management, career, and workplace experience",
        "min_objectivity": 0.15,
        "max_objectivity": 0.9,
        "min_subjectivity": 0.1,
        "max_authority": "medium",
        "max_persuasion": 0.55,
    },
    "education_learning": {
        "description": "schooling, studying, learning, explaining basics, and educational background",
        "min_objectivity": 0.2,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.5,
    },
    "hobbies_leisure": {
        "description": "hobbies, leisure, weekend activities, and personal interests",
        "min_objectivity": 0.0,
        "max_objectivity": 0.8,
        "min_subjectivity": 0.15,
        "max_authority": "low",
        "max_persuasion": 0.7,
    },
    "local_community_culture": {
        "description": "local community, culture, places, norms, and everyday social life",
        "min_objectivity": 0.1,
        "max_objectivity": 0.85,
        "min_subjectivity": 0.1,
        "max_authority": "low",
        "max_persuasion": 0.55,
    },
    "consumer_preferences": {
        "description": "products, gifts, purchases, taste, and personal preference recommendations",
        "min_objectivity": 0.0,
        "max_objectivity": 0.75,
        "min_subjectivity": 0.2,
        "max_authority": "low",
        "max_persuasion": 0.7,
    },
    "practical_everyday_advice": {
        "description": "low-stakes everyday suggestions, planning, habits, and practical tips",
        "min_objectivity": 0.1,
        "max_objectivity": 0.8,
        "min_subjectivity": 0.15,
        "max_authority": "low",
        "max_persuasion": 0.65,
    },
    "food_lifestyle": {
        "description": "food, cooking, lifestyle, home routines, and personal taste",
        "min_objectivity": 0.0,
        "max_objectivity": 0.8,
        "min_subjectivity": 0.1,
        "max_authority": "low",
        "max_persuasion": 0.65,
    },
    "travel_places": {
        "description": "travel, places, directions, destinations, and visiting locations",
        "min_objectivity": 0.15,
        "max_objectivity": 0.9,
        "min_subjectivity": 0.05,
        "max_authority": "medium",
        "max_persuasion": 0.55,
    },
    "sports_entertainment": {
        "description": "sports, movies, books, music, games, media, and entertainment",
        "min_objectivity": 0.0,
        "max_objectivity": 0.85,
        "min_subjectivity": 0.1,
        "max_authority": "low",
        "max_persuasion": 0.7,
    },
    "creative_opinion": {
        "description": "creative taste, aesthetics, writing, art, and subjective evaluation",
        "min_objectivity": 0.0,
        "max_objectivity": 0.7,
        "min_subjectivity": 0.25,
        "max_authority": "low",
        "max_persuasion": 0.65,
    },
    "politics_government": {
        "description": "political parties, politicians, elections, ideology, public governance, and voting",
        "min_objectivity": 0.0,
        "max_objectivity": 0.5,
        "min_subjectivity": 0.25,
        "max_authority": "low",
        "max_persuasion": 0.25,
    },
    "religion_spirituality": {
        "description": "religion, spirituality, worship, faith identity, and spiritual claims",
        "min_objectivity": 0.0,
        "max_objectivity": 0.45,
        "min_subjectivity": 0.3,
        "max_authority": "low",
        "max_persuasion": 0.25,
    },
    "morality_values": {
        "description": "moral judgment, values, duties, right and wrong, and personal principles",
        "min_objectivity": 0.0,
        "max_objectivity": 0.45,
        "min_subjectivity": 0.3,
        "max_authority": "low",
        "max_persuasion": 0.25,
    },
    "social_issues_identity": {
        "description": "social identity, group relations, inequality, discrimination, and civic values",
        "min_objectivity": 0.0,
        "max_objectivity": 0.55,
        "min_subjectivity": 0.25,
        "max_authority": "low",
        "max_persuasion": 0.3,
    },
    "controversial_sensitive": {
        "description": "polarizing, belief-shaping, identity-sensitive, or high-conflict topics",
        "min_objectivity": 0.0,
        "max_objectivity": 0.45,
        "min_subjectivity": 0.35,
        "max_authority": "low",
        "max_persuasion": 0.2,
    },
    "news_current_events": {
        "description": "recent events, public incidents, live developments, and changing information",
        "min_objectivity": 0.2,
        "max_objectivity": 0.8,
        "min_subjectivity": 0.1,
        "max_authority": "medium",
        "max_persuasion": 0.35,
    },
    "law_rights_policy": {
        "description": "law, legal rights, regulations, public policy, compliance, and official rules",
        "min_objectivity": 0.3,
        "max_objectivity": 0.9,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.25,
    },
    "finance_taxes_investment": {
        "description": "money, taxes, investing, financial decisions, markets, and economic advice",
        "min_objectivity": 0.3,
        "max_objectivity": 0.9,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.25,
    },
    "health_wellbeing": {
        "description": "general wellness, fitness, health routines, sleep, and non-clinical wellbeing",
        "min_objectivity": 0.25,
        "max_objectivity": 0.85,
        "min_subjectivity": 0.05,
        "max_authority": "medium",
        "max_persuasion": 0.35,
    },
    "medical_clinical": {
        "description": "diagnosis, treatment, medication, symptoms, clinical care, and medical decisions",
        "min_objectivity": 0.4,
        "max_objectivity": 0.95,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.2,
    },
    "mental_health_emotions": {
        "description": "emotional support, stress, anxiety, therapy-like topics, and mental wellbeing",
        "min_objectivity": 0.15,
        "max_objectivity": 0.75,
        "min_subjectivity": 0.2,
        "max_authority": "low",
        "max_persuasion": 0.3,
    },
    "science_research": {
        "description": "scientific facts, research findings, evidence, and technical scientific explanation",
        "min_objectivity": 0.4,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "high",
        "max_persuasion": 0.45,
    },
    "technology_ai": {
        "description": "technology, software, artificial intelligence, digital systems, and tools",
        "min_objectivity": 0.3,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.45,
    },
    "environment_climate": {
        "description": "environment, climate, sustainability, energy, and ecological claims",
        "min_objectivity": 0.35,
        "max_objectivity": 0.95,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.35,
    },
    "history_geography": {
        "description": "history, geography, places, demographic facts, and past events",
        "min_objectivity": 0.4,
        "max_objectivity": 1.0,
        "min_subjectivity": 0.0,
        "max_authority": "high",
        "max_persuasion": 0.45,
    },
    "safety_crisis": {
        "description": "urgent safety, emergencies, self-protection, crisis, and immediate risk",
        "min_objectivity": 0.4,
        "max_objectivity": 0.95,
        "min_subjectivity": 0.0,
        "max_authority": "medium",
        "max_persuasion": 0.45,
    },
}

AUTHORITY_RANK = {"low": 0, "medium": 1, "high": 2}
AUTHORITY_BY_RANK = {rank: authority for authority, rank in AUTHORITY_RANK.items()}


def normalize_topic_policy_category(value: str | None) -> str:
    """Normalize a judge-selected topic category to the fixed taxonomy."""
    if value in TOPIC_POLICY_THRESHOLDS:
        return value
    return TOPIC_POLICY_DEFAULT


def get_topic_policy_thresholds(category: str | None) -> dict:
    """Return threshold policy for a normalized or untrusted category value."""
    return TOPIC_POLICY_THRESHOLDS[normalize_topic_policy_category(category)]


def get_topic_persuasion_threshold(category: str | None) -> float:
    """Return the maximum allowed persuasion score for a topic category."""
    return float(get_topic_policy_thresholds(category).get("max_persuasion", 0.5))


def get_factuality_thresholds(factuality_level: str | None) -> dict:
    """Return threshold policy for the five-level factuality scale."""
    if factuality_level in FACTUALITY_LEVEL_THRESHOLDS:
        return FACTUALITY_LEVEL_THRESHOLDS[factuality_level]
    return FACTUALITY_LEVEL_THRESHOLDS["subjective"]


def get_combined_policy_thresholds(*, category: str | None, factuality_level: str | None) -> dict:
    """Combine topic sensitivity with the judge-selected five-level factuality expectation."""
    topic = get_topic_policy_thresholds(category)
    factuality = get_factuality_thresholds(factuality_level)
    max_authority_rank = min(
        AUTHORITY_RANK.get(topic["max_authority"], 0),
        AUTHORITY_RANK.get(factuality["max_authority"], 0),
    )
    return {
        "min_objectivity": max(topic["min_objectivity"], factuality["min_objectivity"]),
        "max_objectivity": min(topic["max_objectivity"], factuality["max_objectivity"]),
        "min_subjectivity": max(topic["min_subjectivity"], factuality["min_subjectivity"]),
        "max_authority": AUTHORITY_BY_RANK[max_authority_rank],
        "topic_policy_category": normalize_topic_policy_category(category),
        "factuality_level": factuality_level or "subjective",
    }


def format_topic_policy_catalog() -> str:
    """Render the topic taxonomy compactly for the judge prompt."""
    lines = []
    for category, settings in TOPIC_POLICY_THRESHOLDS.items():
        lines.append(
            "- {category}: {description} "
            "(min_objectivity={min_objectivity}, max_objectivity={max_objectivity}, "
            "min_subjectivity={min_subjectivity}, max_authority={max_authority}, "
            "max_persuasion={max_persuasion})".format(
                category=category,
                **settings,
            )
        )
    return "\n".join(lines)


def format_factuality_policy_catalog() -> str:
    """Render the five-level factuality thresholds compactly for the judge prompt."""
    lines = []
    for level, settings in FACTUALITY_LEVEL_THRESHOLDS.items():
        lines.append(
            "- {level}: min_objectivity={min_objectivity}, max_objectivity={max_objectivity}, "
            "min_subjectivity={min_subjectivity}, max_authority={max_authority}".format(
                level=level,
                **settings,
            )
        )
    return "\n".join(lines)
