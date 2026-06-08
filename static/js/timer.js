// ── INSTELLINGEN (kan overschreven worden door server) ──
let werkTijd = (typeof USER_WERK_MIN !== 'undefined' ? USER_WERK_MIN * 60 : 25 * 60);
let pauzetijd = (typeof USER_PAUZE_MIN !== 'undefined' ? USER_PAUZE_MIN * 60 : 5 * 60);
let huidigeTijd = werkTijd;
let bezig = false;
let interval = null;
let isPauze = false;
 
// ── TIMER STARTEN / STOPPEN ──
function toggleTimer() {
  if (bezig) {
    stopTimer();
  } else {
    startTimer();
  }
}
 
function startTimer() {
  bezig = true;
  const btn = document.getElementById('timerBtn');
  if (btn) btn.textContent = '⏸';
  interval = setInterval(() => {
    huidigeTijd--;
    updateDisplay();
    if (huidigeTijd <= 0) {
      clearInterval(interval);
      bezig = false;
      speelGeluid();
      wisselModus();
    }
  }, 1000);
}
 
function stopTimer() {
  bezig = false;
  clearInterval(interval);
  const btn = document.getElementById('timerBtn');
  if (btn) btn.textContent = '▶';
}
 
function resetTimer() {
  clearInterval(interval);
  bezig = false;
  isPauze = false;
  huidigeTijd = werkTijd;
  updateDisplay();
  const btn = document.getElementById('timerBtn');
  if (btn) btn.textContent = '▶';
  const balk = document.getElementById('timerBalk');
  if (balk) balk.style.background = 'white';
}
 
// ── DISPLAY BIJWERKEN ──
function updateDisplay() {
  const min = Math.floor(huidigeTijd / 60).toString().padStart(2, '0');
  const sec = (huidigeTijd % 60).toString().padStart(2, '0');
  const display = document.getElementById('timerDisplay');
  if (display) display.textContent = `${min}:${sec}`;
}
 
// ── WISSELEN TUSSEN WERK EN PAUZE ──
function wisselModus() {
  const balk = document.getElementById('timerBalk');
  if (!isPauze) {
    // Werk is afgelopen -> ga naar pauze
    isPauze = true;
    huidigeTijd = pauzetijd;
    if (balk) balk.style.background = '#d4edda';
    const minuten = Math.round(pauzetijd / 60);
    melding(`Goed gedaan! Tijd voor ${minuten} minuten pauze.`);
  } else {
    // Pauze is afgelopen -> ga naar werk
    isPauze = false;
    huidigeTijd = werkTijd;
    if (balk) balk.style.background = 'white';
    const minuten = Math.round(werkTijd / 60);
    melding(`Pauze voorbij! Tijd om ${minuten} minuten te focussen.`);
  }
  updateDisplay();
  startTimer();
}
 
// ── GELUIDSSIGNAAL ──
function speelGeluid() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    osc.start();
    osc.stop(ctx.currentTime + 0.4);
    // Sluit de context netjes af na afspelen
    osc.onended = () => ctx.close();
  } catch (e) {
    console.log('Geluid kon niet worden afgespeeld:', e);
  }
}
 
// ── MELDING (notificatie + visuele fallback) ──
function melding(tekst) {
  // 1. Probeer een browser notificatie
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('StudyBuddy ⏱', {
      body: tekst,
      icon: '/static/media/timer.png'
    });
  }
  // 2. Toon altijd ook een melding in de app zelf (werkt ook zonder toestemming)
  toonInAppMelding(tekst);
}
 
// ── VISUELE MELDING IN DE APP ──
function toonInAppMelding(tekst) {
  let popup = document.getElementById('timerPopup');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'timerPopup';
    popup.style.cssText =
      'position:fixed;top:20px;left:50%;transform:translateX(-50%);' +
      'background:#003366;color:white;padding:14px 24px;border-radius:12px;' +
      'font-size:14px;font-family:Arial,sans-serif;z-index:9999;' +
      'box-shadow:0 4px 16px rgba(0,0,0,0.25);transition:opacity 0.3s;';
    document.body.appendChild(popup);
  }
  popup.textContent = '⏱ ' + tekst;
  popup.style.opacity = '1';
  popup.style.display = 'block';
  // Verberg na 5 seconden
  clearTimeout(window._timerPopupTimeout);
  window._timerPopupTimeout = setTimeout(() => {
    popup.style.opacity = '0';
    setTimeout(() => { popup.style.display = 'none'; }, 300);
  }, 5000);
}
 
// ── TOESTEMMING VRAGEN BIJ LADEN ──
document.addEventListener('DOMContentLoaded', () => {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
  if (document.getElementById('timerDisplay')) {
    updateDisplay();
  }
});