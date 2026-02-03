// Простая карусель для раздела работ
//файл cable_system.js
document.addEventListener('DOMContentLoaded', function() {
    const projectsContainer = document.querySelector('.projects-container');
    const projects = document.querySelectorAll('.project-item');
    const indicators = document.querySelectorAll('.indicator');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');


    if (!projectsContainer || projects.length === 0) return;

    let currentIndex = 0;
    const totalProjects = projects.length;

    function showProject(index) {
        // Скрываем все проекты
        projects.forEach(project => {
            project.classList.remove('active');
            project.style.transform = 'translateX(100%)';
            project.style.opacity = '0';
        });

        // Показываем текущий проект
        projects[index].classList.add('active');
        projects[index].style.transform = 'translateX(0)';
        projects[index].style.opacity = '1';

        // Обновляем индикаторы
        indicators.forEach((indicator, i) => {
            indicator.classList.toggle('active', i === index);
        });

        currentIndex = index;
    }

    // События для навигации
    prevBtn.addEventListener('click', () => {
        const newIndex = currentIndex > 0 ? currentIndex - 1 : totalProjects - 1;
        showProject(newIndex);
    });

    nextBtn.addEventListener('click', () => {
        const newIndex = currentIndex < totalProjects - 1 ? currentIndex + 1 : 0;
        showProject(newIndex);
    });

    // События для индикаторов
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => {
            showProject(index);
        });
    });

    // Автопрокрутка
    let autoplayTimer;

    function startAutoplay() {
        autoplayTimer = setInterval(() => {
            const nextIndex = (currentIndex + 1) % totalProjects;
            showProject(nextIndex);
        }, 500000); // Смена каждые 5 секунд
    }

    function stopAutoplay() {
        clearInterval(autoplayTimer);
    }

    // Пауза при наведении
    projectsContainer.addEventListener('mouseenter', stopAutoplay);
    projectsContainer.addEventListener('mouseleave', startAutoplay);

    // Инициализация
    showProject(0);
    startAutoplay();

    // Свайп для мобильных
    let startX = 0;
    let endX = 0;

    projectsContainer.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        stopAutoplay();
    });

    projectsContainer.addEventListener('touchend', (e) => {
        endX = e.changedTouches[0].clientX;
        handleSwipe();
        startAutoplay();
    });

    function handleSwipe() {
        const threshold = 50;
        const diff = startX - endX;

        if (Math.abs(diff) > threshold) {
            if (diff > 0) {
                const newIndex = currentIndex < totalProjects - 1 ? currentIndex + 1 : 0;
                showProject(newIndex);
            } else {
                const newIndex = currentIndex > 0 ? currentIndex - 1 : totalProjects - 1;
                showProject(newIndex);
            }
        }
    }

    // Добавляем стили для анимации
    const style = document.createElement('style');
    style.textContent = `
        .project-item {
            transition: transform 0.5s ease, opacity 0.5s ease;
            position: absolute;
            width: 100%;
        }

        .projects-container {
            position: relative;
            min-height: 500px;
        }
    `;
    document.head.appendChild(style);
});