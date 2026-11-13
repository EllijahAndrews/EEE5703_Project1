## RANDOM CONSTRAINED REGRESSION ##
## Written By: Hailey Gorak ##
# Random seeded regression tests + defined helper class to be integrated into the testbench along with FIFO transaction file. 
# FIFO transaction class must be imported so that pyvsc is implemented and constrained properly.

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
    
        
