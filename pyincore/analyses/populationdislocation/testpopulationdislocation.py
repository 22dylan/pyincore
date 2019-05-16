# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import InsecureIncoreClient
from pyincore.analyses.populationdislocation import PopulationDislocation, PopulationDislocationUtil


def run_without_base_class():
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    seed_i = 1111
    # Population Dislocation
    podi = PopulationDislocation(client)
    merged_block_inv = PopulationDislocationUtil.merge_damage_population_block(
        building_dmg_file='seaside_bldg_dmg_result.csv',
        population_allocation_file='pop_allocation_2222.csv',
        block_data_file='IN-CORE_01av3_SetupSeaside_FourInventories_2018-08-29_bgdata.csv')

    merged_final_inv = podi.get_dislocation(seed_i, merged_block_inv)

    # save to csv
    merged_final_inv.to_csv("final_inventory" + str(seed_i) + ".csv", sep=",")


def run_with_base_class():
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    building_dmg = "5c12856d1f5e0d0667d6410e"
    sto_pop_alloc = "5c12d96f1f5e0d0667d66b2c"
    bg_data = "5c128a161f5e0d0667d64116"

    pop_dis = PopulationDislocation(client)

    pop_dis.load_remote_input_dataset("building_dmg", building_dmg)
    pop_dis.load_remote_input_dataset("population_allocation", sto_pop_alloc)
    pop_dis.load_remote_input_dataset("block_group_data", bg_data)

    # pop_dis.show_gdocstr_docs()

    result_name = "pop-dislocation-results"
    seed = 1111

    pop_dis.set_parameter("result_name", result_name)
    pop_dis.set_parameter("seed", seed)

    pop_dis.run_analysis()


if __name__ == '__main__':
    run_with_base_class()