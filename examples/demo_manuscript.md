# A demonstration manuscript with planted defects

**Authors:** A. Example, B. Demo

**Affiliations:** Institute of Reproducible Examples

**Correspondence:** demo@example.org

---

## Abstract

**Background.** Composite scores are widely used in translational research, and many of them are reported to be prognostic.

**Results.** We built a composite score from twelve genes and tested it in two cohorts. The score was associated with overall survival in both. The effect was stable across subgroups. The effect was stable across subgroups.

**Conclusions.** The score may be useful, but the controls we report suggest caution.

**Keywords:** benchmarking; composite scores; reproducibility

---

## Background

Composite scores are widely used in translational research. They are easy to build and easy to report. They are also easy to get wrong.

Prior work has shown that many published scores do not replicate in independent cohorts. This is a well-known problem. It has been described repeatedly in the methodological literature, and there are now several reporting guidelines that address it.

What remains unclear is how much of this unreliability comes from the score itself, and how much comes from the way the comparison is set up. We therefore set out to separate these two sources of error.

We took three claims of the kind routinely published and repeated each analysis with a matched control. The analyses are described below.

## Methods

### Data

We used two public cohorts. Cohort A contained 412 patients, and cohort B contained 268 patients. Both cohorts were downloaded from a public repository (accession DEMO1234).

### Score construction

The composite score was defined as the mean z-score of twelve genes chosen by variance. We computed the score in both cohorts and standardised it within cohort.

### Statistics

Cox proportional hazards models were fitted with the score as a continuous variable. We report hazard ratios per standard deviation. We therefore repeated every model with and without adjustment for age and sex, and we therefore repeated the stratified analysis in each cohort separately.

### Software

All analyses were run in Python 3.11. The code is available on request.

## Results

### Claim 1: the score is prognostic

The score was associated with overall survival in cohort A (HR 1.31 per SD, 95% CI 1.12–1.53, P = 0.0007). The association was also present in cohort B (HR 1.22, 1.02–1.46, P = 0.03). The score was significantly associated with outcome in both cohorts, and it remained significant after adjustment for age and sex, and it also remained significant when the analysis was restricted to patients with complete data, and it remained significant in a sensitivity analysis that excluded the first year of follow-up.

### Claim 2: the score adds to stage

The score was associated with outcome after adjustment for stage. This suggests the score may capture information beyond stage. The score may capture information beyond stage.

We compared the model with and without the score (Fig. 3A). The improvement was small.

### Claim 3: the score is specific

We compared the score against random gene sets of the same size (Fig. 1B). The score performed better than most random sets. The proportion of random sets that matched the score was 4.2%.

In a second analysis we repeated the comparison with a different penalty, and the proportion of random sets that matched the score was 6.1%.

The PFS analysis gave a similar picture. We repeated the PFS analysis with a stricter definition, and the PFS result was unchanged.

## Discussion

We set out to test whether a composite score built from variance-selected genes carries information beyond standard clinical variables. The answer appears to be yes, with qualifications.

The score was associated with survival in both cohorts. The effect size was modest. The confidence intervals were wide in cohort B, which reflects its smaller size.

Our findings are consistent with prior work on composite scores. They also illustrate why matched controls matter, and they suggest that the proportion of random gene sets matching a score is a useful summary of specificity.

There are limitations. The cohorts are retrospective. The score was built and tested in the same data types. The follow-up differs between cohorts. Validation in prospective cohorts will be needed.

## Conclusions

The composite score is associated with survival in two cohorts, but its incremental value over stage is small and its specificity depends on how the comparison is defined.

## Declarations

**Ethics approval.** Not applicable.

**Competing interests.** None declared.

**Abbreviations.** PFS, progression-free survival; HR, hazard ratio; SD, standard deviation.

## Figure legends

**Fig. 1.** Overview of the analysis. (A) Study design. (B) Comparison against random gene sets.

**Fig. 2.** Survival by score tertile in cohort A.

**Fig. 3.** Incremental value over stage. (A) Likelihood ratio test. (B) Calibration.
