# AIAP Batch 25 Technical Assessment — Travelers' Inn Cancellation Prediction

**Name (as in NRIC):** Wong Jun Hao
**Email:** jhwong03@gmail.com

## Problem statement

Predict, 7 days before arrival, the probability that a confirmed booking will not be
honoured (cancelled or no-show), so reservations staff can act on the highest-risk
bookings (confirmation calls, deposit requirements). Alongside this, descriptive
analysis of pricing flags where rates look mis-set. Full reasoning in `decision_log.md`.

---

## 1. Folder structure

```
.
├── README.md                  # this file
├── eda.ipynb                  # exploratory data analysis (Task 1)
├── decision_log.md            # Task 2
├── prompt_chat_history.md     # Task 4
├── run.sh                     # pipeline entry point
├── requirements.txt           # dependencies
├── config.yaml                # all pipeline configuration (data, cleaning, split,
│                               #   features, model hyperparameters, output)
├── data/                      # hotel.db is downloaded here at runtime; not committed
├── outputs/                   # metrics.json written here after each run
├── .github/workflows/         # GitHub Actions CI (runs the pipeline on push)
└── src/
    ├── main.py                # orchestrates the pipeline end-to-end
    ├── data_loader.py         # downloads hotel.db if absent; loads via SQLite
    ├── preprocess.py          # cleaning: dedup, type casting, category normalisation,
    │                          #   impossible-value removal
    ├── features.py            # derived features, time-based split, sklearn
    │                          #   preprocessing (imputation, encoding, scaling)
    ├── model.py                # model factory (swap model via config)
    └── evaluate.py             # metrics computation and reporting
```

## 2. Running the pipeline

```bash
pip install -r requirements.txt
./run.sh
```

`run.sh` downloads `data/hotel.db` automatically if it isn't present (so a fresh clone,
including the GitHub Actions runner, works with no manual data step), runs the full
pipeline, and writes `outputs/metrics.json`.

**Modifying parameters** — everything is controlled by `config.yaml`, no code edits
needed:

| To change... | Edit in `config.yaml` |
|---|---|
| Which model runs | `model.name`: `logistic_regression` \| `random_forest` \| `hist_gradient_boosting` |
| Model hyperparameters | the matching block under `model.<name>` |
| Train/test years | `split.train_years`, `split.test_years` |
| Decision threshold | `model.threshold` (lower → more recall, more false alarms) |
| Cleaning rules | `cleaning.*` |
| Which columns are excluded as features | `features.exclude` |

A config other than the default can be pointed to without editing `run.sh`:

```bash
CONFIG_PATH=my_experiment.yaml ./run.sh
# or
python -m src.main --config my_experiment.yaml
```

## 3. Pipeline flow

```
 data/hotel.db (SQLite)
        │
        ▼
 ┌─────────────────┐
 │  data_loader.py │  download if absent → load bookings table
 └────────┬────────┘
          ▼
 ┌─────────────────┐
 │  preprocess.py  │  dedupe → fix target encoding → normalise categoricals
 │                 │  → cast numerics → fix hidden missingness → drop
 │                 │  impossible-value rows → drop leakage/unusable columns
 └────────┬────────┘
          ▼
 ┌─────────────────┐
 │   features.py   │  derived features → TIME-BASED SPLIT (train: 2023-24,
 │                 │  test: 2025) → separate X / y
 └────────┬────────┘
          ▼
 ┌───────────────────────────────┐
 │  sklearn Pipeline              │
 │  ┌───────────────────────────┐ │
 │  │ preprocessing (fit on      │ │   one-hot encode categoricals
 │  │ TRAIN ONLY — no test       │ │   (rare levels grouped),
 │  │ leakage)                   │ │   impute + scale numerics
 │  └──────────────┬─────────────┘ │
 │                 ▼               │
 │  ┌───────────────────────────┐ │
 │  │ model.py — classifier     │ │   swappable via config.yaml
 │  │ (HistGradientBoosting)    │ │
 │  └───────────────────────────┘ │
 └────────────────┬───────────────┘
                   ▼
          ┌─────────────────┐
          │  evaluate.py    │  score on held-out 2025 test set →
          │                 │  outputs/metrics.json
          └─────────────────┘
```

