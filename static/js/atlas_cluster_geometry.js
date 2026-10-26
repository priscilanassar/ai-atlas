/* Deterministic, non-overlapping regions in one shared coordinate system. */
(function(root) {
    function layout(groups, kind) {
        const regions = groups.map(group => {
            const side = Math.ceil(Math.sqrt(group.count)) + 1, cells = [];
            for(let y=-side;y<=side;y++) for(let x=-side;x<=side;x++) cells.push({x:x*82,y:y*82});
            cells.sort((a,b)=>a.x*a.x+a.y*a.y-b.x*b.x-b.y*b.y || a.y-b.y || a.x-b.x);
            const points=cells.slice(0,group.count);
            const radius=Math.max(100,...points.map(p=>Math.hypot(p.x,p.y)+62));
            return {...group,points,radius,x:0,y:0};
        });
        if(kind==='year') {
            let edge=0;
            regions.forEach(r=>{r.x=edge+r.radius;edge+=r.radius*2+100;});
        } else if(regions.length>1) {
            let ring=0;
            regions.forEach((a,i)=>regions.slice(i+1).forEach((b,j)=>{
                const angle=Math.PI*(j+1)/regions.length;
                ring=Math.max(ring,(a.radius+b.radius+100)/(2*Math.sin(angle)));
            }));
            regions.forEach((r,i)=>{const angle=-Math.PI/2+i*2*Math.PI/regions.length;r.x=Math.cos(angle)*ring;r.y=Math.sin(angle)*ring;});
        }
        const left=Math.min(0,...regions.map(r=>r.x-r.radius-40));
        const top=Math.min(0,...regions.map(r=>r.y-r.radius-80));
        const right=Math.max(160,...regions.map(r=>r.x+r.radius+40));
        const bottom=Math.max(160,...regions.map(r=>r.y+r.radius+40));
        regions.forEach(r=>{r.x-=left;r.y-=top;});
        return {regions,width:right-left,height:bottom-top};
    }
    if(typeof module!=='undefined'&&module.exports) module.exports=layout;
    else root.atlasClusterGeometry=layout;
})(typeof window==='undefined'?this:window);
