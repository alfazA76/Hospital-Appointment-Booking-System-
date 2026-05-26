/* ═══════════════════════════════════════════════════════════════════════════
   Hospital Appointment Booking System — Client-Side JavaScript
   Theme Switcher, Sidebar Toggle, Flash Messages, Slot Selection
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Theme Switcher ──────────────────────────────────────────────────
    const themeToggle = document.getElementById('themeToggle');
    const htmlEl = document.documentElement;

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlEl.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const current = htmlEl.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            htmlEl.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            updateThemeIcon(next);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
    }

    // ── Sidebar Toggle (Mobile) ─────────────────────────────────────────
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            if (sidebarOverlay) sidebarOverlay.classList.toggle('show');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
        });
    }

    // ── Flash Message Auto-Dismiss ──────────────────────────────────────
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function (msg) {
        // Click to dismiss
        msg.addEventListener('click', function () {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100px)';
            setTimeout(function () { msg.remove(); }, 300);
        });

        // Auto-dismiss after 5 seconds
        setTimeout(function () {
            if (msg.parentNode) {
                msg.style.opacity = '0';
                msg.style.transform = 'translateX(100px)';
                setTimeout(function () { msg.remove(); }, 300);
            }
        }, 5000);
    });

    // ── Time Slot Selection ─────────────────────────────────────────────
    const slotButtons = document.querySelectorAll('.slot-btn:not(.booked)');
    const selectedSlotInput = document.getElementById('selectedSlot');

    slotButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            // Deselect all
            slotButtons.forEach(function (b) { b.classList.remove('selected'); });
            // Select this one
            btn.classList.add('selected');
            if (selectedSlotInput) {
                selectedSlotInput.value = btn.getAttribute('data-time');
            }
        });
    });

    // ── Dynamic Slot Loading (Appointment Booking) ──────────────────────
    const dateInput = document.getElementById('appointmentDate');
    const slotContainer = document.getElementById('slotContainer');
    const doctorIdEl = document.getElementById('doctorId');

    if (dateInput && slotContainer && doctorIdEl) {
        dateInput.addEventListener('change', function () {
            const selectedDate = this.value;
            const doctorId = doctorIdEl.value;

            if (!selectedDate) return;

            slotContainer.innerHTML = '<div class="text-center py-3"><i class="bi bi-arrow-repeat spinning"></i> Loading available slots...</div>';

            fetch(`/patient/slots/${doctorId}/${selectedDate}`)
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (data.error) {
                        slotContainer.innerHTML = '<p class="text-danger">' + data.error + '</p>';
                        return;
                    }

                    if (data.slots.length === 0) {
                        slotContainer.innerHTML = '<div class="empty-state py-4"><i class="bi bi-calendar-x" style="font-size:32px;display:block;margin-bottom:8px;opacity:0.5"></i><p>No available slots for ' + data.day + '. Try another date.</p></div>';
                        return;
                    }

                    let html = '<label class="form-label-custom">Available Slots for ' + data.day + '</label>';
                    html += '<div class="slot-grid">';
                    data.slots.forEach(function (slot) {
                        html += '<button type="button" class="slot-btn" data-time="' + slot + '" onclick="selectSlot(this)">' + slot + '</button>';
                    });
                    html += '</div>';
                    html += '<input type="hidden" name="appointment_time" id="selectedSlot" value="">';
                    slotContainer.innerHTML = html;
                })
                .catch(function (err) {
                    slotContainer.innerHTML = '<p class="text-danger">Failed to load slots. Please try again.</p>';
                    console.error('Slot loading error:', err);
                });
        });
    }

    // ── Search Filter (Doctor List) ─────────────────────────────────────
    const searchInput = document.getElementById('doctorSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const term = this.value.toLowerCase();
            const cards = document.querySelectorAll('.doctor-card-wrapper');
            cards.forEach(function (card) {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }

    // ── Confirmation Dialogs ────────────────────────────────────────────
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const message = btn.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // ── Active Nav Link ─────────────────────────────────────────────────
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    navLinks.forEach(function (link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href)) {
            link.classList.add('active');
        }
    });

});

// ── Global Slot Selection Function ──────────────────────────────────────────
function selectSlot(btn) {
    document.querySelectorAll('.slot-btn').forEach(function (b) {
        b.classList.remove('selected');
    });
    btn.classList.add('selected');
    var input = document.getElementById('selectedSlot');
    if (input) {
        input.value = btn.getAttribute('data-time');
    }
}
