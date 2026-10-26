document.querySelectorAll('[data-project]').forEach(tile => tile.addEventListener('click', event => { if (document.querySelector('.project-globe')?.dataset.dragging) event.preventDefault(); }));

document.querySelectorAll('.project-dialog').forEach((dialog) => {
    dialog.addEventListener('click', (event) => {
        const bounds = dialog.getBoundingClientRect();
        if (event.target === dialog && (
            event.clientX < bounds.left || event.clientX > bounds.right ||
            event.clientY < bounds.top || event.clientY > bounds.bottom
        )) dialog.close();
    });
});

const globe = document.querySelector('.project-globe');
if (globe && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const squares = Array.from(globe.querySelectorAll('.globe-tile[data-project]')).map((element) => ({
        element,
        x: parseFloat(element.style.getPropertyValue('--x')),
        y: parseFloat(element.style.getPropertyValue('--y')),
    }));
    let frame = 0;
    globe.addEventListener('pointermove', (event) => {
        if (event.pointerType === 'touch' || globe.dataset.layout !== 'globe') return;
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            if (globe.dataset.layout !== 'globe') return;
            const rect = globe.getBoundingClientRect();
            const x = (event.clientX - rect.left) / rect.width * 100;
            const y = (event.clientY - rect.top) / rect.height * 100;
            squares.forEach((square) => {
                const distance = Math.hypot(square.x - x, square.y - y);
                const strength = Number(globe.dataset.zoom || 1) >= 3 || globe.dataset.dragging ? 0 : Math.max(0, 1 - distance / 10);
                square.element.style.setProperty('--magnify', 1 + strength * strength * 4);
                square.element.style.zIndex = 1 + Math.round(strength * 80);
            });
        });
    });
    globe.addEventListener('pointerleave', () => {
        cancelAnimationFrame(frame);
        squares.forEach(({element}) => {
            element.style.removeProperty('--magnify');
            element.style.removeProperty('z-index');
        });
    });
}

