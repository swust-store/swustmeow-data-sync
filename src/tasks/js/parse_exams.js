function parseExams() {
  const numbers = { 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 日: 7 };
  const allowed = ["finalExamTable", "midExamTable", "resitExamTable"];
  const exams = [];
  for (const id of allowed) {
    const div = document.getElementById(id);
    if (!div) continue;
    const rows = Array.from(div.querySelectorAll("tr.editRows, tbody tr"));
    for (const tr of rows) {
      const tds = Array.from(tr.querySelectorAll("td"));
      if (tds.length < 9) continue;
      const courseName = (tds[1].textContent || "").trim();
      if (!courseName || courseName === "课程") continue;
      const weekNum =
        parseInt(
          (tds[2].querySelector("span")?.textContent || "").replace(/\D+/g, "")
        ) || 0;
      const orderText = (tds[3].textContent || "").replace(/\s+/g, "");
      let weekday = 0,
        numberOfDay = 0;
      const m = orderText.match(/周([一二三四五六日]).*?([一二三四五六日])/);
      if (m) {
        weekday = numbers[m[1]] || 0;
        numberOfDay = numbers[m[2]] || 0;
      } else if (orderText.length >= 4) {
        weekday = numbers[orderText[1]] || 0;
        numberOfDay = numbers[orderText[3]] || 0;
      }
      const date = (tds[4].querySelector("span")?.textContent || "")
        .trim()
        .replaceAll("/", "-");
      const classroom = (tds[6].textContent || "").trim();
      const seatNo =
        parseInt((tds[7].textContent || "").replace(/\D+/g, "")) || 0;
      const place = (tds[8].textContent || "").trim();
      exams.push({
        type: id,
        courseName,
        weekNum,
        numberOfDay,
        weekday,
        date,
        place,
        classroom,
        seatNo,
      });
    }
  }
  return { exams };
}
