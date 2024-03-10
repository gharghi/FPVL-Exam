let currentExamQuestions = [];
let currentQuestionIndex = 0;
let score = 0;

document.addEventListener('DOMContentLoaded', () => {
    const page = window.location.pathname.split("/").pop();
    const languageListElement = document.getElementById('language-list');
    const typeListElement = document.getElementById('type-list');

    if (page === 'index.html' || page === '' || page === '/') {
        loadLanguages();
    }

    function loadLanguages() {
        fetch('exams.json')
            .then(response => response.json())
            .then(data => {
                const languages = data.languages;
                languages.forEach(lang => {
                    const button = document.createElement('button');
                    button.innerText = `${lang.name} ${lang.flag}`;
                    button.onclick = () => {
                        localStorage.setItem('selectedLanguage', lang.code);
                        displayTypes(lang.types);
                    };
                    languageListElement.appendChild(button);
                });
            })
            .catch(error => console.error('Error loading languages:', error));
    }

    function displayTypes(types) {
        languageListElement.style.display = 'none'; // Hide language selection
        typeListElement.innerHTML = ''; // Clear previous types if any

        types.forEach(type => {
            const button = document.createElement('button');
            button.innerText = type.type;
            button.onclick = () => {
                localStorage.setItem('selectedType', type.type);
                localStorage.setItem('dataPath', type.dataPath); // Save the path to load the correct exams
                window.location.href = 'exam.html'; // Navigate to the exam page
            };
            typeListElement.appendChild(button);
        });
        typeListElement.style.display = 'block'; // Show type selection
    }
});

if (window.location.pathname.endsWith('exam.html')) {
    const dataPath = localStorage.getItem('dataPath');
    if (dataPath) {
        loadExams(dataPath);
    } else {
        console.error('Data path not found. Redirecting to index.');
        window.location.href = 'index.html';
    }
}

function loadExams(dataPath) {
    fetch(dataPath)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load exam data');
            }
            return response.json();
        })
        .then(data => {
            if (!data || !data.exams || !Array.isArray(data.exams) || data.exams.length === 0) {
                throw new Error('Invalid exam data format');
            }
            // Assuming you only have one exam in the file
            currentExamQuestions = data.exams[0].questions;
            displayQuestion();
        })
        .catch(error => console.error('Error loading exams:', error));
}

function displayQuestion() {
    if (currentQuestionIndex < currentExamQuestions.length) {
        const question = currentExamQuestions[currentQuestionIndex];
        document.getElementById('question').innerText = question.question;
        const optionsContainer = document.getElementById('options');
        optionsContainer.innerHTML = '';
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.innerText = option;
            button.className = 'option';
            button.onclick = () => checkAnswer(index);
            optionsContainer.appendChild(button);
        });
        document.getElementById('next').style.visibility = 'hidden';
    } else {
        finishQuiz();
    }
}

function checkAnswer(index) {
    const isCorrect = index === currentExamQuestions[currentQuestionIndex].correctIndex;
    if (isCorrect) {
        score++; // Increment score only if the answer is correct
    }
    const buttons = document.querySelectorAll('.option');
    buttons.forEach((button, i) => {
        if (i === index) {
            if (isCorrect) {
                button.classList.add('correct-answer');
            } else {
                button.classList.add('incorrect-answer');
            }
        } else if (i === currentExamQuestions[currentQuestionIndex].correctIndex) {
            button.classList.add('correct-answer');
        }
        button.disabled = true; // Disable all buttons after answering
    });
    document.getElementById('next').style.visibility = 'visible';
}

document.getElementById('next')?.addEventListener('click', () => {
    currentQuestionIndex++;
    if (currentQuestionIndex < currentExamQuestions.length) {
        displayQuestion();
    } else {
        finishQuiz();
    }
});

function finishQuiz() {
    const totalQuestions = currentExamQuestions.length;
    const percentageScore = (score / totalQuestions) * 100;
    let feedback = '';

    if (percentageScore >= 75) {
        feedback = `Congratulations! You passed with a score of ${percentageScore.toFixed(2)}%`;
    } else {
        feedback = `Sorry, you failed with a score of ${percentageScore.toFixed(2)}%`;
    }

    const quizContainer = document.getElementById('quiz-container');
    quizContainer.innerHTML = `
        <div id="result">Your score: ${score}/${totalQuestions} (${percentageScore.toFixed(2)}%)</div>
        <div id="feedback">${feedback}</div>
        <button id="start-over">Start Over</button>`;

    const startOverButton = document.getElementById('start-over');
    startOverButton.addEventListener('click', () => {
        // Reload the page to start over
        window.location.reload();
    });
}