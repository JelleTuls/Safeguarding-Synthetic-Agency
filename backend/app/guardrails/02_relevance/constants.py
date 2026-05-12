"""Hardcoded token helpers for layer 02 topic-distance scoring."""

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in",
    "into", "is", "it", "its", "just", "me", "more", "most", "my", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "our", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "why", "will", "with", "would",
    "you", "your",
}

RELATED_TERMS = {
    "vote": {"politics", "party", "election", "policy", "government", "voting"},
    "politics": {"vote", "party", "election", "policy", "government"},
    "housing": {"rent", "home", "affordable", "neighbourhood", "mortgage"},
    "climate": {"environment", "nature", "energy", "flooding", "sustainable"},
    "health": {"healthcare", "care", "hospital", "doctor", "medical"},
    "education": {"school", "teacher", "learning", "student", "university"},
    "work": {"job", "career", "profession", "workplace", "colleague"},
    "family": {"partner", "children", "parent", "home", "household"},
    "transport": {"cycling", "bike", "train", "bus", "commute", "public"},
    "agriculture": {"farm", "greenhouse", "rural", "growers", "soil"},
}
