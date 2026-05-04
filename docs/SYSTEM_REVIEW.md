# סקירת מערכת — Claude Agents Framework

סקירה ביקורתית של עיצוב המערכת, ממצאים, המלצות ושיפורים מוצעים.

מיועד לדיון פנימי, לא להחלפת המסמכים הקיימים ב-`docs/`.

---

## חלק 1 — ממצאים: מה עובד טוב

### 1.1 Files-as-protocol הוא בחירת עיצוב חזקה

המעבר ממצב-בזיכרון למצב-בדיסק פותר בעיה אמיתית במערכות multi-agent:

- **שרידות** — כל הפסקה היא נקודת התאוששות. אין "session lost".
- **שקיפות** — כל המצב נצפה ב-`cat`. `STATE.json`, `EVENTS.jsonl`, `feedback/`.
- **החלפיות** — agent בודד ניתן להחלפה בלי לשבור את האחרים, כי החוזה הוא קובץ ולא API.
- **Auditability** — `EVENTS.jsonl` הוא append-only audit trail בחינם.

רוב הפריימוורקים (LangGraph, CrewAI, AutoGen) מסתמכים על זיכרון תהליך.
המערכת הזו לא, וזה הופך אותה ל-recoverable באופן יסודי.

### 1.2 Behavioral contract במקום persona

ההבחנה הזו load-bearing:

```
persona  : "אתה reviewer בכיר עם 10 שנות ניסיון..."  → drift תוך 5 turns
contract : "מצא הפרות חוזה. אל תתקן. פלט בפורמט הזה." → יציב
```

זה מה שמונע מ-`reviewer` להתחיל לתקן ומ-`builder` להחליט החלטות אדריכליות.
הכלל מבני, לא סגנוני.

### 1.3 נתיבי חזרה ממוקדים (typed return paths)

רוב המערכות עושות "loop back to start" כשנכשלות. כאן כל בעיה חוזרת
לבעלים הנכון דרך קובץ feedback מתויג:

| בעיה | קובץ | יעד |
|---|---|---|
| reviewer מצא פגם אדריכלי | `ARCH_FEEDBACK.md` | architect |
| reviewer מצא הפרת חוזה | `REVIEW_FAILURES.md` | builder |
| builder לא בטוח בדרישה | `IMPL_QUESTIONS.md` | planner |
| builder חוסם על תכנון | `DESIGN_QUESTIONS.md` | architect |
| tester מצא AC נכשל | `TEST_FAILURES.md` | builder |

ה-hook `classify_feedback.py` אוכף את התיוג מבחוץ במקום להסתמך על משמעת.
זה הסוג של אכיפה מבנית שמחזיקה לאורך זמן.

### 1.4 Rigor אורתוגונלי ל-Fast

זה נדיר ויפה:

- **rigor** (lite/standard/strict) שולט בעומק התהליך — כמה קבצי plan, אילו gates.
- **fast** שולט בהשהיות — האם המערכת עוצרת לאישור human.

רוב המערכות מערבבות את שניהם ("quick mode", "thorough mode") ומאבדות גמישות.
ההפרדה כאן מאפשרת `strict + interactive`, `lite + fast`, וכל שילוב אחר.

### 1.5 Lessons משפרים את הplan, לא את ה-agent

```
פתרון נאיבי : תזכור עליי את הטעות שעשית פעם → unpredictable
פתרון כאן   : LESSONS.md → injection ל-planner לפני התכנון הבא
```

זה הופך כשלים חוזרים לאילוצים דטרמיניסטיים ובני-מחיקה במקום לזיכרון
אטום ב-agent. עיצובית — נכון.

---

## חלק 2 — איפה יש דאגות

### 2.1 עלות הטקס גבוהה במצבים מסוימים

8 agents, 8 קבצי plan, 6 קבצי feedback, 14 מצבים, 9 סוגי events.
ב-`lite` זה מצטמצם ל-4 קבצי plan, אבל המערכת המנטלית עדיין שלמה.

הסיכון: משתמשים יעקפו את הפלואו במקום ללכת ל-`lite` לשינוי קטן,
כי כניסה ל-`team-flow` מרגישה כמו התחייבות.

### 2.2 ה-FSM מניח agents ממושמעים

