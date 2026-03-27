// Genereer de huidige week
  const dagen = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  const vandaag = new Date();
  const weekContainer = document.getElementById('weekDays');
 
  // Begin bij zondag van deze week
  const startVanWeek = new Date(vandaag);
  startVanWeek.setDate(vandaag.getDate() - vandaag.getDay());
 
  for (let i = 0; i < 7; i++) {
    const dag = new Date(startVanWeek);
    dag.setDate(startVanWeek.getDate() + i);
 
    const isVandaag = dag.toDateString() === vandaag.toDateString();
    const dagNum = dag.getDate().toString().padStart(2, '0');
 
    weekContainer.innerHTML += `
      <div class="week-day ${isVandaag ? 'active' : ''}">
        <span class="day-name">${dagen[i]}</span>
        <span class="day-num">${dagNum}</span>
      </div>
    `;
  }