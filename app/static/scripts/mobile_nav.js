document.addEventListener('DOMContentLoaded', function () {
    // Add scroll shadow effect to navbar
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 10) {
                navbar.classList.add('shadow');
                navbar.classList.add('bg-white');
                navbar.classList.remove('bg-light');
            } else {
                navbar.classList.remove('shadow');
                navbar.classList.add('bg-light');
                navbar.classList.remove('bg-white');
            }
        });
    }
    
    // Close mobile menu when a link is clicked
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.getElementById('navbarNav');
    const bsCollapse = navbarCollapse ? new bootstrap.Collapse(navbarCollapse, {toggle: false}) : null;
    
    if (navLinks && bsCollapse) {
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navbarCollapse.classList.contains('show')) {
                    bsCollapse.toggle();
                }
            });
        });
    }
});
