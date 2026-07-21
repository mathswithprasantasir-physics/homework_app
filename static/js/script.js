// Global variables
let currentHomework = [];

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadFilters();
    loadHomework();
    setupEventListeners();
});

function setupEventListeners() {
    // Apply filters
    document.getElementById('applyFilters')?.addEventListener('click', loadHomework);
    
    // Reset filters
    document.getElementById('resetFilters')?.addEventListener('click', resetFilters);
    
    // Modal close
    document.querySelector('.close-modal')?.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target === document.getElementById('questionModal')) {
            closeModal();
        }
    });
    
    // Admin tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', switchTab);
    });
    
    // Add homework form
    document.getElementById('addHomeworkForm')?.addEventListener('submit', handleAddHomework);
    
    // Question type change
    document.getElementById('hwType')?.addEventListener('change', toggleOptions);
    
    // Question image upload preview
    document.getElementById('hwQuestionImage')?.addEventListener('change', handleQuestionImagePreview);
    
    // Option image upload preview
    document.querySelectorAll('.option-image').forEach(input => {
        input.addEventListener('change', handleOptionImagePreview);
    });
    
    // Load manage homework
    document.getElementById('loadHomework')?.addEventListener('click', loadManageHomework);
}

function loadFilters() {
    // Load classes
    fetch('/api/classes')
        .then(response => response.json())
        .then(classes => {
            const classFilter = document.getElementById('classFilter');
            const hwClass = document.getElementById('hwClass');
            const manageClass = document.getElementById('manageClass');
            
            classes.forEach(cls => {
                const option = document.createElement('option');
                option.value = cls.class;
                option.textContent = `Class ${cls.class}`;
                classFilter.appendChild(option.cloneNode(true));
                if (hwClass) hwClass.appendChild(option.cloneNode(true));
                if (manageClass) manageClass.appendChild(option.cloneNode(true));
            });
        });
    
    // Load subjects
    fetch('/api/subjects')
        .then(response => response.json())
        .then(subjects => {
            const subjectFilter = document.getElementById('subjectFilter');
            const hwSubject = document.getElementById('hwSubject');
            const manageSubject = document.getElementById('manageSubject');
            
            subjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.toLowerCase();
                option.textContent = subject.charAt(0).toUpperCase() + subject.slice(1);
                subjectFilter.appendChild(option.cloneNode(true));
                if (hwSubject) hwSubject.appendChild(option.cloneNode(true));
                if (manageSubject) manageSubject.appendChild(option.cloneNode(true));
            });
        });
    
    // Load weeks
    fetch('/api/weeks')
        .then(response => response.json())
        .then(weeks => {
            const weekFilter = document.getElementById('weekFilter');
            weeks.forEach(week => {
                const option = document.createElement('option');
                option.value = week.week_number;
                option.textContent = week.label;
                weekFilter.appendChild(option);
            });
        });
}

function loadHomework() {
    const classFilter = document.getElementById('classFilter').value;
    const subjectFilter = document.getElementById('subjectFilter').value;
    const typeFilter = document.getElementById('typeFilter').value;
    const weekFilter = document.getElementById('weekFilter').value;
    
    const params = new URLSearchParams();
    if (classFilter) params.append('class', classFilter);
    if (subjectFilter) params.append('subject', subjectFilter);
    if (typeFilter) params.append('type', typeFilter);
    if (weekFilter) params.append('week', weekFilter);
    
    showLoading(true);
    
    fetch(`/api/homework?${params.toString()}`)
        .then(response => response.json())
        .then(homework => {
            currentHomework = homework;
            displayHomework(homework);
            updateResultCount(homework.length);
            showLoading(false);
        })
        .catch(error => {
            console.error('Error loading homework:', error);
            showLoading(false);
            showError('Failed to load homework. Please try again.');
        });
}

