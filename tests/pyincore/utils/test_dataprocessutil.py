import pytest

from pyincore.utils.dataprocessutil import DataProcessUtil as util
from pyincore import Dataset, DataService


@pytest.fixture
def client():
    return pytest.client


def test_get_mapped_result(client):
    bldg_dataset_id = "5f9091df3e86721ed82f701d"
    bldg_dmg_dataset_id = "5f9868c00ace240b22a7f2a5"
    bldg_func_dataset_id = "60674c89c57ada48e492b97b"
    archetype_id = "5fca915fb34b193f7a44059b"

    dmg_ret_json, func_ret_json, max_state_df = util.get_mapped_result_from_dataset_id(
        client, bldg_dataset_id, bldg_dmg_dataset_id, bldg_func_dataset_id, archetype_id)

    assert "by_cluster" in dmg_ret_json.keys() and "by_category" in dmg_ret_json.keys()
    assert "by_cluster" in func_ret_json.keys() and "by_category" in func_ret_json.keys()
    assert "max_state" in max_state_df._info_axis.values


def test_get_mapped_result_from_analysis(client):
    bldg_dataset_id = "5f9091df3e86721ed82f701d"

    bldg_dmg_dataset_id = "5f9868c00ace240b22a7f2a5"  # legacy DS_name
    # bldg_dmg_dataset_id = "602d96e4b1db9c28aeeebdce" # new DS_name
    dmg_result_dataset = Dataset.from_data_service(bldg_dmg_dataset_id, DataService(client))

    archetype_id = "5fca915fb34b193f7a44059b"

    bldg_func_dataset_id = "60674c89c57ada48e492b97b"
    bldg_func_dataset = Dataset.from_data_service(bldg_func_dataset_id, DataService(client))

    dmg_ret_json, func_ret_json, max_state_df = util.get_mapped_result_from_analysis(
        client, bldg_dataset_id, dmg_result_dataset, bldg_func_dataset, archetype_id)

    assert "by_cluster" in dmg_ret_json.keys() and "by_category" in dmg_ret_json.keys()
    assert "by_cluster" in func_ret_json.keys() and "by_category" in func_ret_json.keys()
    assert "max_state" in max_state_df._info_axis.values
