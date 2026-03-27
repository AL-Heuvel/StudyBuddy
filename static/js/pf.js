function previewFoto(input) {
  const preview = document.getElementById('fotoPreview');
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(input. Files[0]);
  }
}