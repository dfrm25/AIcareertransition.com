/**
 * AI Career Transition - Main JavaScript
 * Handles all interactive functionality
 */

// ========================================
// Initialize on DOM Load
// ========================================
document.addEventListener('DOMContentLoaded', function() {
  initNavigation();
  initQuiz();
  initTabs();
  initAccordions();
  initCopyButtons();
  initScrollAnimations();
  initScrollHeader();
  initVideoPlayers();
  initCollapsibleSections();
  initBackToTop();
  initPromptOfDay();
  initPromptFilter();
  initFavorites();
});

// ========================================
// Navigation
// ========================================
function initNavigation() {
  const toggle = document.querySelector('.navbar-toggle');
  const menu = document.querySelector('.navbar-menu');
  const body = document.body;
  
  if (!toggle || !menu) {
    console.error('Navigation elements not found:', { toggle: !!toggle, menu: !!menu });
    return;
  }
  
  // Create backdrop element
  let backdrop = document.querySelector('.navbar-backdrop');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.className = 'navbar-backdrop';
    document.body.appendChild(backdrop);
  }
  
  const toggleMenu = (isOpen) => {
    if (isOpen) {
      menu.classList.add('active');
      backdrop.classList.add('active');
      toggle.setAttribute('aria-expanded', 'true');
      body.style.overflow = 'hidden';
    } else {
      menu.classList.remove('active');
      backdrop.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
      body.style.overflow = '';
    }
  };
  
  toggle.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const isActive = menu.classList.contains('active');
    toggleMenu(!isActive);
  });
  
  // Close menu when clicking backdrop
  backdrop.addEventListener('click', () => {
    toggleMenu(false);
  });
  
  // Close menu when clicking a link (allow navigation to happen first)
  menu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', (e) => {
      // Close menu immediately - navigation will happen anyway
      toggleMenu(false);
    });
  });
  
  // Close menu on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('active')) {
      toggleMenu(false);
    }
  });
}

function initScrollHeader() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  
  let lastScroll = 0;
  
  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
  });
}

// ========================================
// AI Readiness Quiz
// ========================================
const quizQuestions = [
  {
    question: "How often do you currently use AI tools in your work?",
    options: [
      { text: "Never - I haven't started yet", score: 0 },
      { text: "Rarely - Once a month or less", score: 1 },
      { text: "Sometimes - A few times a week", score: 2 },
      { text: "Daily - It's part of my workflow", score: 3 }
    ]
  },
  {
    question: "Which AI tools have you used before?",
    options: [
      { text: "None", score: 0 },
      { text: "ChatGPT or similar chatbots", score: 1 },
      { text: "Multiple AI tools (chatbots, image generators, etc.)", score: 2 },
      { text: "Advanced tools (API integrations, custom prompts, agents)", score: 3 }
    ]
  },
  {
    question: "How would you rate your understanding of prompt engineering?",
    options: [
      { text: "What is prompt engineering?", score: 0 },
      { text: "I know the basics - ask clear questions", score: 1 },
      { text: "Intermediate - I use techniques like few-shot prompting", score: 2 },
      { text: "Advanced - I build complex prompt chains and systems", score: 3 }
    ]
  },
  {
    question: "Have you automated any tasks using AI?",
    options: [
      { text: "No, I haven't tried automation", score: 0 },
      { text: "I've automated simple tasks like email drafts", score: 1 },
      { text: "I've built workflows with tools like Zapier + AI", score: 2 },
      { text: "I've created custom AI agents or applications", score: 3 }
    ]
  },
  {
    question: "How comfortable are you explaining AI concepts to colleagues?",
    options: [
      { text: "Not comfortable - I'm still learning myself", score: 0 },
      { text: "Somewhat - I can explain basics", score: 1 },
      { text: "Comfortable - I often help others get started", score: 2 },
      { text: "Very comfortable - I lead AI initiatives", score: 3 }
    ]
  },
  {
    question: "What's your experience with AI in your specific field?",
    options: [
      { text: "I don't know how AI applies to my field", score: 0 },
      { text: "I've read about use cases but haven't tried them", score: 1 },
      { text: "I use AI for field-specific tasks regularly", score: 2 },
      { text: "I've developed innovative AI applications for my field", score: 3 }
    ]
  },
  {
    question: "How do you approach learning new AI tools?",
    options: [
      { text: "I wait until someone shows me", score: 0 },
      { text: "I try them when required for work", score: 1 },
      { text: "I actively explore new tools monthly", score: 2 },
      { text: "I'm an early adopter - testing new tools weekly", score: 3 }
    ]
  },
  {
    question: "Have you taken any formal AI training or certifications?",
    options: [
      { text: "No formal training", score: 0 },
      { text: "Watched some YouTube tutorials", score: 1 },
      { text: "Completed online courses (Coursera, etc.)", score: 2 },
      { text: "Have professional AI certifications", score: 3 }
    ]
  }
];

