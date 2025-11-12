function detectErrorFromHTML(html) {
  try {
    const s = String(html || "")
      .trim()
      .replace(/\n/g, "");
    const re =
      /<script>\s*alert\s*\(\s*'.*?'\s*\);\s*self\.location\s*=\s*'\/aexp';\s*<\/script>/i;
    return re.test(s);
  } catch (_) {
    return false;
  }
}

function extractTotalPagesFromHTML(html) {
  try {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const p = doc.querySelector("#myPage p");
    const text = p ? p.textContent || "" : "";
    const m = text.match(/第\s*(\d+)\s*页\s*\/\s*共\s*(\d+)\s*页/);
    if (!m) return null;
    return parseInt(m[2], 10);
  } catch (_) {
    return null;
  }
}

function parseExpEntriesFromHTML(html) {
  const entries = [];
  try {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const tables = Array.from(doc.querySelectorAll("table.tablelist"));
    const table = tables.length ? tables[tables.length - 1] : null;
    const trs = table ? table.querySelectorAll("tbody tr") : null;
    if (!trs || trs.length < 2) return entries;
    for (let i = 1; i < trs.length; i++) {
      const tds = trs[i].querySelectorAll("td");
      if (!tds || tds.length < 5) continue;
      const courseName = (tds[0].textContent || "").trim();
      const projectName = (tds[1].textContent || "").trim();
      const timeText = (tds[2].textContent || "").trim();
      const place = (tds[3].textContent || "").trim();
      const teachersRaw = (tds[4].textContent || "").trim();
      let week = 0,
        weekday = 1,
        startSec = 1,
        endSec = 2;
      const m =
        timeText.match(
          /(\d+)周\s*星期([一二三四五六日天])\s*(\d+)\s*-\s*(\d+)节/
        ) ||
        timeText.match(/(\d+)周.*?([一二三四五六日天]).*?(\d+)\s*-\s*(\d+)节/);
      if (m) {
        week = parseInt(m[1], 10) || 0;
        const map = { 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 日: 7, 天: 7 };
        weekday = map[m[2]] || 1;
        startSec = parseInt(m[3], 10) || 1;
        endSec = parseInt(m[4], 10) || startSec;
      }
      const teachers = teachersRaw
        ? teachersRaw.split(/[，,、/\s]+/).filter(Boolean)
        : [];
      const display = projectName || courseName;
      entries.push({
        course_name: courseName,
        display_name: display,
        teachers,
        start_week: week,
        end_week: week,
        place,
        weekday,
        start_section: startSec,
        end_section: endSec,
        is_custom: false,
      });
    }
  } catch (_) {}
  return entries;
}

function fetchExpPage(url) {
  return fetch(url, {
    credentials: "include",
    referrer: "http://sjjx.dean.swust.edu.cn/aexp/stuLeft.jsp",
  })
    .then(async (r) => ({ status: r.status, ok: r.ok, text: await r.text() }))
    .catch((e) => ({ status: 0, ok: false, text: String(e) }));
}

function fetchMany(urls) {
  return Promise.all(urls.map((u) => fetchExpPage(u)));
}
