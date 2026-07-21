// Main JavaScript file for Homework Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Image preview functionality
    const imageInput = document.getElementById('question_image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    preview.innerHTML = `<img src="${e.target.result}" class="img-fluid" alt="Preview">`;
                }
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Question type change handler
    const questionType = document.getElementById('question_type');
    if (questionType) {
        questionType.addEventListener('change', function() {
            const mcqOptions = document.getElementById('mcqOptions');
            if (this.value === 'MCQ') {
                mcqOptions.style.display = 'block';
            } else {
                mcqOptions.style.display = 'none';
            }
        });
    }
    
    // Render LaTeX content
    renderMathInElement(document.body, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
        ],
        throwOnError: false
    });
    
    // Auto-save form data (for admin)
    const questionForm = document.getElementById('questionForm');
    if (questionForm) {
        // Save form data to localStorage before submitting
        questionForm.addEventListener('submit', function() {
            const formData = {
                question_text: document.getElementById('question_text').value,
                question_latex: document.getElementById('question_latex').value,
                marks: document.getElementById('marks').value,
                difficulty: document.getElementById('difficulty').value
            };
            localStorage.setItem('lastQuestion', JSON.stringify(formData));
        });
        
        // Load saved form data
        const savedData = localStorage.getItem('lastQuestion');
        if (savedData && !window.location.search.includes('submitted')) {
            const data = JSON.parse(savedData);
            if (data.question_text) document.getElementById('question_text').value = data.question_text;
            if (data.question_latex) document.getElementById('question_latex').value = data.question_latex;
            if (data.marks) document.getElementById('marks').value = data.marks;
            if (data.difficulty) document.getElementById('difficulty').value = data.difficulty;
        }
    }
});

// Filter functions for homework list
function filterByClass(classLevel) {
    const cards = document.querySelectorAll('.homework-card');
    cards.forEach(card => {
        const cardClass = card.getAttribute('data-class');
        if (!classLevel || cardClass === classLevel) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function searchHomework(query) {
    const cards = document.querySelectorAll('.homework-card');
    cards.forEach(card => {
        const title = card.querySelector('.card-title').textContent.toLowerCase();
        if (title.includes(query.toLowerCase())) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

// Export to PDF functionality
function exportToPDF() {
    window.print();
}

// Share homework functionality
function shareHomework(homeworkId) {
    const url = window.location.origin + '/student/homework/' + homeworkId;
    
    if (navigator.share) {
        navigator.share({
            title: 'Homework Assignment',
            text: 'Check out this homework assignment!',
            url: url
        });
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            alert('Link copied to clipboard!');
        });
    }
}

// Timer for homework
function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = 0;
            display.textContent = "Time's up!";
        }
    }, 1000);
}

// Initialize timer if exists
window.onload = function() {
    var timerElement = document.getElementById('timer');
    if (timerElement) {
        var thirtyMinutes = 60 * 30;
        startTimer(thirtyMinutes, timerElement);
    }
};