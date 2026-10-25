# Verification plan — <Synchronous FIFO>


**Authors: Elijah, Lakshmi, Lona, Hailey** **Spec version: 1.0** **Date:10/18/26**


## 1. Scope


**In scope:** <what this plan claims to verify> Follows a layered constrained-random environment. 


Verifies all behaviour listed in spec for synchronous FIFO, including reset, writes, reads, flags, ordering operations, and all possible corner cases within a constrained random environment.


**Out of scope:** <what it does not — say so plainly; this is not a weakness>


This plan is only able to look at inputs and outputs and verify them against a golden model. It is not able to view the internal DUT and assess what goes on in memory. For example, an ordering issue in memory that does not affect the outputs may be missed by this plan.


**Assumptions about the environment:** WIDTH and DEPTH of FIFO is 8, rd_en, wr_en, wr_data, perform their expected read and write operations. Ordering is strictly FIFO, synchronous First Word Fall Through (FWFT).
(Add Assumptions)




## 2. Feature list


One row per behavior the spec requires. `Req` cites a line or section of the
spec — if you cannot cite one, that is a spec gap and it belongs in section 5.


| ID | Feature | Req | Priority | How it is verified |
|----|---------|-----|----------|--------------------|
| F1 | While reset is 0, the FIFO should empty on the next clock edge       |  Line 21  | H  | directed |
| F2 | When a wr_en pin is high, and the FIFO is not full, data is asserted into the FIFO | Line 22  |  H   | directed |
| F3 | When rd_en is asserted and the FIFO is not empty, a read occurs. | Line 24 | H  | directed |
| F4 | A read and write will occur when both a wr_en and rd_en are asserted while the FIFO is not full or empty on the same clock edge and count will be unchanged. | Line 26 | H | directed |
| F5 | When rd_en is asserted and the FIFO is empty, read is ignored. | Line 24 | M | asserted |
| F6 | A FULL flag should be asserted when the FIFO is full. Always checked. | Line 28 | H | asserted |
| F7 | An EMPTY flag should be asserted when the FIFO is empty. Always checked. | Line 28 | H | asserted |
| F8 | First-in, First-out ordering. | Line 29 | H | asserted |
| F9 | Width of 8 bits, design only accepts data of 8 bits long | Line 6 | H | CRV |
| F10 | Depth of 8 words, design can only accept 8 entries. | Line 7 | H | CRV |
| F11 | “Count” as a current occupancy tracker to trip flags | Line 18, 21, 28 | H | directed
| F12 | Rising-edge clock that keeps the design synchronous and first-word fall-through | Line 12, 3 | H | assertion/formal |




## 3. Coverage model


Coverpoints and their bins. A cross earns its place only if the interaction is where a bug would hide — say which bug.


| ID | Coverpoint | Bins | Why these bins |
|----|-----------|------|----------------|
| C1 |  Assert reset within all states of FIFO; empty, full, partially filled | rst_n | Ensure reset works in every state. |     
| C2 | Assert write when FIFO is full, empty, not-empty. Use random, constrained data to generate input. | wr_en, wr_data|  Ensure write works in every state, including max-width input.  |
| C3 | Assert read when FIFO is full, empty, not-empty. |rd_en, rd_data | Ensure read works in each state (full, empty, not-empty) |
| C4 | Assert read/write at the same time when FIFO is neither full nor empty | rd_en, wr_en, count | Ensure count does not move and the clock remains synchronous. |
| C5 | Write will not force data wider than 8 bits into the FIFO | WIDTH=8, DEPTH=8  | Ensure writing to a full FIFO does not change the width or depth limits |
| C6 | The design flags EMPTY when there is no data (0, not indeterminate)| empty = 1 | Ensure FIFO depth of 0 trips output flag, important for boundary operations and reading when empty |
| C7 | The design trips FULL when it has 8 entries | full  = 1 |  Ensure FIFO depth of 8 trips output flag, important for boundary operations and writing when full |
| C8 | The FIFO is filled in the order that wr_en is written, and FIFO is emptied in the same order by rd_en | wr_en, rd_en | Ensure data is read from queue in the order it is written |
| C9 | Count progresses synchronously with each write (add) and read (subtract), except for on a synchronous read/write | count = depth | depth is the maximum length that count should be. |
| C10 | Writing while full will result in dropped words | wr_en, wr_data | Ensure that writing when full does not go past Full Flag boundary.|
| C11 | Read while empty is ignored by the design | rd_en, rd_data | Ensure prevention of underflow conditions |
| C12 | Boundary cases do not perturb the ordering and will either wrap-around or drop | DEPTH, WIDTH, COUNT | Check to make sure that ordering is preserved with cases that result in driving past Depth |
| C13 | Random input still results in the correct ordering | wr_en, rd_en, random.seed(), rd_data, wr_data | Confirming correct ordering of the FIFO when adding in random inputs |
| C14 | Dynamic flag behaviour | empty = 0, full = 1; empty = 1, full =, 0 | Both flags change states when depth = 0 and depth = 8 respectively. Neither flag can be tripped while the other is in a state of 1. Ensures the design is actually catching empty/full cases. |