The preprocessing transformer lives *inside* the sklearn `Pipeline`, so it is fitted
on the training split only — imputation statistics, category vocabularies and scaling
parameters never see the test set.

## 4. EDA summary

Full analysis, code and charts are in `eda.ipynb`. This is a condensed summary.

**Data quality.** All 36 columns loaded as text from SQLite; the target
(`is_canceled`) was stored under six different encodings (`0`/`1`/`Yes`/`No`/`true`/
`false`); several categoricals had 5–10x more levels than the business definition
allows due to case, spacing and typo variants (e.g. `meal` had 41 levels instead of
5); `agent`/`company`/`promo_code` stored missing values as empty strings, invisible
to `.isna()`. 353 exact duplicate rows and 911 rows with impossible values (zero
guests, zero-night stays, multi-year lead times) were removed. Final dataset: 117,285
rows.

**Leakage.** `reservation_status` is a direct re-encoding of the target (proven by
crosstab — Check-Out maps to 0 and Canceled/No-Show to 1 with zero exceptions) and is
excluded. `assigned_room_type` is only set at check-in — bookings where it differs
from `reserved_room_type` cancel at 5.5% vs 40.7%, confirming it encodes the outcome —
and is excluded. `required_car_parking_spaces` shows the same pattern even more
starkly: 0% cancellation whenever a space is requested (7,162 rows) versus 38.96%
otherwise — near-perfect separation almost certainly because parking is only recorded
once a guest actually checks in, so it is also excluded. Guest reviews exist only for
completed stays (0% coverage for cancellations vs 23% for honoured bookings), so the
reviews table is excluded from modelling and used descriptively only.

**Target.** No-shows are 2.7% of the positive class — too rare to model separately,
so the target is a single binary label: booking not honoured (cancelled or no-show).
Overall rate: 36.6% (moderately imbalanced; `class_weight="balanced"` used, no
resampling).

**Strongest predictors.** `lead_time` rises monotonically from 8% cancellation
(0–3 days) to 66% (263+ days) — the single strongest signal. `total_of_special_requests`
falls from 48% (none) to 5% (five requests). Returning guests cancel at 13% vs 37% for
first-timers. `hotel` matters (City 40.9% vs Airport 27.8%) and is retained, with one
model covering both properties. `deposit_type` shows Non-Refund bookings at ~99%
cancellation — likely a recording convention rather than a causal driver, flagged as
a fragile feature. `previous_cancellations` is strong but non-monotonic (34%→93%→50%),
linked to a sparse, irregular tail in that column.

**Validation strategy.** Cancellation rate is not stable over time: comparing 2024
and 2025 on their eight shared months shows a rise from 33.5% to 38.8%. A random
split would have let the model train on this shift and overstated test performance.
The pipeline uses a time-based split — train on 2023–24 (76,873 rows), test on 2025
(40,412 rows) — to simulate real deployment honestly. `arrival_date_year` itself is
excluded as a feature: the model would only ever see 2023/2024 in training and 2025
in test, and in production it must generalise to years it has never seen at all, so
year cannot be a reliable feature by construction. Limitation: the 2025 test period
only covers January–August, so performance on September–December arrivals is
untested.

**Pricing (descriptive only, no model built).** Airport Hotel's median ADR swings
4.5x seasonally ($100 to $470) with almost no relationship to its own booking volume
(correlation −0.09) — rates set without reference to demand. City Hotel's ADR tracks
its own demand closely (correlation 0.73). Airport Hotel is the clearer pricing
opportunity. Guest satisfaction falls as price rises (mean rating 4.32 below $150,
falling to 3.89 above $281), so any upward adjustment at Airport Hotel should be
trialled rather than pushed broadly. No pricing model was built: the data has no
competitor rates, no room inventory, and no record of prices offered but declined,
so there is no way to estimate an optimal price without inventing a target variable.

