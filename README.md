# IoT-Simulation-Test
The purpose of this work is to simulate the behavior of a production line and the consequent analysis of the data produced from it in an IoT system.
The developed solution is powered by the FIWARE platform.

## Running tests
```console
./start_simulation.sh
```

The script starts the docked components and the components developed in order to simulate the system's behavior. The parameters of the components used, the csv files used and the time scale for the simulation are defined in the script.

## Test Scenario

![Test_Scenario](/img/Testing_Scenario.png)

## FIWARE-Entities
The entities represented in FIWARE are described in the following figure.

![Entities](/img/Entities.png)

## Sequence diagram
The interactions between the different components of the system are represented in the following figure. The interactions presented can be divided into three distinct sets: subscriptions (by Delay Analysis and the components associated with Dashboards) and the acquisition, analysis and presentation of data from the MES database and data from the sensors.

![SeqDiag](/img/SeqDiag.png)

## Data Provider
The data provider is responsible for acquiring data of interest from the MES databases. The data set is acquired taking into account the set already known by the Broker and the relevance of the data for the analyzes in question.

![DataProvider](/img/DataProvider.png)

## Delay Analysis
The Data Analysis component is responsible for analyzing the data acquired from the MES database as well as the sensors. The events of interest are received by Data Alanysis through notifications from the Broker, are analyzed by the component and finally the results are recorded in the Broker.

![DelayAnalysis](/img/DelayAnalysis.png)

