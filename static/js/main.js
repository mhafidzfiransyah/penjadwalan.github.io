document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    events: '/api/schedules',

  eventContent: function (arg) {
  const title = arg.event.title || '(Tanpa Judul)';
  const time = arg.timeText || '';
  return {
    html: `
      <div class="fc-custom-event">
        <div class="fc-event-title">${title}</div>
        <div class="fc-event-time">${time}</div>
      </div>
    `
  };
},



    eventClick: function (info) {
      const event = info.event;
      const fullDate = new Date(event.start);

      const action = prompt(
        "Ketik:\n1 untuk Edit\n2 untuk Hapus\n3 untuk Tambah ke Google Calendar",
        "1"
      );

      if (action === "1") {
        const title = prompt("Edit judul:", event.title);
        if (title === null) return;

        const date = prompt("Edit tanggal (YYYY-MM-DD):", fullDate.toISOString().slice(0, 10));
        if (date === null) return;

        const time = prompt("Edit jam (HH:MM):", fullDate.toTimeString().slice(0, 5));
        if (time === null) return;

        const start = `${date}T${time}`;

        const email = prompt("Edit email (kosongkan jika tidak ada):", event.extendedProps.email || '');

        const reminderStr = prompt(
          "Edit reminder H-n (pisahkan dengan koma)",
          (event.extendedProps.reminder_days || [1]).join(",")
        );
        if (reminderStr === null) return;

        const reminder_days = reminderStr
          .split(',')
          .map(x => parseInt(x.trim()))
          .filter(x => !isNaN(x));

        fetch(`/api/schedules/${event.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, start, email, reminder_days })
        }).then(res => {
          if (res.ok) {
            calendar.refetchEvents();
            alert("✅ Jadwal diperbarui!");
          } else {
            alert("❌ Gagal memperbarui.");
          }
        });

      } else if (action === "2") {
        if (!confirm("Yakin ingin menghapus jadwal ini?")) return;

        fetch(`/api/schedules/${event.id}`, {
          method: 'DELETE'
        }).then(res => {
          if (res.ok) {
            calendar.refetchEvents();
            alert("🗑️ Jadwal dihapus.");
          } else {
            alert("❌ Gagal menghapus jadwal.");
          }
        });

      } else if (action === "3") {
        const gcalStart = event.startStr.replace(/[-:]/g, '').split('+')[0]; // format bersih
        const gcalEnd = gcalStart.slice(0, 8) + 'T010000Z'; // +1 jam dummy

        const gcalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(event.title)}&dates=${gcalStart}/${gcalEnd}&details=${encodeURIComponent("Acara ini berasal dari Aplikasi Penjadwalan Web")}`;

        window.open(gcalUrl, '_blank');
      }
    }
  });

  calendar.render();

  // =================== 🔹 Form Manual ===================
  document.getElementById('event-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const title = document.getElementById('title').value;
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value || '00:00';

    const start = `${date}T${time}`;

    fetch('/api/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, start })
    }).then(res => {
      if (res.ok) {
        calendar.refetchEvents();
        document.getElementById('event-form').reset();
      } else {
        alert("❌ Gagal menambahkan event dari form manual");
      }
    });
  });

  // =================== 🔹 Form Modal Lengkap ===================
  document.getElementById('addEventForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const title = document.getElementById('eventTitle').value;
    const date = document.getElementById('eventDate').value;
    const time = document.getElementById('eventTime').value || '00:00';
    const start = `${date}T${time}`;

    const email = document.getElementById('eventEmail').value;
    const reminderDaysRaw = document.getElementById('reminderDays').value;

    const reminder_days = reminderDaysRaw
      .split(',')
      .map(d => parseInt(d.trim()))
      .filter(n => !isNaN(n));

    const response = await fetch('/api/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, start, email, reminder_days })
    });

    if (response.ok) {
      alert("✅ Jadwal berhasil ditambahkan lewat modal!");
      document.getElementById('addEventForm').reset();
      calendar.refetchEvents();
    } else {
      alert("❌ Gagal menambahkan jadwal dari modal.");
    }
  });
});
