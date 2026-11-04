## RANDOM CONSTRAINED REGRESSION ##
## Written By: Hailey Gorak ##
# Random seeded regression tests + defined helper class to be integrated into the testbench along with FIFO transaction file. 
# FIFO transaction class must be imported so that pyvsc is implemented and constrained properly.

#Burst helper function.
def next_burst(self, occupancy):

    if self.burst_remaining == 0:

        #Random stimulus choice.
        self.burst_mode = random.choice([
            "write",
            "read",
            "rw",
            "idle"
        ])

        self.burst_remaining = random.randint(2, 8)

    self.burst_remaining -= 1

    #Write burst.
    if self.burst_mode == "write":
        self.wr_en = 1
        self.rd_en = 0

    #REad burst.
    elif self.burst_mode == "read":
        self.wr_en = 0
        self.rd_en = 1

    #Simultaneous read write.
    elif self.burst_mode == "rw":
        self.wr_en = 1
        self.rd_en = 1

    #Aything else.
    else:
        self.wr_en = 0
        self.rd_en = 0

    #Randomized data.
    self.wr_data = random.randint(0,255)

    #No illegal transactions.
    if occupancy == 0:
        self.rd_en = 0

    if occupancy == FIFO_DEPTH:
        self.wr_en = 0

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
        
