import json
import time
import re
import statistics
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "http://127.0.0.1:8000"
QUESTIONS_FILE = Path("eval/questions.jsonl")
RESULTS_FILE = Path("eval/results.json")


def load_questions():
    questions = []

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                questions.append(json.loads(line))

    return questions


def call_chat_api(question):
    url = f"{BASE_URL}/chat"

    body = json.dumps({
        "question": question
    }).encode("utf-8")

    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    start_time = time.perf_counter()

    with urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    end_time = time.perf_counter()

    latency = end_time - start_time

    return result, latency


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.split()


def calculate_f1(expected, actual):
    expected_words = normalize(expected)
    actual_words = normalize(actual)

    if not expected_words or not actual_words:
        return 0.0

    expected_set = set(expected_words)
    actual_set = set(actual_words)

    common = expected_set.intersection(actual_set)

    precision = len(common) / len(actual_set)
    recall = len(common) / len(expected_set)

    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)

def percentile(values, percentage):
    sorted_values = sorted(values)

    if not sorted_values:
        return 0

    index = max(
        0,
        int((percentage / 100) * len(sorted_values) + 0.9999) - 1
    )

    return sorted_values[min(index, len(sorted_values) - 1)]

def main():
    questions = load_questions()

    results = []
    latencies = []

    for item in questions:
        question_id = item["id"]
        question = item["question"]
        expected = item["expected_answer"]

        print(f"\nEvaluating {question_id}: {question}")

        try:
            response, latency = call_chat_api(question)

            answer = response.get("answer", "")
            sources = response.get("sources", [])

            score = calculate_f1(expected, answer)

            result = {
                "id": question_id,
                "type": item["type"],
                "question": question,
                "expected_answer": expected,
                "generated_answer": answer,
                "answer_f1": round(score, 4),
                "latency_seconds": round(latency, 3),
                "source_count": len(sources),
                "sources": sources,
                "error": None
            }

            latencies.append(latency)

            print("Answer:", answer)
            print("F1 score:", round(score, 4))
            print("Latency:", round(latency, 3), "seconds")
            print("Sources:", len(sources))

        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            result = {
                "id": question_id,
                "type": item["type"],
                "question": question,
                "error": str(error)
            }

            print("ERROR:", error)

        results.append(result)

    RESULTS_FILE.write_text(
        json.dumps(results, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n========== EVALUATION SUMMARY ==========")
    print("Total questions:", len(questions))
    print("Successful responses:", len(latencies))

    if latencies:
        print("Average latency:", round(statistics.mean(latencies), 3))
        print("Maximum latency:", round(max(latencies), 3))
        print("Minimum latency:", round(min(latencies), 3))
        if latencies:
    print("p50 latency:", round(percentile(latencies, 50), 3))
    print("p95 latency:", round(percentile(latencies, 95), 3))

    print("\nResults saved to:", RESULTS_FILE)


if __name__ == "__main__":
    main()