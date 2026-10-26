(function(root) {
    // A group expands as a whole. No pagination or arbitrary per-panel limit.
    function groupGeometry(count, width, kind) {
        const size = width < 500 ? 48 : 76;
        const step = size + (width < 500 ? 10 : 20);
        const rowStep = step + (kind === 'format' ? 18 : 0);
        const cols = Math.max(1, Math.floor((width - 32) / step));
        const shaped = ['color','type','field'].includes(kind);
        function capacities(rows) {
            return Array.from({length:rows},(_,i)=>{
                const t = rows === 1 ? 0 : (i + .5)/rows * 2 - 1;
                const factor = kind === 'type' ? 1-Math.abs(t) : kind === 'field' ? .65+.35*Math.cos(t*Math.PI)**2 : Math.sqrt(1-t*t);
                return shaped ? Math.max(1,Math.round(cols*factor)) : cols;
            });
        }
        let rows = Math.max(1,Math.ceil(count/cols)), capacity = capacities(rows);
        while(capacity.reduce((a,b)=>a+b,0)<count) capacity=capacities(++rows);
        // Distribute any unused slots symmetrically instead of leaving a long empty tail.
        const used=capacity.map(n=>Math.floor(n*count/capacity.reduce((a,b)=>a+b,0)));
        let remaining=count-used.reduce((a,b)=>a+b,0);
        const order=capacity.map((_,i)=>i).sort((a,b)=>Math.abs(a-(rows-1)/2)-Math.abs(b-(rows-1)/2));
        while(remaining) for(const i of order) if(remaining && used[i]<capacity[i]) {used[i]++;remaining--;}
        const points=[];
        used.forEach((n,row)=>{
            for(let column=0;column<n;column++) {
                const index = ['year','format','tool'].includes(kind) && row%2 ? n-1-column : column;
                const wave = kind==='format' ? Math.sin(index*1.5)*9 : 0;
                points.push({x:width/2+(index-(n-1)/2)*step,y:100+row*rowStep+wave,size});
            }
        });
        return {points,height:Math.max(210,160+(rows-1)*rowStep+size/2),size};
    }
    if(typeof module!=='undefined'&&module.exports) module.exports=groupGeometry;
    else root.atlasGroupGeometry=groupGeometry;
})(typeof window==='undefined'?this:window);
