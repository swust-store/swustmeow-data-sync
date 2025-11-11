function parseCourseTable() {
  const t = Array.from(document.querySelectorAll("h3")).map((h) =>
    h.textContent.trim()
  );
  let termValue = null;
  for (const s of t) {
    const m = s.match(/(\d+-\d+-\d)\s*学期.*?个人课表/);
    if (m) {
      termValue = m[1];
      break;
    }
  }
  let trueTerm = termValue;
  if (termValue) {
    const parts = termValue.split("-");
    if (parts.length === 3) {
      const sy = parseInt(parts[0], 10);
      const ey = parseInt(parts[1], 10);
      const n = parseInt(parts[2], 10);
      trueTerm = `${sy}-${ey}-${n === 1 ? "上" : "下"}`;
    }
  }

  const entries = [];
  const rows = Array.from(
    document.querySelectorAll("table.UICourseTable tbody tr")
  );
  for (let i = 0; i < rows.length; i++) {
    const tr = rows[i];
    const tds = Array.from(tr.querySelectorAll("td"));
    if (tds.length === 0) continue;
    let colStart = 1;
    if (tds.length - colStart > 0) {
      const firstText = (tds[colStart].textContent || "").trim();
      if (firstText.startsWith("第")) colStart += 1;
    }
    for (let j = colStart; j < tds.length; j++) {
      const dayTd = tds[j];
      const lectures = Array.from(dayTd.querySelectorAll("div.lecture"));
      if (lectures.length === 0) continue;
      for (const lec of lectures) {
        const courseName = (
          lec.querySelector("span.course")?.textContent || ""
        ).trim();
        const teachers = (
          lec.querySelector("span.teacher")?.textContent || ""
        ).trim();
        const teacherList = teachers
          ? teachers.split(/[\s/,，]+/).filter(Boolean)
          : [];
        const weekText = (
          lec.querySelector("span.week")?.textContent || ""
        ).trim();
        let startWeek = 1,
          endWeek = 16;
        const wm = weekText.match(/(\d+)\s*-\s*(\d+)/);
        if (wm) {
          startWeek = parseInt(wm[1], 10);
          endWeek = parseInt(wm[2], 10);
        }
        const place = (
          lec.querySelector("span.place")?.textContent || ""
        ).trim();

        const weekday = j - colStart + 1;
        const startSection = 2 * (i + 1) - 1;
        const endSection = 2 * (i + 1);
        entries.push({
          course_name: courseName,
          display_name: courseName,
          teachers: teacherList,
          start_week: startWeek,
          end_week: endWeek,
          place,
          weekday,
          start_section: startSection,
          end_section: endSection,
          is_custom: false,
        });
      }
    }
  }

  return { term: trueTerm, entries };
}
