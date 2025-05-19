document.addEventListener('DOMContentLoaded', function () {
    const openNav = document.getElementById('open-nav');
    const mobileMenu = document.getElementById('mobile-menu');

    if (openNav && mobileMenu) {
        openNav.addEventListener('click', function () {
            if (mobileMenu.style.display === 'none' || mobileMenu.style.display === '') {
                mobileMenu.style.display = 'block';
            } else {
                mobileMenu.style.display = 'none';
            }
        });
    }
});