if (globe) {
    const allTiles = Array.from(globe.querySelectorAll('.globe-tile'));
    const seenProjects = new Set();
    const projects = allTiles.filter(tile => { if (!tile.matches('[data-project]')) return false; const key = tile.getAttribute('href'); if (seenProjects.has(key)) return false; seenProjects.add(key); return true; });
    const controls = Array.from(document.querySelectorAll('button[data-view]'));
    const pause = document.querySelector('.orbit-pause');
    const status = document.querySelector('.view-status');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const scene = globe.closest('.scene-window');
    const orbitControls = document.querySelector('.orbit-controls');
    const orbitCounter = document.querySelector('[data-orbit-position]');
    let mode = 'globe';
    let visibleTiles = [];
    let orbitFrame = 0;
    let orbitPosition = 0;
    let previousTime = 0;
    let userPaused = reducedMotion.matches;
    let interacting = false;
    let orbitDrag = null, orbitRelease;
    let lastVisible = '';

    function renderOrbit() {
        const layout = window.atlasOrbitGeometry(projects.length, orbitPosition, globe.clientWidth, globe.clientHeight);
        const indices = new Set(layout.items.map(item => item.index));
        projects.forEach((tile, index) => {
            const hidden = !indices.has(index);
            if (tile.hidden !== hidden) tile.hidden = hidden;
        });
        visibleTiles = layout.items.map(item => projects[item.index]);
        layout.items.forEach(item => {
            const tile = projects[item.index];
            tile.style.setProperty('--layout-x', `${item.x}px`);
            tile.style.setProperty('--layout-y', `${item.y}px`);
            tile.style.setProperty('--layout-size', `${item.size}px`);
            tile.style.setProperty('--orbit-scale', item.scale);
            tile.style.setProperty('--orbit-tilt', `${item.tilt}deg`);
            tile.style.zIndex = Math.round(item.depth * 100);
            tile.style.opacity = item.opacity;
        });
        globe.style.setProperty('--orbit-cx', `${layout.centerX}px`);
        globe.style.setProperty('--orbit-cy', `${layout.centerY}px`);
        globe.style.setProperty('--orbit-rx', `${layout.radiusX}px`);
        globe.style.setProperty('--orbit-ry', `${layout.radiusY}px`);
        const counter = projects.length ? `${layout.center + 1} / ${projects.length}` : '0 / 0';
        if (orbitCounter.textContent !== counter) orbitCounter.textContent = counter;
        globe.dataset.orbitPosition = orbitPosition.toFixed(3);
        globe.dataset.orbitVisible = layout.items.length;
        orbitControls.querySelectorAll('button').forEach(button => { button.disabled = projects.length <= layout.capacity; });
        pause.disabled = projects.length <= layout.capacity;
        const signature = layout.items.map(item => item.index).join(',');
        if (lastVisible !== signature) {
            lastVisible = signature;
            globe.dispatchEvent(new Event('orbitprojectschange'));
        }
    }

    function animate(time) {
        if (mode !== 'orbit') return;
        if (previousTime && !userPaused && !interacting && !orbitDrag && !document.hidden &&
            !document.body.classList.contains('delete-mode') && !document.querySelector('dialog[open]') &&
            projects.length > (globe.clientWidth < 640 ? 3 : globe.clientWidth < 1000 ? 5 : 7)) {
            orbitPosition = (orbitPosition + Math.min(time - previousTime, 40) * .00015) % projects.length;
            renderOrbit();
        }
        previousTime = time;
        orbitFrame = requestAnimationFrame(animate);
    }

    function arrange() {
        if (mode === 'globe') return;
        if (mode === 'orbit') { renderOrbit(); return; }
        if (mode === 'map') { window.renderAtlasMap(globe, projects); return; }
        const width = globe.clientWidth;
        const columns = width < 500 ? 2 : width < 900 ? 4 : 6;
        const gap = width < 500 ? 8 : 16;
        const size = (width - (columns - 1) * gap) / columns;
        const rows = Math.ceil(visibleTiles.length / columns);
        const captionHeight = width < 500 ? 108 : 82;
        globe.style.setProperty('--scene-height', `${rows * (size + gap + captionHeight)}px`);
        visibleTiles.forEach((tile, index) => {
            tile.style.setProperty('--layout-x', `${index % columns * (size + gap) + size / 2}px`);
            tile.style.setProperty('--layout-y', `${Math.floor(index / columns) * (size + gap + captionHeight) + size / 2}px`);
            tile.style.setProperty('--layout-size', `${size}px`);
        });
    }

    function chooseView(next) {
        if (!['globe', 'mosaic', 'orbit', 'map'].includes(next)) return;
        const mapPicker = document.getElementById('atlas-map-kind');
        if (next === 'orbit') mapPicker.value = 'orbit';
        mode = next === 'map' && mapPicker.value === 'orbit' ? 'orbit' : next;
        cancelAnimationFrame(orbitFrame);
        previousTime = 0;
        globe.dataset.layout = mode;
        document.body.dataset.view = mode;
        globe.dispatchEvent(new Event('layoutchange'));
        allTiles.forEach(tile => {
            tile.style.removeProperty('--magnify');
            tile.style.removeProperty('--depth');
            tile.style.removeProperty('z-index');
            tile.style.removeProperty('opacity');
        });
        visibleTiles = mode === 'globe' ? allTiles : projects;
        const visibleSet = new Set(visibleTiles);
        allTiles.forEach(tile => { tile.hidden = !visibleSet.has(tile); });
        controls.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === mode || (button.dataset.view === 'map' && mode === 'orbit'))));
        pause.hidden = mode !== 'orbit';
        orbitControls.hidden = mode !== 'orbit';
        document.querySelector('.map-toolbar').hidden = !['map','orbit'].includes(mode);
        if (['map','orbit'].includes(mode)) window.updateAtlasMapToolbar();
        scene.setAttribute('aria-label', mode === 'orbit'
            ? 'Explore the orbit. Drag or scroll to rotate, or use left and right arrow keys to discover more projects.'
            : mode === 'map' ? 'Interactive category map. Use plus and minus to zoom, arrow keys to move, zero to fit, or select a category to focus.'
            : mode === 'mosaic' ? 'Explore projects in the mosaic.'
            : 'Explore the globe. Use plus and minus to zoom, arrow keys to move, and zero to reset.');
        updateStatus();
        arrange();
        if (mode === 'orbit') orbitFrame = requestAnimationFrame(animate);
        try { localStorage.setItem('atlas-layout', mode); } catch (_) { /* Storage may be unavailable. */ }
    }

    const mobileLayout = matchMedia('(max-width: 768px)');
    function updateStatus() {
        status.textContent = mobileLayout.matches ? {
            globe: 'Pinch or use + to zoom · Drag when zoomed · Tap a project.',
            mosaic: 'Explore the grid · Tap a project for details.',
            orbit: 'Swipe to rotate · Tap a project for details.',
            map: 'Choose a category · Pinch to zoom · Drag to explore.',
        }[mode] : {
            globe: 'Scroll to zoom · Drag to explore · Select a project for details.',
            mosaic: 'Mosaic / All projects in a grid. Select a project to explore.',
            orbit: 'Drag or scroll to rotate · New projects appear as you turn · Hover to pause.',
            map: 'One map, different connections · Scroll to zoom · Drag to explore · Click a category to focus.',
        }[mode];
    }
    mobileLayout.addEventListener('change', updateStatus);

    function updatePause() {
        pause.textContent = userPaused ? 'Resume motion' : 'Pause motion';
        pause.setAttribute('aria-pressed', String(userPaused));
    }
    pause.addEventListener('click', () => { userPaused = !userPaused; updatePause(); });
    function rotateOrbit(amount) {
        if (!projects.length) return;
        orbitPosition = ((orbitPosition + amount) % projects.length + projects.length) % projects.length;
        renderOrbit();
    }
    orbitControls.querySelectorAll('[data-orbit-step]').forEach(button => button.addEventListener('click', () => rotateOrbit(Number(button.dataset.orbitStep))));
    scene.addEventListener('wheel', event => {
        if (mode !== 'orbit' || !projects.length) return;
        event.preventDefault();
        const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
        rotateOrbit(delta * (event.deltaMode === 1 ? .04 : event.deltaMode === 2 ? 1 : .003));
    }, {passive: false});
    scene.addEventListener('pointerdown', event => {
        if (mode !== 'orbit' || event.button !== 0) return;
        orbitDrag = {id: event.pointerId, x: event.clientX, position: orbitPosition, moved: false};
    });
    scene.addEventListener('pointermove', event => {
        if (!orbitDrag || orbitDrag.id !== event.pointerId) return;
        const distance = event.clientX - orbitDrag.x;
        if (Math.abs(distance) < 5 && !orbitDrag.moved) return;
        orbitDrag.moved = true;
        globe.dataset.dragging = 'true';
        scene.classList.add('is-orbit-dragging');
        scene.setPointerCapture(event.pointerId);
        orbitPosition = orbitDrag.position - distance / Math.max(70, scene.clientWidth * .16);
        renderOrbit();
    });
    function endOrbitDrag(event) {
        if (!orbitDrag || orbitDrag.id !== event.pointerId) return;
        orbitDrag = null;
        scene.classList.remove('is-orbit-dragging');
        clearTimeout(orbitRelease);
        orbitRelease = setTimeout(() => { delete globe.dataset.dragging; }, 80);
    }
    scene.addEventListener('pointerup', endOrbitDrag);
    scene.addEventListener('pointercancel', endOrbitDrag);
    scene.addEventListener('lostpointercapture', endOrbitDrag);
    scene.addEventListener('keydown', event => {
        if (mode !== 'orbit' || event.ctrlKey || event.altKey || event.metaKey) return;
        if (['ArrowLeft', 'ArrowRight', 'Home', ' '].includes(event.key)) {
            if (event.target.closest('[data-project]') && event.key === ' ') return;
            event.preventDefault();
            if (event.key === ' ') { userPaused = !userPaused; updatePause(); }
            else if (event.key === 'Home') { orbitPosition = 0; renderOrbit(); }
            else rotateOrbit(event.key === 'ArrowRight' ? 1 : -1);
        }
    });
    controls.forEach(button => button.addEventListener('click', () => chooseView(button.dataset.view)));
    document.getElementById('atlas-map-kind').addEventListener('change', () => chooseView('map'));
    globe.addEventListener('pointerover', event => { interacting = Boolean(event.target.closest('.globe-tile')); });
    globe.addEventListener('pointerout', event => { if (!event.relatedTarget?.closest?.('.globe-tile')) interacting = false; });
    globe.addEventListener('pointerleave', () => { interacting = false; });
    globe.addEventListener('focusin', () => { interacting = true; });
    globe.addEventListener('focusout', () => { interacting = false; });
    reducedMotion.addEventListener('change', event => { userPaused = event.matches; updatePause(); });
    new ResizeObserver(arrange).observe(globe);
    updatePause();
    let saved = 'globe';
    try { saved = localStorage.getItem('atlas-layout') || 'globe'; } catch (_) { /* Use the default layout. */ }
    chooseView(['globe', 'mosaic', 'orbit', 'map'].includes(saved) ? saved : 'globe');
}