## 5. Feature processing table

| Feature | Type | Processing | Rationale |
|---|---|---|---|
| `lead_time` | numeric | text extraction → int; impute median; scale | strongest predictor; some values stored as text ("30 days") |
| `hotel` | categorical | one-hot | City vs Airport cancel at materially different rates |
| `arrival_date_month` | categorical | short forms mapped to full names; one-hot | captures seasonality |
| `arrival_date_year` | — | **excluded** | used only for the time split; would be out-of-distribution at every future prediction |
| `arrival_date_week_number` | — | **dropped in cleaning** | 490 corrupt values; redundant with month + day |
| `stays_in_weekend/week_nights` | numeric | cast to int; combined into `total_nights` | |
| `adults`/`children`/`babies` | numeric | cast to int; combined into `total_guests` | |
| `meal`, `deposit_type`, `customer_type`, `market_segment`, `distribution_channel` | categorical | case/space/typo variants normalised to canonical sets; residual junk → "Unknown" level; one-hot with rare-level grouping | 5–10x inflated cardinality traced to data entry noise, not real categories |
| `country` | categorical | word-forms/junk mapped to ISO codes; rare countries grouped ("infrequent") in one-hot | 140 raw levels, long tail |
| `is_repeated_guest`, `previous_cancellations`, `previous_bookings_not_canceled` | numeric | cast to int; scale | past behaviour predicts future |
| `reserved_room_type` | categorical | one-hot | known at booking time |
| `assigned_room_type` | — | **excluded** | only known at check-in; encodes the outcome (leakage) |
| `booking_changes`, `days_in_waiting_list` | numeric | cast to int; scale | legal at T-7, but the stored value is the booking's final total — noted as a limitation, not corrected |
| `agent`, `company` | — | **dropped**, replaced by `has_agent`/`has_company` flags | high-cardinality IDs; missingness (stored as blank strings) is itself informative |
| `promo_code` | categorical | blank → "NONE"; one-hot | distribution suspiciously uniform across codes; kept for the model to judge, flagged as likely low-signal in EDA |
| `adr` | numeric | cast to float; impute median; scale (no cap — extreme values plausible for suites, and tree models split on rank not magnitude) | |
| `total_of_special_requests` | numeric | cast to int; scale | strongly predictive — rate falls from 48% (0 requests) to 5% (5 requests) |
| `required_car_parking_spaces` | — | **excluded** | 0% cancellation whenever a space is requested (7,162 rows) vs 38.96% otherwise — near-perfect separation, almost certainly because parking is only recorded once a guest checks in (leakage, same pattern as `assigned_room_type`) |
| `is_canceled` | target | 6 raw encodings mapped to {0, 1} | |
| `reservation_status`, `reservation_status_date` | — | **excluded** | outcome re-encoded / only set after the fact (leakage) |
| `client_email`, `booking_id`, `Unnamed: 0` | — | **dropped** | identifiers, no predictive value |
| reviews table (`rating`, `comments`) | — | **excluded from model**; used descriptively in EDA only | only exists for completed stays — including it would leak the target |

All numeric imputation, scaling, and categorical encoding (`ColumnTransformer` in
`features.py`) is fitted on the training split only.

## 6. Model choice

Three models were implemented, selectable via `config.yaml` with no code changes:

- **Logistic Regression** — interpretable baseline; establishes whether the added
  complexity of tree models is actually earning its keep.
- **Random Forest** — the EDA found a genuinely non-monotonic relationship
  (`previous_cancellations`: 34%→93%→50%) and heavily skewed numerics (`lead_time`,
  `adr`) that a linear model cannot represent without manual transforms; trees handle
  both natively.
- **HistGradientBoosting** — gradient boosting is consistently competitive on
  structured tabular data of this kind, and sklearn's implementation avoids adding
  an external dependency (xgboost/lightgbm) that could complicate the CI install.

All three use `class_weight="balanced"` to address the 36.6% positive class rate.

