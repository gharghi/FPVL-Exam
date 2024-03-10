#!/usr/bin/env python3
import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
import logging
from os import environ

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states
SELECTING_LANGUAGE, SELECTING_TYPE, TAKING_EXAM, EXAM_COMPLETED = range(4)

# Language map with ISO codes, names, and flags
language_map = {
    'en': {'name': 'English', 'flag': '🇬🇧'},
    'pt': {'name': 'Português', 'flag': '🇵🇹'},
}

# Base directory where exam data is stored
base_directory = 'exams'

def load_languages():
    available_languages = []
    for lang_code in os.listdir(base_directory):
        if lang_code in language_map and os.path.isdir(os.path.join(base_directory, lang_code)):
            lang_info = language_map[lang_code]
            available_languages.append({'code': lang_code, 'name': lang_info['name'], 'flag': lang_info['flag']})
    return available_languages

def load_types_for_language(language_code):
    lang_path = os.path.join(base_directory, language_code)
    return [name for name in os.listdir(lang_path) if os.path.isdir(os.path.join(lang_path, name))]

def load_exam_data(language_code, exam_type):
    data_file = os.path.join(base_directory, language_code, exam_type, 'data.json')
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as file:
            return json.load(file)['exams']
    return []

# Start command: lists available languages
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    languages = load_languages()
    keyboard = [[InlineKeyboardButton(f"{lang['name']} {lang['flag']}", callback_data=lang['code'])] for lang in languages]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose a language:', reply_markup=reply_markup)
    return SELECTING_LANGUAGE

# Handler for selecting a language
async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['selected_language'] = query.data
    types = load_types_for_language(query.data)
    keyboard = [[InlineKeyboardButton(type, callback_data=type)] for type in types]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Please choose the exam type:', reply_markup=reply_markup)
    return SELECTING_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    selected_language = context.user_data.get('selected_language')
    selected_type = query.data
    context.user_data['selected_type'] = selected_type  # Store the selected type as well
    exams = load_exam_data(selected_language, selected_type)

    # Correcting the key used to store the current exam data
    if exams:
        context.user_data['current_exams'] = exams  # This should be a list of exams
        context.user_data['question_index'] = 0
        context.user_data['correct_answers'] = 0

        await ask_question(update, context)
        return TAKING_EXAM
    else:
        # Handle case where no exams are found or there's an issue with the data file
        await query.edit_message_text('No exams found for the selected type. Please try another option.')
        return SELECTING_TYPE


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question_index = context.user_data.get('question_index', 0)

    # Assuming we're working with the first exam for simplicity; adjust based on your logic.
    current_exam = context.user_data.get('current_exams', [])[0]

    if question_index < len(current_exam['questions']):
        question = current_exam['questions'][question_index]

        message_text = f"{question_index + 1}. {question['question']}\n"
        for idx, option in enumerate(question['options']):
            message_text += f"\n{chr(65 + idx)}) {option}"

        keyboard = [
            [InlineKeyboardButton(chr(65 + idx), callback_data=f"answer_{idx}") for idx in
             range(len(question['options']))],
            [InlineKeyboardButton("Next Question", callback_data="next")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Determine whether we're responding to a callback query or a regular message
        if update.callback_query:
            await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text=message_text, reply_markup=reply_markup)
    else:
        # If all questions have been answered, proceed to completion
        await exam_completed(update, context)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    question_index = context.user_data.get('question_index', 0)
    current_exams = context.user_data.get('current_exams', [])
    current_exam = current_exams[0] if current_exams else None

    if callback_data.startswith("answer_"):
        selected_option_index = int(callback_data.split("_")[1])
        if current_exam:
            question = current_exam['questions'][question_index]
            correct_answer_index = question.get('correctIndex', 0)

            # Rebuild the question text with feedback for the selected answer
            message_text = f"{question_index + 1}. {question['question']}\n"
            for idx, option in enumerate(question['options']):
                if idx == correct_answer_index:
                    option += " ✅"
                if idx == selected_option_index and selected_option_index != correct_answer_index:
                    option += " ❌"
                message_text += f"\n{chr(65 + idx)}) {option}"

            # Determine whether to increment the correct answers count
            if selected_option_index == correct_answer_index:
                context.user_data['correct_answers'] += 1

            # Prepare the "Next Question" button
            keyboard = [[InlineKeyboardButton("Next Question", callback_data="next")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(text=message_text, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="There was an error loading the exam data. Please try again.")

    elif callback_data == "next":
        # Increment the question index for the next question
        context.user_data['question_index'] += 1
        await next_question(update, context)


async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    question_index = context.user_data.get('question_index', 0) + 1
    current_exams = context.user_data.get('current_exams', [])

    # Assuming we're working with the first exam for simplicity; adjust based on your logic.
    current_exam = current_exams[0] if current_exams else None

    if current_exam and question_index < len(current_exam['questions']):
        context.user_data['question_index'] = question_index
        await ask_question(update, context)
    else:
        await exam_completed(update, context)


async def exam_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    correct_answers = context.user_data['correct_answers']

    # Assuming the first exam in the list for demonstration
    current_exam = context.user_data.get('current_exams', [])[0]  # Adjust this based on your exam selection logic

    selected_language = context.user_data.get('selected_language')
    selected_type = context.user_data.get('selected_type')
    total_questions = len(current_exam['questions'])

    language_name = language_map[selected_language]['name']
    flag = language_map[selected_language]['flag']
    exam_name = f"{language_name} {flag} - {selected_type}"

    result = "Passed" if correct_answers / total_questions >= 0.75 else "Failed"
    score_text = f"Exam completed! Your score: {correct_answers}/{total_questions} ({correct_answers / total_questions:.0%}). Result: {result}."

    save_results(update.effective_user.username, exam_name, correct_answers, total_questions)

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text=score_text)
    else:
        await update.message.reply_text(text=score_text)

    context.user_data.clear()  # Reset user data for a new session


def save_results(user_name, exam_name, score, total_questions):
    result = {
        'username': user_name,
        'exam_name': exam_name,
        'score': score,
        'total_questions': total_questions,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        with open('results.json', 'r', encoding='utf-8') as file:
            results = json.load(file)
    except FileNotFoundError:
        results = []

    results.append(result)
    with open('results.json', 'w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

def main():
    application = Application.builder().token(environ.get("TELEGRAM_BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_LANGUAGE: [CallbackQueryHandler(select_language)],
            SELECTING_TYPE: [CallbackQueryHandler(select_type)],
            TAKING_EXAM: [CallbackQueryHandler(handle_answer, pattern='^answer_'), CallbackQueryHandler(next_question, pattern='^next')],
            EXAM_COMPLETED: []
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()