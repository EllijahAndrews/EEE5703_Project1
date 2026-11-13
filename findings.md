# FINDINGS — <Project 1> · <Lona, Lakshmi, Ellijah, Hailey>


> The number is the start of the argument, not the end of it. This file is
> where you say what the number means and what it does not cover.


## Score


| Pool | found | total | % |
|------|------:|------:|--:|
| released (practice) | 8 | 8 | 100% |
| hidden (reported at grading) | | | |


**Command run: just test fifo_crv, just mutate fifo_crv**


```
51382.01ns INFO     cocotb.regression                  test_burst_random_regression passed
 51382.01ns INFO     cocotb.regression                  ***************************************************************************************************
                                                        ** TEST                                       STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        ***************************************************************************************************
                                                        ** test_fifo.test_smoke                        PASS          81.00           0.00      17932.17  **
                                                        ** test_fifo.test_fifo_layered                 PASS         111.00           0.01      14543.67  **
                                                        ** test_fifo.test_fill_to_full                 PASS         121.00           0.01      15511.80  **
                                                        ** test_fifo.test_write_while_full             PASS         131.00           0.01      14979.77  **
                                                        ** test_fifo.test_read_while_empty             PASS          51.00           0.00      22536.21  **
                                                        ** test_fifo.test_simultaneous_read_write      PASS          91.00           0.01      16772.24  **
                                                        ** test_fifo.test_pointer_wraparound           PASS         281.00           0.02      13742.40  **
                                                        ** test_fifo.test_random_interleave            PASS        5041.00           0.47      10821.88  **
                                                        ** test_fifo.test_reset_while_partially_full   PASS         191.00           0.01      15005.83  **
                                                        ** test_fifo.test_seeded_random_regression     PASS       10041.00          10.24        980.93  **
                                                        ** test_fifo.test_multi_seed_regression        PASS       25201.00          26.24        960.35  **
                                                        ** test_fifo.test_burst_random_regression      PASS       10041.00           0.96      10420.85  **
                                                        ***************************************************************************************************
                                                        ** TESTS=12 PASS=12 FAIL=0 SKIP=0                         51382.01          41.00       1253.32  **
                                                        ***************************************************************************************************


[baseline] running clean fifo.sv through fifo_crv ...
  clean RTL: 12 tests passed.


  [found  ] full_offbyone        (test-failed)  -- full asserts one entry too early (cnt == DEPTH-1)
  [found  ] empty_offbyone       (test-failed)  -- empty asserts one entry too early (cnt == 1)
  [found  ] ignore_full          (test-failed)  -- writes are accepted even when full (overflow)
  [found  ] ignore_empty         (test-failed)  -- reads are accepted even when empty (underflow)
  [found  ] count_wr_dec         (test-failed)  -- a write-only cycle decrements the count
  [found  ] rd_data_wrptr        (test-failed)  -- rd_data reads from the write pointer instead of the read pointer
  [found  ] mem_corrupt          (test-failed)  -- stored data is corrupted (+1) on write
  [found  ] wrptr_wrap_early     (test-failed)  -- write pointer wraps one slot early


==== found/total = 8/8  =  100.0%  (threshold 90%) ====


Note: Coverage Report provided in Final Report
```


## Survivors


One row per mutant your suite did not find. `Reachable?` is the important
column: a survivor you never reached is a *stimulus* problem, a survivor you reached but did not notice is a *checking* problem, and they have different fixes.


No survivors, our suite was able to find and catch all released mutants. Further analysis provided in the final report. 


## What I changed, and what it bought


| Change | Score before | Score after | Which survivors it caught |
|--------|-------------:|------------:|---------------------------|
|Write when full | 4/8 | 6/8 | full_offbyone, wrptr_wrap_early|
|Read while empty | 6/8 | 7/8 | ignore_full |
|Simultaneous read write| 7/8 | 8/8 | ignore_empty |




## Residual risk


What this suite still cannot catch, stated plainly. Name a fault class, not a mutant id — the pool is a sample, not the population.


Reset during wraparounds/boundary cases – ex, if a boundary case triggers incorrect reset behavior. This is a controllability miss. The fault is only exposed if a test drives the design into a specific state (pointer at the wrap boundary, FIFO exactly full or empty) and then asserts reset at that moment. 
Forcing a Write/Read Op during a Reset. Write/read during a reset state is never ignored, which may affect reset behavior. This is also a controllability miss. The suite never applies stimulus (a write or read request) while reset is asserted, so the “ignored during reset” behavior is never exercised. There’s also a small observability concern - we would also need a check to ensure that nothing happened. For example, after reset releases, we could confirm the pointers, count, and flags are at their reset values and that the read data or the next read returns nothing from the “ignored” write. If your checkers only compare outputs during normal operation, a leaked write could be missed by the test suite.




**If I had another day:** We would add a full reset test to run reset during wraparounds, boundary cases, and during reads/writes to fully cover the reset functionality. Our coverage currently is lacking in this area only, resulting in a 94.05% coverage of the dut.
