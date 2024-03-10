import json
import os
import glob
from docx import Document


def extract_questions_from_docx(filename):
    doc = Document(filename)
    questions = []
    question = None
    for para in doc.paragraphs:
        if para.text.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.",
                                         "13.", "14.", "15.", "16.", "17.", "18.", "19.", "20.", "21.", "22.", "23.",
                                         "24.", "25.", "26.", "27.", "28.", "29.", "30.", "31.", "32.", "33.", "34.",
                                         "35.", "36.", "37.", "38.", "39.", "40.", "41.", "42.", "43.", "44.", "45.",
                                         "46.", "47.", "48.", "49.", "50.")):
            if question:
                questions.append(question)
            question = {"question": para.text.strip()[3:], "options": [], "correctIndex": 0}
        elif para.text.strip().startswith(("a)", "b)", "c)", "d)")):
            option_text = para.text.strip()[3:]
            question["options"].append(option_text)
            if para.runs and para.runs[0].font.highlight_color:  # Check if the first run has a highlight
                question["correctIndex"] = len(question["options"]) - 1
    if question:  # Add the last question
        questions.append(question)
    return questions


def convert_to_json(directory):
    exams = []
    files = glob.glob(os.path.join(directory, '*.docx'))  # List all .docx files in the directory
    for file in files:
        exam_name = os.path.splitext(os.path.basename(file))[0]
        questions = extract_questions_from_docx(file)
        exams.append({"name": exam_name, "questions": questions})

    sorted_exams = sorted(exams, key=lambda x: x['name'])
    with open("data.json", "w", encoding="utf-8") as jsonfile:
        json.dump({"exams": sorted_exams}, jsonfile, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    convert_to_json("exams")
