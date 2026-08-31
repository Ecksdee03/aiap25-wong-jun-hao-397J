# AIAP Technical Assessment — Decision Log

**Candidate name (as in NRIC): Wong Jun Hao**

**Email (as used in your application): jhwong03@gmail.com**

---

## A note on this document

This decision log is the primary instrument by which we understand your thinking. The questions below cover the reasoning behind your work — from how you define the problem at the start to the decisions you made during the work itself. Do answer all five questions in your own words. 

You may use AI assistance freely on the technical deliverables (the EDA and the ML pipeline), but this Decision Log itself should be written by you — it is the record of your own thinking that we cross-check against your chat history.


---


## 1. Clarifying questions

What questions would you ask to better define and narrow the problem statement? For each question, briefly explain how the answer would meaningfully change your approach. 

Note: If it helps your decision-making, you may assume and list out the stakeholders' likely answers.


**Your answer:**

1. How much does one unsold room cost versus a confirmation call, a selective deposit, or an overbooking gone wrong?
This helps clarifies on the setting of the classification threshold and whether to justify prioritising recall over precision with numbers.

2. What's the capacity in terms of number of reservation calls we can take a day? Is overbooking allowed?
If capacity is ~N calls/day, the metric becomes precision rather than recall, and the threshold gets set to flag ~N bookings.

3. Is previous_cancellations computed from history before that booking or only over the dataset given from 2023-2025? These can help to inform whether they are more leakage vectors.

4. Is a no-show the same problem as a cancellation?
This helps to determines whether to check one binary target vs two classes. From the data, no-shows are 2.7% of positives, so I combined both — but the question was what got me to check.


---

## 2. Defining the Problem Statement

Restate, in your own words, the refined problem you decided to solve. List your key assumptions. Briefly note what other framings you considered, and what you deliberately left out or scoped down, and why.


**Your answer:**

Problem statement: 
Predict, 7 days before arrival, the probability that a confirmed booking will not be honoured (cancelled or no-show). Alongside this, use descriptive analysis of pricing to flag where rates look mis-set.

Assume: We only have this dataset to work with. We know nothing else about the business other than what was given in the extract, 2023–25 booking behaviour is broadly representative of the near future; is_canceled is accurately recorded.

Framing rejected and what's scoped out — dynamic pricing. Because no other basis to base on from the given dataset, no competitor rates to reference against, no room inventory data etc.

Left out: NLP on review comments, hyperparameter tuning - due to time constraints.


---

## 3. Key decisions during Solution Development

Walk through three key decisions you made during Solution Development. For each: what options did you consider, what did you choose, and why? These can be technical (modelling choices, feature handling, evaluation metrics) or about the work itself (what to prioritise, what to drop, how to spend your time).


**Your answer:**

1. Time-based split over random split i.e. training on 2023-2024 data and predicting on 2025 data. Because overall cancellation rate is not consistent. On the eight months that 2024 and 2025 share, cancellation rose from 33.5% to 38.8%. A random 80/20 split puts all years together, and it would have put ~80% of 2025 in training, letting the model absorb the higher rate and overstating deployment performance. 

Accepted limitation: 2025 covers only Jan–Aug, so Sep–Dec performance is untested. 

2. Prioritising a working pipeline over an ambitious one, such as not having hyperparameter tuning, no second model for pricing. 

The rationale is that a failing run.sh and a poorly structured README are explicit penalties, and additional time spent on these is not worth the potential loss of marks due to time constraints.

3. Leakage audits.
Excluding columns like assigned_room_type from the prediction models. Because a room is only assigned for a guest who arrived so including it would confound the model. 

Another example is reservation_status - which s a direct re-encoding of the target (proven by crosstab — Check-Out maps to 0 and Canceled/No-Show to 1 with zero exceptions)


---

## 4. Use of the AI assistant

Where did you use the AI assistant in this work? Give three specific examples of something the assistant suggested that you changed, rejected, or significantly modified — and explain your reasoning.


**Your answer:**

I used it throughout the entire assessment - from the brainstorming to the EDA to the modelling and evaluation.

a. I rejected the adr > 1000 and adults > 10 drop rules. I figured Singapore suites can legitimately cost over $1,000/night, especially for group tourist bookings.

b. I caught an unverified claim about required_car_parking_spaces. The AI had listed it as a strong predictor in the README feature table. I challenged it, ran the groupby, and the result showed it was leakage — which changed the pipeline (excluding it from the features instead), the README, and the final mmodel metrics.

c. I rejected an over-engineered EDA cell. The AI wrote the outlier checks as dictionary of rules looped over in a for-loop initially, I pointed out it was clearer and more organised for them to be plain sequential filters for each column instead, even if the code might be longer.


---

## 5. Next Steps

If you had one more week to continue this project, what would you do next, and why? What signals from your current work make those the right next steps?


**Your answer:**

1. Hyperparameter tuning e.g. GridSearchCV/RandomizedSearchCV. The signal is because the current values and thresholds used are defaults but never optimised, and this is one of the cheapest remaining gains.
I would retrain the model many times with different values and keep whichever combination scores best on validation data, to refit the model.

2. Validate Sep–Dec performance. The signal is that the current test period covers only Jan–Aug 2025.


---