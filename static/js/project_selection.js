const selectionToggle = document.querySelector('.delete-mode-toggle');
const selectionBar = document.querySelector('.bulk-selection-bar');
const selectionTiles = [...document.querySelectorAll('[data-delete-url]')];
const selectedProjects = new Set();
let selectingProjects = false;

function updateAtlasSelection() {
    if (!selectionBar) return;
    selectionBar.hidden = !selectingProjects;
    selectionBar.querySelector('[data-selected-count]').textContent = `${selectedProjects.size} selected`;
    selectionBar.querySelector('[data-review-selection]').disabled = !selectedProjects.size;
    const inputs = selectionBar.querySelector('[data-selected-inputs]');
    inputs.replaceChildren(...[...selectedProjects].map(id => {
        const input = document.createElement('input'); input.type = 'hidden'; input.name = 'project_ids'; input.value = id; return input;
    }));
    selectionTiles.forEach(tile => {
        const selected = selectedProjects.has(tile.dataset.projectPk);
        tile.classList.toggle('is-selected', selected);
        if (!tile.dataset.detailLabel) tile.dataset.detailLabel = tile.getAttribute('aria-label');
        tile.setAttribute('aria-label', selectingProjects ? `${selected ? 'Deselect' : 'Select'} ${tile.querySelector('.tile-title').textContent} for deletion` : tile.dataset.detailLabel);
    });
    if (selectingProjects) document.querySelector('.view-status').textContent = 'Select projects, then choose Review deletion. Nothing is deleted until you confirm.';
}
if (selectionToggle) {
    selectionToggle.addEventListener('click', () => {
        selectingProjects = !selectingProjects;
        document.body.classList.toggle('delete-mode', selectingProjects);
        selectionToggle.setAttribute('aria-pressed', String(selectingProjects));
        selectionToggle.textContent = selectingProjects ? 'Exit selection' : 'Delete projects';
        if (!selectingProjects) {
            selectedProjects.clear();
            document.querySelector('.view-status').textContent = 'Select a project to explore. Use the view controls to change perspective.';
        }
        updateAtlasSelection();
    });
    selectionTiles.forEach(tile => {
        tile.addEventListener('click', event => {
            if (!selectingProjects) return;
            event.preventDefault();
            if (document.querySelector('.project-globe').dataset.dragging) return;
            const id = tile.dataset.projectPk;
            if (selectedProjects.has(id)) selectedProjects.delete(id); else selectedProjects.add(id);
            updateAtlasSelection();
        });
        tile.addEventListener('keydown', event => {
            if (selectingProjects && event.key === ' ') { event.preventDefault(); tile.click(); }
        });
    });
    selectionBar.querySelector('[data-select-shown]').addEventListener('click', () => {
        selectionTiles.filter(tile => !tile.hidden).forEach(tile => selectedProjects.add(tile.dataset.projectPk)); updateAtlasSelection();
    });
    selectionBar.querySelector('[data-clear-selection]').addEventListener('click', () => { selectedProjects.clear(); updateAtlasSelection(); });
    document.querySelector('.project-globe').addEventListener('layoutchange', () => queueMicrotask(updateAtlasSelection));
    if (new URLSearchParams(location.search).get('select') === '1') selectionToggle.click();
}

const projectPicker = document.querySelector('#project-bulk-picker');
if (projectPicker) {
    const form = projectPicker.querySelector('[data-project-picker-form]');
    const rows = [...projectPicker.querySelectorAll('.project-picker-item')];
    const boxes = rows.map(row => row.querySelector('input[type="checkbox"]'));
    function updatePicker() {
        const count = boxes.filter(box => box.checked).length;
        form.querySelector('[data-selected-count]').textContent = `${count} selected`;
        form.querySelector('[data-review-selection]').disabled = !count;
    }
    document.querySelector('[data-open-project-picker]').addEventListener('click', () => projectPicker.showModal());
    projectPicker.querySelector('[data-selection-search]').addEventListener('input', event => {
        const query = event.target.value.trim().toLocaleLowerCase();
        rows.forEach(row => { row.hidden = !row.textContent.toLocaleLowerCase().includes(query); });
    });
    form.addEventListener('change', updatePicker);
    form.querySelector('[data-select-shown]').addEventListener('click', () => { rows.filter(row => !row.hidden).forEach(row => { row.querySelector('input').checked = true; }); updatePicker(); });
    form.querySelector('[data-clear-selection]').addEventListener('click', () => { boxes.forEach(box => { box.checked = false; }); updatePicker(); });
}
