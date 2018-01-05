### motivation

Synthetic data is commonly used in many areas of computing, including
generating application test data, analysis of algorithms, database performance
testing, and sales demos. Generating synthetic data that looks real or has
interesting insights is often neglected due to time constraints.

When coming up with new samples, many fake data generators will generate data
from [Independently and Identitically
Distributed](https://en.wikipedia.org/wiki/Independent_and_identically_distributed_random_variables)
(IID) variables. The effect of using IID variables is that we often end up
with datasets that look obviously fake and contain records with fields that do
not make sense, such as getting latitude and longitudes from Antarctica or
incongruent country and city combinations.

Using plait.py one can model common datasets that include markov processes -
utility usage, sales numbers, browser usage, taxi rides and so on - as well as
datasets that include objects: people, devices, addresses, etc. It's possible
to add in seasonality and periodicity, as well as environmental externalities,
e.g. holidays or failure events.

A key point is that the datasets will have an underlying model that has real
patterns: f.e. it is possible to generate a dataset of taxi rides that model
the cost based on distance, time of day and traffic. It's even possible to add
bad tippers from a specific neighborhood.

By using fine details in Plait.py models, datasets are given a shape and
narrative.
