#Combined contents of fifotransaction.py, randomregression.py, and fifocoverage.py

import vsc

FIFO_DEPTH = 8
FIFO_WIDTH = 8

@vsc.randobj
class FifoTransaction:

    def __init__(self):

        #Random stimulus.
        self.wr_en   = vsc.rand_bit_t(1)
        self.rd_en   = vsc.rand_bit_t(1)
        self.wr_data = vsc.rand_bit_t(FIFO_WIDTH)

        #Current occupancy, provided at test.
        self.count   = vsc.rand_uint8_t()

    #No illegal fifo depth entries. Constrain stimulus to FIFO restrictions.
    @vsc.constraint
    def occupancy_c(self):
        self.count <= FIFO_DEPTH

    #No illegal transactions. Constrain operational codes
    #It would be useless to generate stimulus that gets ignored anyhow. Skip these and focus on more usefull stimuli.
    @vsc.constraint
    def legal_ops_c(self):

        with vsc.if_then(self.count == 0):
            #Empty FIFO
            self.rd_en == 0

        with vsc.if_then(self.count == FIFO_DEPTH):
            #Full FIFO
            self.wr_en == 0

    #Skew read/write frequency to avoid useless scenarios or equal rd/wr distribution.
    @vsc.constraint
    def operation_dist_c(self):

        #Write frequency
        vsc.dist(self.wr_en, [
            vsc.weight(1, 40),
            vsc.weight(0, 60)
        ])

        #Read frequency
        vsc.dist(self.rd_en, [
            vsc.weight(1, 40),
            vsc.weight(0, 60)
        ])

    #Occupancy stressing to avoid equal distribution of stimulus. Test boundaries, oversample, and provide coverage to corner cases.
    @vsc.constraint
    def occupancy_dist_c(self):

        vsc.dist(self.count, [

            #Empty
            vsc.weight(0, 15),

            #Near empty
            vsc.weight((1,2), 25),

            #Middle
            vsc.weight((3,5), 20),

            #Near full
            vsc.weight((6,7), 25),

            #Full
            vsc.weight(8, 15)
        ])

    #Encourage simultaneous read + write.
    @vsc.constraint
    def simultaneous_rw_c(self):

        #FIFO cannot be FULL or EMPTY
        with vsc.if_then((self.count > 0) &
                         (self.count < FIFO_DEPTH)):
            
            vsc.dist(self.wr_en, [
                vsc.weight(1, 60),
                vsc.weight(0, 40)
            ])

            vsc.dist(self.rd_en, [
                vsc.weight(1, 60),
                vsc.weight(0, 40)
            ])

@vsc.covergroup
class FifoCoverage(object):
    def __init__(self):
        # Values passed to sample(), in this order
        self.with_sample(dict(
            count=vsc.uint8_t(),   # PRE-edge occupancy
            wr_en=vsc.bit_t(1),
            rd_en=vsc.bit_t(1),
            rst_n=vsc.bit_t(1),
        ))

        # Occupancy: one bin per level (fills the occupancy table, C9/C12)
        self.cp_occ = vsc.coverpoint(
            self.count,
            bins={f"occ_{i}": vsc.bin(i) for i in range(FIFO_DEPTH + 1)}
        )

        # FIFO state: empty / mid / full (C2, C3, C6, C7)
        self.cp_state = vsc.coverpoint(
            self.count,
            bins=dict(
                empty=vsc.bin(0),
                mid=vsc.bin([1, FIFO_DEPTH - 1]),
                full=vsc.bin(FIFO_DEPTH),
            )
        )

        self.cp_wr = vsc.coverpoint(self.wr_en, bins=dict(off=vsc.bin(0), on=vsc.bin(1)))
        self.cp_rd = vsc.coverpoint(self.rd_en, bins=dict(off=vsc.bin(0), on=vsc.bin(1)))
        self.cp_rst = vsc.coverpoint(self.rst_n, bins=dict(asserted=vsc.bin(0), released=vsc.bin(1)))

        # X2 / section 8: op x state. 2x2x3 = 12 bins, including the
        # undefined/illegal combos (rd+wr at empty, rd+wr at full, wr at full, rd at empty)
        self.cross_op_state = vsc.cross([self.cp_wr, self.cp_rd, self.cp_state])

        # C1 / section 8: reset asserted in each state, with and without traffic
        self.cross_rst_state = vsc.cross([self.cp_rst, self.cp_state, self.cp_wr, self.cp_rd])

