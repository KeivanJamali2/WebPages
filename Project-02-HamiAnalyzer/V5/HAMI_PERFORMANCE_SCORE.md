# Hami Performance Score — findings and implementation notes

**Date:** 1405-06-14 (2026-09-05) · **Applies to:** `V5/` (the live app)

These notes cover two things: the answer to "why do the request counts disagree between
my two analyses?", and the new **Hami Performance Score** analysis built on top of that answer.

---

## 1. Why "Total Requests per Hami" and "Hami First Response Time Detail" disagree

They are not two views of the same number. They count different populations.

| | Total Requests per Hami | First Response / Duration |
|---|---|---|
| Anchored on | `requests.first_date` (ticket **opened**) | individual `messages.date` |
| Source | `requests` table alone | `messages` INNER JOIN `requests` |
| Requires | nothing | ≥2 dated messages **inside the window** |
| `unknown` hami | in the CSV (234) | absent |

For the saved window `1404-08-01` → `1405-01-01`, cities یزد + بافق, the arithmetic is exact:

```
1988   Total Requests per Hami (includes unknown)
-234   unknown hami — Excel-only imports with no messages at all
-  3   only one message inside the window, so no response to measure
+ 60   opened BEFORE the window but still conversing inside it
=1811   First Response / Duration detail
```

Verified per-hami against both detail CSVs — all 20 hamis match exactly.

The `+60` term is the counter-intuitive one: it is why the response-time analysis reports
**more** requests per hami than the "total", not fewer.

### The `unknown` bucket

234 of those requests belong to `hami_id = 'unknown'`. These are Excel-only imports — that
source does not say which staff member handled the ticket, and carries no messages. They
inflate `total_requests_per_hami.csv` and are invisible to any message-based analysis.

Note that `total_requests_per_hami` drops `unknown` from the **chart** but **not** from the
**CSV**, so eyeballing the two CSVs on `/downloads` makes the gap look larger than it is.

---

## 2. The date-reference bug in `response_time_per_person`

**Question asked:** is a request selected by its first message date or its last one?
**Answer: neither.**

`get_response_times_data` (`database.py`) filters *individual messages*:

```sql
WHERE m.date >= start AND m.date < end
```

`response_time_per_person` (`analyzer.py`) then keeps requests where ≥2 messages survive and
measures between **those surviving messages only**.

So for a request that opened before the window, `times[0]` is not the student's opening
message — it is whichever message happens to land first inside the window.

### Worked example — request 263

```
opened            1404-04-22 23:27:00
hami replied      1404-04-23 08:36:00     -> true first response = 9.15h
closed            1404-10-25 10:30:00

OLD code sees only the 2 closing messages inside the window:
  1404-10-25 10:29:57 -> 1404-10-25 10:30:00  =  0.00h
  ...and its `if first_response > 0` guard then SILENTLY DISCARDS the sample.
```

So the old path both mis-measures boundary-straddling requests and silently drops some of
them. Measured effect on published figures for hami 105002: first response reads **156.9h**
but is really **52.0h**; duration reads **399.2h** but is really **153.5h**.

### Useful schema facts (verified, 6824/6824 rows each)

- `requests.first_date` **is exactly** the first message timestamp.
- `requests.last_date` **is exactly** the last message timestamp.
- Both are full `YYYY-MM-DD HH:MM:SS` Jalali strings, so lexicographic `>=` / `<` works.

**`response_time_per_person` was deliberately left unchanged.** Its CSVs and plot still carry
this behaviour. Fixing it is a separate decision.

---

## 3. The new analysis: Hami Performance Score

Registered in `available_analyses.txt` as `hami_performance_score`, shown last on `/analyze`.

### Cohorts

Two different cohorts, on purpose:

| Metric | Cohort | Size (saved window) |
|---|---|---|
| Request count | opened in period (`first_date`), city filter, excl. `unknown` | 1754 |
| First response, duration | **closed** in period (`last_date`), then **all** messages of those requests loaded | 1817 |

Volume answers *"how much work arrived this period"*; timing answers *"how well was the work
that finished this period handled"*. Loading every message of a selected request — rather than
only the in-window ones — is what avoids the bug in section 2.

### Aggregation

Per hami, the **median** of the per-request values, not the mean. These distributions are
strongly right-skewed: hami 105009's mean first response is 73.3h against a median of 26.4h,
a 2.8x gap driven by a handful of stragglers. The mean would punish a hami for a few
forgotten tickets rather than describe their normal behaviour.

### Formula

```
z_count    = +(count    - mean) / sd
z_first    = -(first    - mean) / sd     # negated: faster is better
z_duration = -(duration - mean) / sd     # negated: faster is better
z_quality  = +(quality  - mean) / sd

final = 0.250*z_count + 0.125*z_first + 0.125*z_duration + 0.500*z_quality
```

`sd` is the **sample** standard deviation (`ddof=1`), computed over the hamis in the report.

`final` is a weighted z-score centred near 0, roughly −0.85 … +0.97 on the current data.
It is **not** a 0–100 score.

### Missing data

- A hami with **no requests** in the period is excluded from the report entirely.
- A hami with **no Quality of Response score** is excluded from the composite and named in a
  warning, rather than being ranked on three quarters of the formula.
- If **nobody** has been graded for the period, the CSV is still written with the three
  activity metrics and their z-scores, `final_score` is left blank, and the warning lists the
  evaluation periods that *do* exist.

### Outputs

