function kiesOptie(type, btn, waarde) {
  const groep = btn.parentElement;
  groep.querySelectorAll('.keuze-btn').forEach(b => b.classList.remove('actief'));
  btn.classList.add('actief');
  document.getElementById(type + 'Input').value = waarde;
}