**Crosses**


| ID | Cross | The interaction it is aimed at |
|----|-------|-------------------------------|
| X1 |  C8 x C9 x C13 | The FIFO keeps its ordering no matter the amount of reads/writes | Order/memory errors that can occur without observance | 
| X2 | C2 x C3 x C4 x C9 x C10 x C11 | Reading and writing from the FIFO maintains ordering, and behaves properly with R/W sequences, and full/empty FIFOs. |
| X3 | C12 x C13 | Ordering is preserved during random cases and boundaries. |
| X4 | C14 X C5 x C6 x C7 | Full and empty states are properly caught, and flagged. |


**Illegal / ignore bins:** <what is excluded and on what authority in the spec> 
Read on empty asserts correctly- the spec states that the assertion is ignored. This means indeterminate states (invalid read header) may not be acknowledged, causing memory errors.


## 4. Test matrix


Every feature maps to at least one test; every test traces back to a feature.
An untraceable test is a test nobody can defend.


| Test | Features | Kind | Pass criterion |
|------|----------|------|----------------|
| Assert reset during empty | F1 | directed | FIFO does not change, clock remains synchronous |
| Assert reset during full | F1, F12 | directed | FIFO count/depth goes to 0, clock remains synchronous, ordering after a reset remains FIFO
| Assert reset when !empty and !full | F1 | directed | FIFO count/depth goes to 0, clock remains synchronous, ordering after a reset remains FIFO
| Write words of random width to the FIFO | F2, F8, F9 | directed | Words larger than WIDTH do not get shoved in, no illegal entries are pushed through.
| Write words when full = 1 | F2, F11 | directed | When full, a write is dropped and the ordering does not change. 
| Write words when empty = 0 and full = 0 | F2, F11 | directed | This should be a successful write with no drops and no corruption.
| Read when empty = 1 | F4, F5, F11 | directed | The read is ignored.
| Read when full = 1 | F3, F11 | directed | The count of the FIFO decreases and the full flag goes to 0.
| Read when full = 0, empty = 0 | F3, F11 | directed | Count should decrease, read order should be successful.
| Multiple writes followed by multiple reads | F2, F3, F4, F5, F8 | directed | FIFO ordering stays in tact, no count change for simultaneous reads/writes.
| Simultaneous read/write on boundary lines | F4, F11 | directed | read will not occur on empty, write will not occur on full, the count will change.
| Write to full | F2, F6, F8,F10, F11 | directed/asserted | FULL flag will trip, new words will be dropped, old data will not be corrupted.
| Read to empty | F3, F7, F8, F11 | directed/asserted | Ordering will be respected, empty flag will trip, further reads will be ignored.
| Many random writes | F2, F8, F11 | directed | Ordering is respected, full flags trip
| Many random writes + reads | F2, F3, F8, F11 | directed/asserted | Respective flags are tripped, ordering is respected.




## 5. Risk and spec ambiguity


| # | Ambiguity or risk | Where in the spec | How I resolved it | Residual |
|---|-------------------|-------------------|-------------------|----------|
| 1 | When read + write are simultaneous (including a full/empty FIFO), they both happen – but what happens to the data? Is a slot freed and overwritten, or is the write value dropped? | Behavior #4/Spec Gap| Tested both | Assumption that feature 4 is correctly implemented |
| 2 |Ordering of read + write during simultaneous read/writes. Which operation happens first? | Behavior #4| Tested both | Assume that read is commanded before write |
| 3 | After write into empty FIFO, when does rd_data show the new value?| Behavior #3| Feed in input data values, to evaluate and check read and write operations | Assume it shows on the next clock cycle, if every op takes 1.|  
| 4 | Reset behavior: Does reset override simultaneous read/write requests, and what happens to data during reset? | Behavior #1 | Trigger a reset after it has been used or partially filled and verify its behavior | Assume that it performs reset as expected, and clears the pointers |




## 6. Closure criteria


State the numbers *before* you start, so closure is a measurement and not a
negotiation.


- Functional coverage target: **90%** of the model in section 3
- Mutation target: **18/20** on the hidden pool 
- Assertions: every property paired with a passing `cover` (no vacuous passes)
- What I will report as **not verified**: When read + write are simultaneous, they both happen – but what happens to the data?, Ordering of read + write during simultaneous read/writes. Which operation happens first?, After write into empty FIFO, when does rd_data show the new value?, Reset behavior: Does reset override simultaneous read/write requests?, and what happens to data during reset?



