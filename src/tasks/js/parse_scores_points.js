function parseScoresPoints() {
  const num = (s) => {
    if (s == null) return null;
    const m = ("" + s).replace(/[^0-9.\-]+/g, "");
    if (!m) return null;
    const v = parseFloat(m);
    return Number.isNaN(v) ? null : v;
  };
  const text = (el) => (el ? el.textContent.trim() : "");

  const points = (() => {
    const circles = Array.from(document.querySelectorAll("#Summary .UICircle"));
    if (circles.length < 2) return {};
    const creditsLis = circles[0].querySelectorAll("li");
    const pointsLis = circles[1].querySelectorAll("li");
    return {
      totalCredits: num(creditsLis?.[0]?.querySelector("em")?.textContent),
      requiredCoursesCredits: num(
        creditsLis?.[1]?.querySelector("em")?.textContent
      ),
      averagePoints: num(pointsLis?.[0]?.querySelector("em")?.textContent),
      requiredCoursesPoints: num(
        pointsLis?.[1]?.querySelector("em")?.textContent
      ),
      degreeCoursesPoints: num(
        pointsLis?.[2]?.querySelector("em")?.textContent
      ),
    };
  })();

  const planScores = (() => {
    const out = [];
    const tables = Array.from(document.querySelectorAll("#Plan table.UItable"));
    for (const table of tables) {
      const rows = Array.from(table.querySelectorAll("tr"));
      if (rows.length === 0) continue;
      const academicYear = text(rows[0].querySelector("span.number.bold"));
      let currentTerm = "";
      let inTerm = false;
      for (let i = 1; i < rows.length; i++) {
        const tr = rows[i];
        const termCell = tr.querySelector('td[width="11"][rowspan]');
        if (termCell) {
          const v = text(termCell);
          currentTerm = v === "秋" ? "上" : "下";
          inTerm = true;
          continue;
        }
        if (tr.querySelector('td[colspan="8"]')) {
          inTerm = false;
          continue;
        }
        if (!inTerm) continue;

        const tds = Array.from(tr.querySelectorAll("td"));
        if (tds.length < 7) continue;
        const courseName = text(tds[0]);
        if (!courseName || courseName === "课程") continue;
        const courseId = text(tds[1].querySelector("span")) || text(tds[1]);
        const credit = num(text(tds[2].querySelector("span")));
        const courseType = text(tds[3]) || null;
        const needEvaluation =
          tr.outerHTML.includes("请先完成课程教学质量评价");
        const formalScore = needEvaluation
          ? null
          : text(tds[4].querySelector("span")) || text(tds[4]) || null;
        const resitScore = needEvaluation
          ? null
          : text(tds[5].querySelector("span")) || text(tds[5]) || null;
        const points = needEvaluation
          ? null
          : num(text(tds[6].querySelector("span")));
        out.push({
          courseName,
          courseId,
          credit: credit ?? 0,
          courseType,
          formalScore,
          resitScore,
          points,
          scoreType: "plan",
          term:
            academicYear && currentTerm ? `${academicYear}-${currentTerm}` : "",
          needEvaluation,
        });
      }
    }
    return out;
  })();

  const parseOther = (rootId, scoreType) => {
    const out = [];
    const root = document.getElementById(rootId);
    if (!root) return out;
    const rows = Array.from(root.querySelectorAll("tr.cellBorder"));
    for (const tr of rows) {
      const tds = Array.from(tr.querySelectorAll("td"));
      if (tds.length < 7) continue;
      const termRaw = text(tds[0].querySelector("span"));
      const m = termRaw.match(/^(\d{4}-\d{4})-(\d)$/);
      const term = m ? `${m[1]}-${m[2] === "1" ? "上" : "下"}` : termRaw;
      const courseName = text(tds[1]);
      if (!courseName || courseName === "课程") continue;
      const courseId = text(tds[2].querySelector("span")) || text(tds[2]);
      const credit = num(text(tds[3].querySelector("span")));
      const needEvaluation = tr.outerHTML.includes("请先完成课程教学质量评价");
      const formalScore = needEvaluation
        ? null
        : text(tds[4].querySelector("span")) || text(tds[4]) || null;
      const resitScore = needEvaluation
        ? null
        : text(tds[5].querySelector("span")) || text(tds[5]) || null;
      const points = needEvaluation
        ? null
        : num(text(tds[6].querySelector("span")) || text(tds[6]));
      out.push({
        courseName,
        courseId,
        credit: credit ?? 0,
        courseType: null,
        formalScore,
        resitScore,
        points,
        scoreType,
        term,
        needEvaluation,
      });
    }
    return out;
  };

  const otherCommon = parseOther("Common", "common");
  const otherPhysical = parseOther("Physical", "physical");

  return { scores: [...planScores, ...otherCommon, ...otherPhysical], points };
}
