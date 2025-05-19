/**
 * accessibility.js
 * Keyboard navigation and focus management for DoseDash
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add focus outline to elements when keyboard navigation is detected
    document.body.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-nav');
        }
    });

    // Remove focus outline when mouse is used
    document.body.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-nav');
    });

    // Make cards keyboard navigable
    const cards = document.querySelectorAll('.card[role="button"], .resident-card, .medication-item');
    cards.forEach(card => {
        if (!card.getAttribute('tabindex')) {
            card.setAttribute('tabindex', '0');
        }
        
        // Handle "Enter" key for activating cards
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                // Find and click first link or button in the card
                const clickable = card.querySelector('a, button');
                if (clickable) {
                    clickable.click();
                }
            }
        });
    });

    // Improve modal accessibility
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        
        // Find the header and set aria-labelledby
        const modalHeader = modal.querySelector('.modal-title, h1, h2, h3, h4, h5');
        if (modalHeader) {
            const headerId = modalHeader.id || `modal-header-${Math.random().toString(36).substring(2, 9)}`;
            modalHeader.id = headerId;
            modal.setAttribute('aria-labelledby', headerId);
        }

        // Make close buttons more accessible
        const closeButtons = modal.querySelectorAll('[data-dismiss="modal"], .close-modal');
        closeButtons.forEach(button => {
            button.setAttribute('aria-label', 'Close dialog');
        });

        // Trap focus within modal when open
        modal.addEventListener('shown.bs.modal', trapFocus);
    });

    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.classList.add('visually-hidden', 'skip-link');
    skipLink.textContent = 'Skip to main content';

    skipLink.addEventListener('focus', function() {
        this.classList.add('visually-shown');
    });
    skipLink.addEventListener('blur', function() {
        this.classList.remove('visually-shown');
    });

    document.body.insertBefore(skipLink, document.body.firstChild);

    // Add main-content ID to the main content area if it doesn't exist
    const mainContent = document.querySelector('main') || document.querySelector('.main-content');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
});

/**
 * Trap focus within a modal or dialog
 * @param {HTMLElement} modal - The modal element
 */
function trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstFocusableElement = focusableElements[0];
    const lastFocusableElement = focusableElements[focusableElements.length - 1];
    
    // Set initial focus
    firstFocusableElement.focus();
    
    modal.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            // Shift+Tab
            if (e.shiftKey && document.activeElement === firstFocusableElement) {
                e.preventDefault();
                lastFocusableElement.focus();
            } 
            // Tab
            else if (!e.shiftKey && document.activeElement === lastFocusableElement) {
                e.preventDefault();
                firstFocusableElement.focus();
            }
        }
        
        // Escape key closes modal
        if (e.key === 'Escape') {
            modal.querySelector('[data-dismiss="modal"]').click();
        }
    });
}
