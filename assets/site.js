/* Parish demo site — shared script.
   Everything visual is CSS-only so the same look can be rebuilt on
   WordPress.com without custom JavaScript. This file only handles:
     1. the mobile menu button and accordion sub-menus
     2. keeping desktop dropdown panels inside the viewport
     3. the Events page month calendar, drawn from a JSON list of events
        (on WordPress the same spot holds a Google Calendar embed) */
(function () {
  'use strict';

  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('primaryNav');
  var yr = document.getElementById('yr');
  if (yr) yr.textContent = new Date().getFullYear();

  /* ---------- 1. mobile menu ---------- */
  if (toggle && nav) {
    var savedScroll = 0;
    function setMenu(open) {
      if (open === nav.classList.contains('is-open')) return;
      if (open) {
        savedScroll = window.pageYOffset || document.documentElement.scrollTop;
        document.body.style.top = -savedScroll + 'px';
        document.body.classList.add('menu-open');
      } else {
        document.body.classList.remove('menu-open');
        document.body.style.top = '';
        window.scrollTo(0, savedScroll);
      }
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }
    toggle.addEventListener('click', function () { setMenu(!nav.classList.contains('is-open')); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 1000) setMenu(false); });
    // tap outside the header closes the menu; following a link closes it too
    document.addEventListener('click', function (e) {
      if (!nav.classList.contains('is-open')) return;
      if (e.target.closest('#siteHeader')) return;
      setMenu(false);
    });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });

    // accordion sub-menus on small screens
    Array.prototype.forEach.call(nav.querySelectorAll('.nav-sub-toggle'), function (btn) {
      btn.addEventListener('click', function () {
        var li = btn.parentNode;
        var open = !li.classList.contains('is-open');
        // opening one panel closes its siblings, so the list stays short
        if (open) Array.prototype.forEach.call(li.parentNode.children, function (sib) {
          if (sib !== li && sib.classList.contains('is-open')) {
            sib.classList.remove('is-open');
            var sb = sib.querySelector(':scope > .nav-sub-toggle'); if (sb) sb.setAttribute('aria-expanded', 'false');
          }
        });
        li.classList.toggle('is-open', open);
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    // open the sub-menu that contains the current page so it is visible on load
    var current = nav.querySelector('ul ul a[aria-current]');
    if (current) {
      var li = current.closest('li.has-sub');
      if (li) { li.classList.add('is-open'); var b = li.querySelector('.nav-sub-toggle'); if (b) b.setAttribute('aria-expanded', 'true'); }
    }

    /* ---------- 2. keep dropdowns on screen ---------- */
    function flip() {
      Array.prototype.forEach.call(nav.querySelectorAll('.nav ul ul'), function (ul) {
        ul.classList.remove('flip-left');
        var r = ul.getBoundingClientRect();
        if (r.right > window.innerWidth - 8) ul.classList.add('flip-left');
      });
    }
    Array.prototype.forEach.call(nav.querySelectorAll('.nav > ul > li.has-sub'), function (li) {
      li.addEventListener('mouseenter', flip);
      li.addEventListener('focusin', flip);
    });
  }

  /* ---------- site search (static: JSON index; WordPress: Search block) ---------- */
  var sToggle = document.getElementById('searchToggle');
  var sPanel = document.getElementById('siteSearch');
  var sInput = document.getElementById('searchInput');
  var sClose = document.getElementById('searchClose');
  var sResults = document.getElementById('searchResults');
  var sIndex = null;
  function setSearch(open) {
    if (!sPanel) return;
    sPanel.hidden = !open;
    sToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      if (nav && nav.classList.contains('is-open')) setMenu(false);
      sInput.focus();
      if (!sIndex) fetch('/assets/search.json').then(function (r) { return r.json(); }).then(function (d) { sIndex = d; runSearch(); }).catch(function () {});
    } else { sToggle.focus(); }
  }
  function runSearch() {
    if (!sIndex) return;
    var q = sInput.value.trim().toLowerCase();
    sResults.innerHTML = '';
    if (q.length < 2) return;
    var words = q.split(/\s+/);
    var scored = sIndex.map(function (p) {
      var t = p.t.toLowerCase(), s = (p.s || '').toLowerCase(), d = (p.d || '').toLowerCase();
      var score = 0;
      var all = words.every(function (w) { return t.indexOf(w) !== -1 || s.indexOf(w) !== -1 || d.indexOf(w) !== -1; });
      if (!all) return null;
      words.forEach(function (w) { if (t.indexOf(w) !== -1) score += 3; if (s.indexOf(w) !== -1) score += 1; if (d.indexOf(w) !== -1) score += 1; });
      return { p: p, score: score };
    }).filter(Boolean).sort(function (a, b) { return b.score - a.score; }).slice(0, 8);
    if (!scored.length) { sResults.innerHTML = '<li class="search__none">No pages match “' + sInput.value.replace(/</g, '&lt;') + '”.</li>'; return; }
    sResults.innerHTML = scored.map(function (x) {
      return '<li><a href="' + x.p.u + '"><strong>' + x.p.t + '</strong>' + (x.p.s ? ' <span class="search__section">· ' + x.p.s + '</span>' : '') + (x.p.d ? '<span class="search__desc">' + x.p.d + '</span>' : '') + '</a></li>';
    }).join('');
  }
  if (sToggle && sPanel) {
    sToggle.addEventListener('click', function () { setSearch(sPanel.hidden); });
    sClose.addEventListener('click', function () { setSearch(false); });
    sInput.addEventListener('input', runSearch);
    sPanel.querySelector('form').addEventListener('submit', function (e) {
      var first = sResults.querySelector('a');
      if (first) { e.preventDefault(); location.href = first.getAttribute('href'); }
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !sPanel.hidden) setSearch(false); });
  }

  /* ---------- "Next Mass" pill ----------
     <p class="next-mass__line" id="nextMass" data-schedule='[[0,"09:00","English"],[0,"11:00","English"],…]' hidden>
     weekday 0 = Sunday. Text is filled in from the visitor's clock. */
  var nm = document.getElementById('nextMass');
  if (nm) {
    try {
      var sched = JSON.parse(nm.getAttribute('data-schedule'));
      var now = new Date();
      var best = null;
      for (var dayOff = 0; dayOff < 8 && !best; dayOff++) {
        var d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + dayOff);
        var todays = sched.filter(function (s) { return s[0] === d.getDay(); }).sort(function (a, b) { return a[1] < b[1] ? -1 : 1; });
        for (var i = 0; i < todays.length; i++) {
          var hm = todays[i][1].split(':');
          var t = new Date(d.getFullYear(), d.getMonth(), d.getDate(), +hm[0], +hm[1]);
          if (t > now) { best = { t: t, label: todays[i][2], dayOff: dayOff }; break; }
        }
      }
      if (best) {
        var h = best.t.getHours(), m = best.t.getMinutes();
        var time = (h % 12 || 12) + ':' + (m < 10 ? '0' : '') + m + ' ' + (h < 12 ? 'AM' : 'PM');
        var when = best.dayOff === 0 ? 'today' : best.dayOff === 1 ? 'tomorrow' : ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][best.t.getDay()];
        nm.innerHTML = '<strong>Next Mass:</strong> ' + when + ' at ' + time + (best.label ? ' (' + best.label + ')' : '');
        nm.hidden = false;
      }
    } catch (e) {}
  }

  /* ---------- contact form helpers ---------- */
  var form = document.querySelector('form.contact-form');
  if (form) {
    var params = new URLSearchParams(location.search);
    var subj = params.get('subject');
    var sel = form.querySelector('select[name="subject"]');
    if (subj && sel) { Array.prototype.forEach.call(sel.options, function (o) { if (o.value.toLowerCase() === subj.toLowerCase() || o.text.toLowerCase() === subj.toLowerCase()) sel.value = o.value; }); }
    if (params.get('sent') === '1') {
      form.hidden = true;
      var thanks = document.querySelector('.contact-form__thanks');
      if (thanks) { thanks.hidden = false; thanks.scrollIntoView({ block: 'center' }); }
    }
  }

  /* ---------- 3. Events calendar ---------- */
  // <div class="month-cal" id="eventsCalendar" data-events='[{"date":"2026-10-04","title":"…","href":"#…","cls":"parish"}, …]'>
  // Recurring events use "weekday" (0=Sun…6=Sat) plus "weeks" ([1,3] = 1st and 3rd of the month) or "every":true.
  var cal = document.getElementById('eventsCalendar');
  if (!cal) return;
  var events;
  try { events = JSON.parse(cal.getAttribute('data-events') || '[]'); } catch (e) { return; }
  var grid = cal.querySelector('.month-cal__grid');
  var title = cal.querySelector('.month-cal__month');
  var prev = cal.querySelector('.month-cal__prev');
  var next = cal.querySelector('.month-cal__next');
  var list = cal.querySelector('.month-cal__list');
  if (!grid || !title) return;

  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var start = cal.getAttribute('data-start');            // "2026-09" pins the demo to a known month
  var now = start ? new Date(start + '-01T12:00:00') : new Date();
  var view = new Date(now.getFullYear(), now.getMonth(), 1);
  var minView = new Date(view.getFullYear(), view.getMonth() - 1, 1);
  var maxView = new Date(view.getFullYear(), view.getMonth() + 6, 1);

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function iso(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }

  function eventsOn(d) {
    var out = [];
    var key = iso(d);
    var weekOfMonth = Math.ceil(d.getDate() / 7);
    events.forEach(function (ev) {
      if (ev.date === key) out.push(ev);
      else if (ev.weekday !== undefined && ev.weekday === d.getDay()) {
        if (ev.every || (ev.weeks && ev.weeks.indexOf(weekOfMonth) !== -1)) out.push(ev);
      }
    });
    return out;
  }

  function draw() {
    var y = view.getFullYear(), m = view.getMonth();
    title.textContent = MONTHS[m] + ' ' + y;
    var first = new Date(y, m, 1).getDay();
    var days = new Date(y, m + 1, 0).getDate();
    var html = '';
    DAYS.forEach(function (d) { html += '<div class="month-cal__dow" aria-hidden="true">' + d + '</div>'; });
    for (var i = 0; i < first; i++) html += '<div class="month-cal__cell month-cal__cell--pad" aria-hidden="true"></div>';
    var todayKey = iso(new Date());
    var upcoming = [];
    for (var day = 1; day <= days; day++) {
      var d = new Date(y, m, day);
      var evs = eventsOn(d);
      var cls = 'month-cal__cell' + (iso(d) === todayKey ? ' is-today' : '') + (evs.length ? ' has-events' : '');
      html += '<div class="' + cls + '"><span class="month-cal__day">' + day + '</span>';
      evs.forEach(function (ev) {
        var label = ev.short || ev.title;
        html += '<a class="month-cal__event month-cal__event--' + (ev.cls || 'parish') + '" href="' + (ev.href || '#') + '" title="' + (ev.title + (ev.time ? ', ' + ev.time : '')).replace(/"/g, '&quot;') + '">' + label + '</a>';
        upcoming.push({ d: d, ev: ev });
      });
      html += '</div>';
    }
    grid.innerHTML = html;
    if (prev) prev.disabled = view <= minView;
    if (next) next.disabled = view >= maxView;
    if (list) {
      list.innerHTML = upcoming.length ? upcoming.map(function (u) {
        return '<li><span class="month-cal__list-date">' + DAYS[u.d.getDay()] + ' ' + u.d.getDate() + '</span> <a href="' + (u.ev.href || '#') + '">' + u.ev.title + '</a>' + (u.ev.time ? '<span class="month-cal__list-time">' + u.ev.time + '</span>' : '') + '</li>';
      }).join('') : '<li>No events listed this month.</li>';
    }
  }
  if (prev) prev.addEventListener('click', function () { view = new Date(view.getFullYear(), view.getMonth() - 1, 1); draw(); });
  if (next) next.addEventListener('click', function () { view = new Date(view.getFullYear(), view.getMonth() + 1, 1); draw(); });
  cal.classList.add('is-ready');
  draw();
})();
