document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('navToggle');
    const nav = document.getElementById('mainNav');
    if (toggle && nav) {
        toggle.addEventListener('click', () => nav.classList.toggle('open'));
    }

    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity .4s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Dashboard sidebar toggle (mobile)
    const sidebar = document.getElementById('dashboardSidebar');
    if (sidebar) {
        const overlay = document.getElementById('sidebarOverlay');
        const toggleBtn = document.getElementById('sidebarToggle');
        const closeBtn = document.getElementById('sidebarClose');
        function openSidebar() { sidebar.classList.add('open'); if (overlay) overlay.classList.add('open'); }
        function closeSidebar() { sidebar.classList.remove('open'); if (overlay) overlay.classList.remove('open'); }
        if (toggleBtn) toggleBtn.addEventListener('click', openSidebar);
        if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
        if (overlay) overlay.addEventListener('click', closeSidebar);
        sidebar.querySelectorAll('.sidebar-nav a').forEach(function(link) {
            link.addEventListener('click', closeSidebar);
        });
    }
});
