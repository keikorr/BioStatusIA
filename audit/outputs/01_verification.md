# 01 - Numerical verification of published values

Checked quantities: 112 | PASS: 107 | MISMATCH: 4 | not comparable: 1

## Mismatches

| table | dataset | quantity | published | recomputed | note |
|---|---|---|---|---|---|
| I | 08 Parkinson's | sensitivity (test) | 0.965 | 0.965517 |  |
| text II-F | 05 Brain tumor (4c) | macro recall (4 d.p., v1 text) | 0.9008 | 0.900694 | v1 value equals the mean of per-class recalls rounded to 3 d.p. (0.9007); exact value from counts is 0.9007 |
| I | 07 Heart (5c) | macro recall (3 d.p., report) | 0.222 | 0.222511 |  |
| text II-F | 07 Heart (5c) | macro recall (4 d.p., v1 text) | 0.2226 | 0.222511 | v1 value equals the mean of per-class recalls rounded to 3 d.p. (0.2226); exact value from counts is 0.2225 |

## Share of end-to-end time inside the timed crew call

- run 01 (tabular): 0.519
- run 02 (image): 0.966
- run 03 (tabular): 0.103
- run 04 (tabular): 0.256
- run 05 (image): 0.975
- run 06 (image): 0.992
- run 07 (tabular): 0.576
- run 08 (tabular): 0.547
