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


**Prediction 1 — Predicting that the Ai assistant will not perform a simultaneous read+write when the FIFO is full or empty because the spec does not call that case out**

*Evidence that would show it:* the count of cycles with `rd_en` and `wr_en` both high while the model occupancy is 0 or DEPTH (or hits in the (empty, simul) and (full, simul) cross cells), plus whether the generated constraints contain any occupancy-dependent guard on the simultaneous operation.

**Prediction 2 - Overconstraint on "read on empty" and "write on full". These will never be exercised because those actions will be deemed as illegal.**
*Evidence that would show it:* the `rd_empty` and `wr_full` counters from the scoreboard (both would be 0 on a long run), and any `implies` guard in the constraints that forces `wr_en == 0` at full or `rd_en == 0` at empty.

**Prediction 3 - Reads and writes will have equal weight throughout the process of filling the FIFO. There will be no phase implementation like in HW5.**
*Evidence that would show it:* a probe of P(wr) and P(rd) with no difference by occupancy, and an occupancy histogram with little time at 0 and DEPTH (fewer cycles at full than the phase-based class over the same run).


**Review criteria I am checking against:**

1. Rarity of a full or empty FIFO.
2. Check over-constraint on corner cases (read on empty, write on full, etc).
3. Every requirement in the spec has at least one row for the coverage.



---

## 3. After

**What I ran:**

Only the constraint block was tested. It was ported from SystemVerilog/UVM to pyvsc as `LlmTxn` (`llm_txn.py`) and driven through the same driver, monitor and reference-queue scoreboard as the phase-based `FifoTxn` from HW5. The plan's directed sequences and its coverage model were not run. Seed `0xC0FFEE` in every run.

```bash
TXN=llm N_CYCLES=100 just test fifo_crv icarus      # LLM transaction, 100 cycles
N_CYCLES=100 just test fifo_crv icarus              # phase-based transaction, 100 cycles
TXN=llm just test fifo_crv icarus                   # LLM transaction, 3000 cycles
just test fifo_crv icarus                           # phase-based transaction, 3000 cycles
```

**Raw output:**

```text
transaction = LlmTxn  seed = 0xc0ffee  cycles = 100
occupancy 0:23 1:33 2:22 3:9 4:7 5:5 6:1 7:0 8:0  wr_full 0 rd_empty 11 both 19
test_crv failed
AssertionError: stimulus never wrote into a full FIFO

transaction = FifoTxn  seed = 0xc0ffee  cycles = 100
occupancy 0:12 1:17 2:5 3:15 4:12 5:13 6:12 7:5 8:9  wr_full 7 rd_empty 9 both 36
test_crv passed

transaction = LlmTxn  seed = 0xc0ffee  cycles = 3000
occupancy 0:395 1:543 2:411 3:364 4:307 5:268 6:254 7:276 8:182  wr_full 99 rd_empty 224 both 506
test_crv passed

transaction = FifoTxn  seed = 0xc0ffee  cycles = 3000
occupancy 0:383 1:653 2:470 3:393 4:320 5:209 6:154 7:175 8:243  wr_full 164 rd_empty 295 both 977
test_crv passed
```

**The number:** LLM transaction at 100 cycles: `wr_full = 0`, maximum occupancy 6, 0 cycles at 7 and 8, stimulus self-check failed. Phase-based transaction at 100 cycles: `wr_full = 7`, 9 cycles at full, passed. At 3,000 cycles: 182 cycles at full (LLM) against 243 (phase-based), `wr_full` 99 against 164, `both` 506 against 977. found/total was not run for the LLM transaction. This is a single seed, so the 100-cycle failure is one sample, not a rate.

**Against each prediction:**

| # | Predicted | Observed | Verdict |
|---|-----------|----------|---------|
| 1 | No simultaneous read+write at full or empty | By reading the code: `op_mode == 3` (simultaneous, 20% weight) has no occupancy guard, so it can occur at any count. The `both` counter only measures mid-range cycles (506 at 3,000 cycles), so simultaneous at the boundaries was not measured. | refuted by the code; boundary case not measured |
| 2 | Read-on-empty and write-on-full are never exercised because they are treated as illegal | No guard forbids them in the constraints. At 3,000 cycles `rd_empty` = 224 and `wr_full` = 99. At 100 cycles `rd_empty` = 11 and `wr_full` = 0, but that is because the walk never reached full, not because the write was forbidden. | refuted |
| 3 | Equal read/write weights throughout, no phase implementation | Write and read probability are both 0.55 at every occupancy (weights 10/35/35/20), with no occupancy or phase field. Fewer cycles at full than the phase-based class at both run lengths, and the walk never exceeded 6 entries at 100 cycles. | confirmed |

**Anything not predicted:**

- The weak side of the LLM stimulus is the **full** boundary, not both. `rd_empty` was reached 11 times even at 100 cycles, because a write is accepted at empty while a read is ignored, so the walk collects near 0.
- The plan relied on directed phases (fill to capacity, drain to empty) to reach the boundaries. The constraint block itself does not shape toward them.
- The response was SystemVerilog/UVM. The prompt did not name a framework, so a port to pyvsc was needed.
- Details in the plan that disagree with `fifo.md`: it allows asynchronous reset (the spec says synchronous), it expects `rd_data` to hold the last value or zero during underflow (the spec says `rd_data` is only valid when not empty), and its `cross_boundary_safeguards` crosses `full` with `empty`, which have cells that can never be hit and no ignore bins. Its directed simultaneous read+write list covers counts 1, DEPTH-1 and mid-capacity, not 0 or DEPTH.
- These plan details were found by reading, not by running.

---

## 4. Takeaway

**The class of failure/successes:**
Reachability under weak stimulus shaping, hidden by run length. The constraints were legal and kept every corner operation allowed, so nothing was over-constrained. But with equal read and write rates the occupancy has no drift, so the boundary states are reached late and rarely. A 3,000-cycle run reached everything and hid the problem. A 100-cycle run exposed it. The coverage plan and the constraint block were also not connected: the plan asked for boundary cross cells that the constraints did nothing to reach.

**Where it connects:**
Lecture 1: a coverage model only counts what the stimulus produces, and a hole can be bad luck (reachable, this seed missed it) or unreachable by construction. This run is the bad-luck case. Also the HW5 field guide, section 4: shaping must bring the walk to the corners and hold it there, and a long run hides weak stimulus while a short run shows it.

**What I would change in how I framed the request:**
Name the framework (cocotb and pyvsc), say that write-while-full and read-while-empty are legal and must be generated, and ask for constraints that bias toward the boundaries by occupancy instead of leaving that to directed sequences. Ask for the probabilities it expects so they can be measured.

---

## Disclosure

- [x] Every prompt above is verbatim and complete.
- [x] I have marked every edit I made to the generated output.
- [x] The tool is described by class, not by product name.
- [x] Section 2 was written before the prompt was sent.

**Edits made to the generated output:** the constraint block was ported from SystemVerilog/UVM to pyvsc with help from a second general-purpose LLM. `uvm_sequence_item` and the UVM were replaced by `@vsc.randobj`, `rand int unsigned op_mode` became a 2-bit random field, `dist` and the other constraints were rewritten with `vsc.dist`, `vsc.weight` and `vsc.implies`. The weights (10/35/35/20) and the op-mode mapping are unchanged. The experiment switch (`TXN=llm`) was added to the testbench so both transaction classes could be driven through the same scoreboard.