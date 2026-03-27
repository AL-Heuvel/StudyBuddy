function updateTimer(type, waarde) {
  if (type === 'werk') {
    werkTijd = parseInt(waarde) * 60;
    if (!bezig) {
      huidigeTijd = werkTijd;
      updateDisplay();
    }
  } else {
    pauzetijd = parseInt(waarde) * 60;
  }
}