let werkTijd = 25 * 60;
let pauzetijd = 5 * 60;
let huidigeTijd = werkTijd;
let bezig = false;
let interval = null;
let isPauze = false;

function toggleTimer() {
  if (bezig) {
    stopTimer();
  } else {
    startTimer();
  }
}

function startTimer() {
  bezig = true;
  document.getElementById('timerBtn').textContent = '⏸';
  interval = setInterval(() => {
    huidigeTijd--;
    updateDisplay();
    if (huidigeTijd <= 0) {
      clearInterval(interval);
      bezig = false;
      speelGeluid();
      stuurNotificatie();
      wisselModus();
    }
  }, 1000);
}

function stopTimer() {
  bezig = false;
  clearInterval(interval);
  document.getElementById('timerBtn').textContent = '▶';
}

function updateDisplay() {
  const min = Math.floor(huidigeTijd / 60).toString().padStart(2, '0');
  const sec = (huidigeTijd % 60).toString().padStart(2, '0');
  document.getElementById('timerDisplay').textContent = `${min}:${sec}`;
}

function wisselModus() {
  if (!isPauze) {
    isPauze = true;
    huidigeTijd = pauzetijd;
    document.getElementById('timerBalk').style.background = '#d4edda';
    stuurNotificatie('Pauze tijd! 5 minuten rust.');
  } else {
    isPauze = false;
    huidigeTijd = werkTijd;
    document.getElementById('timerBalk').style.background = 'white';
    stuurNotificatie('Werk tijd! 25 minuten focussen.');
  }
  startTimer();
}

function speelGeluid() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  osc.connect(ctx.destination);
  osc.frequency.value = 880;
  osc.start();
  osc.stop(ctx.currentTime + 0.3);
}

function stuurNotificatie(tekst = 'Timer is klaar!') {
  if ('Notification' in window) {
    if (Notification.permission === 'granted') {
      new Notification('StudyBuddy ⏱', { body: tekst });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(p => {
        if (p === 'granted') new Notification('StudyBuddy ⏱', { body: tekst });
      });
    }
  }
}

// Vraag toestemming bij laden
document.addEventListener('DOMContentLoaded', () => {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
});