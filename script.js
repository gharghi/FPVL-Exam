let exams = [];
let currentExamQuestions = [];
let currentQuestionIndex = 0;
let score = 0;

// Determine the page context and execute the appropriate logic
const page = window.location.pathname.split("/").pop();

if (page === "index.html" || page === "" || page === "/") {
  document.addEventListener('DOMContentLoaded', () => {
    loadExams();
  });
} else if (page === "exam.html") {
  document.addEventListener('DOMContentLoaded', () => {
    const selectedExamIndex = localStorage.getItem('selectedExamIndex');
    if (selectedExamIndex !== null) {
      loadExamQuestions(parseInt(selectedExamIndex));
    } else {
      window.location.href = 'index.html';
    }
  });
}

function loadExams() {
  fetch('data.json')
    .then(response => response.json())
    .then(data => {
      exams = data.exams;
      const examList = document.getElementById('exam-list');
      exams.forEach((exam, index) => {
        const button = document.createElement('button');
        button.innerText = exam.name;
        button.onclick = () => {
          localStorage.setItem('selectedExamIndex', index);
          window.location.href = 'exam.html';
        };
        examList.appendChild(button);
      });
    })
    .catch(error => {
      console.error('There was an error loading the exam list:', error);
    });
}

function loadExamQuestions(examIndex) {
  fetch('data.json')
    .then(response => response.json())
    .then(data => {
      currentExamQuestions = data.exams[examIndex].questions;
      displayQuestion();
    })
    .catch(error => {
      console.error('There was an error loading the exam questions:', error);
    });
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
      button.onclick = () => checkAnswer(index, button);
      optionsContainer.appendChild(button);
    });
  } else {
    finishQuiz();
  }
}

function checkAnswer(index, button) {
  const isCorrect = index === currentExamQuestions[currentQuestionIndex].correctIndex;
  document.querySelectorAll('#options button').forEach(btn => {
    btn.disabled = true;
    if (currentExamQuestions[currentQuestionIndex].options.indexOf(btn.innerText) === currentExamQuestions[currentQuestionIndex].correctIndex) {
      btn.style.backgroundColor = 'lightgreen';
    } else {
      btn.style.backgroundColor = '#f8d7da';
    }
  });
  if (isCorrect) {
    score++;
  } else {
    button.style.backgroundColor = 'red';
  }
  document.getElementById('next').style.visibility = 'visible';
}

function finishQuiz() {
  document.getElementById('quiz-container').innerHTML = `<div id="result">Your score: ${score}/${currentExamQuestions.length}</div>`;
  let feedback = '';
  if (score === currentExamQuestions.length) {
    feedback = 'Perfect score! Great job!';
  } else if (score > currentExamQuestions.length / 2) {
    feedback = 'Pretty good! But there\'s room for improvement.';
  } else {
    feedback = 'Consider practicing more. Keep trying!';
  }
  document.getElementById('quiz-container').innerHTML += `<div id="feedback">${feedback}</div>`;
}

document.getElementById('next')?.addEventListener('click', () => {
  currentQuestionIndex++;
  if (currentQuestionIndex < currentExamQuestions.length) {
    displayQuestion();
  } else {
    finishQuiz();
  }
});