LLMs לא ממושמעים בהגדרה:
- אגנט עלול לכתוב feedback בפורמט שגוי.
- אגנט עלול ליצור קובץ ולא להשלים את המשימה (orphan).
- אגנט עלול לדלג על יצירת קובץ שצריך להיות שם.

`classify_feedback.py` מטפל במקרה אחד. `/verify-state` מנקה drift בדיעבד,
אבל זה ידני. "קובץ קיים = פתוח" שביר ל-orphans מ-runs ישנים.

### 2.3 הכלל "reviewer לא מתקן" יוצר churn בתיקונים טריוויאליים

typo ב-import → `REVIEW_FAILURES.md` → builder turn חדש → אישור human.
תיאורטית נקי, מעשית יקר. עבור פיצ'ר ממוצע יכולים להיות 5-10 ממצאים
טריוויאליים שכל אחד מהם דורש מחזור מלא.

### 2.4 עלות טוקנים לא נצפית

- `architect` ב-Opus לכל discovery
- `reviewer` ב-Sonnet לכל conversation
- `tester`, `retro`, `planner` נוספים על זה

ב-`standard` עם 5 conversations זה מצטבר. אין היום שום מקום שמראה למשתמש
"הפיצ'ר הזה עלה X". זה אומר שאי-אפשר לקבל החלטה מושכלת בין `lite` ל-`standard`
על בסיס עלות.

### 2.5 הפילוסופיה מניחה תהליך waterfall-ish

מצוין ל-features מתוכננים מראש (auth, payment, migration).
פחות טוב ל:
- עבודה חקרנית ("בוא נבין איך X משפיע")
- refactoring טהור (אין AC, אין user value)
- דיבאג (התסמין ידוע, השורש לא)

ה-PRD-import מסגיר את ההנחה — המערכת רוצה ספק ברור לפני שהיא רצה.

### 2.6 Onboarding — דיוק

המגע הראשון מטופל מצוין על ידי `/help` ו-`/go`. אבל יש שכבות:

| שכבה | עלות | מי פותר היום |
|---|---|---|
| מגע ראשון | נמוך | `/help`, `/go` |
| הבנת ה-pipeline ה-happy path | נמוך-בינוני | `/help` עם המצבים |
| feedback file לא צפוי שנפתח | בינוני | `/help` מזהה `feedback-open` |
| FSM תקוע / drift / orphan | גבוה | `/verify-state` קיים, אבל צריך לדעת עליו |
| התאמת תבניות `plan/` לפרויקט | גבוה | אין סקיל ייעודי |

המסקנה: עלות הכניסה היומיומית מטופלת היטב. עלות ה-recovery
וה-customization עדיין גבוהה, אבל מורגשת רק כשמשהו לא הולך כמתוכנן.

---

## חלק 3 — שיפורים מוצעים

הצעות ממוינות לפי ערך-לעלות. הראשונות בעלות יחס הכי טוב.

### 3.1 TTL/heartbeat ל-feedback files [ערך גבוה, עלות נמוכה]

**בעיה:** "קובץ קיים = פתוח" שביר ל-orphans.

**פתרון:** הוסיפו metadata ב-frontmatter של כל feedback file:

```yaml
---
created_at: 2026-05-04T08:12:00Z
created_by_event: <event_id>
ttl_hours: 24
---
```

`SessionStart` hook (או `/verify-state`) יסיר feedback ש:
- `event_id` שלו לא קיים ב-`EVENTS.jsonl` הנוכחי, או
- `created_at + ttl_hours` חלף.

**תוצאה:** "deleted = resolved" הופך מאמינות-במשמעת ל-invariant נאכף.

### 3.2 תיוג `[AUTO_FIX]` ב-reviewer [ערך גבוה, עלות נמוכה]

**בעיה:** churn סביב תיקונים טריוויאליים.

**פתרון:** ה-reviewer יכול לסמן ממצאים טריוויאליים (typo, unused import,
missing newline) כ-`[AUTO_FIX]` ולכלול patch קצר ב-`REVIEW_FAILURES.md`.
ה-builder מחיל patches עם תיוג זה ב-batch בלי human turn.
ממצאים שה-reviewer לא בטוח לגביהם — נשארים violations רגילים.