fifo_cov = FifoCoverage()

#Burst helper function.
class BurstDriver:

    def __init__(self):
        self.burst_remaining = 0
        self.burst_mode = "idle"

    def next_burst(self, occupancy):

        #Select a new burst when the previous one finishes
        if self.burst_remaining == 0:

            self.burst_mode = random.choice([
                "write",
                "read",
                "rw",
                "idle"
            ])

            self.burst_remaining = random.randint(2, 8)

        self.burst_remaining -= 1

        #Generate operations based on burst mode
        if self.burst_mode == "write":
            wr_en = 1
            rd_en = 0

        elif self.burst_mode == "read":
            wr_en = 0
            rd_en = 1

        elif self.burst_mode == "rw":
            wr_en = 1
            rd_en = 1

        else:
            wr_en = 0
            rd_en = 0

        #Prevent illegal operations
#        if occupancy == 0:
#            rd_en = 0

        if occupancy == FIFO_DEPTH:
            wr_en = 0

        #Random write data
        wr_data = random.randint(0, 255)

        return wr_en, rd_en, wr_data


class BurstDriver:

    def __init__(self):
        self.burst_remaining = 0
        self.burst_mode = "idle"

    def next_burst(self, occupancy):

        #Select a new burst when the previous one finishes
        if self.burst_remaining == 0:

            self.burst_mode = random.choice([
                "write",
                "read",
                "rw",
                "idle"
            ])

            self.burst_remaining = random.randint(2, 8)

        self.burst_remaining -= 1

        #Generate operations based on burst mode
        if self.burst_mode == "write":
            wr_en = 1
            rd_en = 0

        elif self.burst_mode == "read":
            wr_en = 0
            rd_en = 1

        elif self.burst_mode == "rw":
            wr_en = 1
            rd_en = 1

        else:
            wr_en = 0
            rd_en = 0

        #Prevent illegal operations
#        if occupancy == 0:
#            rd_en = 0

        if occupancy == FIFO_DEPTH:
            wr_en = 0

        #Random write data
        wr_data = random.randint(0, 255)

        return wr_en, rd_en, wr_data


#Seeded random regression test with one seed.
@cocotb.test()
async def test_seeded_random_regression(dut):

    model = await setup_fifo(dut)

    seed = 12345
    random.seed(seed)

    #Define class.
    txn = FifoTransaction()

    #loop
    for _ in range(1000):

        txn.count = model.count
        #Randomize the transaction input.
        txn.randomize(model.count)

        await check_cycle(
            dut,
            model,
            wr_en=txn.wr_en,
            rd_en=txn.rd_en,
            wr_data=txn.wr_data
        )

    dut._log.info(
        "Single-seeded random regression passed"
    )

#Coverage across multiple seeds.
@cocotb.test()
async def test_multi_seed_regression(dut):

    #Array of seeds to use.
    seeds = [
        1,
        10,
        100,
        1000,
        12345
    ]

    #Loop through seed
    for seed in seeds:

        model = await setup_fifo(dut)

        random.seed(seed)

        txn = FifoTransaction()

        dut._log.info(
            f"Starting seed {seed}"
        )
        #Loop through stimulus
        for _ in range(500):

            txn.randomize(model.count)

            await check_cycle(
                dut,
                model,
                wr_en=txn.wr_en,
                rd_en=txn.rd_en,
                wr_data=txn.wr_data
            )
        
    dut._log.info(
        "Multi-seeded random regression passed"
    )

#Burst test
@cocotb.test()
async def test_burst_random_regression(dut):

    model = await setup_fifo(dut)

    seed = 12345
    random.seed(seed)

    burst = BurstDriver()

    dut._log.info(
        f"Starting burst regression with seed={seed}"
    )

    #Generate 1000 burst-driven transactions
    for cycle_num in range(1000):

        #Generate next burst transaction
        wr_en, rd_en, wr_data = burst.next_burst(
            model.count
        )

        dut._log.info(
            f"Cycle={cycle_num} "
            f"Burst={burst.burst_mode} "
            f"Remaining={burst.burst_remaining} "
            f"WR={wr_en} "
            f"RD={rd_en} "
            f"DATA=0x{wr_data:02X} "
            f"COUNT={model.count}"
        )

        #Drive DUT and check against golden model
        await check_cycle(
            dut,
            model,
            wr_en=wr_en,
            rd_en=rd_en,
            wr_data=wr_data
        )

    dut._log.info(
        "Burst random regression passed"
    )
    
        