let currentQuestion = 0;
let quizAnswers = [];

function initQuiz() {
  const quizContainer = document.getElementById('quiz-container');
  if (!quizContainer) return;
  
  renderQuestion();
}

function renderQuestion() {
  const quizContainer = document.getElementById('quiz-container');
  const question = quizQuestions[currentQuestion];
  
  // Progress steps
  let progressHTML = '<div class="quiz-progress">';
  for (let i = 0; i < quizQuestions.length; i++) {
    let stepClass = 'quiz-progress-step';
    if (i < currentQuestion) stepClass += ' completed';
    if (i === currentQuestion) stepClass += ' active';
    progressHTML += `<div class="${stepClass}"></div>`;
  }
  progressHTML += '</div>';
  
  // Question
  let questionHTML = `
    <div class="quiz-question">
      <div class="quiz-question-number">Question ${currentQuestion + 1} of ${quizQuestions.length}</div>
      <div class="quiz-question-text">${question.question}</div>
    </div>
  `;
  
  // Options
  let optionsHTML = '<div class="quiz-options">';
  question.options.forEach((option, index) => {
    const selected = quizAnswers[currentQuestion] === index ? 'selected' : '';
    optionsHTML += `
      <div class="quiz-option ${selected}" data-index="${index}" onclick="selectOption(${index})">
        <div class="quiz-option-indicator"></div>
        <div class="quiz-option-text">${option.text}</div>
      </div>
    `;
  });
  optionsHTML += '</div>';
  
  // Actions
  let actionsHTML = '<div class="quiz-actions">';
  if (currentQuestion > 0) {
    actionsHTML += `<button class="btn btn-secondary" onclick="prevQuestion()">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      Previous
    </button>`;
  } else {
    actionsHTML += '<div></div>';
  }
  
  if (currentQuestion < quizQuestions.length - 1) {
    actionsHTML += `<button class="btn btn-primary" onclick="nextQuestion()" id="next-btn" disabled>
      Next
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
    </button>`;
  } else {
    actionsHTML += `<button class="btn btn-primary" onclick="showResults()" id="finish-btn" disabled>
      See Results
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
    </button>`;
  }
  actionsHTML += '</div>';
  
  quizContainer.innerHTML = progressHTML + questionHTML + optionsHTML + actionsHTML;
  
  // Enable button if answer already selected
  if (quizAnswers[currentQuestion] !== undefined) {
    const btn = document.getElementById('next-btn') || document.getElementById('finish-btn');
    if (btn) btn.disabled = false;
  }
}

function selectOption(index) {
  quizAnswers[currentQuestion] = index;
  
  // Update UI
  document.querySelectorAll('.quiz-option').forEach((opt, i) => {
    opt.classList.toggle('selected', i === index);
  });
  
  // Enable next button
  const btn = document.getElementById('next-btn') || document.getElementById('finish-btn');
  if (btn) btn.disabled = false;
}

function nextQuestion() {
  if (quizAnswers[currentQuestion] === undefined) return;
  currentQuestion++;
  renderQuestion();
}

function prevQuestion() {
  if (currentQuestion > 0) {
    currentQuestion--;
    renderQuestion();
  }
}

