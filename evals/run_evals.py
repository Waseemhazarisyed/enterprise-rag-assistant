import json
import requests

API_URL = "http://127.0.0.1:8000/api/v1/chat"


def run_evaluation():
    with open("evals/test_cases.json", "r") as file:
        test_cases = json.load(file)

    total = len(test_cases)
    passed = 0

    for index, test in enumerate(test_cases, start=1):
        question = test["question"]
        expected_text = test["expected_answer_contains"]
        expected_source = test["expected_source"]

        response = requests.get(
            API_URL,
            params={"question": question},
        )

        data = response.json()

        answer = data.get("answer", "")
        sources = data.get("sources", [])

        answer_pass = expected_text.lower() in answer.lower()

        if expected_source is None:
            source_pass = True
        else:
            source_pass = any(
                source.get("filename") == expected_source
                for source in sources
            )

        test_passed = answer_pass and source_pass

        if test_passed:
            passed += 1

        print("\n" + "=" * 60)
        print(f"Test {index}: {question}")
        print(f"Answer: {answer}")
        print(f"Answer Check: {'PASS' if answer_pass else 'FAIL'}")
        print(f"Source Check: {'PASS' if source_pass else 'FAIL'}")
        print(f"Overall: {'PASS' if test_passed else 'FAIL'}")

    score = (passed / total) * 100

    print("\n" + "=" * 60)
    print(f"FINAL SCORE: {passed}/{total} ({score:.1f}%)")


if __name__ == "__main__":
    run_evaluation()