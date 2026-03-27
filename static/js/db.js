function filterTaken(dag) {
  document.querySelectorAll('.day-tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
}