function showResults() {
  const quizContainer = document.getElementById('quiz-container');
  
  // Calculate score
  let totalScore = 0;
  quizAnswers.forEach((answerIndex, questionIndex) => {
    totalScore += quizQuestions[questionIndex].options[answerIndex].score;
  });
  
  const maxScore = quizQuestions.length * 3;
  const percentage = Math.round((totalScore / maxScore) * 100);
  
  // Determine level and recommendation
  let level, title, description, recommendation, ctaLink, ctaText;
  
  if (percentage < 30) {
    level = '101';
    title = 'AI Beginner';
    description = "You're at the start of your AI journey! That's great - there's huge potential for growth. Our 101 courses are designed specifically for you, with step-by-step guidance to build your foundation.";
    recommendation = "Start with AI 101: Learn the fundamentals of AI tools, basic prompt engineering, and how to integrate AI into your daily workflow.";
    ctaLink = '101.html';
    ctaText = 'Start AI 101 Courses';
  } else if (percentage < 60) {
    level = '101-201';
    title = 'AI Practitioner';
    description = "You have solid AI basics! You're using tools but there's room to deepen your skills. We recommend completing any 101 gaps, then moving to 201 for advanced techniques.";
    recommendation = "Review 101 fundamentals, then advance to 201: Learn advanced prompting, automation, and field-specific AI applications.";
    ctaLink = '101.html';
    ctaText = 'Review 101 & Start 201';
  } else {
    level = '201';
    title = 'AI Power User';
    description = "Impressive! You're already leveraging AI effectively. Our 201 courses will help you master advanced techniques, build AI-powered applications, and lead AI initiatives.";
    recommendation = "Jump into AI 201: Master advanced agents, build custom applications, and learn to lead AI transformation in your organization.";
    ctaLink = '201.html';
    ctaText = 'Start AI 201 Courses';
  }
  
  quizContainer.innerHTML = `
    <div class="quiz-result">
      <div class="quiz-result-score">${percentage}%</div>
      <h3 class="quiz-result-title">${title}</h3>
      <p class="quiz-result-description">${description}</p>
      
      <div class="quiz-result-recommendation">
        <h4>📚 Our Recommendation</h4>
        <p>${recommendation}</p>
      </div>
      
      <div class="flex justify-center gap-md">
        <a href="${ctaLink}" class="btn btn-primary btn-lg">
          ${ctaText}
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
        <button class="btn btn-secondary" onclick="restartQuiz()">Retake Quiz</button>
      </div>
    </div>
  `;
  
  // Store result in localStorage for personalization
  localStorage.setItem('aiReadinessLevel', level);
  localStorage.setItem('aiReadinessScore', percentage);
}

function restartQuiz() {
  currentQuestion = 0;
  quizAnswers = [];
  renderQuestion();
}

// ========================================
// Tab Navigation
// ========================================
function initTabs() {
  const tabContainers = document.querySelectorAll('[data-tabs]');
  
  tabContainers.forEach(container => {
    const tabs = container.querySelectorAll('.tab');
    const contents = container.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        
        // Update tabs
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update content
        contents.forEach(content => {
          content.classList.toggle('active', content.id === target);
        });
      });
    });
  });
}

// ========================================
// Accordions
// ========================================
function initAccordions() {
  const accordions = document.querySelectorAll('.accordion-item');
  
  accordions.forEach(item => {
    const header = item.querySelector('.accordion-header');
    
    header.addEventListener('click', () => {
      const isActive = item.classList.contains('active');
      
      // Close all accordions in the same group
      item.closest('.accordion').querySelectorAll('.accordion-item').forEach(acc => {
        acc.classList.remove('active');
      });
      
      // Toggle current
      if (!isActive) {
        item.classList.add('active');
      }
    });
  });
}

// ========================================
// Copy to Clipboard
// ========================================
function initCopyButtons() {
  document.querySelectorAll('.prompt-card-copy').forEach(btn => {
    btn.addEventListener('click', async () => {
      const promptText = btn.closest('.prompt-card').querySelector('.prompt-card-text').textContent;
      
      try {
        await navigator.clipboard.writeText(promptText);
        btn.classList.add('copied');
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
        
        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
        }, 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    });
  });
}

// ========================================
// Scroll Animations
// ========================================
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });
  
  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
  });
}

// ========================================
// Video Players
// ========================================
function initVideoPlayers() {
  document.querySelectorAll('.video-card-play').forEach(btn => {
    btn.addEventListener('click', function() {
      const thumbnail = this.closest('.video-card-thumbnail');
      const videoId = thumbnail.dataset.videoId;
      
      if (videoId) {
        // Replace thumbnail with iframe
        thumbnail.innerHTML = `
          <iframe 
            src="https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0" 
            title="Video player"
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
          </iframe>
        `;
      }
    });
  });
}

// Global function for inline play buttons
function playVideo(videoId) {
  window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
}

// ========================================
// Collapsible Sections
// ========================================
function toggleCollapsible(id) {
  const content = document.getElementById(id);
  if (!content) return;
  
  const header = content.previousElementSibling;
  const toggle = header ? header.querySelector('.collapse-toggle') : null;
  
  if (!toggle) return;
  
  const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
  
  content.classList.toggle('collapsed');
  toggle.setAttribute('aria-expanded', !isExpanded);
}

function initCollapsibleSections() {
  // Initialize all collapsible sections as expanded by default
  const collapsibles = document.querySelectorAll('.collapsible-content');
  collapsibles.forEach(content => {
    content.classList.remove('collapsed');
  });
}

// ========================================
// Back to Top Button
// ========================================
function initBackToTop() {
  const backToTopBtn = document.getElementById('back-to-top');
  if (!backToTopBtn) return;
  
  // Show/hide button based on scroll position
  window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
      backToTopBtn.classList.add('visible');
    } else {
      backToTopBtn.classList.remove('visible');
    }
  });
  
  // Smooth scroll to top when clicked
  backToTopBtn.addEventListener('click', () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
}

