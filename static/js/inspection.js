const input = document.querySelector('#image-input');
const dropzone = document.querySelector('#dropzone');
const preview = document.querySelector('#preview');
const previewImage = document.querySelector('#preview-image');
const fileName = document.querySelector('#file-name');
const fileSize = document.querySelector('#file-size');
const analyze = document.querySelector('#analyze-button');
const message = document.querySelector('#analysis-message');
let selectedFile = null;

function selectFile(file) {
  if (!file) return;
  const allowed = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type) || file.size > 10 * 1024 * 1024) {
    message.textContent = 'Choose a JPG, PNG, or WEBP image under 10 MB.';
    return;
  }
  selectedFile = file;
  previewImage.src = URL.createObjectURL(file);
  fileName.textContent = file.name;
  fileSize.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
  preview.classList.remove('hidden');
  dropzone.classList.add('hidden');
  analyze.disabled = false;
  message.textContent = '';
}
input?.addEventListener('change', () => selectFile(input.files[0]));
['dragenter', 'dragover'].forEach(event => dropzone?.addEventListener(event, e => { e.preventDefault(); dropzone.classList.add('active'); }));
['dragleave', 'drop'].forEach(event => dropzone?.addEventListener(event, e => { e.preventDefault(); dropzone.classList.remove('active'); }));
dropzone?.addEventListener('drop', e => selectFile(e.dataTransfer.files[0]));
document.querySelector('#remove-file')?.addEventListener('click', () => { selectedFile = null; input.value = ''; preview.classList.add('hidden'); dropzone.classList.remove('hidden'); analyze.disabled = true; });
document.querySelector('#inspection-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  if (!selectedFile) return;
  analyze.disabled = true;
  analyze.textContent = 'Analyzing image...';
  message.textContent = 'The model is reviewing the image. Please wait.';
  const formData = new FormData();
  formData.append('image', selectedFile);
  try {
    const response = await fetch('/api/inspection/analyze', { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('[name=csrf_token]').value }, body: formData });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error(result.error || 'Unable to process the image.');
    window.location.href = `/inspection/${result.inspection_id}`;
  } catch (error) {
    analyze.disabled = false;
    analyze.textContent = 'Analyze image ↗';
    message.textContent = error.message;
  }
});
