voltest
=======

Openstack volume testing script

This test will spin up a cluster of machines on separate physical hosts, and proceed to benchmark the performance of the various storage systems available. The goal is to make it a little easier for ops teams to assess the viability of the many options available when setting up storage for an Openstack cluster.

Storage systems:

VM Local disk
VM Ephemeral Disk
volume servive

Tests:

Use iozone/bonnie++

streaming read
streaming write
random read
random write

Fill up the cluster 50%
Run the same test on each VM and measure performance
Run a mixture of tests on each VM and measure performance

present data
???
profit!

