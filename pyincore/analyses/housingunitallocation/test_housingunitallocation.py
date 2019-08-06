# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import InsecureIncoreClient
from pyincore.analyses.housingunitallocation.housingunitallocation import HousingUnitAllocation


def run_with_base_class():
    client = InsecureIncoreClient()

    pop_inv = "5c34da82c5c0e40670b77633"
    addr_point_inv = "5c34db03c5c0e40670b77637"
    bg_inv = "5c34db0ec5c0e40670b7763b"

    result_name = "housing-unit-allocation"
    seed = 1238
    iterations = 5

    spa = HousingUnitAllocation(client)
    spa.load_remote_input_dataset("housing_unit_inventory", pop_inv)
    spa.load_remote_input_dataset("address_point_inventory", addr_point_inv)
    spa.load_remote_input_dataset("building_inventory", bg_inv)

    spa.set_parameter("result_name", result_name)
    spa.set_parameter("seed", seed)
    spa.set_parameter("iterations", iterations)

    spa.run_analysis()

    return True


if __name__ == '__main__':
    run_with_base_class()