const nav = document.querySelector('.navbar');
new ResizeObserver(() => document.documentElement.style.setProperty('--nav-height', `${nav.getBoundingClientRect().height}px`)).observe(nav);

if (globe) {
    const scene = globe.closest('.scene-window');
    const controls = document.querySelector('.zoom-controls');
    const output = document.querySelector('#zoom-level');
    const navigation = document.querySelector('.globe-navigation');
    const cameraKey = `atlas-camera:${location.pathname}${location.search}`;
    let projectIndex = -1;
    const slider = document.querySelector('#zoom-range');
    const pointers = new Map();
    let zoom = 1, panX = 0, panY = 0, gesture = null, releaseTimer;
    function renderZoom() {
        const limit = globe.clientWidth * (zoom - .5) / 2;
        panX = Math.max(-limit, Math.min(limit, panX));
        panY = Math.max(-limit, Math.min(limit, panY));
        globe.style.setProperty('--scene-zoom', zoom);
        globe.style.setProperty('--pan-x', `${panX}px`);
        globe.style.setProperty('--pan-y', `${panY}px`);
        scene.classList.toggle('is-zoomed', zoom > 1);
        scene.classList.toggle('is-close-up', zoom >= 3);
        globe.dataset.zoom = zoom;
        output.value = `${Math.round(zoom * 100)}%`;
        try { sessionStorage.setItem(cameraKey, JSON.stringify({zoom, x: panX / globe.clientWidth, y: panY / globe.clientWidth})); } catch (_) { /* Optional camera memory. */ }
        slider.value = Math.log(zoom) / Math.log(40) * 100;
        document.querySelector('[data-zoom="out"]').disabled = zoom <= 1;
        document.querySelector('[data-zoom="in"]').disabled = zoom >= 40;
    }
    function setZoom(value, x, y) {
        const rect = scene.getBoundingClientRect();
        const anchorX = (x ?? rect.left + rect.width / 2) - rect.left - rect.width / 2;
        const anchorY = (y ?? rect.top + rect.height / 2) - rect.top - rect.height / 2;
        const next = Math.max(1, Math.min(40, value));
        panX = anchorX - (anchorX - panX) * next / zoom;
        panY = anchorY - (anchorY - panY) * next / zoom;
        zoom = next;
        renderZoom();
    }
    function reset() { zoom = 1; panX = panY = 0; renderZoom(); }
    document.querySelectorAll('[data-zoom]').forEach(button => button.addEventListener('click', () => {
        if (button.dataset.zoom === 'reset') reset();
        else setZoom(button.dataset.zoom === 'explore' ? 4 : zoom * (button.dataset.zoom === 'in' ? 1.4 : 1 / 1.4));
    }));
    const projectTiles = [...globe.querySelectorAll('[data-project]')];
    document.querySelectorAll('[data-pan]').forEach(button => button.addEventListener('click', () => {
        const step = Math.min(scene.clientWidth, scene.clientHeight) * .4;
        panX += button.dataset.pan === 'left' ? step : button.dataset.pan === 'right' ? -step : 0;
        panY += button.dataset.pan === 'up' ? step : button.dataset.pan === 'down' ? -step : 0;
        renderZoom();
    }));
    document.querySelectorAll('[data-jump]').forEach(button => button.addEventListener('click', () => {
        if (!projectTiles.length) return;
        if (projectIndex < 0 && button.dataset.jump === 'previous') projectIndex = 0;
        projectIndex = (projectIndex + (button.dataset.jump === 'next' ? 1 : -1) + projectTiles.length) % projectTiles.length;
        const tile = projectTiles[projectIndex];
        zoom = Math.max(zoom, 8);
        panX = -((parseFloat(tile.style.getPropertyValue('--x')) / 100) - .5) * globe.clientWidth * zoom;
        panY = -((parseFloat(tile.style.getPropertyValue('--y')) / 100) - .5) * globe.clientWidth * zoom;
        renderZoom();
        tile.focus({preventScroll: true});
    }));
    slider.addEventListener('input', () => setZoom(Math.pow(40, Number(slider.value) / 100)));
    scene.addEventListener('wheel', event => {
        if (globe.dataset.layout !== 'globe') return;
        event.preventDefault();
        const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? scene.clientHeight : 1);
        setZoom(zoom * Math.exp(-delta * .002), event.clientX, event.clientY);
    }, {passive: false});
    function startGesture() {
        const points = [...pointers.values()];
        if (!points.length) { gesture = null; return; }
        const center = points.length > 1 ? {x: (points[0].x + points[1].x) / 2, y: (points[0].y + points[1].y) / 2} : points[0];
        gesture = { ...center, px: panX, py: panY, zoom, distance: points.length > 1 ? Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y) : 0 };
    }
    scene.addEventListener('pointerdown', event => {
        if (globe.dataset.layout !== 'globe' || event.button !== 0) return;
        pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
        startGesture();
    });
    scene.addEventListener('pointermove', event => {
        if (!pointers.has(event.pointerId) || !gesture) return;
        pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
        const points = [...pointers.values()];
        const center = points.length > 1 ? {x: (points[0].x + points[1].x) / 2, y: (points[0].y + points[1].y) / 2} : points[0];
        // A single finger can scroll the mobile page while the globe is fitted.
        if (event.pointerType === 'touch' && points.length === 1 && zoom === 1 && matchMedia('(max-width: 768px)').matches) return;
        const dx = center.x - gesture.x, dy = center.y - gesture.y;
        if (Math.hypot(dx, dy) > 5 || points.length > 1) {
            scene.setPointerCapture(event.pointerId);
            globe.dataset.dragging = 'true';
            scene.classList.add('is-dragging');
            if (points.length > 1 && gesture.distance > 0) {
                panX = gesture.px; panY = gesture.py; zoom = gesture.zoom;
                setZoom(gesture.zoom * Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y) / gesture.distance, gesture.x, gesture.y);
                panX += dx; panY += dy;
            } else { panX = gesture.px + dx; panY = gesture.py + dy; }
            renderZoom();
        }
    });
    function endGesture(event) {
        pointers.delete(event.pointerId);
        startGesture();
        if (pointers.size) return;
        scene.classList.remove('is-dragging');
        clearTimeout(releaseTimer);
        releaseTimer = setTimeout(() => { delete globe.dataset.dragging; }, 80);
    }
    scene.addEventListener('pointerup', endGesture);
    scene.addEventListener('pointercancel', endGesture);
    scene.addEventListener('keydown', event => {
        if (globe.dataset.layout !== 'globe' || event.ctrlKey || event.metaKey || event.altKey) return;
        if (['+', '=', '-', '0', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
            event.preventDefault();
            if (event.key === '0') reset();
            else if (['+', '=', '-'].includes(event.key)) setZoom(zoom * (event.key === '-' ? 1 / 1.4 : 1.4));
            else {
                panX += event.key === 'ArrowLeft' ? (event.shiftKey ? 400 : 100) : event.key === 'ArrowRight' ? (event.shiftKey ? -400 : -100) : 0;
                panY += event.key === 'ArrowUp' ? (event.shiftKey ? 400 : 100) : event.key === 'ArrowDown' ? (event.shiftKey ? -400 : -100) : 0;
                renderZoom();
            }
        }
    });
    globe.addEventListener('layoutchange', () => {
        controls.hidden = globe.dataset.layout !== 'globe';
        navigation.hidden = controls.hidden;
        reset();
    });
    controls.hidden = globe.dataset.layout !== 'globe';
        navigation.hidden = controls.hidden;
    window.addEventListener('resize', renderZoom);
    try {
        const camera = JSON.parse(sessionStorage.getItem(cameraKey));
        if (camera && globe.dataset.layout === 'globe' && [camera.zoom, camera.x, camera.y].every(Number.isFinite)) {
            zoom = Math.max(1, Math.min(40, camera.zoom)); panX = camera.x * globe.clientWidth; panY = camera.y * globe.clientWidth;
        }
    } catch (_) { /* Start with the full view if camera storage is unavailable. */ }
    renderZoom();
}

document.querySelectorAll('[data-new-collection]').forEach(button => {
    button.addEventListener('click', () => {
        const projectId = button.dataset.newCollection || '';
        document.querySelectorAll('dialog[open]').forEach(dialog => dialog.close());
        document.querySelector('#new-collection-project').value = projectId;
        document.querySelector('#new-collection').showModal();
    });
});
