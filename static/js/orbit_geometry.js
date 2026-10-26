(function (root) {
    function orbitGeometry(count, position, width, height) {
        const capacity = width < 640 ? 3 : width < 1000 ? 5 : 7;
        const slots = Math.min(count, capacity);
        const step = capacity === 3 ? .6 : capacity === 5 ? .45 : .34;
        const centerX = width * .5, centerY = height * .54;
        const radiusX = Math.min(width * .43, 680), radiusY = Math.min(height * .14, 105);
        const size = Math.min(154, width * (capacity === 3 ? .23 : capacity === 5 ? .145 : .1));
        const items = [];
        for (let index = 0; index < count; index++) {
            const delta = count <= capacity ? index - (count - 1) / 2
                : ((index - position + count / 2) % count + count) % count - count / 2;
            if (delta < -slots / 2 || delta >= slots / 2) continue;
            const phase = delta * step;
            const depth = Math.cos(phase);
            items.push({index, x: centerX + Math.sin(phase) * radiusX,
                y: centerY + depth * radiusY, size, scale: .48 + depth * .52,
                tilt: -phase * 18, depth,
                opacity: count <= capacity ? 1 : Math.min(1, Math.max(.12, (slots / 2 - Math.abs(delta)) / .6))});
        }
        return {items, capacity, center: count ? ((Math.round(position) % count) + count) % count : 0,
            centerX, centerY, radiusX, radiusY};
    }
    if (typeof module !== 'undefined' && module.exports) module.exports = orbitGeometry;
    else root.atlasOrbitGeometry = orbitGeometry;
})(typeof window === 'undefined' ? this : window);