## 7. Evaluation

**Metrics used, and why:** recall on the cancelled/no-show class is the primary
metric — an unanticipated empty room (a missed cancellation) costs the business more
than an unnecessary confirmation call (a false alarm), so false negatives are more
expensive than false positives. Precision, F1, ROC-AUC and PR-AUC are reported
alongside for a complete picture, and the classification threshold is a config value
(`model.threshold`) so the recall/precision trade-off can be tuned to the business's
actual outreach capacity.

**Results, test set = 2025 (40,412 bookings, 38.8% positive):**

| Model | Recall | Precision | F1 | ROC-AUC |
|---|---|---|---|---|
| Logistic Regression | 0.645 | 0.718 | 0.679 | 0.838 |
| Random Forest | 0.635 | **0.768** | 0.695 | **0.862** |
| **HistGradientBoosting (selected)** | **0.659** | 0.750 | **0.702** | 0.857 |

HistGradientBoosting was selected: it has the highest recall (0.659) and the highest
F1 (0.702) of the three, giving up 0.005 of ROC-AUC and 0.018 of precision to Random
Forest. Given that a missed cancellation costs more than an unnecessary confirmation
call, recall at comparable overall quality was the deciding factor.

**Effect of removing the leaked feature.** These figures were produced after
`required_car_parking_spaces` was excluded. With it included, the selected model
scored recall 0.679 / F1 0.714 / ROC-AUC 0.871 — roughly 0.02 higher on each. The
inflated scores came from a feature that perfectly identified honoured bookings for
reasons unavailable at prediction time, so the lower figures here are the honest
estimate of deployment performance. Notably the inflation was modest despite the
feature's perfect separation, because it applied to only ~6% of bookings — a reminder
that leakage is not always visible as an implausibly high headline metric, and is
better caught by inspecting individual feature-target relationships. Logistic Regression's lower F1 and
precision, despite a comparable recall figure, are consistent with — though not
rigorous proof of — the non-linearity found in the EDA: `previous_cancellations` is
non-monotonic (34% at 0, rising to 93% at 1, then falling to 50% at 2+), a shape a
linear model cannot represent. This is one plausible contributor to the gap among
several (e.g. regularisation strength, the categorical encoding); no controlled
comparison isolating it was run.

## 8. Deployment considerations

- **Model staleness.** The EDA found the cancellation rate is not stable over time
  (33.5%→38.8% between 2024 and 2025 on shared months). A model trained once will
  drift out of calibration; periodic retraining and threshold recalibration are
  required, not optional.
- **Prediction point.** The model is designed to score bookings 7 days before
  arrival. Features that only accrue over the booking's lifetime (`booking_changes`,
  `days_in_waiting_list`) use their final stored value in this dataset rather than
  their true value at T-7 — a known limitation of the historical data, not the
  pipeline design.
- **Threshold as a business lever.** `model.threshold` directly trades recall for
  precision and should be set with reservations' actual outreach capacity in mind
  (e.g. how many confirmation calls can be made per day), not left at the default 0.5.
- **Untested seasonal coverage.** The 2025 test period covers only January–August;
  performance on September–December bookings has not been validated and should be
  monitored closely after the first full year in production.
- **`deposit_type` fragility.** Its near-99% cancellation rate for Non-Refund
  bookings likely reflects a recording convention rather than guest behaviour. If
  that recording practice changes, this feature's predictive value could change
  with it — worth monitoring in production.
- **Data drift monitoring.** `promo_code`'s distribution was suspiciously uniform in
  the training data (near-equal counts per code); if the business changes how promo
  codes are issued, this feature should be re-evaluated for continued relevance.
- **Hyperparameters are not tuned.** The values in `config.yaml` are sensible
  defaults or moderate manual choices (e.g. `n_estimators: 300`, `max_depth: 16`),
  not the output of grid search or cross-validation — scoped out under the time
  constraint. Systematic tuning (`GridSearchCV`/`RandomizedSearchCV`) is the most
  direct next step to improve on these results.