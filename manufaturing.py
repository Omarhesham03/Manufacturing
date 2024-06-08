# Imprting the required libraries 
import pandas as pd
import random
import simpy

# defining the precessing times for multiple operations 
processingTime = {
    'inspecting': 6,
    'loading': 5,
    'machining': 10,
    'assembling': 8,
    'packaging': 4
}

# defining values for the estimated time and the breakdown rate
maintainance = 2
breakdown = 0.3

# getting the number of workers in each operation 
NWorkers = {
    'inspecting': 2,
    'loading': 2,
    'machining': 3,
    'assembling': 4,
    'packaging': 3
}

# defining the shift in length, the simulation time and the number of products
shiftLength = 4
simulationTime = 100
Nproducts = 2

#implementing a class for the manufacturing line 
class MLine:
    def __init__(self, env):
        # initializing the environment
        self.env = env
        # defining resources needed for each stage 
        self.stages = {
            stage: simpy.Resource(env, capacity=NWorkers[stage]) for stage in NWorkers
        }
        # creating resource for the repair team with capacity of 2
        self.repair_team = simpy.Resource(env, capacity=2)
        # making empty array for the data
        self.data = []

    def process_part(self, part, product_type):
        stages = ['loading', 'machining', 'assembling', 'inspecting', 'packaging']
        for stage in stages:
            # calculating the processing time 
            processing_time = processingTime[stage] * (1 if product_type == 1 else 1.2)
            with self.stages[stage].request() as request:
                # defining the start time 
                start = self.env.now
                # waiting for resources availability
                yield request
                try:
                    yield self.env.timeout(processing_time)
                    # checking the breakdown randomly
                    if random.random() < breakdown:
                        yield self.env.process(self.repair_machine(stage))
                    # defining the end time 
                    end  = self.env.now
                    # storing the saved data
                    self.data.append({
                        'Part': part,
                        'Stage': stage,
                        'Start Time': start,
                        'Finish Time': end ,
                        'Duration': end  - start,
                        'Product Type': product_type
                    })
                except simpy.Interrupt:
                    # handling the inturrupt
                    yield self.env.process(self.repair_machine(stage))

    def repair_machine(self, stage):
        with self.repair_team.request() as repair:
            # defining the start time 
            start_repair = self.env.now
            # wait for the availability of the repair team 
            yield repair
            # simulate the duration
            yield self.env.timeout(maintainance)

# starting the manufacturing using the parameters of the id and the product type
def part_manufacturer(env, line, part_id, product_type):
    yield env.process(line.process_part(part_id, product_type))

def setup(env, num_parts_per_type):
    # creating instance of the class
    line = MLine(env)

    # looping for each product type
    for product_type in range(1, Nproducts + 1):
        # starting the process for the number of the parts
        for i in range(num_parts_per_type):
            # making the process for each part
            env.process(part_manufacturer(env, line, f"Part_{i + 1}", product_type))
    
    # simulating for the total time 
    yield env.timeout(simulationTime)
    # converting the colleced data to a data frame
    data_frame = pd.DataFrame(line.data)
    return data_frame

# defining the environment 
ENVIRONMENT = simpy.Environment()
# starting the process of the environment 
process = ENVIRONMENT.process(setup(ENVIRONMENT, 5))
#running the simulating 
ENVIRONMENT.run()
# getting the data frame from the collected value
df = process.value
# displaying the data frame 
print(df)