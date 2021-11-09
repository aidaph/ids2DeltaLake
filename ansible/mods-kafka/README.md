Role Name
=========

This role installs a distributed kafka engine with 3 brokers using docker containers. 

Requirements
------------

If this role is installed above the OpenStack Iaas compute engine it is needed that the kafka ports are open. Go to section <security groups< in Neutron and create a new SecGroup named "kafka". Add Ingress rule and open a port range  from 9092 to 9094, that are the defined ports in this configuration. For security reasons, only allow the ports for the subnet where the machine is allocated (CIDR X.X.X.X/24). 

Role Details
--------------
This role installs kafka via docker-compose engine. Docker-compose needs a previous installation of docker, furthermore a task installing docker `install-docker.yml` is included in the main task file. Once docker is running, docker-compose is installed in another task. Finally, docker-compose download the required containers for the repo. 
    
Docker images used (detailed in `templates/docker-compose.yml`): 
 - For zookeeper: bitnami/zookeeper:3.6.2
 - For kafka brokers: bitnami/kafka:2.7.0


Author Information
------------------

Aida Palacio Hoz (aidaph@ifca.unican.es)
