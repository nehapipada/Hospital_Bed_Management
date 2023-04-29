#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import random
from enum import Enum

class Policy_priority(Enum):
    '''
    This enum defines whether COVID and normal buffers are maintained while
    '''
    PRIORITY_COVID=0
    PRIORITY_NORMAL=1
    PRIORITY_BALANCED=2


class Scenario:

    def __init__(self,
                 population = 5000000,
                 total_beds = 4000,
                 requests=(1000,4000),
                 discharge_rate = (1000,4000),
                 covid_beds_share = 0,
                 covid_conversion_cost = 5000,
                 normal_conversion_cost = 0,
                 covid_mortality = 0.0117,
                 normal_mortality = 0.0001,
                 value_of_life = 500000,
                 dos_covid_cost = 20000,
                 dos_normal_cost = 1000,
                 covid_inpatients = 0,
                 normal_inpatients = 0,
                 policy_priority = Policy_priority['PRIORITY_BALANCED'].value,
                 policy_covid_buffer = 0,
                 policy_normal_buffer = 0):
        self.population = population
        self.total_beds = total_beds
        self.covid_beds_share = min(1, max(0, covid_beds_share))
        self.beds_vector = (self.total_beds * self.covid_beds_share, self.total_beds * (1-self.covid_beds_share))
        self.requests = requests
        self.discharge_rate = discharge_rate
        self.covid_beds_share = covid_beds_share
        self.covid_conversion_cost = covid_conversion_cost
        self.normal_conversion_cost = normal_conversion_cost
        self.covid_mortality = covid_mortality
        self.normal_mortality = normal_mortality
        self.value_of_life = value_of_life
        self.dos_covid_cost = dos_covid_cost
        self.dos_normal_cost = dos_normal_cost
        self.covid_inpatients = max(0, self.beds_vector[0], covid_inpatients)
        self.normal_inpatients = max(0, self.beds_vector[1], normal_inpatients)
        self.available_covid_beds = self.beds_vector[0] - self.covid_inpatients
        self.available_normal_beds = self.beds_vector[1] - self.normal_inpatients
        self.policy_priority = policy_priority
        self.policy_covid_buffer = policy_covid_buffer
        self.policy_normal_buffer = policy_normal_buffer

    def tune_parameters(self, initial_pop,
                        covid_tests = 5000,
                        test_positivity_rate = 0.1,
                        normal_requests = 4000):
        self.population = initial_pop
        self.requests = (normal_requests, covid_tests * test_positivity_rate)
        self.discharge_rate = ()

    def get_bed_quota_from_policy(self):
        if (self.policy_priority == Policy_priority.PRIORITY_NORMAL):
            self.policy_covid_buffer = 0
        elif (self.policy_priority == Policy_priority.PRIORITY_COVID):
            self.policy_normal_buffer = 0

        variable_beds_pool = 1 - self.policy_covid_buffer - self.policy_normal_buffer

        self.covid_beds_share = self.policy_covid_buffer + (variable_beds_pool * (self.requests[0] / self.requests[1]))

        covid_beds = self.covid_beds_share * self.total_beds

        normal_beds = self.total_beds - covid_beds

        return (covid_beds, normal_beds)

    def calculate_annual_cost_function(self):
        cumulative_cost = 0

        for week in range(0,53):
            covid_discharges = max(0, np.random.normal(self.discharge_rate[0], 1000))
            normal_discharges = max(0, np.random.normal(self.discharge_rate[1], 1000))

            covid_discharges = min(self.covid_inpatients, covid_discharges)
            normal_discharges = min(self.normal_inpatients, normal_discharges)

            self.covid_inpatients = self.covid_inpatients - covid_discharges
            self.normal_inpatients = self.normal_inpatients - normal_discharges

            # applying effects of discharge and new requests:
            self.available_covid_beds = self.beds_vector[0] - self.covid_inpatients
            self.available_normal_beds = self.beds_vector[1] - self.normal_inpatients

            covid_requests = max(0, np.random.normal(self.requests[0], 1000))
            normal_requests = max(0, np.random.normal(self.requests[1], 1000))

            # applying effect of COVID Denial of Service
            if(covid_requests > self.available_covid_beds):
                self.covid_inpatients = self.beds_vector[0]
                covid_dos = covid_requests - self.available_covid_beds
                cumulative_cost = cumulative_cost + (covid_dos * self.dos_covid_cost)
            else:
                self.covid_inpatients = self.covid_inpatients + covid_requests

            self.available_covid_beds = self.beds_vector[0] - self.covid_inpatients

            # applying effect of normal Denial of Service
            if(normal_requests > self.available_normal_beds):
                self.normal_inpatients = self.beds_vector[1]
                normal_dos = normal_requests - self.available_normal_beds
                cumulative_cost = cumulative_cost + (normal_dos * self.dos_normal_cost)
            else:
                self.normal_inpatients = self.normal_inpatients + normal_requests

            self.available_normal_beds = self.beds_vector[1] - self.normal_inpatients


            # applying effect of reassigning beds
            target_bed_distribution = self.get_bed_quota_from_policy()
            self.beds_vector = target_bed_distribution

            covid_beds_added = target_bed_distribution[0] - self.beds_vector[0]
            normal_beds_added = target_bed_distribution[1] - self.beds_vector[1]

            #accounting for new COVID beds
            if(covid_beds_added>0):
                cumulative_cost = cumulative_cost + self.covid_conversion_cost * covid_beds_added

            # accounting for occupied COVID beds reassigned to normal
            if (self.available_covid_beds < (-covid_beds_added)):
                cumulative_cost = cumulative_cost + (self.dos_covid_cost * (-covid_beds_added - self.available_covid_beds))
                self.covid_inpatients = self.beds_vector[0]
            self.available_covid_beds = self.beds_vector[0] - self.covid_inpatients

            # accounting for new normal beds
            if (normal_beds_added > 0):
                cumulative_cost = cumulative_cost + self.normal_conversion_cost * normal_beds_added

            # accounting for occupied normal beds reassigned to COVID
            if (self.available_normal_beds < (-normal_beds_added)):
                 cumulative_cost = cumulative_cost + (self.dos_normal_cost * (-normal_beds_added - self.available_normal_beds))
                 self.normal_inpatients = self.beds_vector[1]
            self.available_normal_beds = self.beds_vector[1] - self.normal_inpatients

        return cumulative_cost





# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    scenario=Scenario(policy_priority=Policy_priority.PRIORITY_COVID,policy_covid_buffer=0.9)

    print(scenario.calculate_annual_cost_function())


# In[ ]:




