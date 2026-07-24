// Global variables
let currentHomework = [];

// ============================================
// LaTeX Rendering Functions
// ============================================

function renderMath() {
    if (typeof renderMathInElement === 'function') {
        try {
            renderMathInElement(document.body, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '\\[', right: '\\]', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false}
                ],
                throwOnError: false,
                trust: true,
                macros: {
                    "\\R": "\\mathbb{R}",
                    "\\N": "\\mathbb{N}",
                    "\\Z": "\\mathbb{Z}",
                    "\\Q": "\\mathbb{Q}"
                }
            });
        } catch (e) {
            console.log('LaTeX render error:', e);
        }
    }
}

function reRenderMath() {
    setTimeout(renderMath, 300);
}

// ============================================
// Initialize Page
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    loadFilters();
    loadHomework();
    setupEventListeners();
    
    // Initial LaTeX render after page load
    setTimeout(renderMath, 1000);
});

// ============================================
// Setup Event Listeners
// ============================================

function setupEventListeners() {
    // Apply filters
    document.getElementById('applyFilters')?.addEventListener('click', loadHomework);
    
    // Reset filters
    document.getElementById('resetFilters')?.addEventListener('click', resetFilters);
    
    // Class filter - load chapters and topics when class changes
    document.getElementById('classFilter')?.addEventListener('change', function() {
        const subject = document.getElementById('subjectFilter')?.value || '';
        const classValue = this.value;
        loadChapters(subject, classValue);
        loadTopics(null, subject, classValue);
    });
    
    // Subject filter - load chapters when subject changes
    document.getElementById('subjectFilter')?.addEventListener('change', function() {
        const classValue = document.getElementById('classFilter')?.value || '';
        loadChapters(this.value, classValue);
        loadTopics(null, this.value, classValue);
    });
    
    // Chapter filter - load topics when chapter changes
    document.getElementById('chapterFilter')?.addEventListener('change', function() {
        const subject = document.getElementById('subjectFilter')?.value || '';
        const classValue = document.getElementById('classFilter')?.value || '';
        loadTopics(this.value, subject, classValue);
    });
    
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

// ============================================
// Load Filters - FIXED: No duplicate entries
// ============================================

function loadFilters() {
    // Load classes - FIXED: Clear ALL selects properly
    fetch('/api/classes')
        .then(response => response.json())
        .then(classes => {
            const classFilter = document.getElementById('classFilter');
            const hwClass = document.getElementById('hwClass');
            const manageClass = document.getElementById('manageClass');
            
            // Clear and populate classFilter
            if (classFilter) {
                classFilter.innerHTML = '<option value="">All Classes</option>';
                classes.forEach(cls => {
                    const option = document.createElement('option');
                    option.value = cls.class;
                    option.textContent = `Class ${cls.class}`;
                    classFilter.appendChild(option);
                });
            }
            
            // Clear and populate hwClass
            if (hwClass) {
                hwClass.innerHTML = '<option value="">Select Class</option>';
                classes.forEach(cls => {
                    const option = document.createElement('option');
                    option.value = cls.class;
                    option.textContent = `Class ${cls.class}`;
                    hwClass.appendChild(option);
                });
            }
            
            // Clear and populate manageClass
            if (manageClass) {
                manageClass.innerHTML = '<option value="">All Classes</option>';
                classes.forEach(cls => {
                    const option = document.createElement('option');
                    option.value = cls.class;
                    option.textContent = `Class ${cls.class}`;
                    manageClass.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading classes:', error));
    
    // Load subjects - FIXED: Clear ALL selects properly
    fetch('/api/subjects')
        .then(response => response.json())
        .then(subjects => {
            const subjectFilter = document.getElementById('subjectFilter');
            const hwSubject = document.getElementById('hwSubject');
            const manageSubject = document.getElementById('manageSubject');
            
            // Clear and populate subjectFilter
            if (subjectFilter) {
                subjectFilter.innerHTML = '<option value="">All Subjects</option>';
                subjects.forEach(subject => {
                    const option = document.createElement('option');
                    option.value = subject.toLowerCase();
                    option.textContent = subject.charAt(0).toUpperCase() + subject.slice(1);
                    subjectFilter.appendChild(option);
                });
            }
            
            // Clear and populate hwSubject
            if (hwSubject) {
                hwSubject.innerHTML = '<option value="">Select Subject</option>';
                subjects.forEach(subject => {
                    const option = document.createElement('option');
                    option.value = subject.toLowerCase();
                    option.textContent = subject.charAt(0).toUpperCase() + subject.slice(1);
                    hwSubject.appendChild(option);
                });
            }
            
            // Clear and populate manageSubject
            if (manageSubject) {
                manageSubject.innerHTML = '<option value="">All Subjects</option>';
                subjects.forEach(subject => {
                    const option = document.createElement('option');
                    option.value = subject.toLowerCase();
                    option.textContent = subject.charAt(0).toUpperCase() + subject.slice(1);
                    manageSubject.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading subjects:', error));
    
    // Load weeks - FIXED: Clear properly
    fetch('/api/weeks')
        .then(response => response.json())
        .then(weeks => {
            const weekFilter = document.getElementById('weekFilter');
            if (weekFilter) {
                weekFilter.innerHTML = '<option value="">All Weeks</option>';
                weeks.forEach(week => {
                    const option = document.createElement('option');
                    option.value = week.week_number;
                    option.textContent = week.label;
                    weekFilter.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading weeks:', error));
}

// ============================================
// Load Chapters with Class Filter
// ============================================

function loadChapters(subject, classValue) {
    const chapterFilter = document.getElementById('chapterFilter');
    if (!chapterFilter) return;
    
    const params = new URLSearchParams();
    if (subject) params.append('subject', subject);
    if (classValue) params.append('class', classValue);
    
    fetch(`/api/chapters?${params.toString()}`)
        .then(response => response.json())
        .then(chapters => {
            chapterFilter.innerHTML = '<option value="">All Chapters</option>';
            chapters.forEach(chapter => {
                const option = document.createElement('option');
                option.value = chapter;
                option.textContent = chapter;
                chapterFilter.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading chapters:', error));
}

// ============================================
// Load Topics with Class Filter
// ============================================

function loadTopics(chapter, subject, classValue) {
    const topicFilter = document.getElementById('topicFilter');
    if (!topicFilter) return;
    
    const params = new URLSearchParams();
    if (chapter) params.append('chapter', chapter);
    if (subject) params.append('subject', subject);
    if (classValue) params.append('class', classValue);
    
    fetch(`/api/topics?${params.toString()}`)
        .then(response => response.json())
        .then(topics => {
            topicFilter.innerHTML = '<option value="">All Topics</option>';
            topics.forEach(topic => {
                const option = document.createElement('option');
                option.value = topic;
                option.textContent = topic;
                topicFilter.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading topics:', error));
}

// ============================================
// Load Homework with Filters
// ============================================

function loadHomework() {
    const classFilter = document.getElementById('classFilter')?.value || '';
    const subjectFilter = document.getElementById('subjectFilter')?.value || '';
    const chapterFilter = document.getElementById('chapterFilter')?.value || '';
    const topicFilter = document.getElementById('topicFilter')?.value || '';
    const typeFilter = document.getElementById('typeFilter')?.value || '';
    const weekFilter = document.getElementById('weekFilter')?.value || '';
    
    const params = new URLSearchParams();
    if (classFilter) params.append('class', classFilter);
    if (subjectFilter) params.append('subject', subjectFilter);
    if (chapterFilter) params.append('chapter', chapterFilter);
    if (topicFilter) params.append('topic', topicFilter);
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
            
            // Re-render LaTeX after loading
            reRenderMath();
        })
        .catch(error => {
            console.error('Error loading homework:', error);
            showLoading(false);
            showError('Failed to load homework. Please try again.');
        });
}

// ============================================
// Display Homework Cards
// ============================================

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
    
    grid.innerHTML = homework.map(hw => {
        // Handle options display
        let optionsCount = 0;
        if (hw.type === 'mcqs' && hw.options) {
            optionsCount = hw.options.length;
        }
        
        // Display chapter and topic if available
        let chapterTopicHTML = '';
        if (hw.chapter || hw.topic) {
            chapterTopicHTML = `
                <div class="chapter-topic-tags">
                    ${hw.chapter ? `<span class="badge badge-chapter"><i class="fas fa-layer-group"></i> ${hw.chapter}</span>` : ''}
                    ${hw.topic ? `<span class="badge badge-topic"><i class="fas fa-tags"></i> ${hw.topic}</span>` : ''}
                </div>
            `;
        }
        
        return `
            <div class="homework-card" onclick="showQuestionDetail('${hw.id}')">
                <span class="badge badge-${hw.type}">${hw.type.toUpperCase()}</span>
                <span class="subject-tag">${hw.subject.charAt(0).toUpperCase() + hw.subject.slice(1)}</span>
                <h3>Class ${hw.class}</h3>
                ${chapterTopicHTML}
                <div class="question-text">${hw.question}</div>
                ${hw.question_image ? `<img src="${hw.question_image}" alt="Question image" class="question-image">` : ''}
                <div class="meta">
                    <span><i class="fas fa-star"></i> ${hw.marks || 1} marks</span>
                    <span><i class="fas fa-calendar"></i> ${hw.date || 'No date'}</span>
                    ${optionsCount > 0 ? `<span><i class="fas fa-list"></i> ${optionsCount} options</span>` : ''}
                    ${hw.has_image ? `<span><i class="fas fa-image"></i> Has image</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // Re-render LaTeX for new content
    reRenderMath();
}

// ============================================
// Show Question Detail in Modal
// ============================================

function showQuestionDetail(hwId) {
    const hw = currentHomework.find(h => h.id === hwId);
    if (!hw) {
        showError('Homework not found');
        return;
    }
    
    const modal = document.getElementById('questionModal');
    const detail = document.getElementById('questionDetail');
    
    let optionsHTML = '';
    if (hw.type === 'mcqs' && hw.options && hw.options.length > 0) {
        optionsHTML = `
            <div class="options-section" style="margin-top: 20px;">
                <h4>Options:</h4>
                ${hw.options.map((opt, idx) => {
                    const letter = String.fromCharCode(65 + idx);
                    const text = typeof opt === 'string' ? opt : opt.text || '';
                    const image = typeof opt === 'object' ? opt.image : null;
                    const isCorrect = hw.correct_answer === letter;
                    
                    // Check if option has image
                    const hasOptionImage = image && image !== 'null' && image !== 'None';
                    
                    return `
                        <div style="padding: 12px 15px; margin: 10px 0; background: ${isCorrect ? '#d4edda' : 'var(--light-gray)'}; border-radius: 8px; border-left: 4px solid ${isCorrect ? '#28a745' : '#ddd'};">
                            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                                <strong style="font-size: 1.1rem;">${letter}.</strong>
                                <span style="flex: 1;">${text}</span>
                                ${isCorrect ? ' <span style="color: #28a745; font-weight: bold;">✅ Correct</span>' : ''}
                            </div>
                            ${hasOptionImage ? `<div style="margin-top: 8px;"><img src="${image}" alt="Option ${letter}" style="max-width: 150px; max-height: 100px; border-radius: 6px; border: 1px solid #ddd;"></div>` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    // Display chapter and topic if available
    let chapterTopicHTML = '';
    if (hw.chapter || hw.topic) {
        chapterTopicHTML = `
            <div style="margin: 10px 0;">
                ${hw.chapter ? `<span class="badge badge-chapter" style="background: #6c5ce7; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px;"><i class="fas fa-layer-group"></i> ${hw.chapter}</span>` : ''}
                ${hw.topic ? `<span class="badge badge-topic" style="background: #00b894; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem;"><i class="fas fa-tags"></i> ${hw.topic}</span>` : ''}
            </div>
        `;
    }
    
    detail.innerHTML = `
        <div style="margin-bottom: 20px;">
            <span class="badge badge-${hw.type}">${hw.type.toUpperCase()}</span>
            <span class="subject-tag">${hw.subject.charAt(0).toUpperCase() + hw.subject.slice(1)}</span>
            <span class="subject-tag">Class ${hw.class}</span>
            ${hw.marks ? `<span class="subject-tag"><i class="fas fa-star"></i> ${hw.marks} marks</span>` : ''}
        </div>
        ${chapterTopicHTML}
        <div style="margin-bottom: 15px; font-size: 1.15rem; line-height: 1.8;">
            <strong>Question:</strong><br>
            ${hw.question}
        </div>
        ${hw.question_image ? `<div style="margin: 15px 0;"><img src="${hw.question_image}" alt="Question image" style="max-width: 100%; border-radius: 8px; border: 1px solid #ddd;"></div>` : ''}
        ${optionsHTML}
        <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid var(--light-gray);">
            <p><strong><i class="fas fa-calendar"></i> Date:</strong> ${hw.date || 'Not specified'}</p>
            ${hw.hint ? `<p><strong><i class="fas fa-lightbulb"></i> Hint:</strong> ${hw.hint}</p>` : ''}
            ${hw.week ? `<p><strong><i class="fas fa-calendar-week"></i> Week:</strong> ${hw.week}</p>` : ''}
        </div>
    `;
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Re-render LaTeX for modal content
    setTimeout(renderMath, 500);
}

// ============================================
// Modal Functions
// ============================================

function closeModal() {
    const modal = document.getElementById('questionModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// ============================================
// Filter Functions
// ============================================

function resetFilters() {
    const classFilter = document.getElementById('classFilter');
    const subjectFilter = document.getElementById('subjectFilter');
    const chapterFilter = document.getElementById('chapterFilter');
    const topicFilter = document.getElementById('topicFilter');
    const typeFilter = document.getElementById('typeFilter');
    const weekFilter = document.getElementById('weekFilter');
    
    if (classFilter) classFilter.value = '';
    if (subjectFilter) subjectFilter.value = '';
    if (chapterFilter) chapterFilter.value = '';
    if (topicFilter) topicFilter.value = '';
    if (typeFilter) typeFilter.value = '';
    if (weekFilter) weekFilter.value = '';
    
    // Reload chapters and topics
    loadChapters();
    loadTopics();
    
    loadHomework();
}

// ============================================
// UI Helper Functions
// ============================================

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
    // Simple alert for now - can be improved with a toast notification
    alert('❌ Error: ' + message);
}

function showSuccess(message) {
    alert('✅ Success: ' + message);
}

// ============================================
// Image Upload Functions
// ============================================

function handleQuestionImagePreview(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('questionImagePreview');
    if (!preview) return;
    
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
            img.style.marginTop = '10px';
            preview.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
}

function handleOptionImagePreview(e) {
    const file = e.target.files[0];
    const optionIndex = e.target.dataset.option;
    const preview = document.getElementById(`optionPreview${optionIndex}`);
    
    if (!preview) return;
    
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

// ============================================
// Admin Functions
// ============================================

function switchTab(e) {
    const tab = e.target.dataset.tab;
    if (!tab) return;
    
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    const tabContent = document.getElementById(`${tab}Tab`);
    if (tabContent) {
        tabContent.classList.add('active');
    }
}

function toggleOptions() {
    const type = document.getElementById('hwType');
    const optionsGroup = document.getElementById('optionsGroup');
    
    if (!type || !optionsGroup) return;
    
    optionsGroup.style.display = type.value === 'mcqs' ? 'block' : 'none';
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

function getCorrectAnswer() {
    const radio = document.querySelector('input[name="correctOption"]:checked');
    if (radio) {
        const index = parseInt(radio.value);
        return String.fromCharCode(65 + index);
    }
    return null;
}

// ============================================
// Add Homework
// ============================================

function handleAddHomework(e) {
    e.preventDefault();
    
    const classVal = document.getElementById('hwClass')?.value;
    const subject = document.getElementById('hwSubject')?.value;
    const type = document.getElementById('hwType')?.value;
    const question = document.getElementById('hwQuestion')?.value;
    const marks = document.getElementById('hwMarks')?.value;
    const date = document.getElementById('hwDate')?.value;
    const hint = document.getElementById('hwHint')?.value;
    const chapter = document.getElementById('hwChapter')?.value;
    const topic = document.getElementById('hwTopic')?.value;
    const questionImageFile = document.getElementById('hwQuestionImage')?.files[0];
    
    if (!classVal || !subject || !type || !question) {
        showError('Please fill in all required fields (Class, Subject, Type, Question)');
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
            image: null,
            imageFile: imageFile
        });
    });
    
    // Get correct answer
    const correctRadio = document.querySelector('input[name="correctOption"]:checked');
    const correctAnswer = correctRadio ? String.fromCharCode(65 + parseInt(correctRadio.value)) : null;
    
    // Check if this is an update or add
    const submitBtn = document.querySelector('#addHomeworkForm button[type="submit"]');
    const isUpdate = submitBtn && submitBtn.dataset.editId;
    
    if (isUpdate) {
        updateHomework(submitBtn.dataset.editId);
        return;
    }
    
    // Upload images and submit
    uploadImagesAndSubmit({
        class: classVal,
        subject: subject,
        type: type,
        question: question,
        marks: marks,
        date: date,
        hint: hint,
        chapter: chapter,
        topic: topic,
        questionImageFile: questionImageFile,
        options: options,
        correctAnswer: correctAnswer
    });
}

function uploadImagesAndSubmit(data) {
    let imagesToUpload = [];
    
    // Check if question image needs upload
    if (data.questionImageFile) {
        const formData = new FormData();
        formData.append('image', data.questionImageFile);
        imagesToUpload.push({
            type: 'question',
            data: formData
        });
    }
    
    // Check if option images need upload
    data.options.forEach((opt, index) => {
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
        submitHomeworkData(data, null, []);
        return;
    }
    
    // Upload images one by one
    let uploadedImages = {};
    let uploadCount = 0;
    
    imagesToUpload.forEach((item) => {
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
                const optionImagePaths = data.options.map((_, idx) => uploadedImages[idx] || null);
                submitHomeworkData(
                    data,
                    uploadedImages.question || null,
                    optionImagePaths
                );
            }
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            showError('Error uploading image: ' + error.message);
            uploadCount++;
        });
    });
}

function submitHomeworkData(data, questionImagePath, optionImages) {
    const finalOptions = data.options.map((opt, idx) => ({
        text: opt.text,
        image: optionImages[idx] || null
    }));
    
    const submitData = {
        class: data.class,
        subject: data.subject,
        type: data.type,
        question: data.question,
        question_image: questionImagePath,
        options: finalOptions,
        correct_answer: data.correctAnswer,
        marks: data.marks || 1,
        date: data.date || new Date().toISOString().split('T')[0],
        hint: data.hint || '',
        chapter: data.chapter || '',
        topic: data.topic || ''
    };
    
    fetch('/api/add_homework', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('Homework added successfully!');
            document.getElementById('addHomeworkForm').reset();
            document.querySelectorAll('.image-preview, .option-preview').forEach(el => {
                if (el) el.innerHTML = '';
            });
            loadHomework();
            loadManageHomework();
            
            // Re-render LaTeX
            reRenderMath();
        } else {
            showError('Failed to add homework: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        showError('Error adding homework: ' + error.message);
    });
}

// ============================================
// Manage Homework
// ============================================

function loadManageHomework() {
    const classFilter = document.getElementById('manageClass')?.value || '';
    const subjectFilter = document.getElementById('manageSubject')?.value || '';
    const chapterFilter = document.getElementById('manageChapter')?.value || '';
    const topicFilter = document.getElementById('manageTopic')?.value || '';
    
    const params = new URLSearchParams();
    if (classFilter) params.append('class', classFilter);
    if (subjectFilter) params.append('subject', subjectFilter);
    if (chapterFilter) params.append('chapter', chapterFilter);
    if (topicFilter) params.append('topic', topicFilter);
    
    const list = document.getElementById('manageList');
    if (!list) return;
    
    list.innerHTML = '<p style="text-align: center; color: var(--gray);">Loading...</p>';
    
    fetch(`/api/homework?${params.toString()}`)
        .then(response => response.json())
        .then(homework => {
            if (homework.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: var(--gray);">No homework found</p>';
                return;
            }
            
            list.innerHTML = homework.map(hw => {
                const hasQuestionImage = hw.question_image && hw.question_image !== 'null' && hw.question_image !== 'None';
                const hasOptionImages = hw.options && hw.options.some(opt => opt.image && opt.image !== 'null' && opt.image !== 'None');
                
                // Display chapter and topic if available
                let chapterTopicDisplay = '';
                if (hw.chapter || hw.topic) {
                    chapterTopicDisplay = `
                        <br>
                        <small>
                            ${hw.chapter ? `<i class="fas fa-layer-group"></i> ${hw.chapter}` : ''}
                            ${hw.chapter && hw.topic ? ' | ' : ''}
                            ${hw.topic ? `<i class="fas fa-tags"></i> ${hw.topic}` : ''}
                        </small>
                    `;
                }
                
                return `
                    <div class="manage-item">
                        <div class="item-info">
                            <strong>Class ${hw.class}</strong> - ${hw.subject.charAt(0).toUpperCase() + hw.subject.slice(1)}
                            ${chapterTopicDisplay}
                            <br>
                            <small><strong>${hw.type.toUpperCase()}:</strong> ${hw.question.substring(0, 60)}${hw.question.length > 60 ? '...' : ''}</small>
                            <br>
                            <small>
                                ${hasQuestionImage ? '<i class="fas fa-image" style="color: var(--primary);"></i> Has question image ' : ''}
                                ${hasOptionImages ? '<i class="fas fa-images" style="color: var(--secondary);"></i> Has option images ' : ''}
                                ${hw.options ? `<i class="fas fa-list"></i> ${hw.options.length} options` : ''}
                            </small>
                            <br>
                            <small><i class="fas fa-calendar"></i> ${hw.date || 'No date'} | <i class="fas fa-star"></i> ${hw.marks || 1} marks</small>
                        </div>
                        <div class="item-actions">
                            <button class="btn btn-secondary btn-sm" onclick="editHomework('${hw.id}')">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteHomework('${hw.id}')">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
            
            // Re-render LaTeX
            reRenderMath();
        })
        .catch(error => {
            console.error('Error loading homework:', error);
            list.innerHTML = '<p style="text-align: center; color: var(--danger);">Error loading homework. Please try again.</p>';
        });
}

// ============================================
// Delete Homework
// ============================================

function deleteHomework(hwId) {
    if (!confirm('⚠️ Are you sure you want to delete this homework? This action cannot be undone!')) return;
    
    fetch(`/api/delete_homework/${hwId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('Homework deleted successfully!');
            loadManageHomework();
            loadHomework();
        } else {
            showError('Failed to delete homework: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        showError('Error deleting homework: ' + error.message);
    });
}

// ============================================
// Edit Homework
// ============================================

function editHomework(hwId) {
    const hw = currentHomework.find(h => h.id === hwId);
    if (!hw) {
        showError('Homework not found');
        return;
    }
    
    // Switch to add tab
    const addTabBtn = document.querySelector('[data-tab="add"]');
    if (addTabBtn) {
        addTabBtn.click();
    }
    
    // Fill form with data
    const hwClass = document.getElementById('hwClass');
    const hwSubject = document.getElementById('hwSubject');
    const hwType = document.getElementById('hwType');
    const hwQuestion = document.getElementById('hwQuestion');
    const hwMarks = document.getElementById('hwMarks');
    const hwDate = document.getElementById('hwDate');
    const hwHint = document.getElementById('hwHint');
    const hwChapter = document.getElementById('hwChapter');
    const hwTopic = document.getElementById('hwTopic');
    const questionImagePreview = document.getElementById('questionImagePreview');
    
    if (hwClass) hwClass.value = hw.class;
    if (hwSubject) hwSubject.value = hw.subject;
    if (hwType) hwType.value = hw.type;
    if (hwQuestion) hwQuestion.value = hw.question;
    if (hwMarks) hwMarks.value = hw.marks || 1;
    if (hwDate) hwDate.value = hw.date || '';
    if (hwHint) hwHint.value = hw.hint || '';
    if (hwChapter) hwChapter.value = hw.chapter || '';
    if (hwTopic) hwTopic.value = hw.topic || '';
    
    // Show question image if exists
    if (questionImagePreview && hw.question_image) {
        questionImagePreview.innerHTML = `
            <img src="${hw.question_image}" style="max-width: 200px; max-height: 150px; border-radius: 8px; border: 2px solid var(--light-gray); margin-top: 10px;">
            <p><small>Current image</small></p>
        `;
    }
    
    // Handle options if MCQ
    if (hw.type === 'mcqs' && hw.options && hw.options.length > 0) {
        toggleOptions();
        const optionTexts = document.querySelectorAll('.option-text');
        const optionPreviews = document.querySelectorAll('.option-preview');
        
        hw.options.forEach((opt, idx) => {
            if (optionTexts[idx]) {
                const text = typeof opt === 'string' ? opt : opt.text || '';
                optionTexts[idx].value = text;
            }
            
            if (optionPreviews[idx]) {
                const image = typeof opt === 'object' ? opt.image : null;
                if (image && image !== 'null' && image !== 'None') {
                    optionPreviews[idx].innerHTML = `
                        <img src="${image}" style="max-width: 100px; max-height: 80px; border-radius: 4px; border: 2px solid var(--light-gray); margin-top: 5px;">
                    `;
                }
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
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-sync"></i> Update Homework';
        submitBtn.dataset.editId = hwId;
    }
    
    // Change form submit handler for update
    const form = document.getElementById('addHomeworkForm');
    if (form) {
        form.onsubmit = function(e) {
            e.preventDefault();
            updateHomework(hwId);
        };
    }
    
    // Scroll to form
    form?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ============================================
// Update Homework
// ============================================

function updateHomework(hwId) {
    // Collect form data
    const classVal = document.getElementById('hwClass')?.value;
    const subject = document.getElementById('hwSubject')?.value;
    const type = document.getElementById('hwType')?.value;
    const question = document.getElementById('hwQuestion')?.value;
    const marks = document.getElementById('hwMarks')?.value;
    const date = document.getElementById('hwDate')?.value;
    const hint = document.getElementById('hwHint')?.value;
    const chapter = document.getElementById('hwChapter')?.value;
    const topic = document.getElementById('hwTopic')?.value;
    
    if (!classVal || !subject || !type || !question) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Collect options
    const options = [];
    const optionTexts = document.querySelectorAll('.option-text');
    const optionImageInputs = document.querySelectorAll('.option-image');
    
    optionTexts.forEach((input, index) => {
        const text = input.value.trim();
        const imageInput = optionImageInputs[index];
        let imagePath = null;
        
        // If there's a preview image already, keep it
        const preview = document.getElementById(`optionPreview${index}`);
        if (preview) {
            const existingImg = preview.querySelector('img');
            if (existingImg) {
                // This is a hack - we should store the image path
                // For now, we'll assume if there's an image preview, it's already uploaded
                imagePath = existingImg.src;
            }
        }
        
        if (text || imagePath) {
            options.push({
                text: text,
                image: imagePath
            });
        }
    });
    
    // Get correct answer
    const correctRadio = document.querySelector('input[name="correctOption"]:checked');
    const correctAnswer = correctRadio ? String.fromCharCode(65 + parseInt(correctRadio.value)) : null;
    
    const data = {
        class: classVal,
        subject: subject,
        type: type,
        question: question,
        question_image: document.getElementById('questionImagePreview')?.querySelector('img')?.src || null,
        options: options,
        correct_answer: correctAnswer,
        marks: marks || 1,
        date: date || new Date().toISOString().split('T')[0],
        hint: hint || '',
        chapter: chapter || '',
        topic: topic || ''
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
            showSuccess('Homework updated successfully!');
            
            // Reset form
            document.getElementById('addHomeworkForm').reset();
            document.querySelectorAll('.image-preview, .option-preview').forEach(el => {
                if (el) el.innerHTML = '';
            });
            
            // Reset submit button
            const submitBtn = document.querySelector('#addHomeworkForm button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Add Homework';
                delete submitBtn.dataset.editId;
            }
            
            // Reset form handler
            const form = document.getElementById('addHomeworkForm');
            if (form) {
                form.onsubmit = handleAddHomework;
            }
            
            loadHomework();
            loadManageHomework();
            
            // Re-render LaTeX
            reRenderMath();
        } else {
            showError('Failed to update homework: ' + (result.error || 'Unknown error'));
        }
    })
    .catch(error => {
        showError('Error updating homework: ' + error.message);
    });
}

// ============================================
// Export functions for global access
// ============================================

window.showQuestionDetail = showQuestionDetail;
window.deleteHomework = deleteHomework;
window.editHomework = editHomework;
window.renderMath = renderMath;
window.reRenderMath = reRenderMath;
window.loadHomework = loadHomework;
window.loadManageHomework = loadManageHomework;
window.closeModal = closeModal;
window.resetFilters = resetFilters;