**תוצאה:** שומר על "reviewer לא מתקן" כעקרון, מבטל את ה-churn.

### 3.3 Cost meter ב-RETRO.md [ערך בינוני-גבוה, עלות בינונית]

**בעיה:** אין ויזיביליות לעלות.

**פתרון:** הוסיפו ל-`EVENTS.jsonl` שדות `tokens_in`, `tokens_out`, `cost_usd`
לכל event מסוג `AGENT_DONE`. ה-retro מציג סיכום:

```
Cost: $4.20
  architect (Opus)  : $2.50  (60%)
  builder (Sonnet)  : $1.10  (26%)
  reviewer (Sonnet) : $0.40  (10%)
  tester (Sonnet)   : $0.20  (5%)
```

**תוצאה:** משתמשים יוכלו לקבל החלטה מושכלת בין `lite` ל-`standard`
על בסיס עלות בפועל מפיצ'רים קודמים.

### 3.4 Rigor escalator במקום בחירה מראש [ערך בינוני, עלות בינונית]

**בעיה:** משתמש לא יודע מראש איזה rigor הפיצ'ר דורש.

**פתרון:** ברירת מחדל `lite`. ה-orchestrator מציע אוטומטית עלייה ל-`standard` כש:
- `builder` מוצא תלות חוצה layers
- `discoverer` מזהה מסלול > 3 קבצים
- מספר conversations > 3
- מילות מפתח ב-`STORM_SEED.md`: "auth", "payment", "migration"

ההצעה דרך `HUMAN_QUESTIONS.md`:
```
Scope גדל מעבר ל-lite (3 layers, 5 conversations).
לעלות ל-standard? [yes/no]
```

**תוצאה:** משתמש לא חוזה rigor מראש; המערכת מציעה כשהיא מזהה סיבה.

### 3.5 Inline `/quick` שאילתא בין agents [ערך בינוני, עלות נמוכה]

**בעיה:** שאלות אטומיות יוצרות feedback files מיותרים.

**פתרון:** חריג ממוקד לכלל "קבצים בלבד" — `builder` יכול להפעיל `quick`
לשאלה אטומית ("מה ה-import path של `X`?") בלי ליצור `IMPL_QUESTIONS.md`.

הגבלות (כדי לא לשבור את ה-FSM):
- 2 tool calls מקסימום
- אסור לכתוב לדיסק
- התשובה לא נשמרת ב-state
- לא נוצר event

**תוצאה:** מקצר feedback loops טריוויאליים בלי לפגוע ב-determinism.

### 3.6 `/help --doctor` לאבחון מצב [ערך גבוה, עלות נמוכה]

**בעיה:** כשהמערכת תקועה (orphan, drift, FSM stuck), המשתמש לא יודע מה לעשות.

**פתרון:** `/help --doctor` מריץ `/verify-state` מתחת לקלעים, מסכם בעברית
פשוטה מה דרוש, ומציע פעולה אחת:

```
מצאתי 2 בעיות:
  1. REVIEW_FAILURES.md מתייחס ל-conv-3, אבל PROGRESS.md אומר conv-2.
     הצעה: נקה את REVIEW_FAILURES.md ידנית — הוא יתום מ-run קודם.
  2. STATE.json אומר BUILDING, אבל אין conversation פעיל.
     הצעה: רוץ /team-flow <feature> build כדי לחזור למצב יציב.

האם להריץ את ההצעה הראשונה? [yes/no]
```

**תוצאה:** שכבת recovery יורדת מ"גבוהה" ל"בינונית" עם אותו ממשק שהמשתמש מכיר.

---

## חלק 4 — שני סקילים חדשים: `/explore` ו-`/debug`

החדשה הטובה: ה-FSM, פרוטוקול ה-feedback, ו-`classify_feedback.py` כבר תומכים
ב-workflow-ים שאינם waterfall כ-data structures גנריים. צריך רק סקילים חדשים
שמשתמשים בתת-קבוצה אחרת של States ו-Files. **הליבה לא צריכה להשתנות.**

### 4.1 `/explore <question>` — מצב חקרני

**מתי להשתמש:** "בוא נבין איך X משפיע", "האם נכון לשנות מ-Y ל-Z?",
"מה ה-data flow של פיצ'ר A?". אין AC, אין יעד יישומי, יש שאלה.

