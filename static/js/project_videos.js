// Decode only a few visible previews, and always give the hovered project priority.
const previewVideos = [...document.querySelectorAll('[data-preview-video]')];
const videoMotionPreference = matchMedia('(prefers-reduced-motion: reduce)');
const previewMobile = matchMedia('(max-width: 768px)');
const connection = navigator.connection;
const conserveVideoData = () => connection?.saveData || ['slow-2g','2g'].includes(connection?.effectiveType);
const releasePreviewTimers = new WeakMap();
const visiblePreviews = new Set();
let preferredPreview = null, previewFrame = 0;
function updatePreviews() {
    cancelAnimationFrame(previewFrame);
    previewFrame = requestAnimationFrame(() => {
        const available = [...visiblePreviews].filter(video => !video.closest('[hidden]') && !video.dataset.failed);
        const limit = previewMobile.matches ? 2 : 4;
        const distances = new Map(available.map(video => { const r=video.getBoundingClientRect(); return [video,Math.hypot(r.x+r.width/2-innerWidth/2,r.y+r.height/2-innerHeight/2)]; }));
        available.sort((a, b) => {
            return distances.get(a) - distances.get(b);
        });
        const candidates = videoMotionPreference.matches || conserveVideoData() ? [] : available.slice(0, limit);
        if (preferredPreview && available.includes(preferredPreview) && !candidates.includes(preferredPreview)) candidates.unshift(preferredPreview);
        const playing = document.hidden || document.body.classList.contains('delete-mode') ? new Set() : new Set(candidates.slice(0, limit));
        previewVideos.forEach(video => {
            video.dataset.wantsPlay = String(playing.has(video));
            if (!playing.has(video)) {
                video.pause(); video.classList.remove('is-playing');
                if (video.hasAttribute('src') && !releasePreviewTimers.has(video)) releasePreviewTimers.set(video,setTimeout(()=>{
                    releasePreviewTimers.delete(video);
                    if(video.dataset.wantsPlay==='false'){ video.removeAttribute('src'); video.load(); }
                },5000));
                return;
            }
            clearTimeout(releasePreviewTimers.get(video)); releasePreviewTimers.delete(video);
            if (!video.getAttribute('src')) { video.src = video.dataset.src; video.muted = true; }
            video.play().then(() => { if(video.dataset.wantsPlay==='true')video.classList.add('is-playing');else video.pause(); }).catch(() => video.classList.remove('is-playing'));
        });
    });
}
const previewObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => { if (entry.isIntersecting) visiblePreviews.add(entry.target); else visiblePreviews.delete(entry.target); });
    updatePreviews();
}, {threshold: .15});
previewVideos.forEach(video => {
    previewObserver.observe(video);
    const tile = video.closest('[data-project]');
    tile.addEventListener('pointerenter', () => { preferredPreview = video; updatePreviews(); });
    tile.addEventListener('focusin', () => { preferredPreview = video; updatePreviews(); });
    tile.addEventListener('pointerleave', () => { preferredPreview = null; updatePreviews(); });
    video.addEventListener('error', () => { video.dataset.failed = 'true'; video.classList.remove('is-playing'); });
});
document.querySelector('.project-globe')?.addEventListener('layoutchange', updatePreviews);
document.querySelector('.project-globe')?.addEventListener('orbitprojectschange', updatePreviews);
document.querySelector('.delete-mode-toggle')?.addEventListener('click', updatePreviews);
document.addEventListener('visibilitychange', updatePreviews);
videoMotionPreference.addEventListener('change', updatePreviews);
previewMobile.addEventListener('change', updatePreviews);
connection?.addEventListener('change', updatePreviews);
document.querySelectorAll('[data-project-video]').forEach(video => video.addEventListener('error', () => {
    const message = document.createElement('p'); message.className = 'video-error'; message.textContent = 'Video unavailable. Please use the original project link.';
    if (!video.parentElement.querySelector('.video-error')) video.after(message);
}));

const primaryPlayer = document.querySelector('[data-project-video][data-autoplay]');
const primaryPlayButton = document.querySelector('[data-toggle-project-video]');
if (primaryPlayer && primaryPlayButton) {
    function updatePlayButton() { primaryPlayButton.textContent = primaryPlayer.paused ? 'Play video' : 'Pause video'; }
    primaryPlayButton.addEventListener('click', () => {
        if (primaryPlayer.paused) primaryPlayer.play().catch(updatePlayButton); else primaryPlayer.pause();
    });
    primaryPlayer.addEventListener('play', updatePlayButton);
    primaryPlayer.addEventListener('pause', updatePlayButton);
    primaryPlayer.addEventListener('ended', updatePlayButton);
    if (!videoMotionPreference.matches && !conserveVideoData()) { primaryPlayer.muted = true; primaryPlayer.play().catch(updatePlayButton); }
}
