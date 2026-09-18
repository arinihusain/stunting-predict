/* Applies the stored theme before first paint. Included inline, synchronously, as the
   first executing element in <head> — an external file could paint the wrong theme first.
   Storage values: 'light' | 'dark' | absent (absent = follow the OS preference). */
(function () {
    try {
        var saved = localStorage.getItem('sp-theme');
        var dark = saved
            ? saved === 'dark'
            : window.matchMedia('(prefers-color-scheme: dark)').matches;
        var root = document.documentElement;
        root.classList.toggle('dark', dark);
        root.style.colorScheme = dark ? 'dark' : 'light';
    } catch (e) {
        /* Storage blocked (private mode, hardened browser) — stay on the light theme. */
    }
})();
