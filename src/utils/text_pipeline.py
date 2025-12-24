import re
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

from sklearn.feature_extraction.text import CountVectorizer
from transformers import pipeline
from transformers import AutoTokenizer, pipeline

model_name = "facebook/bart-large-cnn"

tokenizer = AutoTokenizer.from_pretrained(model_name)
summarizer = pipeline("summarization", model=model_name, tokenizer=tokenizer, device=0)

nlp = spacy.load("en_core_web_sm")
# summarizer = pipeline("summarization", model=model_name)


def clean_and_tokenize(text: str) -> list[str]:
    """Tokenize and clean a Unicode string."""
    tokens = word_tokenize(text)
    tokens = [t.lower() for t in tokens if t.isalpha()]

    stop_words = set(stopwords.words("english"))
    return [t for t in tokens if t not in stop_words]

def compute_word_freq(tokens: list[str]) -> dict[str, int]:
    """Compute frequency distribution of words."""
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    return dict(sorted(freq.items(), key=lambda item: item[1], reverse=True))

# def parse_text(html: str) -> str:
#     """Extract visible text from HTML."""
#     soup = BeautifulSoup(html, "html.parser")

#     for tag in soup(["script", "style", "noscript"]):
#         tag.extract()

#     text = soup.get_text(separator="\n")
#     lines = [line.strip() for line in text.splitlines() if line.strip()]
#     return "\n".join(lines)

def tokenize_text(text):
    # doc = nlp(text)
    # tokens = [token.text.lower() for token in doc if token.is_alpha]
    # return " ".join(tokens), doc
    doc = nlp(text)
    tokens = [word.lemma_.lower().strip() for word in doc if not word.is_stop and not word.is_punct]
    return tokens

def count_vectorize_text(text):
    count_vector = CountVectorizer(tokenizer=tokenize_text)
    count_vector.fit_transform([text])
    names_out = count_vector.get_feature_names_out()
    vocab = count_vector.vocabulary_
    return names_out, vocab

def extract_key_points(text):
    key_points = re.findall(r'\* (.+)', text)
    return key_points

def extract_named_entities(text):
    doc = nlp(text)
    named_entities = [(ent.text, ent.label_) for ent in doc.ents]
    return named_entities

def chunk_text(text, max_tokens=900):
    tokens = tokenizer.encode(text)
    chunks = [
        tokens[i:i + max_tokens]
        for i in range(0, len(tokens), max_tokens)
    ]
    return [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks]

def extract_summary(text, max_length=500, min_length=10):
    if not text.strip():
        return ""

    word_count = len(text.split())

    max_length = min(max_length, word_count)
    min_length = min(min_length, max_length - 1)
    print("Text length:", len(text))
    print("Word count:", len(text.split()))
    print("max_length:", max_length)
    print("min_length:", min_length)

    summary = summarizer(
        text,
        max_length=max_length,
        min_length=min_length,
        truncation=True,
        do_sample=False
    )
    return summary

def summarize_long_text(text, max_length=150, min_length=50):
    chunks = chunk_text(text)

    summaries = []
    for chunk in chunks:
        summary = summarizer(
            chunk,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )[0]["summary_text"]
        summaries.append(summary)

    return " ".join(summaries)
