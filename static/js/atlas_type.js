// Fit actual glyph outlines into one frame: font metrics cannot move the title.
document.querySelectorAll('[data-atlas-type]').forEach(async word => {
    const faces = [...word.querySelectorAll('.atlas-type-face')];
    const preference = matchMedia('(prefers-reduced-motion: reduce)');
    let current = 0, timer;
    const styles = faces.map(face => getComputedStyle(face.querySelector('text')));
    const font = style => `${style.fontStyle} ${style.fontWeight} 100px ${style.fontFamily}`;
    if (document.fonts) await Promise.allSettled(styles.map(style => document.fonts.load(font(style), 'ATLAS')));
    const context = document.createElement('canvas').getContext('2d');
    faces.forEach((face, index) => {
        if (context) {
            context.font = font(styles[index]);
            context.fontKerning = 'normal';
            const ink = context.measureText('ATLAS');
            const width = ink.actualBoundingBoxLeft + ink.actualBoundingBoxRight;
            const height = ink.actualBoundingBoxAscent + ink.actualBoundingBoxDescent;
            if (width > 0 && height > 0) {
                face.setAttribute('viewBox', `${-ink.actualBoundingBoxLeft} ${-ink.actualBoundingBoxAscent} ${width} ${height}`);
                return;
            }
        }
        const box = face.querySelector('text').getBBox();
        if (box.width && box.height) face.setAttribute('viewBox', `${box.x} ${box.y} ${box.width} ${box.height}`);
    });
    function show(index) {
        current = index;
        faces.forEach((face, i) => face.classList.toggle('is-active', i === index));
        word.dataset.currentFont = faces[index].dataset.face;
    }
    function updateMotion() {
        clearInterval(timer);
        if (preference.matches) show(0);
        else if (!document.hidden) timer = setInterval(() => show((current + 1) % faces.length), 1900);
    }
    show(0);
    word.dataset.ready = 'true';
    updateMotion();
    preference.addEventListener('change', updateMotion);
    document.addEventListener('visibilitychange', updateMotion);
    window.addEventListener('pagehide', () => clearInterval(timer), {once: true});
});
