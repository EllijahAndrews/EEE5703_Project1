"""STUDENT STARTER -- Week 4 FIFO testbench.

Build a driver / monitor / scoreboard testbench around the FWFT FIFO. Use the
golden model (models.fifo_model.FifoModel) as your scoreboard and check count,
full, empty, and rd_data *every* cycle. Hit the corners: fill to full, drain to
empty, write-while-full (dropped), read-while-empty (ignored), simultaneous
read+write, and pointer wrap.

Run:            make                # (or make SIM=icarus)
Score:          cd code && just mutate fifo        # found/total (released pool)

Right now this only does three writes and one weak check -- raise the found/total.
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from models.fifo_model import FifoModel
import random

#PYVSC CLASS IMPORT
import vsc

# ============================================================
# PYVSC Fifo Transaction Class
# ============================================================
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

# ============================================================
# Burst Helper Function
# ============================================================
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
        if occupancy == 0:
            rd_en = 0

        if occupancy == FIFO_DEPTH:
            wr_en = 0

        #Random write data
        wr_data = random.randint(0, 255)

        return wr_en, rd_en, wr_data


@cocotb.test()
async def test_smoke(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

    for i in range(3):
        dut.wr_en.value = 1
        dut.wr_data.value = 0x40 + i
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
    dut.wr_en.value = 0
    assert int(dut.count.value) == 3, f"count={int(dut.count.value)}"
    # TODO: read the values back and check rd_data order against a FifoModel;
    # TODO: add full/empty corners, simultaneous read+write, and wrap-around.
    for i in range(3):
        await cycle(
            dut,
            wr_en=1,
            rd_en=0,
            wr_data=0x40 + i
        )
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from models.fifo_model import FifoModel


# ============================================================
# Driver
# ============================================================

async def cycle(dut, wr_en=0, rd_en=0, wr_data=0):
    """
    Drive a single FIFO transaction.

    Inputs are driven on the falling edge.
    Outputs are sampled after the next rising edge.
    """

    await FallingEdge(dut.clk)

    dut.wr_en.value = wr_en
    dut.rd_en.value = rd_en
    dut.wr_data.value = wr_data

    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


# ============================================================
# Monitor
# ============================================================

def monitor(dut):
    """
    Sample DUT outputs.
    """

    return {
        "count": int(dut.count.value),
        "full": int(dut.full.value),
        "empty": int(dut.empty.value),
        "rd_data": int(dut.rd_data.value),
    }


# ============================================================
# Scoreboard
# ============================================================

async def check_cycle(dut, model, wr_en=0, rd_en=0, wr_data=0):

    #
    # Predict next state using the golden model.
    # The model uses pre-edge state exactly like the DUT.
    #
    model.step(
        wr_en=wr_en,
        wr_data=wr_data,
        rd_en=rd_en,
    )

    #
    # Drive DUT
    #
    await cycle(
        dut,
        wr_en=wr_en,
        rd_en=rd_en,
        wr_data=wr_data,
    )

    #
    # Monitor DUT
    #
    actual = monitor(dut)

    #
    # Compare against model every cycle
    #
    assert actual["count"] == model.count, (
        f"COUNT mismatch: expected={model.count} got={actual['count']}"
    )

    assert actual["full"] == int(model.full), (
        f"FULL mismatch: expected={int(model.full)} got={actual['full']}"
    )

    assert actual["empty"] == int(model.empty), (
        f"EMPTY mismatch: expected={int(model.empty)} got={actual['empty']}"
    )

    #
    # FWFT check
    #
    if not model.empty:
        assert actual["rd_data"] == model.head, (
            f"RD_DATA mismatch: expected=0x{model.head:02x} "
            f"got=0x{actual['rd_data']:02x}"
        )


# ============================================================
# Test
# ============================================================

@cocotb.test()
async def test_fifo_layered(dut):

    cocotb.start_soon(
        Clock(dut.clk, 10, units="ns").start()
    )

    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0

    #
    # Reset DUT
    #
    for _ in range(3):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    #
    # Reset reference model
    #
    model = FifoModel(8, 8)
    model.reset()

    await FallingEdge(dut.clk)

    #
    # Write three values
    #
    for i in range(3):
        await check_cycle(
            dut,
            model,
            wr_en=1,
            rd_en=0,
            wr_data=0x40 + i,
        )

    #
    # Read them back
    #
    for _ in range(3):
        await check_cycle(
            dut,
            model,
            wr_en=0,
            rd_en=1,
            wr_data=0,
        )

    #
    # Idle cycle
    #
    await check_cycle(
        dut,
        model,
        wr_en=0,
        rd_en=0,
        wr_data=0,
    )

    dut._log.info("Layered FIFO test passed")

async def setup_fifo(dut):
    cocotb.start_soon(
        Clock(dut.clk, 10, units="ns").start()
    )

    dut.wr_en.value = 0
    dut.rd_en.value = 0
    dut.wr_data.value = 0
    dut.rst_n.value = 0

    for _ in range(3):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

    model = FifoModel(8, 8)
    model.reset()

    return model  

@cocotb.test()
async def test_fill_to_full(dut):

    model = await setup_fifo(dut)

    for i in range(8):
        await check_cycle(
            dut, model,
            wr_en=1,
            rd_en=0,
            wr_data=i
        )

    assert int(dut.full.value) == 1
    assert int(dut.count.value)

@cocotb.test()
async def test_write_while_full(dut):

    model = await setup_fifo(dut)

    for i in range(8):
        await check_cycle(dut, model, 1, 0, i)

    await check_cycle(
        dut, model,
        wr_en=1,
        rd_en=0,
        wr_data=99
    )

    assert int(dut.count.value) == 8
    assert int(dut.full.value) == 1

@cocotb.test()
async def test_read_while_empty(dut):

    model = await setup_fifo(dut)

    await check_cycle(
        dut, model,
        wr_en=0,
        rd_en=1
    )

    assert int(dut.count.value) == 0
    assert int(dut.empty.value) == 1

@cocotb.test()
async def test_simultaneous_read_write(dut):

    model = await setup_fifo(dut)

    for i in range(4):
        await check_cycle(dut, model, 1, 0, i)

    count_before = int(dut.count.value)

    await check_cycle(
        dut, model,
        wr_en=1,
        rd_en=1,
        wr_data=55
    )

    assert int(dut.count.value) == count_before

@cocotb.test()
async def test_pointer_wraparound(dut):

    model = await setup_fifo(dut)

    for i in range(8):
        await check_cycle(dut, model, 1, 0, i)

    for _ in range(4):
        await check_cycle(dut, model, 0, 1)

    for i in range(4):
        await check_cycle(
            dut, model,
            1, 0,
            100 + i
        )

    while not model.empty:
        await check_cycle(dut, model, 0, 1)


@cocotb.test()
async def test_random_interleave(dut):

    model = await setup_fifo(dut)

    seed = 12345
    rng = random.Random(seed)

    dut._log.info(f"Running random test with seed={seed}")

    for cycle_num in range(500):

        wr_en = rng.choice([0, 1])
        rd_en = rng.choice([0, 1])

        wr_data = rng.randint(0, 255)

        await check_cycle(
            dut,
            model,
            wr_en=wr_en,
            rd_en=rd_en,
            wr_data=wr_data
        )

    dut._log.info("Random interleave test passed")
    
# ============================================================
# Seeded Random Regression
# ============================================================    
    
#Seeded random regression test with one seed.
@cocotb.test()
async def test_seeded_random_regression(dut):

    model = await setup_fifo(dut)

    seed = 1337
    random.seed(seed)

    #Define class.
    txn = FifoTransaction()

    #loop
    for _ in range(1000):

        txn.count = model.count
        #Randomize the transaction input.
        txn.randomize()

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
        txn.count = model.count

        dut._log.info(
            f"Starting seed {seed}"
        )
        #Loop through stimulus
        for _ in range(500):

            txn.randomize()

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
    
# ============================================================
# Burst Random Regression
# ============================================================

@cocotb.test()
async def test_burst_random_regression(dut):

    model = await setup_fifo(dut)

    seed = 13030
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