function displayHomework(homework) {
    const grid = document.getElementById('homeworkGrid');
    if (!grid) return;
    
    if (homework.length === 0) {
        grid.innerHTML = `
            <div class="homework-card" style="grid-column: 1/-1; text-align: center; padding: 50px;">
                <i class="fas fa-inbox" style="font-size: 3rem; color: var(--gray);"></i>
                <h3 style="margin-top: 15px; color: var(--gray);">No homework found</h3>
                <p style="color: var(--gray);">Try adjusting your filters</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = homework.map(hw => `
        <div class="homework-card" onclick="showQuestionDetail('${hw.id}')">
            <span class="badge badge-${hw.type}">${hw.type.toUpperCase()}</span>
            <span class="subject-tag">${hw.subject.charAt(0).toUpperCase() + hw.subject.slice(1)}</span>
            <h3>Class ${hw.class}</h3>
            <p class="question-text">${hw.question}</p>
            ${hw.question_image ? `<img src="${hw.question_image}" alt="Question image" class="question-image">` : ''}
            <div class="meta">
                <span><i class="fas fa-star"></i> ${hw.marks || 1} marks</span>
                <span><i class="fas fa-calendar"></i> ${hw.date || 'No date'}</span>
                ${hw.type === 'mcqs' && hw.options ? `<span><i class="fas fa-list"></i> ${hw.options.length} options</span>` : ''}
            </div>
        </div>
    `).join('');
}

function showQuestionDetail(hwId) {
    const hw = currentHomework.find(h => h.id === hwId);
    if (!hw) return;
    
    const modal = document.getElementById('questionModal');
    const detail = document.getElementById('questionDetail');
    
    let optionsHTML = '';
    if (hw.type === 'mcqs' && hw.options && hw.options.length > 0) {
        optionsHTML = `
            <div class="options-section" style="margin-top: 20px;">
                <h4>Options:</h4>
                ${hw.options.map((opt, idx) => {
                    const letter = String.fromCharCode(65 + idx);
                    const isCorrect = hw.correct_answer === letter;
                    return `
                        <div style="padding: 10px 12px; margin: 8px 0; background: ${isCorrect ? '#d4edda' : 'var(--light-gray)'}; border-radius: 6px; border-left: 4px solid ${isCorrect ? '#28a745' : '#ddd'};">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <strong>${letter}.</strong>
                                <span>${opt.text || ''}</span>
                                ${isCorrect ? ' ✅' : ''}
                            </div>
                            ${opt.image ? `<img src="${opt.image}" alt="Option ${letter}" style="max-width: 100px; max-height: 80px; margin-top: 5px; border-radius: 4px;">` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    detail.innerHTML = `
        <div style="margin-bottom: 20px;">
            <span class="badge badge-${hw.type}">${hw.type.toUpperCase()}</span>
            <span class="subject-tag">${hw.subject.charAt(0).toUpperCase() + hw.subject.slice(1)}</span>
            <span class="subject-tag">Class ${hw.class}</span>
        </div>
        <h2 style="margin-bottom: 15px;">${hw.question}</h2>
        ${hw.question_image ? `<img src="${hw.question_image}" alt="Question image" style="max-width: 100%; border-radius: 8px; margin: 15px 0;">` : ''}
        ${optionsHTML}
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--light-gray);">
            <p><strong>Marks:</strong> ${hw.marks || 1}</p>
            <p><strong>Date:</strong> ${hw.date || 'No date'}</p>
            ${hw.hint ? `<p><strong>Hint:</strong> ${hw.hint}</p>` : ''}
        </div>
    `;
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('questionModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function resetFilters() {
    document.getElementById('classFilter').value = '';
    document.getElementById('subjectFilter').value = '';
    document.getElementById('typeFilter').value = '';
    document.getElementById('weekFilter').value = '';
    loadHomework();
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

function updateResultCount(count) {
    const el = document.getElementById('resultCount');
    if (el) {
        el.textContent = `${count} assignment${count !== 1 ? 's' : ''} found`;
    }
}

function showError(message) {
    alert(message);
}

// Image upload functions
function handleQuestionImagePreview(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('questionImagePreview');
    preview.innerHTML = '';
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const img = document.createElement('img');
            img.src = event.target.result;
            img.style.maxWidth = '200px';
            img.style.maxHeight = '150px';
            img.style.borderRadius = '8px';
            img.style.border = '2px solid var(--light-gray)';
            preview.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
}

function handleOptionImagePreview(e) {
    const file = e.target.files[0];
    const optionIndex = e.target.dataset.option;
    const preview = document.getElementById(`optionPreview${optionIndex}`);
    
    if (preview) {
        preview.innerHTML = '';
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const img = document.createElement('img');
                img.src = event.target.result;
                img.style.maxWidth = '100px';
                img.style.maxHeight = '80px';
                img.style.borderRadius = '4px';
                img.style.border = '2px solid var(--light-gray)';
                img.style.marginTop = '5px';
                preview.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    }
}

// Admin functions
function switchTab(e) {
    const tab = e.target.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tab}Tab`).classList.add('active');
}

function toggleOptions() {
    const type = document.getElementById('hwType').value;
    const optionsGroup = document.getElementById('optionsGroup');
    optionsGroup.style.display = type === 'mcqs' ? 'block' : 'none';
}

function getOptionsWithImages() {
    const optionTexts = document.querySelectorAll('.option-text');
    const optionImages = document.querySelectorAll('.option-image');
    const options = [];
    
    optionTexts.forEach((input, index) => {
        const text = input.value.trim();
        const imageInput = optionImages[index];
        let imagePath = null;
        
        if (imageInput && imageInput.files && imageInput.files[0]) {
            // Image will be uploaded separately
            imagePath = imageInput.dataset.uploadedPath || null;
        }
        
        if (text || imagePath) {
            options.push({
                text: text,
                image: imagePath
            });
        }
    });
    
    return options;
}

function handleAddHomework(e) {
    e.preventDefault();
    
    const classVal = document.getElementById('hwClass').value;
    const subject = document.getElementById('hwSubject').value;
    const type = document.getElementById('hwType').value;
    const question = document.getElementById('hwQuestion').value;
    const marks = document.getElementById('hwMarks').value;
    const date = document.getElementById('hwDate').value;
    const hint = document.getElementById('hwHint').value;
    const questionImageFile = document.getElementById('hwQuestionImage').files[0];
    
    if (!classVal || !subject || !type || !question) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Collect option data
    const options = [];
    const optionTexts = document.querySelectorAll('.option-text');
    const optionImageInputs = document.querySelectorAll('.option-image');
    
    optionTexts.forEach((input, index) => {
        const text = input.value.trim();
        const imageInput = optionImageInputs[index];
        let imageFile = imageInput ? imageInput.files[0] : null;
        
        options.push({
            text: text,
            image: null, // Will be set after upload
            imageFile: imageFile
        });
    });
    
    // Get correct answer
    const correctRadio = document.querySelector('input[name="correctOption"]:checked');
    const correctAnswer = correctRadio ? String.fromCharCode(65 + parseInt(correctRadio.value)) : null;
    
    // Upload question image if exists
    let questionImagePath = null;
    
    // Function to submit with all data
    function submitHomeworkWithData(questionImagePath, optionImages) {
        const finalOptions = options.map((opt, idx) => ({
            text: opt.text,
            image: optionImages[idx] || null
        }));
        
        const data = {
            class: classVal,
            subject: subject,
            type: type,
            question: question,
            question_image: questionImagePath,
            options: finalOptions,
            correct_answer: correctAnswer,
            marks: marks,
            date: date,
            hint: hint
        };
        
        fetch('/api/add_homework', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert('Homework added successfully!');
                document.getElementById('addHomeworkForm').reset();
                document.querySelectorAll('.image-preview, .option-preview').forEach(el => el.innerHTML = '');
                loadHomework();
                loadManageHomework();
            } else {
                alert('Failed to add homework: ' + (result.error || 'Unknown error'));
            }
        })
        .catch(error => {
            alert('Error adding homework: ' + error.message);
        });
    }
    
    // Upload images
    let imagesToUpload = [];
    
    // Check if question image needs upload
    if (questionImageFile) {
        const formData = new FormData();
        formData.append('image', questionImageFile);
        imagesToUpload.push({
            type: 'question',
            data: formData
        });
    }
    
    // Check if option images need upload
    options.forEach((opt, index) => {
        if (opt.imageFile) {
            const formData = new FormData();
            formData.append('image', opt.imageFile);
            imagesToUpload.push({
                type: 'option',
                index: index,
                data: formData
            });
        }
    });
    
    // If no images to upload, submit directly
    if (imagesToUpload.length === 0) {
        submitHomeworkWithData(null, []);
        return;
    }
    
    // Upload images one by one
    let uploadedImages = {};
    let uploadCount = 0;
    
    imagesToUpload.forEach((item, idx) => {
        fetch('/api/upload_image', {
            method: 'POST',
            body: item.data
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                if (item.type === 'question') {
                    uploadedImages.question = result.image_path;
                } else if (item.type === 'option') {
                    uploadedImages[item.index] = result.image_path;
                }
            }
            uploadCount++;
            
            // If all images are uploaded, submit the homework
            if (uploadCount === imagesToUpload.length) {
                const optionImagePaths = options.map((_, idx) => uploadedImages[idx] || null);
                submitHomeworkWithData(
                    uploadedImages.question || null,
                    optionImagePaths
                );
            }
        })
        .catch(error => {
            alert('Error uploading image: ' + error.message);
            uploadCount++;
        });
    });
}

function loadManageHomework() {
    const classFilter = document.getElementById('manageClass').value;
    const subjectFilter = document.getElementById('manageSubject').value;
    
    const params = new URLSearchParams();
    if (classFilter) params.append('class', classFilter);
    if (subjectFilter) params.append('subject', subjectFilter);
    
    fetch(`/api/homework?${params.toString()}`)
        .then(response => response.json())
        .then(homework => {
            const list = document.getElementById('manageList');
            if (homework.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: var(--gray);">No homework found</p>';
                return;
            }
            
            list.innerHTML = homework.map(hw => `
                <div class="manage-item">
                    <div class="item-info">
                        <strong>Class ${hw.class}</strong> - ${hw.subject.charAt(0).toUpperCase() + hw.subject.slice(1)}
                        <br>
                        <small>${hw.type.toUpperCase()}: ${hw.question.substring(0, 50)}${hw.question.length > 50 ? '...' : ''}</small>
                        <br>
                        <small>
                            ${hw.question_image ? '<i class="fas fa-image" style="color: var(--primary);"></i> Has image ' : ''}
                            ${hw.options && hw.options.some(opt => opt.image) ? '<i class="fas fa-images" style="color: var(--secondary);"></i> Option images ' : ''}
                        </small>
                        <br>
                        <small>Date: ${hw.date || 'No date'} | Marks: ${hw.marks || 1}</small>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-secondary btn-sm" onclick="editHomework('${hw.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteHomework('${hw.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            alert('Error loading homework: ' + error.message);
        });
}

function deleteHomework(hwId) {
    if (!confirm('Are you sure you want to delete this homework?')) return;
    
    fetch(`/api/delete_homework/${hwId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Homework deleted successfully!');
            loadManageHomework();
            loadHomework();
        } else {
            alert('Failed to delete homework: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        alert('Error deleting homework: ' + error.message);
    });
}

function editHomework(hwId) {
    const hw = currentHomework.find(h => h.id === hwId);
    if (!hw) {
        alert('Homework not found');
        return;
    }
    
    // Switch to add tab
    document.querySelector('[data-tab="add"]').click();
    
    // Fill form with data
    document.getElementById('hwClass').value = hw.class;
    document.getElementById('hwSubject').value = hw.subject;
    document.getElementById('hwType').value = hw.type;
    document.getElementById('hwQuestion').value = hw.question;
    document.getElementById('hwMarks').value = hw.marks || 1;
    document.getElementById('hwDate').value = hw.date || '';
    document.getElementById('hwHint').value = hw.hint || '';
    
    // Show question image if exists
    if (hw.question_image) {
        const preview = document.getElementById('questionImagePreview');
        preview.innerHTML = `
            <img src="${hw.question_image}" style="max-width: 200px; max-height: 150px; border-radius: 8px; border: 2px solid var(--light-gray);">
            <p><small>Current image</small></p>
        `;
    }
    
    // Handle options if MCQ
    if (hw.type === 'mcqs' && hw.options) {
        toggleOptions();
        const inputs = document.querySelectorAll('.option-text');
        const previews = document.querySelectorAll('.option-preview');
        
        hw.options.forEach((opt, idx) => {
            if (inputs[idx]) {
                inputs[idx].value = opt.text || '';
            }
            if (previews[idx] && opt.image) {
                previews[idx].innerHTML = `
                    <img src="${opt.image}" style="max-width: 100px; max-height: 80px; border-radius: 4px; border: 2px solid var(--light-gray);">
                `;
            }
        });
        
        if (hw.correct_answer) {
            const correctIndex = hw.correct_answer.charCodeAt(0) - 65;
            const radio = document.querySelector(`input[name="correctOption"][value="${correctIndex}"]`);
            if (radio) radio.checked = true;
        }
    }
    
    // Change submit button to update
    const submitBtn = document.querySelector('#addHomeworkForm button[type="submit"]');
    submitBtn.innerHTML = '<i class="fas fa-sync"></i> Update Homework';
    submitBtn.dataset.editId = hwId;
    
    // Change form submit handler for update
    const form = document.getElementById('addHomeworkForm');
    form.onsubmit = function(e) {
        e.preventDefault();
        updateHomework(hwId);
    };
}

function updateHomework(hwId) {
    // Similar to add but with PUT request
    const data = {
        class: document.getElementById('hwClass').value,
        subject: document.getElementById('hwSubject').value,
        type: document.getElementById('hwType').value,
        question: document.getElementById('hwQuestion').value,
        marks: document.getElementById('hwMarks').value,
        date: document.getElementById('hwDate').value,
        hint: document.getElementById('hwHint').value,
        options: getOptionsWithImages(),
        correct_answer: getCorrectAnswer()
    };
    
    fetch(`/api/update_homework/${hwId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Homework updated successfully!');
            document.getElementById('addHomeworkForm').reset();
            document.querySelectorAll('.image-preview, .option-preview').forEach(el => el.innerHTML = '');
            loadHomework();
            loadManageHomework();
            
            // Reset form
            const submitBtn = document.querySelector('#addHomeworkForm button[type="submit"]');
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Add Homework';
            delete submitBtn.dataset.editId;
            document.getElementById('addHomeworkForm').onsubmit = handleAddHomework;
        } else {
            alert('Failed to update homework: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        alert('Error updating homework: ' + error.message);
    });
}

function getCorrectAnswer() {
    const radio = document.querySelector('input[name="correctOption"]:checked');
    if (radio) {
        const index = parseInt(radio.value);
        return String.fromCharCode(65 + index);
    }
    return null;
}

// Make functions globally accessible
window.showQuestionDetail = showQuestionDetail;
window.deleteHomework = deleteHomework;
window.editHomework = editHomework;
