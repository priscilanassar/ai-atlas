const assert=require('node:assert/strict');
const layout=require('../static/js/atlas_cluster_geometry');
for(const counts of [[],[1],[132,40,11],[80,1,4,12,8,15,26,7,30,2,1,6,12],[1200,5,1]]) {
    for(const kind of ['type','color','field','year','format']) {
        const groups=counts.map((count,i)=>({label:String(i),count}));
        const result=layout(groups,kind);
        assert.deepEqual(result,layout(groups,kind),'Positions must be deterministic.');
        result.regions.forEach((r,i)=>{
            assert.equal(r.points.length,counts[i]);
            assert.ok(r.x-r.radius>=0&&r.y-r.radius>=0&&r.x+r.radius<=result.width&&r.y+r.radius<=result.height);
            result.regions.slice(i+1).forEach(other=>assert.ok(Math.hypot(r.x-other.x,r.y-other.y)>=r.radius+other.radius+99,'Regions overlap.'));
            r.points.forEach((p,j)=>{
                assert.ok(Math.hypot(p.x,p.y)+46<r.radius,'Card escapes its region.');
                r.points.slice(j+1).forEach(q=>assert.ok(Math.abs(p.x-q.x)>=64||Math.abs(p.y-q.y)>=64,'Cards overlap.'));
            });
            if(kind==='year'&&i)assert.ok(r.x>result.regions[i-1].x);
        });
    }
}
console.log('Unified map: complete, deterministic, bounded, non-overlapping regions and cards.');
