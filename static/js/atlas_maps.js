/* One map; changing the attribute moves the same projects between regions. */
(() => {
    const descriptions = {
        color: 'Dominant cover color, arranged around the spectrum. Select a color to see its projects up close.',
        year: 'Earlier years on the left, later years on the right. Publication year is used when a project date is missing.',
        field: 'Creative fields form distinct regions. Curator labels take priority; otherwise the existing category and title provide a suggested field.',
        type: 'Art, Experiment and Brand Project share one map. Curator labels take priority; otherwise the description suggests a type.',
        format: 'Images, videos and series form separate regions, based on the registered media and curator labels.',
        orbit: 'Drag or scroll to rotate through the projects.',
    };
    const palette={red:'#e44732',orange:'#ec8228',yellow:'#dfb923',green:'#4a8652',blue:'#377fca',purple:'#8a59b5',pink:'#df83a7',brown:'#946247',black:'#222',gray:'#93938d',white:'#fff',multicolor:'#d77872',unassigned:'#a3a38e'};
    const data=JSON.parse(document.getElementById('atlas-map-data')?.textContent||'{}');
    const picker=document.getElementById('atlas-map-kind'),legend=document.querySelector('.map-legend');
    const globe=document.querySelector('.project-globe'),scene=globe.closest('.scene-window');
    const controls=document.querySelector('.map-camera-controls'),output=controls.querySelector('output');
    const reduced=matchMedia('(prefers-reduced-motion: reduce)');
    let geometry,scale=1,x=0,y=0,minScale=1,active='',previousKind='',drag=null,release;
    const pointers=new Map();
    try{picker.value=localStorage.getItem('atlas-map-kind')||'type';}catch(_){picker.value='type';}
    if(!descriptions[picker.value])picker.value='type';
    const isMap=()=>globe.dataset.layout==='map';
    window.updateAtlasMapToolbar=()=>{
        document.getElementById('map-description').textContent=descriptions[picker.value];
        legend.hidden=controls.hidden=picker.value==='orbit';
        try{localStorage.setItem('atlas-map-kind',picker.value);}catch(_){}
    };
    function camera(animate=false){
        globe.classList.toggle('map-camera-animated',animate&&!reduced.matches);
        // Keep some of the map visible even after a long drag.
        x=Math.max(48-geometry.width*scale,Math.min(scene.clientWidth-48,x));
        y=Math.max(48-geometry.height*scale,Math.min(scene.clientHeight-48,y));
        globe.style.setProperty('--map-x',`${x}px`);globe.style.setProperty('--map-y',`${y}px`);
        globe.style.setProperty('--map-scale',scale);
        output.textContent=`${Math.round(scale/minScale*100)}%`;
    }
    function fit(){
        if(!geometry)return;
        minScale=Math.min((scene.clientWidth-32)/geometry.width,(scene.clientHeight-32)/geometry.height,1);
        scale=minScale;x=(scene.clientWidth-geometry.width*scale)/2;y=(scene.clientHeight-geometry.height*scale)/2;
        active='';highlight();camera(true);
    }
    function highlight(){
        legend.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.group===active)));
        globe.querySelectorAll('[data-project]').forEach(t=>t.classList.toggle('map-muted',!!active&&t.dataset.mapGroup!==active));
    }
    function focus(region){
        active=region.label;
        scale=Math.min(2.5,Math.max(minScale,Math.min((scene.clientWidth-40)/(region.radius*2+40),(scene.clientHeight-60)/(region.radius*2+100))));
        x=scene.clientWidth/2-region.x*scale;y=scene.clientHeight/2-(region.y-20)*scale;
        highlight();camera(true);
    }
    function zoom(factor,px=scene.clientWidth/2,py=scene.clientHeight/2){
        const next=Math.min(Math.max(4,minScale*16),Math.max(minScale,scale*factor));
        x=px-(px-x)*next/scale;y=py-(py-y)*next/scale;scale=next;camera();
    }
    window.renderAtlasMap=(_,tiles)=>{
        const kind=picker.value;
        window.updateAtlasMapToolbar();
        const groups=new Map();
        tiles.forEach(tile=>{const label=data[tile.dataset.projectPk]?.[kind]||'Not documented';if(!groups.has(label))groups.set(label,[]);groups.get(label).push(tile);});
        const order=kind==='color'?Object.keys(palette):kind==='type'?['Art','Experiment','Brand Project']:[];
        const entries=[...groups].sort((a,b)=>order.length?(order.indexOf(a[0])<0?999:order.indexOf(a[0]))-(order.indexOf(b[0])<0?999:order.indexOf(b[0])):a[0].localeCompare(b[0],'en',{numeric:true}));
        // Stable ID ordering means switching attributes never assigns random positions.
        entries.forEach(([,works])=>works.sort((a,b)=>Number(a.dataset.projectPk)-Number(b.dataset.projectPk)));
        geometry=window.atlasClusterGeometry(entries.map(([label,works])=>({label,count:works.length})),kind);
        globe.querySelector('.map-backdrop')?.remove();
        const backdrop=document.createElement('div');backdrop.className='map-backdrop';globe.prepend(backdrop);
        legend.replaceChildren();
        geometry.regions.forEach((region,index)=>{
            const name=region.label==='unassigned'?'Not assigned':region.label;
            const area=document.createElement('div');area.className='map-region';area.dataset.group=region.label;area.dataset.projectCount=region.count;
            Object.assign(area.style,{left:`${region.x-region.radius}px`,top:`${region.y-region.radius}px`,width:`${region.radius*2}px`,height:`${region.radius*2}px`});
            area.style.setProperty('--region-color',kind==='color'?palette[region.label]||'#555':'#263b29');
            const label=document.createElement('button');label.type='button';label.className='map-region-label';label.textContent=`${name} · ${region.count}`;label.setAttribute('aria-label',`Focus ${name}, ${region.count} projects`);label.addEventListener('click',()=>focus(region));area.append(label);backdrop.append(area);
            const chip=document.createElement('button');chip.type='button';chip.textContent=`${name} · ${region.count}`;chip.dataset.group=region.label;
            chip.style.setProperty('--region-color',kind==='color'?palette[region.label]||'#555':'#111');chip.addEventListener('click',()=>active===region.label?fit():focus(region));legend.append(chip);
            entries[index][1].forEach((tile,i)=>{
                const point=region.points[i];tile.dataset.mapGroup=region.label;
                tile.style.setProperty('--layout-x',`${region.x+point.x}px`);tile.style.setProperty('--layout-y',`${region.y+point.y}px`);tile.style.setProperty('--layout-size','64px');tile.style.setProperty('--caption-shift','0px');
            });
        });
        if(kind!==previousKind)active='';
        const selected=geometry.regions.find(r=>r.label===active);
        minScale=Math.min((scene.clientWidth-32)/geometry.width,(scene.clientHeight-32)/geometry.height,1);
        selected?focus(selected):fit();previousKind=kind;
        if(!entries.length)document.getElementById('map-description').textContent='No projects match your search.';
    };
    controls.addEventListener('click',e=>{const action=e.target.closest('[data-map-camera]')?.dataset.mapCamera;if(action==='fit')fit();else if(action)zoom(action==='in'?1.5:1/1.5);});
    scene.addEventListener('wheel',e=>{if(!isMap())return;e.preventDefault();const rect=scene.getBoundingClientRect();zoom(Math.exp(-e.deltaY*(e.deltaMode===1?.035:.002)),e.clientX-rect.left,e.clientY-rect.top);},{passive:false});
    scene.addEventListener('pointerdown',e=>{
        if(!isMap()||e.button!==0||e.target.closest('.map-region-label'))return;
        clearTimeout(release);delete globe.dataset.dragging;
        pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});drag={x:e.clientX,y:e.clientY,moved:false};
        if(pointers.size===2){const [a,b]=[...pointers.values()];drag.distance=Math.hypot(a.x-b.x,a.y-b.y);}
    });
    scene.addEventListener('pointermove',e=>{
        if(!isMap()||!pointers.has(e.pointerId)||!drag)return;
        const old=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
        if(pointers.size===2){
            const [a,b]=[...pointers.values()],distance=Math.hypot(a.x-b.x,a.y-b.y),rect=scene.getBoundingClientRect();
            if(drag.distance)zoom(distance/drag.distance,(a.x+b.x)/2-rect.left,(a.y+b.y)/2-rect.top);drag.distance=distance;drag.moved=true;
        }else{
            if(!drag.moved&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<5)return;
            x+=drag.moved?e.clientX-old.x:e.clientX-drag.x;y+=drag.moved?e.clientY-old.y:e.clientY-drag.y;drag.moved=true;camera();
        }
        globe.dataset.dragging='true';scene.classList.add('is-map-dragging');scene.setPointerCapture(e.pointerId);
    });
    function end(e){pointers.delete(e.pointerId);if(pointers.size){drag.distance=0;return;}drag=null;scene.classList.remove('is-map-dragging');release=setTimeout(()=>delete globe.dataset.dragging,100);}
    scene.addEventListener('pointerup',end);scene.addEventListener('pointercancel',end);scene.addEventListener('lostpointercapture',end);
    scene.addEventListener('click',e=>{if(isMap()&&globe.dataset.dragging){e.preventDefault();e.stopPropagation();}},true);
    scene.addEventListener('keydown',e=>{
        if(!isMap()||e.target.closest('button,input,select')||e.ctrlKey||e.altKey||e.metaKey)return;
        if(['+','=','-','0','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){
            e.preventDefault();if(e.key==='0')fit();else if(['+','=','-'].includes(e.key))zoom(e.key==='-'?1/1.5:1.5);else{x+=e.key==='ArrowLeft'?80:e.key==='ArrowRight'?-80:0;y+=e.key==='ArrowUp'?80:e.key==='ArrowDown'?-80:0;camera();}
        }
    });
    globe.addEventListener('focusin',e=>{if(!isMap())return;const tile=e.target.closest('[data-project]');if(tile){const region=geometry?.regions.find(r=>r.label===tile.dataset.mapGroup);if(region)focus(region);const px=parseFloat(tile.style.getPropertyValue('--layout-x')),py=parseFloat(tile.style.getPropertyValue('--layout-y'));scale=Math.max(scale,.85);x=scene.clientWidth/2-px*scale;y=scene.clientHeight/2-py*scale;camera(true);}});
    globe.addEventListener('layoutchange',()=>{pointers.clear();drag=null;scene.classList.remove('is-map-dragging');});
})();
