const assert = require('node:assert/strict');
const layout = require('../static/js/map_geometry.js');
for (const width of [256, 305, 680, 1300]) {
    for (const count of [0, 1, 8, 21, 120, 1200]) {
        for (const kind of ['type', 'color', 'year', 'field', 'format', 'tool']) {
            const group = layout(count, width, kind);
            assert.equal(group.points.length, count, 'The entire group must be placed.');
            group.points.forEach((a, index) => {
                assert.ok(a.size >= 44, 'Cards remain usable on touch screens.');
                assert.ok(a.x-a.size/2 >= 0 && a.x+a.size/2 <= width && a.y+a.size/2 <= group.height);
                group.points.slice(index+1).forEach(b => {
                    assert.ok(Math.abs(a.x-b.x) >= a.size || Math.abs(a.y-b.y) >= a.size,
                        `Overlapping cards: ${width}px, ${count} works, ${kind}`);
                });
            });
        }
    }
}
console.log('All map groups are complete, within bounds and without overlapping cards.');