- `plots/hami_performance_score.png` — top panel: `final_score` sorted descending (skyblue).
  Bottom panel: the four **weighted** contributions side by side, so it is visible which
  metric drove each score. Hami-name reference table on the right.
- `downloads/hami_performance_score.csv` — `hami_id, hami_name, count,
  first_response_median_h, duration_median_h, quality, z_count, z_first_response,
  z_duration, z_quality, final_score`, sorted by `final_score` descending.

---

## 4. How to use it

1. Go to **Evaluations** and enter *Quality of Response* for each hami, for the **exact same
   period** you will analyse. The period must match exactly — `1404-08-01` → `1405-01-01` on
   the Evaluations page only feeds an analysis run for those same two dates.
2. Go to **Analyze**, set the same dates, tick **Hami Performance Score**.
3. Optionally open **Metric weights** under that checkbox. The four must add up to 1; a
   running total under the boxes turns red when they do not. A set that does not sum to 1 is
   rejected with a warning and the defaults are used instead.
4. Run. Results appear on `/plots` and `/downloads`.

Without quality scores you get the three activity metrics and a warning, not a final score.

---

## 5. Caveats worth remembering

**Z-scores are outlier-sensitive.** They are built from the mean and standard deviation, both
of which an outlier moves. Hami 105011's 470h median duration inflates the duration `sd` from
62.4h to 103.9h, which compresses everyone else's duration z toward zero and gives that hami
a −3.45 on a metric weighted at only 12.5%. Using the median per hami already absorbed most
of this (it pulled 105011 from 766.8h down to 469.9h). The contribution panel exists so this
reads as an outlier rather than as a verdict.

**Scores are relative to the cohort and the period.** A z-score says "how far from this
period's average", so the numbers are not comparable between periods, and adding or removing
a hami shifts everyone. Quality of Response is z-scored too, so all four inputs share this
property and the composite is at least internally consistent.

**The count metric measures workload, not effort.** A hami with 8 requests was not necessarily
underperforming — they may have joined mid-period. Count is weighted at 25%, the second
largest, so this matters. Note also that count correlates *negatively* with response speed
(Spearman ρ ≈ −0.58), meaning busy hamis tend to reply more slowly, so the volume weight
partly works against the timing weights.

**`get_all_employees()` only scans `messages.to_name`.** An employee who only ever sent
messages and never received one does not appear on the Evaluations page. Left unchanged
because widening it would alter the existing employee analyses.

---

## 6. Files changed

| File | Change |
|---|---|
| `database.py` | new `get_hami_timing_data()` — anchors on `last_date`, returns all messages of selected requests |
| `analyzer.py` | new `hami_performance_score()` in `SQLiteAnalyzer` |
| `config.py` | `HAMI_SCORE_WEIGHTS`; weights persisted through save/load of `analysis_config.json` |
| `app.py` | weight parsing + validation in the `/analyze` POST; entry in `analysis_functions` |
| `templates/analyze.html` | "Metric weights" collapse under the new checkbox + live running total |
| `available_analyses.txt` | one new line registering the analysis |

Nothing else was modified. `response_time_per_person`, `total_requests_per_hami` and all
place/faculty analyses are untouched.

---

## 7. Verification record

- New timing query returns exactly **1817** requests; count cohort exactly **1754**.
- Every z column: mean `0.000000000000`, sd `1.000000000000` (ddof=1).
- `final_score` reproduces the weighted sum with **zero** floating-point difference; hand-checked.
- Negation confirmed: the slowest first-response has the lowest `z_first_response`.
- **Zero collateral damage** — full batch run with and without the new analysis produced
  **59 of 59 shared files byte-identical**; only the two new files appeared.
- Weight validation: sum 0.9 warns and falls back; non-numeric falls back silently; a valid
  custom set sticks and changes the ranking.
- Degraded mode and partial-coverage mode both produce a populated CSV and a clear warning,
  no traceback.
- Test data removed afterwards: `evaluations` back to 0 rows; `requests` 7310, `messages`
  31712, `hami_names` 22 all unchanged; `plots/` and `downloads/` restored byte-identical;
  `analysis_config.json` identical apart from the new `score_weights` key.

### Reference: metric values for the saved window

Window `1404-08-01` → `1405-01-01`, cities یزد + بافق. Medians, in hours.

| hami | count | first response | duration |
|---|---|---|---|
| 105018 | 249 | 19.6 | 47.8 |
| 105007 | 246 | 3.8 | 24.4 |
| 105010 | 159 | 20.1 | 46.9 |
| 105004 | 142 | 14.2 | 32.1 |
| 105009 | 102 | 27.9 | 98.6 |
| 105012 | 94 | 16.3 | 45.9 |
| 105006 | 91 | 27.6 | 87.5 |
| 105266 | 89 | 34.6 | 153.9 |
| 105434 | 86 | 24.3 | 45.7 |
| 105002 | 75 | 52.0 | 153.5 |
| 105015 | 69 | 25.8 | 71.5 |
| 105860 | 58 | 17.3 | 96.4 |
| 105017 | 57 | 18.4 | 122.5 |
| 105016 | 50 | 14.3 | 50.7 |
| 105003 | 50 | 19.4 | 42.6 |
| 105008 | 36 | 42.0 | 147.8 |
| 105335 | 35 | 71.3 | 142.6 |
| 105001 | 29 | 22.9 | 75.7 |
| 105011 | 29 | 28.7 | 469.9 |
| 105005 | 8 | 130.1 | 278.0 |
