# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
from pyincore import BaseAnalysis


class HousingUnitAllocation(BaseAnalysis):
    def __init__(self, incore_client):
        super(HousingUnitAllocation, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'housing-unit-allocation',
            'description': 'Probabilistic Housing Unit Allocation Analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': False,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': True,
                    'description': 'Initial Seed for the Probabilistic model',
                    'type': int
                },
                {
                    'id': 'iterations',
                    'required': True,
                    'description': 'No of iterations to perform the probabilistic model on',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'housing_unit_inventory',
                    'required': True,
                    'description': 'Housing Unit Inventory CSV data, aka Census Block data. Corresponds to a possible '
                                   'occupied housing unit, vacant housing unit, or a group quarters',
                    'type': ['incore:housingUnitInventory']
                },
                {
                    'id': 'address_point_inventory',
                    'required': True,
                    'description': 'CSV dataset of address locations available in a block. Corresponds to a '
                                   'specific address where a housing unit or group quarters could be assigned',
                    'type': ['incore:addressPoints']
                },
                {
                    'id': 'building_inventory',
                    'required': True,
                    'description': 'Building Inventory CSV dataset for each building/structure. A structure '
                                   'can have multiple addresses',
                    'type': ['ergo:buildingInventory']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'description': 'A csv file with the merged dataset of the inputs, aka Probabilistic'
                                   'Housing Unit Allocation',
                    'type': 'incore:housingUnitAllocation'
                }
            ]
        }

    def run(self):
        """Merges Housing Unit Inventory, Address Point Inventory and Building Inventory.
         The results of this analysis are aggregated per structure/building. Generates
         one csv result per iteration.

        Returns:
               bool: True if successful, False otherwise

        """

        # Get seed
        seed = self.get_parameter("seed")

        # Get Iterations
        iterations = self.get_parameter("iterations")

        # Get desired result name
        result_name = self.get_parameter("result_name")

        # Housing Unit Inventory Dataset
        pop_inv = self.get_input_dataset("housing_unit_inventory").get_dataframe_from_csv()

        # Address Point Inventory Dataset
        addr_point_inv = self.get_input_dataset("address_point_inventory").get_dataframe_from_csv()

        # Building Inventory dataset
        bg_inv = self.get_input_dataset("building_inventory").get_dataframe_from_csv()

        csv_source = "dataframe"

        for i in range(iterations):
            seed_i = seed + i
            sorted_housing_unit_address_inventory = self.get_iteration_probabilistic_allocation(
                pop_inv, addr_point_inv, bg_inv, seed_i)
            temp_output_file = result_name + "_" + str(seed_i) + ".csv"

            self.set_result_csv_data("result",
                                     sorted_housing_unit_address_inventory,
                                     temp_output_file, csv_source)
        return True

    def prepare_housing_unit_inventory(self, housing_unit_inventory, seed):
        """Merge order to Building and Address inventories.

        Args:
            housing_unit_inventory (pd.DataFrame): Housing unit inventory
            seed (int): random number generator seed for reproducibility

        Returns:
            pd.DataFrame: Sorted housing unit inventory

        """
        size_row, size_col = housing_unit_inventory.shape
        np.random.seed(seed)
        sorted_housing_unit0 = housing_unit_inventory.sort_values(by=["lvtypuntid"])

        # Create Random merge order for housing unit inventory
        random_order_housing_unit = np.random.uniform(0, 1, size_row)

        sorted_housing_unit0["randomblock"] = random_order_housing_unit

        #  gsort BlockID -LiveTypeUnit Tenure randomaorderpop
        sorted_housing_unit1 = sorted_housing_unit0.sort_values(by=["blockid", "ownershp", "vacancy", "randomblock"],
                                                                ascending=[True, True, True, True])

        # by BlockID: gen RandomMergeOrder = _n
        sorted_housing_unit1["mergeorder"] = sorted_housing_unit1.groupby(["blockid"]).cumcount()

        sorted_housing_unit2 = sorted_housing_unit1.sort_values(by=["blockid", "mergeorder"],
                                                                ascending=[True, False])
        return sorted_housing_unit2

    def merge_infrastructure_inventory(self, address_point_inventory, building_inventory ):
        """Merge order to Building and Address inventories.

        Args:
            address_point_inventory (pd.DataFrame): address point inventory
            building_inventory (pd.DataFrame): building inventory

        Returns:
            pd.DataFrame: merged address and building inventories

        """
        sorted_pnt_0 = address_point_inventory.sort_values(by=["strctid"])
        sorted_bld_0 = building_inventory.sort_values(by=["strctid"])

        addresspt_building_inv = pd.merge(sorted_bld_0, sorted_pnt_0,
                                          how='outer', on="strctid",
                                          left_index=False, right_index=False,
                                          sort=True, copy=True, indicator=True,
                                          validate="1:m")

        addresspt_building_inv = self.compare_merges(sorted_pnt_0.columns, sorted_bld_0.columns,
                                                     addresspt_building_inv)

        return addresspt_building_inv

    def prepare_infrastructure_inventory(self, seed_i: int, critical_bld_inv: pd.DataFrame):
        """Assign Random merge order to Building, Water and Address inventories. Use main
        seed value.

        Args:
            seed_i (int): random number generator seed for reproducibility
            critical_bld_inv (pd.DataFrame): Merged inventories

        Returns:
            pd.DataFrame: Sorted merged critical infrastructure

        """
        size_row, size_col = critical_bld_inv.shape

        sort_critical_bld_0 = critical_bld_inv.sort_values(by=["addrptid"])

        seed_i2: int = seed_i + 1
        np.random.seed(seed_i2)

        randomaparcel = np.random.uniform(0, 1, size_row)
        sort_critical_bld_0["randomaparcel"] = randomaparcel

        sort_critical_bld_1 = sort_critical_bld_0.sort_values(by=["blockid", "huestimate", "randomaparcel"],
                                                              ascending=[True, True, True])
        sort_critical_bld_1["mergeorder"] = sort_critical_bld_1.groupby(["blockid"]).cumcount()

        sort_critical_bld_2 = sort_critical_bld_1.sort_values(by=["blockid", "mergeorder"],
                                                              ascending=[True, False])
        return sort_critical_bld_2

    def merge_inventories(self, sorted_housing_unit: pd.DataFrame, sorted_infrastructure: pd.DataFrame):
        """Merge (Sorted) Housing Unit Inventory and (Sorted) Infrastructure Inventory.

        Args:
            sorted_housing_unit (pd.DataFrame):  Sorted Housing Unit Inventory
            sorted_infrastructure (pd.DataFrame):  Sorted infrastructure inventory. This includes
                Building inventory and Address point inventory.

        Returns:
            pd.DataFrame: Final merge of all four inventories

        """
        housing_unit_address_point_inventory = pd.merge(sorted_infrastructure, sorted_housing_unit,
                                                        how='outer', left_on=["blockid", "mergeorder"],
                                                        right_on=["blockid", "mergeorder"],
                                                        sort=True, suffixes=("_x", "_y"),
                                                        copy=True, indicator="exists3", validate="1:1")

        # check for duplicate columns from merge
        housing_unit_address_point_inventory = self.compare_merges(sorted_housing_unit.columns,
                                                                   sorted_infrastructure.columns,
                                                                   housing_unit_address_point_inventory)

        sorted_housing_unit_address_inventory = housing_unit_address_point_inventory.sort_values(
            by=["lvtypuntid"])

        output = sorted_housing_unit_address_inventory[sorted_housing_unit_address_inventory["exists3"] == 'both']
        return output

    def get_iteration_probabilistic_allocation(self, housing_unit_inventory, address_point_inventory, building_inventory, seed):
        """Merge inventories

        Args:
            housing_unit_inventory (pd.DataFrame): Housing Unit Inventory
            address_point_inventory (pd.DataFrame): Address Point inventory
            building_inventory (pd.DataFrame): Building inventory
            seed (int): random number generator seed for reproducibility

            Returns:
                pd.DataFrame: Merged table

        """
        sorted_housing_unit = self.prepare_housing_unit_inventory(housing_unit_inventory, seed)

        critical_building_inv = self.merge_infrastructure_inventory(address_point_inventory, building_inventory)
        sorted_infrastructure = self.prepare_infrastructure_inventory(seed, critical_building_inv)

        output = self.merge_inventories(sorted_housing_unit, sorted_infrastructure)
        return output

    # utility functions
    def compare_merges(self, table1_cols, table2_cols, table_merged):
        """Compare two lists of columns and run compare columns on columns in both lists.
        It assumes that suffixes are _x and _y

        Args:
            table1_cols (list):         columns in table 1
            table2_cols (list):         columns in table 2
            table_merged (pd.DataFrame):merged table

            Returns:
                pd.DataFrame: Merged table

        """
        match_column = set(table1_cols).intersection(table2_cols)
        for col in match_column:
            # Compare two columns and marked similarity or rename and drop
            if col+"_x" in table_merged.columns and col+"_y" in table_merged.columns:
                table_merged = self.compare_columns(table_merged, col+"_x", col+"_y", True)

        return table_merged

    def compare_columns(self, table, col1, col2, drop):
        """Compare two columns. If not equal create Tru/False column, if equal rename one of them
        with the base name and drop the other.

        Args:
            table (pd.DataFrame):      Data Frame table
            col1 (pd.Series):          Column 1
            col2 (pd.Series):          Column 2
            drop (bool):               rename and drop column

        Returns:
            pd.DataFrame: Table with True/False column

        """
        # Values in columns match or not, add True/False column
        table.loc[table[col1] == table[col2], col1+"-"+col2] = True
        table.loc[table[col1] != table[col2], col1+"-"+col2] = False

        if table[col1].equals(table[col2]):
            col1_base = col1.rsplit("_", 1)[0]
            col2_base = col1.rsplit("_", 1)[0]
            if col1_base == col2_base and drop:

                table[col1_base] = table[col1]
                table = table.drop(columns=[col1, col2, col1+"-"+col2])

        return table
