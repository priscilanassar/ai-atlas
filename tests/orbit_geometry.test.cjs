const test = require('node:test');
const assert = require('node:assert/strict');
const geometry = require('../static/js/orbit_geometry.js');

test('one turn reveals every project with a bounded number of unique visible cards', () => {
    for (const width of [375, 768, 1264, 1920]) {
        for (const count of [0, 1, 3, 7, 8, 136, 1500]) {
            const seen = new Set();
            for (let position = 0; position < Math.max(1, count); position++) {
                const state = geometry(count, position, width, 1080);
                assert.equal(state.items.length, Math.min(count, state.capacity));
                assert.equal(new Set(state.items.map(item => item.index)).size, state.items.length);
                state.items.forEach(item => seen.add(item.index));
            }
            assert.equal(seen.size, count);
        }
    }
});

test('cards remain separated and inside the viewport while rotating', () => {
    for (const [width, height] of [[320, 740], [375, 740], [768, 1024], [1000, 720], [1264, 712], [1920, 1080]]) {
        for (let position = -3; position <= 3; position += .05) {
            const items = geometry(136, position, width, height).items.sort((a, b) => a.x - b.x);
            for (let i = 0; i < items.length; i++) {
                const item = items[i], half = item.size * item.scale / 2;
                assert.ok(item.x - half >= 0 && item.x + half <= width);
                assert.ok(item.y - half >= 0 && item.y + half <= height - 60);
                if (i) {
                    const previous = items[i - 1];
                    assert.ok(item.x - half >= previous.x + previous.size * previous.scale / 2,
                        `Cards overlap at width ${width}, position ${position}`);
                }
            }
        }
    }
});

test('negative and repeated turns wrap without losing catalogue position', () => {
    for (const position of [-301, -1.25, 0, 7.2, 300]) {
        const a = geometry(150, position, 1264, 712);
        const b = geometry(150, position + 150 * 3, 1264, 712);
        assert.equal(a.center, b.center);
        assert.deepEqual(a.items.map(item => item.index), b.items.map(item => item.index));
        a.items.forEach((item, index) => assert.ok(Math.abs(item.x - b.items[index].x) < .00001));
    }
});
