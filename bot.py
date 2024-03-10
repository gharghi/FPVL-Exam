#!/usr/bin/env python3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, \
    ConversationHandler
import json
from datetime import datetime
from os import environ

# Enable logging
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states
SELECTING_EXAM, TAKING_EXAM, EXAM_COMPLETED = range(3)


# Load exam data from JSON file
def load_exam_data(filename='data.json'):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data['exams']


# Save results to results.json
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


# Start command: lists available exams
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    exams = load_exam_data()
    keyboard = [[InlineKeyboardButton(exam['name'], callback_data=str(index))] for index, exam in enumerate(exams)]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Please choose an exam:', reply_markup=reply_markup)
    return SELECTING_EXAM


# Callback query handler for selecting an exam
async def select_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    if callback_data.isdigit():
        exam_index = int(callback_data)
        exams = load_exam_data()
        context.user_data['current_exam'] = exams[exam_index]
        context.user_data['question_index'] = 0
        context.user_data['correct_answers'] = 0

        await ask_question(update, context)
        return TAKING_EXAM
    else:
        await query.edit_message_text('Please select an exam from the list.')
        return SELECTING_EXAM


# Function to display the next question
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_exam = context.user_data['current_exam']
    question_index = context.user_data['question_index']
    question = current_exam['questions'][question_index]

    message_text = f"{question_index + 1}. {question['question']}\n"
    for idx, option in enumerate(question['options']):
        message_text += f"\n{chr(65 + idx)}) {option}"

    keyboard = [
        [InlineKeyboardButton(chr(65 + idx), callback_data=f"answer_{idx}") for idx in range(len(question['options']))],
        [InlineKeyboardButton("Next Question", callback_data="next")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Separate handling based on callback data type
    if callback_data.startswith("answer_"):
        selected_option_index = int(callback_data.split("_")[1])
        question_index = context.user_data['question_index']
        current_exam = context.user_data['current_exam']
        question = current_exam['questions'][question_index]
        correct_answer_index = question['correctIndex']

        # Prepare the feedback for correct/incorrect answer
        feedback = " ✅" if selected_option_index == correct_answer_index else " ❌"
        options_feedback = [option + feedback if i == correct_answer_index else option for i, option in
                            enumerate(question['options'])]
        message_text = f"{question_index + 1}. {question['question']}\n" + "\n".join(
            [f"{chr(65 + i)}) {opt}" for i, opt in enumerate(options_feedback)])

        # Update the correct_answers count
        if selected_option_index == correct_answer_index:
            context.user_data['correct_answers'] += 1

        # Show the "Next Question" button or finish quiz
        keyboard = [[InlineKeyboardButton("Next Question", callback_data="next")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)

    elif callback_data == "next":
        await next_question(update, context)


# Implementing next_question function
async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    question_index = context.user_data['question_index'] + 1
    current_exam = context.user_data['current_exam']

    if question_index < len(current_exam['questions']):
        context.user_data['question_index'] = question_index
        await ask_question(update, context)
    else:
        await exam_completed(update, context)

async def exam_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    correct_answers = context.user_data['correct_answers']
    total_questions = len(context.user_data['current_exam']['questions'])
    score_text = f"Exam completed! Your score: {correct_answers}/{total_questions}"

    # Save results
    save_results(update.effective_user.username, context.user_data['current_exam']['name'], correct_answers, total_questions)

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text=score_text)
    else:
        await update.message.reply_text(text=score_text)

    # Clear the user data for the current exam
    del context.user_data['current_exam']
    del context.user_data['question_index']
    del context.user_data['correct_answers']


def main() -> None:
    # Create the Application and pass it your bot's token
    application = Application.builder().token(environ["TELEGRAM_BOT_TOKEN"]).build()

    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_EXAM: [CallbackQueryHandler(select_exam)],
            TAKING_EXAM: [CallbackQueryHandler(handle_answer)],
            EXAM_COMPLETED: []  # Define states and callbacks for exam completion
        },
        fallbacks=[CommandHandler('start', start)]
    )

    # Add handlers to the application
    application.add_handler(conv_handler)

    # Run the bot
    application.run_polling()


if __name__ == '__main__':
    main()
