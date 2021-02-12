from pyincore import IncoreClient, MappingSet, FragilityService
from pyincore.globals import INCORE_TEST_URL
from pyincore import Dataset
from pyincore.analyses.buildingdamage import BuildingDamage
from pyincore.analyses.cumulativebuildingdamage.cumulativebuildingdamage import CumulativeBuildingDamage


def run_with_base_class():
    client = IncoreClient(INCORE_TEST_URL)
    fragility_service = FragilityService(client)

    # Seaside building dataset
    bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"

    # New madrid earthquake using Atkinson Boore 1995
    eq_hazard_type = "earthquake"
    eq_hazard_id = "5ba8ed5cec23090435209069"

    # Earthquake mapping
    eq_mapping_id = "5b47b350337d4a3629076f2c"

    # Run Building Damage Analysis for Earthquake (Seaside)
    bldg_dmg_eq = BuildingDamage(client)
    bldg_dmg_eq.load_remote_input_dataset("buildings", bldg_dataset_id)

    result_name = "eq_bldg_dmg_result"
    bldg_dmg_eq.set_parameter("result_name", result_name)
    eq_mapping_set = MappingSet(fragility_service.get_mapping(eq_mapping_id))
    bldg_dmg_eq.set_input_dataset('dfr3_mapping_set', eq_mapping_set)
    bldg_dmg_eq.set_parameter("hazard_type", eq_hazard_type)
    bldg_dmg_eq.set_parameter("hazard_id", eq_hazard_id)
    bldg_dmg_eq.set_parameter("num_cpu", 4)
    bldg_dmg_eq.run_analysis()
    eq_damage_output = bldg_dmg_eq.get_output_dataset("result")

    # START: Seaside example Tsunami
    tsunami_hazard_type = "tsunami"
    tsunami_hazard_id = "5bc9e25ef7b08533c7e610dc"

    # Tsunami mapping
    tsunami_mapping_id = "5b48fb1f337d4a478e7bd54d"

    # Run seaside tsunami building damage
    bldg_dmg_tsunami = BuildingDamage(client)
    bldg_dmg_tsunami.load_remote_input_dataset("buildings", bldg_dataset_id)
    tsunami_result_name = "tsunami_bldg_dmg_result"
    bldg_dmg_tsunami.set_parameter("result_name", tsunami_result_name)
    tsu_mapping_set = MappingSet(fragility_service.get_mapping(tsunami_mapping_id))
    bldg_dmg_tsunami.set_input_dataset('dfr3_mapping_set', tsu_mapping_set)
    bldg_dmg_tsunami.set_parameter("hazard_type", tsunami_hazard_type)
    bldg_dmg_tsunami.set_parameter("hazard_id", tsunami_hazard_id)
    bldg_dmg_tsunami.set_parameter("num_cpu", 4)
    bldg_dmg_tsunami.run_analysis()
    tsunami_damage_output = bldg_dmg_tsunami.get_output_dataset("result")

    # START: Cumulative Building Damage Analysis
    # Read the output files generated by the two previous building damage analyses
    cumulative_bldg_dmg = CumulativeBuildingDamage(client)
    cumulative_bldg_dmg.set_input_dataset("eq_bldg_dmg", eq_damage_output)
    cumulative_bldg_dmg.set_input_dataset("tsunami_bldg_dmg", tsunami_damage_output)

    # Specify the result name
    result_name = "Cumulative_Bldg_Dmg_Result"
    # Set analysis parameters
    cumulative_bldg_dmg.set_parameter("num_cpu", 4)
    cumulative_bldg_dmg.set_parameter("result_name", result_name)
    # Run Cumulative Building Damage analysis
    cumulative_bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