// ========================================
// Form Handling — Feedback, Feature, Contact
// Same Google Apps Script handles all (form param routes to Feedback spreadsheet)
// ========================================
var FORM_SUBMIT_URL = 'https://script.google.com/macros/s/AKfycbwlodnDDto_5AE8NSh-6IX8LwcUL89fOCjkcQomNSbh9L1lQS1HJpmu2FDUNWYuBzqi/exec';

function submitFormViaPing(params, btn, msgEl, successText) {
  if (!params.form || !params.message) return;
  if (btn) { btn.disabled = true; btn.innerHTML = 'Sending...'; }
  if (msgEl) { msgEl.style.display = 'none'; }
  var qs = Object.keys(params).map(function(k) {
    return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
  }).join('&');
  var url = FORM_SUBMIT_URL + '?' + qs;
  var img = new Image();
  img.onload = img.onerror = function() {
    if (msgEl) {
      msgEl.textContent = successText || 'Thank you! Your message has been received.';
      msgEl.style.color = '#10b981';
      msgEl.style.display = 'block';
    }
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = btn.getAttribute('data-original-html') || 'Submit';
    }
  };
  img.src = url;
}

function handleFeedbackSubmit(event) {
  event.preventDefault();
  var form = event.target;
  var btn = form.querySelector('#feedback-submit-btn') || form.querySelector('button[type="submit"]');
  var msgEl = document.getElementById('feedback-msg');
  var name = (form.querySelector('[name="name"]') || {}).value || '';
  var email = (form.querySelector('[name="email"]') || {}).value || '';
  var role = (form.querySelector('[name="role"]') || {}).value || '';
  var type = (form.querySelector('[name="type"]') || {}).value || '';
  var message = (form.querySelector('[name="message"]') || {}).value || '';
  if (!message) return;
  if (btn) btn.setAttribute('data-original-html', btn.innerHTML);
  submitFormViaPing({
    form: 'feedback',
    name: name,
    email: email,
    category: role,
    subject: type,
    message: message
  }, btn, msgEl, 'Thank you! Your feedback has been submitted successfully.');
}

function handleFeatureSubmit(event) {
  event.preventDefault();
  var form = event.target;
  var btn = form.querySelector('button[type="submit"]');
  var msgEl = document.getElementById('feature-msg');
  var title = (form.querySelector('[name="title"]') || {}).value || '';
  var category = (form.querySelector('[name="category"]') || {}).value || '';
  var description = (form.querySelector('[name="description"]') || {}).value || '';
  var email = (form.querySelector('[name="email"]') || {}).value || '';
  if (!description) return;
  if (btn) btn.setAttribute('data-original-html', btn.innerHTML);
  submitFormViaPing({
    form: 'feature',
    name: '',
    email: email,
    subject: title,
    category: category,
    message: description
  }, btn, msgEl, 'Thank you! Your feature idea has been submitted.');
}

function handleContactSubmit(event) {
  event.preventDefault();
  var form = event.target;
  var btn = form.querySelector('button[type="submit"]');
  var msgEl = document.getElementById('contact-msg');
  var name = (form.querySelector('[name="name"]') || {}).value || '';
  var email = (form.querySelector('[name="email"]') || {}).value || '';
  var subject = (form.querySelector('[name="subject"]') || {}).value || '';
  var message = (form.querySelector('[name="message"]') || {}).value || '';
  if (!message || !name || !email || !subject) return;
  if (btn) btn.setAttribute('data-original-html', btn.innerHTML);
  submitFormViaPing({
    form: 'contact',
    name: name,
    email: email,
    subject: subject,
    category: '',
    message: message
  }, btn, msgEl, 'Thank you! We\'ll be in touch soon.');
}

// ========================================
// Smooth Scroll
// ========================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// ========================================
// Personalization based on quiz results
// ========================================
function getPersonalizedContent() {
  const level = localStorage.getItem('aiReadinessLevel');
  const score = localStorage.getItem('aiReadinessScore');
  
  if (level && score) {
    // Show personalized welcome message
    const welcome = document.querySelector('.personalized-welcome');
    if (welcome) {
      welcome.innerHTML = `
        <p>Welcome back! Based on your AI readiness score of ${score}%, we recommend ${level} courses for you.</p>
      `;
      welcome.style.display = 'block';
    }
  }
}

// Run personalization on page load
document.addEventListener('DOMContentLoaded', getPersonalizedContent);

