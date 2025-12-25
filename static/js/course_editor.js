// Расширенные функции для редактора курсов
class CourseEditor {
    constructor() {
        this.lessonCount = 0;
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateLessonNumbers();
    }
    
    bindEvents() {
        // Добавление урока
        document.getElementById('add-lesson-btn')?.addEventListener('click', () => this.addLesson());
        
        // Удаление урока
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-lesson')) {
                this.removeLesson(e.target.closest('.lesson-item'));
            }
        });
        
        // Предварительный просмотр изображения
        document.getElementById('image_url')?.addEventListener('change', (e) => {
            this.previewImage(e.target.value);
        });
    }
    
    addLesson() {
        const container = document.getElementById('lessons-container');
        const template = document.getElementById('new-lesson-template');
        
        if (template) {
            const clone = template.cloneNode(true);
            clone.classList.remove('d-none');
            clone.removeAttribute('id');
            
            this.lessonCount++;
            const title = clone.querySelector('h6');
            if (title) title.textContent = `Урок ${this.lessonCount}`;
            
            container.appendChild(clone);
        }
    }
    
    removeLesson(lessonElement) {
        if (lessonElement && document.querySelectorAll('.lesson-item').length > 1) {
            lessonElement.remove();
            this.updateLessonNumbers();
        }
    }
    
    updateLessonNumbers() {
        const lessons = document.querySelectorAll('.lesson-item');
        this.lessonCount = lessons.length;
        
        lessons.forEach((lesson, index) => {
            const title = lesson.querySelector('h6');
            if (title) {
                title.textContent = `Урок ${index + 1}`;
            }
        });
    }
    
    previewImage(url) {
        const preview = document.getElementById('image-preview');
        if (preview && url) {
            preview.src = url;
            preview.style.display = 'block';
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new CourseEditor();
});