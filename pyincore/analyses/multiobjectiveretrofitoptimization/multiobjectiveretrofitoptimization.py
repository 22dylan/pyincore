# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import BaseAnalysis
import sys
import os
import pandas as pd
import numpy as np
import csv
import time
import matplotlib.pyplot as plt
#from gurobipy import *
import scipy.interpolate as interp
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
from pandas import DataFrame
from pyomo.environ import ConcreteModel, Set, Var, Param, Objective, Constraint
from pyomo.environ import quicksum, minimize, maximize, NonNegativeReals, Any
from pyomo.environ import sum_product
import pyomo.environ as pyo
#from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverManagerFactory
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.util.infeasible import log_infeasible_constraints
#import palettable.colorbrewer
import zipfile
import getopt
import glob

class MultiObjectiveRetrofitOptimization(BaseAnalysis):
    """
        This analysis computes a series of linear programming models for single- and multi-objective
        optimization related to the effect of extreme weather on a community in terms of three objective functions.
        The three objectives used in this program are to minimize economic loss, minimize population dislocation,
        and maximize building functionality. The computation proceeds by iteratively solving constrained linear
        models using epsilon steps.

        The output of the computation a collection of optimal resource allocations.

        Contributors
            | Science: Charles Nicholson, Yunjie Wen
            | Implementation: Dale Cochran , Tarun Adluri , Jorge Duarte, Santiago Núñez-Corrales,
                              and NCSA IN-CORE Dev Team

        Related publications


        Args:
            incore_client (IncoreClient): Service authentication.
        """

    # Column descriptors
    __Q_col = 'Q_t_hat'
    __Q_rs_col = 'Q_t_hat_rs'
    __SC_col = 'Sc'
    __SC_rs_col = 'Sc_rs'

    __budget_default = 0.2

    def __init__(self, incore_client):
        super(MultiObjectiveRetrofitOptimization, self).__init__(incore_client)

    def run(self):
        """Execute the multiobjective retrofit optimization analysis using parameters and input data."""
        # Read parameters
        model_solver = self.get_parameter('model_solver')
        num_epsilon_steps = self.get_parameter('num_epsilon_steps')

        budget_available = self.__budget_default
        if self.get_parameter('max_budget') != 'default':
            budget_available = self.get_parameter('budget_available')

        inactive_submodels = []

        in_subm = self.get_parameter('inactive_submodels')

        if in_subm is not None:
            inactive_submodels = in_subm

        scaling_factor = 1.0
        if self.get_parameter('scale_data'):
            scaling_factor = self.get_parameter('scaling_factor')

        building_repairs_csv = self.get_input_dataset('building_repairs_data').get_csv_reader()
        strategy_costs_csv = self.get_input_dataset('strategy_costs_data').get_csv_reader()

        self.multiobjective_retrofit_optimization_model(model_solver, num_epsilon_steps, budget_available,
                                                        scaling_factor, inactive_submodels, building_repairs_csv,
                                                        strategy_costs_csv)


    def multiobjective_retrofit_optimization_model(self, model_solver, num_epsilon_steps, budget_available,
                                                   scaling_factor, inactive_submodels, building_functionality_csv,
                                                   strategy_costs_csv):
        """Performs the computation of the model.

        Args:
            model_solver (str): model solver to use for analysis
            num_epsilon_steps (int): number of epsilon values for the multistep optimization algorithm
            budget_available (float): budget constraint of the optimization analysis
            scaling_factor (float): scaling factor for Q and Sc matrices
            inactive_submodels (list): submodels to avoid during the computation
            building_functionality_csv (pd.DataFrame): building repairs after a disaster event
            strategy_costs_csv (pd.DataFrame): strategy cost data per building
        """
        # Setup the model
        base_model, sum_sc = self.configure_model(budget_available, scaling_factor, building_functionality_csv,
                                                  strategy_costs_csv)
        model_with_objectives = self.configure_model_objectives(base_model)
        model_with_constraints = self.configure_model_retrofit_costs(model_with_objectives)

        # Choose the solver setting
        model_solver_setting = None
        if model_solver == "gurobi":
            modelSolverSetting = pyo.SolverFactory('gurobi', solver_io="python")
        else:
            modelSolverSetting = pyo.SolverFactory(model_solver)

        # Solve each model individually
        model_solved_individual = self.solve_individual_models(model_with_constraints, model_solver_setting, sum_sc)


    def configure_model(self, budget_available, scaling_factor, building_functionality_csv, strategy_costs_csv):
        """ Configure the base model to perform the multiobjective optimization.

        Args:
            budget_available (float): available budget
            scaling_factor (float): value to scale monetary input data
            building_functionality_csv (DataFrame): table containing building functionality data
            strategy_costs_csv (DataFrame): table containing retrofit strategy costs data
        Returns
            ConcreteModel: a base, parameterized cost/functionality model
        """
        # Rescale data
        myData = building_functionality_csv[self.__Q_col] / scaling_factor
        myData_Sc = strategy_costs_csv[self.__SC_col] / scaling_factor

        # Setup pyomo
        model = ConcreteModel()

        model.Z = Set(initialize=myData.Z.unique())  # Set of all unique blockid numbers in the 'Z' column.
        model.S = Set(initialize=myData.S.unique())  # Set of all unique archtypes in the 'S' column.
        model.K = Set(initialize=myData.K.unique())  # Set of all unique numbers in the 'K' column.
        model.K_prime = Set(initialize=myData_Sc["K'"].unique())

        zsk = []
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']  # Identify the i ∈ Z value.
            j = myData.loc[y, 'S']  # Identify the j ∈ S value.
            k = myData.loc[y, 'K']  # Identify the k ∈ K value.
            zsk.append((i, j, k))  # Add the combination to the list.
        zsk = sorted(set(zsk), key=zsk.index)  # Convert the list to an ordered set for Pyomo.
        model.ZSK = Set(initialize=zsk)  # Define and initialize the ZSK set in Pyomo.

        zs = []
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']  # Identify the i ∈ Z value.
            j = myData.loc[y, 'S']  # Identify the j ∈ S value.
            zs.append((i, j))  # Add the combination to the list.
        zs = sorted(set(zs), key=zs.index)  # Convert the list to an ordered set for Pyomo.
        model.ZS = Set(initialize=zs)  # Define and initialize the ZS set in Pyomo.

        kk_prime = []
        for y in range(len(myData_Sc)):
            k = myData_Sc.loc[y, 'K']  # Identify the k ∈ K value.
            k_prime = myData_Sc.loc[y, "K'"]  # Identify the k ∈ K value.
            kk_prime.append((k, k_prime))  # Add the combination to the list.
        kk_prime = sorted(set(kk_prime), key=kk_prime.index)  # Convert the list to an ordered set for Pyomo.
        model.KK_prime = Set(initialize=kk_prime)  # Define and initialize the KK_prime set in Pyomo.

        k_primek = []
        for y in range(len(myData_Sc)):
            k = myData_Sc.loc[y, 'K']  # Identify the k ∈ K value.
            k_prime = myData_Sc.loc[y, "K'"]  # Identify the k ∈ K value.
            if k_prime <= k:
                k_primek.append((k_prime, k))  # Add the combination to the list.
        k_primek = sorted(set(k_primek), key=k_primek.index)  # Convert the list to an ordered set for Pyomo.
        model.K_primeK = Set(initialize=k_primek)  # Define and initialize the K_primeK set in Pyomo.

        # Define the set of all ZSKK' combinations:
        zskk_prime = []
        for y in range(len(myData_Sc)):
            i = myData_Sc.loc[y, 'Z']  # Identify the i ∈ Z value.
            j = myData_Sc.loc[y, 'S']  # Identify the j ∈ S value.
            k = myData_Sc.loc[y, 'K']  # Identify the k ∈ K value.
            k_prime = myData_Sc.loc[y, "K'"]  # Identify the k ∈ K value.
            zskk_prime.append((i, j, k, k_prime))  # Add the combination to the list.
        zskk_prime = sorted(set(zskk_prime), key=zskk_prime.index)  # Convert the list to an ordered set for Pyomo.
        model.ZSKK_prime = Set(initialize=zskk_prime)  # Define and initialize the ZSKK_prime set in Pyomo.

        ####################################################################################################
        # DEFINE VARIABLES AND PARAMETERS:
        ####################################################################################################
        # Declare the decision variable x_ijk (total # buildings in zone i of structure type j at code level k after retrofitting):
        model.x_ijk = Var(model.ZSK, within=NonNegativeReals)

        # Declare the decision variable y_ijkk_prime (total # buildings in zone i of structure type j retrofitted from code level k to code level k_prime):
        model.y_ijkk_prime = Var(model.ZSKK_prime, within=NonNegativeReals)

        # Declare economic loss cost parameter l_ijk:
        model.l_ijk = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.l_ijk[i, j, k] = myData.loc[y, 'l']

        # Declare dislocation parameter d_ijk:
        model.d_ijk = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.d_ijk[i, j, k] = myData.loc[y, 'd_ijk']

        # Declare the number of buildings parameter b_ijk:
        model.b_ijk = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.b_ijk[i, j, k] = myData.loc[y, 'b']

        # Declare the building functionality parameter Q_t_hat:
        model.Q_t_hat = Param(model.ZSK, within=NonNegativeReals, mutable=True)
        for y in range(len(myData)):
            i = myData.loc[y, 'Z']
            j = myData.loc[y, 'S']
            k = myData.loc[y, 'K']
            model.Q_t_hat[i, j, k] = myData.loc[y, 'Q_t_hat']

        # Declare the retrofit cost parameter Sc_ijkk':
        model.Sc_ijkk_prime = Param(model.ZSKK_prime, within=NonNegativeReals, mutable=True)
        for y in range(len(myData_Sc)):
            i = myData_Sc.loc[y, 'Z']
            j = myData_Sc.loc[y, 'S']
            k = myData_Sc.loc[y, 'K']
            k_prime = myData_Sc.loc[y, "K'"]
            model.Sc_ijkk_prime[i, j, k, k_prime] = myData_Sc.loc[y, 'Sc']

        ####################################################################################################
        # DECLARE THE TOTAL MAX BUDGET AND TOTAL AVAILABLE BUDGET:
        ####################################################################################################
        # Define the total max budget based on user's input:
        model.B = Param(mutable=True, within=NonNegativeReals)

        if budget_available != self.__budget_default:
            sumSc = quicksum(
                pyo.value(model.Sc_ijkk_prime[i, j, k, 3]) * pyo.value(model.b_ijk[i, j, k]) for i, j, k in model.ZSK)
        else:
            sumSc = budget_available
        # Define the total available budget based on user's input:
        model.B = sumSc * budget_available

        return model, sumSc

    def configure_model_objectives(self, model):
        """ Configure the model by adding objectives

        Args:
            model (ConcreteModel): a base cost/functionality model

        Returns:
            ConcreteModel: a model extended with objective functions

        """
        model.objective_1 = Objective(rule=self.obj_economic, sense=minimize)
        model.econ_loss = Param(mutable=True, within=NonNegativeReals)  # ,default=10000000000)

        model.objective_2 = Objective(rule=self.obj_dislocation, sense=minimize)
        model.dislocation = Param(mutable=True, within=NonNegativeReals)  # ,default=30000)

        model.objective_3 = Objective(rule=self.obj_functionality, sense=maximize)
        model.functionality = Param(mutable=True, within=NonNegativeReals)  # ,default=1)

        return model

    def configure_model_retrofit_costs(self, model):
        model.retrofit_budget_constraint = Constraint(rule=self.retrofit_cost_rule)
        model.number_buildings_ij_constraint = Constraint(model.ZS, rule=self.number_buildings_ij_rule)
        model.building_level_constraint = Constraint(model.ZSK, rule=self.building_level_rule)

        return model

    def solve_individual_models(self, model, model_solver_setting, sum_sc):
        print("Max Budget: $", sum_sc)
        print("Available Budget: $", pyo.value(model.B))
        print("")

        model = self.solve_model_1(model, model_solver_setting)
        model = self.solve_model_2(model, model_solver_setting)
        model = self.solve_model_3(model, model_solver_setting)

        return model

    def solve_model_1(self, model, model_solver_setting):
        starttime = time.time()
        print("Initial solve for objective function 1 starting.")
        # Activate objective function 1 (minimize economic loss) and deactivate others:
        model.objective_1.activate()
        model.objective_2.deactivate()
        model.objective_3.deactivate()

        # Solve the model:
        results = model_solver_setting.solve(model)

        # Save the results if the solver returns an optimal solution:
        if (results.solver.status == SolverStatus.ok) and (
                results.solver.termination_condition == TerminationCondition.optimal):
            model.econ_loss = quicksum(
                pyo.value(model.l_ijk[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign economic loss to the model.econ_loss parameter.
            model.dislocation = quicksum(
                pyo.value(model.d_ijk[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign dislocation to the model.dislocation parameter.
            model.functionality = quicksum(
                pyo.value(model.Q_t_hat[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign functionality to the model.functionality parameter.
            obj_1_min_epsilon = pyo.value(model.objective_1)  # Save the optimal economic loss value.
            obj_2_value_1 = pyo.value(model.dislocation)  # Save the dislocation value when optimizing economic loss.
            obj_3_value_1 = pyo.value(
                model.functionality)  # Save the functionality value when optimizing economic loss.
            print("Initial solve for objective function 1 complete.")
            print("Economic Loss: ", pyo.value(model.econ_loss),
                  "Dislocation: ", pyo.value(model.dislocation),
                  "Functionality: ", pyo.value(model.functionality))

            print("Economic loss min epsilon (optimal value):", obj_1_min_epsilon)
            print("Dislocation when optimizing Economic Loss:", obj_2_value_1)
            print("Functionality when optimizing Economic Loss:", obj_3_value_1)
            print("")
        else:
            print("Not Optimal")

        endtime = time.time()
        elapsedtime = endtime - starttime
        print("Elapsed time for initial obj 1 solve: ", elapsedtime)
        print("")

        return model

    def solve_model_2(self, model, model_solver_setting):
        starttime = time.time()
        print("Initial solve for objective function 2 starting.")
        # Activate objective function 2 (minimize dislocation) and deactivate others:
        model.objective_1.deactivate()
        model.objective_2.activate()
        model.objective_3.deactivate()

        # Solve the model:
        results = model_solver_setting.solve(model)

        # Save the results if the solver returns an optimal solution:
        if (results.solver.status == SolverStatus.ok) and (
                results.solver.termination_condition == TerminationCondition.optimal):
            model.econ_loss = quicksum(
                pyo.value(model.l_ijk[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign economic loss to the model.econ_loss parameter.
            model.dislocation = quicksum(
                pyo.value(model.d_ijk[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign dislocation to the model.dislocation parameter.
            model.functionality = quicksum(
                pyo.value(model.Q_t_hat[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign functionality to the model.functionality parameter.
            obj_2_min_epsilon = pyo.value(model.objective_2)  # Save the optimal dislocation value.
            obj_1_value_2 = pyo.value(model.econ_loss)  # Save the economic loss value when optimizing dislocation.
            obj_3_value_2 = pyo.value(model.functionality)  # Save the functionality value when optimizing dislocation.
            print("Initial solve for objective function 2 complete.")
            print("Economic Loss: ", pyo.value(model.econ_loss),
                  "Dislocation: ", pyo.value(model.dislocation),
                  "Functionality: ", pyo.value(model.functionality))

            print("Dislocation min epsilon (optimal value):", obj_2_min_epsilon)
            print("Economic Loss when optimizing Dislocation:", obj_1_value_2)
            print("Functionality when optimizing Dislocation:", obj_3_value_2)
            print("")
        else:
            print("Not Optimal")

        endtime = time.time()
        elapsedtime = endtime - starttime
        print("Elapsed time for initial obj 2 solve: ", elapsedtime)
        print("")

        return model

    def solve_model_3(self, model, model_solver_setting):
        starttime = time.time()
        print("Initial solve for objective function 3 starting.")
        # Activate objective function 3 (maximize functionality) and deactivate others:
        model.objective_1.deactivate()
        model.objective_2.deactivate()
        model.objective_3.activate()

        # Solve the model:
        results = model_solver_setting.solve(model)

        # Save the results if the solver returns an optimal solution:
        if (results.solver.status == SolverStatus.ok) and (
                results.solver.termination_condition == TerminationCondition.optimal):
            model.econ_loss = quicksum(
                pyo.value(model.l_ijk[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign economic loss to the model.econ_loss parameter.
            model.dislocation = quicksum(
                pyo.value(model.d_ijk[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign dislocation to the model.dislocation parameter.
            model.functionality = quicksum(
                pyo.value(model.Q_t_hat[i, j, k]) * pyo.value(model.x_ijk[i, j, k]) for (i, j, k) in
                model.ZSK)  # Assign functionality to the model.functionality parameter.
            obj_3_max_epsilon = pyo.value(model.objective_3)  # Save the optimal functionality value.
            obj_1_value_3 = pyo.value(model.econ_loss)  # Save the economic loss value when optimizing functionality.
            obj_2_value_3 = pyo.value(model.dislocation)  # Save the dislocation value when optimizing functionality.
            print("Initial solve for objective function 3 complete.")
            print("Economic Loss: ", pyo.value(model.econ_loss),
                  "Dislocation: ", pyo.value(model.dislocation),
                  "Functionality: ", pyo.value(model.functionality))

            print("Functionality max epsilon (optimal value):", obj_3_max_epsilon)
            print("Economic Loss when optimizing Functionality:", obj_1_value_3)
            print("Dislocation when optimizing Functionality:", obj_2_value_3)
        else:
            print("Not Optimal")

        endtime = time.time()
        elapsedtime = endtime - starttime
        print("Elapsed time for initial obj 3 solve: ", elapsedtime)

        return model

    ## Objective functions
    @staticmethod
    def obj_economic(model):
        # return(sum_product(model.l_ijk,model.x_ijk))
        return (quicksum(model.l_ijk[i, j, k] * model.x_ijk[i, j, k] for (i, j, k) in model.ZSK))

    @staticmethod
    def obj_dislocation(model):
        # return(sum_product(model.d_ijk,model.x_ijk))
        return (quicksum(model.d_ijk[i, j, k] * model.x_ijk[i, j, k] for (i, j, k) in model.ZSK))

    @staticmethod
    def obj_functionality(model):
        # return(sum_product(model.Q_t_hat,model.x_ijk))
        return (quicksum(model.Q_t_hat[i, j, k] * model.x_ijk[i, j, k] for (i, j, k) in model.ZSK))

    # Retrofit cost constraints
    @staticmethod
    def retrofit_cost_rule(model):
        return (None,
                quicksum(
                    model.Sc_ijkk_prime[i, j, k, k_prime] * model.y_ijkk_prime[i, j, k, k_prime] for (i, j, k, k_prime)
                    in model.ZSKK_prime),  # zskk_prime),
                pyo.value(model.B))

    @staticmethod
    def number_buildings_ij_rule(model, i, j):
        return (quicksum(pyo.value(model.b_ijk[i, j, k]) for k in model.K),
                quicksum(model.x_ijk[i, j, k] for k in model.K),
                quicksum(pyo.value(model.b_ijk[i, j, k]) for k in model.K))

    @staticmethod
    def building_level_rule(model, i, j, k):
        model.a = Param(mutable=True)
        model.c = Param(mutable=True)

        model.a = quicksum(model.y_ijkk_prime[i, j, k_prime, k] for k_prime in model.K_prime if
                           (i, j, k_prime, k) in model.zskk_prime)
        model.c = quicksum(model.y_ijkk_prime[i, j, k, k_prime] for k_prime in model.K_prime if
                           (i, j, k, k_prime) in model.zskk_prime)
        return (pyo.value(model.b_ijk[i, j, k]),
                model.x_ijk[i, j, k] + quicksum(model.y_ijkk_prime[i, j, k, k_prime] for k_prime in model.K_prime if
                                                (i, j, k, k_prime) in model.zskk_prime) - quicksum(
                    model.y_ijkk_prime[i, j, k_prime, k] for k_prime in model.K_prime if
                    (i, j, k_prime, k) in model.zskk_prime),
                pyo.value(model.b_ijk[i, j, k]))

    def get_spec(self):
        """Get specifications of the multiobjective retrofit optimization model.

        Returns:
            obj: A JSON object of specifications of the multiobjective retrofit optimization model.

        """
        return {
            'name': 'multiobjective-retrofit-optimization',
            'description': 'Multiobjective retrofit optimization model',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'model_solver',
                    'required': True,
                    'description': 'Choice of the model solver to use',
                    'type': str
                },
                {
                    'id': 'num_epsilon_steps',
                    'required': True,
                    'description': 'Number of epsilon values to evaluate',
                    'type': int
                },
                {
                    'id': 'max_budget',
                    'required': True,
                    'description': 'Selection of maximum possible budget',
                    'type': str
                },
                {
                    'id': 'budget_available',
                    'required': False,
                    'description': 'Custom budget value',
                    'type': int
                },
                {
                    'id': 'inactive_submodels',
                    'required': False,
                    'description': 'Identifier of submodels to inactivate during analysis',
                    'type': [int]
                },
                {
                    'id': 'scale_data',
                    'required': True,
                    'description': 'Choice for scaling data',
                    'type': bool
                },
                {
                    'id': 'scaling_factor',
                    'required': False,
                    'description': 'Custom scaling factor',
                    'type': float
                },
            ],
            'input_datasets': [
                {
                    'id': 'building_repairs_data',
                    'required': True,
                    'description': 'A csv file with building functionality data',
                    'type': 'incore:multiobjectiveBuildingFunctionality'
                },
                {
                    'id': 'strategy_costs_data',
                    'required': True,
                    'description': 'A csv file with strategy cost data'
                                   'per building',
                    'type': 'incore:multiobjectiveStrategyCosts'
                },
            ],
            'output_datasets': [
                {
                    'id': 'ds_result',
                    'parent_type': 'xxxx',
                    'description': 'A csv file',
                    'type': 'incore:multiobjectiveRetrofitOptimization'
                }
            ]
        }