**מבנה קבצים:**
```
explorations/<topic>/
  EXPLORE.md           ← session log: שאלות, ממצאים, file:line refs
  TRACE.md             ← discoverer output
  CONCLUSIONS.md       ← מה למדנו
  feedback/
    HUMAN_QUESTIONS.md ← נשאר עובד
```

**שינוי לעומת `/team-flow`:**
- אין `plans/`, אין `STORM_SEED.md`, אין `PROGRESS.md`.
- ה-driver הוא `discoverer`, לא `builder`. הוא כבר כתוב ל"follows visible
  paths, captures trace".
- אין `reviewer`, אין `tester`, אין `retro`.

**מסיים עם החלטה:**
```
המסקנות מצדיקות feature?
  [yes] /team-flow <name> --from-exploration <topic>
        (CONCLUSIONS.md מוזרק כ-context ל-storm)
  [no]  ה-exploration נשאר תיעוד; שום דבר לא נבנה
```

### 4.2 `/debug <symptom>` — pipeline ייעודי לבאגים

**מתי להשתמש:** באג ידוע (תסמין נצפה), שורש לא ידוע.

**מבנה קבצים:**
```
debugs/<symptom-name>/
  SYMPTOM.md     ← מה נשבר, איך זה מתבטא, סביבה
  REPRO.md       ← שלבים מינימליים לשחזור
  ROOT_CAUSE.md  ← מה השורש (כתוב על ידי discoverer/builder)
  FIX.md         ← מה השינוי
  feedback/
    HUMAN_QUESTIONS.md
    TEST_FAILURES.md ← עובד גם כאן
```

**מצבים חדשים ב-FSM (extension, לא replacement):**
```
INVESTIGATING → REPRODUCING → ROOT_CAUSE_FOUND → FIXING → VERIFYING → DONE
```

**Tester רץ פעמיים:**
1. **לפני התיקון** — לוודא שה-repro עקבי. אם הבדיקה כבר עוברת — אין באג.
2. **אחרי התיקון** — לוודא שתוקן. אם נכשל — חזרה ל-FIXING דרך `TEST_FAILURES.md`.

**שימוש חוזר ב-agents קיימים:**
- `discoverer` — מאתר את ה-stack trace, הקבצים המעורבים.
- `builder` — כותב את ה-FIX.
- `tester` — מאמת.
- `reviewer` — מצומצם: רק בודק שה-FIX לא שובר חוזים אחרים.

---

## חלק 5 — סדר ביצוע מומלץ

לפי השפעה לכל יחידת מאמץ:

1. **TTL ל-feedback files** (3.1) — עוצר bug class שלם, שינוי קטן.
2. **`/help --doctor`** (3.6) — מוריד את עלות ה-recovery, עוטף יכולת קיימת.
3. **Cost meter** (3.3) — מאפשר למשתמשים לקבל החלטות מושכלות.
4. **`[AUTO_FIX]` ב-reviewer** (3.2) — מוריד את ה-churn היומיומי.
5. **`/debug`** (4.2) — פותח use case שלם. שימוש חוזר במקסימום ב-agents קיימים.
6. **`/explore`** (4.1) — דומה, פותח use case שני.
7. **Inline `/quick`** (3.5) — אופטימיזציה מצטברת.
8. **Rigor escalator** (3.4) — דורש heuristics יותר עדינים, עלות גבוהה יותר.

---

## חלק 6 — מה לא להשתנות

עיצובי הליבה שלא הייתי נוגע בהם:

1. **Files-as-protocol** — זה היסוד. כל שיפור צריך לחזק אותו, לא להחליש.
2. **Behavioral contract במקום persona** — אל תוסיפו "אישיות" ל-agents.
3. **Reviewer לא מתקן** — `[AUTO_FIX]` הוא חריג ממוקד, לא ביטול.
4. **One-way spine עם typed return paths** — ה-feedback routing הוא הנכס
   העיצובי הכי חזק; אל תוסיפו broadcast.
5. **Human checkpoints כברירת מחדל** — `fast` הוא opt-in, לא אופציה שווה.

---

*כתב: סקירה חיצונית, מאי 2026.*
