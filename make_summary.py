import json
import sys

def make_summary(directory):
    with open(f"{directory}/data.json", 'r') as file:
        data = json.load(file)
    unique_questions = []
    for exam in data['exams']:
        for question in exam['questions']:
            if question["question"] not in [q["question"] for q in unique_questions]:
                unique_questions.append(question)
    with open("data.json", "w", encoding="utf-8") as jsonfile:
        json.dump({"exams": [{"name":"Unique Questions","questions":unique_questions}]}, jsonfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    make_summary(sys.argv[1])
