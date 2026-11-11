# Check the Machine — ai_log.md

**Name: Ellijah, Lakshmi, Hailey, Lona**
**Section: EEE 5703**
**Week: Project 1**
**Autonomy tier: self-directed**
**Assistant used: a general-purpose LLM**

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

LLM Response:

Verification Plan: Synchronous FWFT FIFO
Target DUT: dut/fifo.sv | Author: Verification Engineering
1. ARCHITECTURE & VERIFICATION STRATEGY
This document establishes a complete verification specification for the parameterized synchronous First-Word
Fall-Through (FWFT) FIFO. The testbench framework utilizes a shadow reference model implemented via a
std::queue within an interactive scoreboard environment.
    DUT Parameters: WIDTH (default 8), DEPTH (default 8).
    FWFT Check Rule: Data output rd_data continuously reflects shadow queue head queue[0] whenever !empty.
    Flag Checks: empty == (queue.size() == 0), full == (queue.size() == DEPTH), and count == queue.size() verified on every active clock edge.
2. FUNCTIONAL COVERAGE MODEL (FIFO_COVERGROUP)
covergroup fifo_covergroup @(posedge clk disable iff (!rst_n));
    // Single Signals
    cp_wr_en: coverpoint wr_en { bins disabled = {0}; bins enabled = {1}; }
    cp_rd_en: coverpoint rd_en { bins disabled = {0}; bins enabled = {1}; }
    cp_full:  coverpoint full  { bins not_full  = {0}; bins is_full = {1}; }
    cp_empty: coverpoint empty { bins not_empty = {0}; bins is_empty = {1}; }
    // Occupancy Tracking
    cp_count: coverpoint count {
    bins empty_state = {0};
    bins one_entry   = {1};
    bins mid_range   = {[2 : DEPTH-2]};
    bins full_minus1 = {DEPTH-1};
    bins max_full    = {DEPTH};
}

// Crosses
cross_wr_full:  cross cp_wr_en, cp_full { bins wr_when_full = binsof(cp_wr_en.enabled) && 
binsof(cp_full.is_full); }
cross_rd_empty: cross cp_rd_en, cp_empty { bins rd_when_empty = binsof(cp_rd_en.enabled) 
&& binsof(cp_empty.is_empty); }
cross_count_op: cross cp_count, cp_wr_en, cp_rd_en;
endgroup

3. TRANSACTION CONSTRAINTS (FIFO_TRANSACTION.SV)
class fifo_transaction #(parameter WIDTH = 8) extends uvm_sequence_item;
  rand bit              wr_en;
  rand bit              rd_en;
  rand bit [WIDTH-1:0]  wr_data;
  typedef enum { NOP, WRITE_ONLY, READ_ONLY, SIMULTANEOUS } op_mode_e;
  rand op_mode_e op_mode;
  constraint c_op_weights {
    op_mode dist { NOP :/ 10, WRITE_ONLY :/ 35, READ_ONLY :/ 35, SIMULTANEOUS :/ 20 };
  }
  constraint c_signal_mapping {
    (op_mode == NOP)          -> { wr_en == 0; rd_en == 0; }
    (op_mode == WRITE_ONLY)   -> { wr_en == 1; rd_en == 0; }
    (op_mode == READ_ONLY)    -> { wr_en == 0; rd_en == 1; }
    (op_mode == SIMULTANEOUS) -> { wr_en == 1; rd_en == 1; }
  }
endclass

4. TEST SCENARIO CHECKLIST & CORNER CASES
Test Scenario             Stimulus Sequence                             Pass Criterion
Reset Verification        Assert rst_n=0 mid-transaction.               count=0, empty=1, full=0 on next edge.
Write-while-Full          Drive wr_en=1 when count == DEPTH.            Write dropped, no count change or memory corruption.
Read-while-Empty          Drive rd_en=1 when count == 0.                Read ignored, no underflow occurs.
Simultaneous R+W          Assert wr_en=1 and rd_en=1 simultaneously     Data popped/pushed on same edge; count unchanged.
Pointer Wrap-around       Run continuous interleaved operations for     No data corruption or pointer misalignments observed.
                          > 2×DEPTH cycles.
                                                

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
| 2 | overconstraint on boundaries (wr on FUll, rd on empty) | wr on FULL | refuted  |
| 3 | Reads and writes will have equal weight | The code generated by the ai assistant has wr_en and read_en both at 35% weidht. | confirmed


**Anything I did not predict:**

Something I didn't predict was how often the FIFO is filled being affected due to not having a kind of "phase" like in HW5. In HW5 the FIFO could walk towards being full or empty with the DRAIN/FILL design. 

---
## 4. Takeaway

**The class of failure (or of success):**
Constraint set failure 

**Where it connects:**
This connects to week 5 of our lectures where we learn to properly set constraints to test our edge cases thoroughly. 

**What I would change in how I framed the request:**
To lessen the upfront code conversion, the specific environemnt (cocotb, etc) that is being worked in should be given. Give our own feature list that gives the tool more direction on how to write the testbench.

---

## Disclosure

- [x] Every prompt above is verbatim and complete.
- [x] I have marked every edit I made to the generated output.
- [x] The tool is described by class, not by product name.
- [x] Section 2 was written before the prompt was sent.



