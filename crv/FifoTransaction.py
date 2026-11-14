## PYVSC TRANSACTION CLASS ##
## Written By: Hailey Gorak ##
# Constrained random regression designed to run several transactions that adjust based on constraint weights.
# Designed to skip useless stimuli and provide the best randomized stimulus for the testbench. Focus on unique/interesting legal scenarios.

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
