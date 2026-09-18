/* Shared behaviour for every page. Loaded with `defer` from base.html, so it runs
   before any page script (deferred scripts execute in document order) and can
   publish helpers on window.SP.

   This file runs on all five pages, so every init() must guard on its elements
   being present. Accordions use native <details>/<summary> and need no JS. */

(function () {
    'use strict';

    var THEME_KEY = 'sp-theme';

    /* ---------------------------------------------------------------- theme */

    function currentTheme() {
        return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        var root = document.documentElement;
        root.classList.toggle('dark', theme === 'dark');
        root.style.colorScheme = theme;
        try {
            localStorage.setItem(THEME_KEY, theme);
        } catch (e) {
            /* Storage blocked — the theme still applies for this page view. */
        }
        document.dispatchEvent(new CustomEvent('theme:change', { detail: { theme: theme } }));
    }

    function initTheme() {
        var buttons = document.querySelectorAll('[data-theme-toggle]');
        if (!buttons.length) return;

        function syncLabels() {
            var next = currentTheme() === 'dark' ? 'terang' : 'gelap';
            buttons.forEach(function (btn) {
                btn.setAttribute('aria-label', 'Ganti ke tema ' + next);
                btn.setAttribute('title', 'Ganti ke tema ' + next);
            });
        }

        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
            });
        });

        document.addEventListener('theme:change', syncLabels);
        syncLabels();
    }

    /* ------------------------------------------------------------ mobile nav */

    function initNavSheet() {
        var toggle = document.querySelector('[data-nav-toggle]');
        var sheet = document.getElementById('mobileNavSheet');
        if (!toggle || !sheet) return;

        function setOpen(open) {
            sheet.hidden = !open;
            toggle.setAttribute('aria-expanded', String(open));
        }

        toggle.addEventListener('click', function () {
            setOpen(sheet.hidden);
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && !sheet.hidden) {
                setOpen(false);
                toggle.focus();
            }
        });

        document.addEventListener('click', function (event) {
            if (sheet.hidden) return;
            if (sheet.contains(event.target) || toggle.contains(event.target)) return;
            setOpen(false);
        });

        setOpen(false);
    }

    /* ------------------------------------------------------- password toggle */

    function initPasswordToggles() {
        var toggles = document.querySelectorAll('[data-password-toggle]');
        if (!toggles.length) return;

        toggles.forEach(function (btn) {
            var input = document.getElementById(btn.getAttribute('data-password-toggle'));
            var use = btn.querySelector('use');
            if (!input || !use) return;

            btn.addEventListener('click', function () {
                var show = input.type === 'password';
                input.type = show ? 'text' : 'password';
                use.setAttribute('href', show ? '#icon-eye-off' : '#icon-eye');
                btn.setAttribute('aria-pressed', String(show));
                btn.setAttribute(
                    'aria-label',
                    show ? 'Sembunyikan password' : 'Tampilkan password'
                );
            });
        });
    }

    /* ----------------------------------------------------------- form errors */

    /* Replaces the inline oninvalid/oninput attribute pairs the templates used to
       carry. Each input declares its own message via data-msg; the message renders
       into the sibling .field-error instead of a native browser bubble. */
    function initFormValidation() {
        var forms = document.querySelectorAll('form[data-validate]');
        if (!forms.length) return;

        forms.forEach(function (form) {
            form.setAttribute('novalidate', 'novalidate');

            form.addEventListener('submit', function (event) {
                var firstInvalid = null;
                fields(form).forEach(function (input) {
                    if (!showError(input) && !firstInvalid) firstInvalid = input;
                });
                if (firstInvalid) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    firstInvalid.focus();
                }
            });

            fields(form).forEach(function (input) {
                input.addEventListener('input', function () {
                    if (input.classList.contains('input--invalid')) showError(input);
                });
                input.addEventListener('blur', function () {
                    if (input.value !== '') showError(input);
                });
            });
        });
    }

    function fields(form) {
        return Array.prototype.slice.call(form.querySelectorAll('.input, .select'));
    }

    /* Returns true when the field is valid. */
    function showError(input) {
        var wrap = input.closest('.field');
        var slot = wrap ? wrap.querySelector('[data-error]') : null;
        var ok = input.checkValidity();

        input.classList.toggle('input--invalid', !ok);
        if (!slot) return ok;

        if (ok) {
            slot.textContent = '';
            slot.hidden = true;
        } else {
            slot.textContent = messageFor(input);
            slot.hidden = false;
        }
        return ok;
    }

    function messageFor(input) {
        var custom = input.getAttribute('data-msg');
        if (input.validity.valueMissing && custom) return custom;
        if (input.validity.rangeUnderflow) {
            return 'Nilai minimal ' + input.getAttribute('min') + '.';
        }
        if (input.validity.rangeOverflow) {
            return 'Nilai maksimal ' + input.getAttribute('max') + '.';
        }
        if (input.validity.stepMismatch || input.validity.badInput) {
            return 'Masukkan angka yang valid (gunakan titik untuk desimal).';
        }
        return custom || 'Data ini belum valid.';
    }

    /* ---------------------------------------------------------------- modals */

    var lastFocused = null;

    function openModal(modal) {
        if (!modal) return;
        lastFocused = document.activeElement;
        modal.hidden = false;
        document.body.style.overflow = 'hidden';

        var target = modal.querySelector('[data-autofocus]') || focusables(modal)[0];
        if (target) target.focus();
    }

    function closeModal(modal) {
        if (!modal || modal.hidden) return;
        modal.hidden = true;
        document.body.style.overflow = '';
        if (lastFocused && lastFocused.focus) lastFocused.focus();
        lastFocused = null;
    }

    function focusables(root) {
        return Array.prototype.slice
            .call(root.querySelectorAll(
                'a[href], button:not(:disabled), input:not(:disabled), select, textarea, [tabindex]:not([tabindex="-1"])'
            ))
            .filter(function (el) { return el.offsetParent !== null; });
    }

    function initModals() {
        var modals = document.querySelectorAll('.modal');
        if (!modals.length) return;

        modals.forEach(function (modal) {
            modal.addEventListener('click', function (event) {
                if (event.target === modal) closeModal(modal);
            });
            modal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
                btn.addEventListener('click', function () { closeModal(modal); });
            });
        });

        document.addEventListener('keydown', function (event) {
            var open = document.querySelector('.modal:not([hidden])');
            if (!open) return;

            if (event.key === 'Escape') {
                closeModal(open);
                return;
            }
            if (event.key !== 'Tab') return;

            /* Trap focus inside the open dialog. */
            var items = focusables(open);
            if (!items.length) return;
            var first = items[0];
            var last = items[items.length - 1];

            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });
    }

    /* ------------------------------------------------------------------ boot */

    window.SP = {
        openModal: openModal,
        closeModal: closeModal,
        showError: showError,
        currentTheme: currentTheme
    };

    initTheme();
    initNavSheet();
    initPasswordToggles();
    initFormValidation();
    initModals();
})();