// ========================================
// Prompt of the Day (automatic — zero maintenance)
// Changes daily based on date math; cycles through all existing prompts
// ========================================
function initPromptOfDay() {
  const container = document.getElementById('prompt-of-day');
  if (!container) return;

  const prompts = Array.from(document.querySelectorAll('.prompt-section .prompt-card'));
  if (!prompts.length) return;

  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const dayOfYear = Math.floor((now - start) / 86400000);
  const idx = dayOfYear % prompts.length;
  const card = prompts[idx];

  const title = card.querySelector('.prompt-card-title')?.textContent?.trim() || '';
  const text = card.querySelector('.prompt-card-text')?.textContent?.trim() || '';
  const category = card.querySelector('.prompt-card-category')?.textContent?.trim() || '';

  container.innerHTML = `
    <div class="prompt-card" style="max-width:680px;margin:0 auto;">
      <div class="prompt-card-header">
        <span class="prompt-card-category">${category}</span>
        <button class="prompt-card-copy potd-copy" title="Copy to clipboard">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        </button>
      </div>
      <h4 class="prompt-card-title">${title}</h4>
      <div class="prompt-card-text">${text}</div>
    </div>`;

  const btn = container.querySelector('.potd-copy');
  if (btn) {
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(text);
        btn.classList.add('copied');
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
        }, 2000);
      } catch(e) {}
    });
  }
}

// ========================================
// Client-side Prompt Filter / Search
// ========================================
function initPromptFilter() {
  const input = document.getElementById('prompt-search');
  if (!input) return;

  const clearBtn = document.getElementById('prompt-search-clear');

  function doFilter() {
    const query = input.value.toLowerCase().trim();
    if (clearBtn) clearBtn.style.display = query ? 'flex' : 'none';

    let totalVisible = 0;
    document.querySelectorAll('.prompt-section').forEach(section => {
      let sectionVisible = 0;
      section.querySelectorAll('.prompt-card').forEach(card => {
        const match = !query || card.textContent.toLowerCase().includes(query);
        card.style.display = match ? '' : 'none';
        if (match) sectionVisible++;
      });
      section.style.display = sectionVisible > 0 ? '' : 'none';
      totalVisible += sectionVisible;
    });

    const noResults = document.getElementById('prompt-no-results');
    if (noResults) noResults.style.display = totalVisible === 0 ? 'block' : 'none';
  }

  input.addEventListener('input', doFilter);
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      doFilter();
      input.focus();
    });
  }
}

// ========================================
// Save to Favourites (localStorage)
// ========================================
function initFavorites() {
  if (!document.querySelector('.prompt-card')) return;

  let saved = [];
  try { saved = JSON.parse(localStorage.getItem('savedPrompts') || '[]'); } catch(e) {}

  function updateCounter() {
    const counter = document.getElementById('saved-count');
    if (!counter) return;
    counter.textContent = saved.length;
  }

  function showToast(msg) {
    const t = document.createElement('div');
    t.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0f172a;color:#fff;padding:10px 22px;border-radius:8px;font-size:0.875rem;z-index:9999;pointer-events:none;transition:opacity 0.3s;';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 1800);
  }

  document.querySelectorAll('.prompt-card').forEach(card => {
    const title = card.querySelector('.prompt-card-title')?.textContent?.trim() || '';
    const header = card.querySelector('.prompt-card-header');
    if (!header || !title) return;

    const isSaved = () => saved.includes(title);

    const btn = document.createElement('button');
    btn.className = 'prompt-card-fav';
    btn.title = isSaved() ? 'Unsave' : 'Save prompt';
    btn.setAttribute('aria-label', isSaved() ? 'Unsave prompt' : 'Save prompt');
    const heartFilled = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
    const heartEmpty = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
    btn.innerHTML = isSaved() ? heartFilled : heartEmpty;
    if (isSaved()) btn.style.color = '#ef4444';

    btn.addEventListener('click', () => {
      if (isSaved()) {
        saved = saved.filter(s => s !== title);
        btn.innerHTML = heartEmpty;
        btn.style.color = '';
        btn.title = 'Save prompt';
        showToast('Removed from saved');
      } else {
        saved.push(title);
        btn.innerHTML = heartFilled;
        btn.style.color = '#ef4444';
        btn.title = 'Unsave';
        showToast('Prompt saved!');
      }
      localStorage.setItem('savedPrompts', JSON.stringify(saved));
      updateCounter();
    });

    const copyBtn = header.querySelector('.prompt-card-copy');
    if (copyBtn) {
      header.insertBefore(btn, copyBtn);
    } else {
      header.appendChild(btn);
    }
  });

  updateCounter();
}
