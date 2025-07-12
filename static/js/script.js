// InkBoard JavaScript - Main Application Logic

class InkBoard {
    constructor() {
        this.currentCreationId = null;
        this.currentSection = 'create';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadGallery();
        this.showSection('create'); // Default to create section
    }

    setupEventListeners() {
        // Scene form submission
        document.getElementById('scene-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateContent();
        });

        // Journal modal save button
        document.getElementById('save-journal').addEventListener('click', () => {
            this.saveJournal();
        });

        // Handle modal close
        document.getElementById('journalModal').addEventListener('hidden.bs.modal', () => {
            this.currentCreationId = null;
            document.getElementById('journal-text').value = '';
        });
    }

    async generateContent() {
        const sceneIdea = document.getElementById('scene-idea').value.trim();
        
        if (!sceneIdea) {
            this.showAlert('Please enter a scene idea', 'danger');
            return;
        }

        try {
            this.showLoading(true);
            this.setButtonLoading(true);

            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    scene_idea: sceneIdea
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResult(data);
                this.loadGallery(); // Refresh gallery
                document.getElementById('scene-idea').value = ''; // Clear input
                this.showAlert('Story and image generated successfully!', 'success');
            } else {
                this.showAlert(data.error || 'Failed to generate content', 'danger');
            }

        } catch (error) {
            console.error('Error generating content:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        } finally {
            this.showLoading(false);
            this.setButtonLoading(false);
        }
    }

    displayResult(data) {
        const resultsSection = document.getElementById('results-section');
        
        // Build image section only if image was generated
        const imageSection = data.image_url ? `
            <div class="col-lg-6 mb-4">
                <div class="image-container">
                    <img src="${data.image_url}" alt="Generated Scene" class="img-fluid rounded shadow">
                </div>
            </div>
        ` : '';
        
        // Adjust story column width based on whether image exists
        const storyColClass = data.image_url ? 'col-lg-6' : 'col-12';
        
        // Build download button only if image exists
        const downloadButton = data.image_url ? `
            <button class="btn btn-outline-success btn-sm" onclick="inkBoard.downloadImage('${data.image_url}')">
                <i class="fas fa-download me-1"></i>
                Download Image
            </button>
        ` : '';
        
        const resultHTML = `
            <div class="col-12 mb-5">
                <div class="card shadow-lg border-0">
                    <div class="card-body p-4">
                        <h4 class="card-title text-center mb-4">
                            <i class="fas fa-sparkles me-2"></i>
                            Your Creation
                        </h4>
                        <div class="row">
                            ${imageSection}
                            <div class="${storyColClass}">
                                <div class="story-container">
                                    <h5 class="mb-3">
                                        <i class="fas fa-book-open me-2"></i>
                                        Your Story
                                    </h5>
                                    <p class="story-text">${data.story}</p>
                                    <div class="mt-3">
                                        <button class="btn btn-outline-primary btn-sm me-2" onclick="inkBoard.openJournal('${data.creation_id}')">
                                            <i class="fas fa-journal-whills me-1"></i>
                                            Add Journal Entry
                                        </button>
                                        ${downloadButton}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        resultsSection.innerHTML = resultHTML;
        
        // Smooth scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    async loadGallery() {
        try {
            const response = await fetch('/get_creations');
            const data = await response.json();
            
            const galleryGrid = document.getElementById('gallery-grid');
            
            if (data.creations && data.creations.length > 0) {
                const galleryHTML = data.creations.map(creation => this.createGalleryItem(creation)).join('');
                galleryGrid.innerHTML = galleryHTML;
            } else {
                galleryGrid.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-palette fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No creations yet</h5>
                        <p class="text-muted">Start by describing a scene above!</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading gallery:', error);
        }
    }

    createGalleryItem(creation) {
        const journalEntry = creation.journal_entry ? 
            `<div class="journal-entry">
                <small class="text-muted">
                    <i class="fas fa-journal-whills me-1"></i>
                    Journal Entry:
                </small>
                <p class="mb-0 mt-1">${creation.journal_entry}</p>
            </div>` : '';

        // Only include image section if image exists
        const imageSection = creation.image_url ? 
            `<img src="${creation.image_url}" alt="Scene: ${creation.scene_idea}" loading="lazy">` : '';
        
        // Only include download button if image exists
        const downloadButton = creation.image_url ? 
            `<button class="btn btn-outline-success btn-sm" onclick="inkBoard.downloadImage('${creation.image_url}')">
                <i class="fas fa-download me-1"></i>
                Download
            </button>` : '';

        return `
            <div class="gallery-item">
                ${imageSection}
                <div class="gallery-item-content">
                    <div class="gallery-item-scene">
                        <i class="fas fa-quote-left me-1"></i>
                        ${creation.scene_idea}
                    </div>
                    <div class="gallery-item-story">
                        ${creation.story}
                    </div>
                    ${journalEntry}
                    <div class="gallery-item-actions">
                        <button class="btn btn-outline-primary btn-sm" onclick="inkBoard.openJournal('${creation.id}', '${creation.journal_entry || ''}')">
                            <i class="fas fa-journal-whills me-1"></i>
                            ${creation.journal_entry ? 'Edit' : 'Add'} Journal
                        </button>
                        ${downloadButton}
                    </div>
                </div>
            </div>
        `;
    }

    openJournal(creationId, existingText = '') {
        this.currentCreationId = creationId;
        document.getElementById('journal-text').value = existingText;
        
        const modal = new bootstrap.Modal(document.getElementById('journalModal'));
        modal.show();
    }

    async saveJournal() {
        if (!this.currentCreationId) {
            this.showAlert('No creation selected', 'danger');
            return;
        }

        const journalText = document.getElementById('journal-text').value.trim();

        try {
            const response = await fetch('/save_journal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    creation_id: this.currentCreationId,
                    journal_entry: journalText
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Journal entry saved!', 'success');
                this.loadGallery(); // Refresh gallery
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('journalModal'));
                modal.hide();
            } else {
                this.showAlert(data.error || 'Failed to save journal', 'danger');
            }

        } catch (error) {
            console.error('Error saving journal:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        }
    }

    downloadImage(imageUrl) {
        // Create a temporary link element to trigger download
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `inkboard-creation-${Date.now()}.png`;
        link.target = '_blank';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showAlert('Image download started!', 'success');
    }

    showLoading(show) {
        const loadingSection = document.getElementById('loading-section');
        const resultsSection = document.getElementById('results-section');
        
        if (show) {
            loadingSection.classList.remove('d-none');
            resultsSection.innerHTML = ''; // Clear previous results
        } else {
            loadingSection.classList.add('d-none');
        }
    }

    setButtonLoading(loading) {
        const btn = document.getElementById('generate-btn');
        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.spinner-border');
        
        if (loading) {
            btn.classList.add('loading');
            btn.disabled = true;
            btnText.classList.add('d-none');
            spinner.classList.remove('d-none');
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
            btnText.classList.remove('d-none');
            spinner.classList.add('d-none');
        }
    }

    showAlert(message, type) {
        // Remove existing alerts
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        // Create new alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the main container
        const main = document.querySelector('main');
        main.insertBefore(alert, main.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.classList.add('d-none');
        });

        // Remove active class from all nav buttons
        document.querySelectorAll('.btn-nav').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('d-none');
        }

        // Add active class to the correct button
        const buttonSelectors = {
            'create': 'Create Story',
            'gallery': 'Gallery', 
            'journal': 'Journal'
        };
        
        document.querySelectorAll('.btn-nav').forEach(btn => {
            if (btn.textContent.trim().includes(buttonSelectors[sectionName])) {
                btn.classList.add('active');
            }
        });

        // Update current section
        this.currentSection = sectionName;

        // Load content based on section
        if (sectionName === 'gallery') {
            this.loadGallery();
        } else if (sectionName === 'journal') {
            this.loadJournalEntries();
        }
    }

    async loadJournalEntries() {
        try {
            const response = await fetch('/get_creations');
            const data = await response.json();
            
            const journalContainer = document.getElementById('journal-entries');
            
            // Filter creations that have journal entries
            const entriesWithJournal = data.creations?.filter(creation => creation.journal_entry) || [];
            
            if (entriesWithJournal.length > 0) {
                const journalHTML = entriesWithJournal.map(creation => this.createJournalEntry(creation)).join('');
                journalContainer.innerHTML = journalHTML;
            } else {
                journalContainer.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-journal-whills fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No journal entries yet</h5>
                        <p class="text-muted">Create a story and add journal entries to see them here!</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading journal entries:', error);
        }
    }

    createJournalEntry(creation) {
        const date = new Date().toLocaleDateString();
        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="card journal-card">
                    <div class="card-body">
                        <div class="journal-meta mb-2">
                            <small class="text-muted">
                                <i class="fas fa-calendar me-1"></i>
                                ${date}
                            </small>
                        </div>
                        <h6 class="card-title">
                            <i class="fas fa-quote-left me-1"></i>
                            ${creation.scene_idea}
                        </h6>
                        <div class="journal-entry-preview mb-3">
                            <p class="card-text">${creation.journal_entry}</p>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <button class="btn btn-sm btn-outline-primary" onclick="inkBoard.openJournal('${creation.id}', '${creation.journal_entry}')">
                                <i class="fas fa-edit me-1"></i>
                                Edit
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="inkBoard.viewFullStory('${creation.id}')">
                                <i class="fas fa-eye me-1"></i>
                                View Story
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    viewFullStory(creationId) {
        // Switch to gallery and highlight the specific creation
        this.showSection('gallery');
        // You could add highlighting logic here
    }
}

// Initialize the application
const inkBoard = new InkBoard();

// Additional utility functions
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling for all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add loading animation to images
    document.addEventListener('load', function(e) {
        if (e.target.tagName === 'IMG') {
            e.target.style.opacity = '0';
            e.target.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                e.target.style.opacity = '1';
            }, 100);
        }
    }, true);
});

// Handle window resize for masonry grid
window.addEventListener('resize', function() {
    // Trigger reflow for masonry grid
    const grid = document.getElementById('gallery-grid');
    if (grid) {
        grid.style.columnCount = '';
        grid.offsetHeight; // Force reflow
    }
});
