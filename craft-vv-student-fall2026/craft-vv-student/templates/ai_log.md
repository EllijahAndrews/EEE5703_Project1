# Check the Machine — ai_log.md

**Name: Ellijah, Lakshmi, Hailey, Ilona**
**Section:EEE 5703**
**Week: Project 1**
**Autonomy tier:self-directed**
**Assistant used:a general-purpose LLM**

---

## 1. Task
**Prompt (verbatim): Here is the specification for a FIFO. Write a verification plan for it: coverage model (coverpoints and the crosses worth measuring), and a block of constraints. Make the plan complete enough that a second engineer could implement it without asking you anything.**

---

## 2. Before


**Prediction 1 — Predicting that the AI assistant will not perform a simultaneous read+write when the FIFO is full or empty because the spec does not call that case out**

*Evidence that would show it: wr_en and rd_en signals will not be high when count is at DEPTH or 0.

**Prediction 2 - Overconstraint on "read on empty" and "write on full". These will never be exercised because those actions will be deemed as illegal.** 
*Evidence that would show it:* wr_en will not be high when count is at DEPTH. rd_en will not be high when count is at  0.

**Prediction 3 - Reads and writes will have equal weight throughout the process of filling the FIFO. There will be no phase implementation like in HW5.** Equal weighted probablility for reads and writes at each value of count or the lack of any weight would be valid evidence that a type of "phase" is not implemented. 


**Review criteria I am checking against:**

1. Rarity of a full or empty FIFO.
2. Check over-constraint on corner cases (read on empty, write on full, etc).
3. Every requirement in the spec has at least one row for the coverage.


**What was edited: Constraint block ported from SystemVerilog/UVM to pyvsc with help from a second general-purpose LLM; I changed uvm_sequence_item to @vsc.randobj, rand int to a 2-bit field, and dropped the redundant bounds constraint.**
---

## 3. After



**What I ran:**

```bash

TXN=llm just test fifo_crv icarus                   # LLM transaction, 3000 cycles
just test fifo_crv icarus                           # phase-based transaction, 3000 cycles


TXN=llm N_CYCLES=3000 just mutate fifo_crv
just mutate fifo_crv
```

**Raw output:**

```text
All tested on the same seed to compare CTM against HW5.


--------3000 Cycle llmTXN--------
TXN=llm just test fifo_crv icarus 
LlmTxn  seed = 0xc0ffee  cycles = 3000
occupancy 0:395 1:543 2:411 3:364 4:307 5:268 6:254 7:276 8:182  wr_full 99 rd_empty 224 both 506
test_crv passed

just test fifo_crv icarus   
------3000 Cycle HW5 benchmark------ 
FifoTxn  seed = 0xc0ffee  cycles = 3000
occupancy 0:383 1:653 2:470 3:393 4:320 5:209 6:154 7:175 8:243  wr_full 164 rd_empty 295 both 977
test_crv passed'



TXN=llm N_CYCLES=3000 just mutate fifo_crv
8/8 Mutants found

just mutate fifo_crv
8/8 mutants found

```

**The number:** Found 8/8, coverage %, vacuity verdict, sby result, lint count>

**Against each prediction:**

| # | Predicted | Observed | Verdict |
|---|-----------|----------|---------|
| 1 | No simultaneous wr + rd | wr_en happens on a Full FIFO|  refuted |
| 2 | overconstraint on boundaries (wr on FUll, rd on empty) | wr on FULL  ![alt text](image.png)    | refuted  |


**Anything I did not predict:**

---
## 4. Takeaway

<!-- Name the CLASS of failure, not this instance, and connect it to a course
     concept. Then one sentence on your own framing. If the machine was right,
     say so plainly — you are graded on the verification, never on finding a
     failure. -->

**The class of failure (or of success):**

**Where it connects:**

**What I would change in how I framed the request:**

---

## Disclosure

- [ ] Every prompt above is verbatim and complete.
- [ ] I have marked every edit I made to the generated output.
- [ ] The tool is described by class, not by product name.
- [ ] Section 2 was written before the prompt was sent.
