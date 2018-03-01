### Internal install instructions

#### Prerequisites:
1. Common file system for input dirs and project dirs (all nodes all the time)
2. Master node 24/7 running 
    1. no GPU/SSD necessary
    2. can double as a worker
    3. sufficient RAM (16GB?)
    4. ssh accessible from lab computers
    5. port 39000 HTTP accessible from lab computers
    6. all standalone workers accessible from this node (ssh)
    7. all clusters accesible from this node (can launch jobs)
    8. reliable disk for holding database
3. at least one worker node or cluster scheduler
    1. can be same as master
    2. GPU/SSD needed
    3. user on worker must be ssh accessible from user on master without password!
    4. user on worker needs to be able to read/write all input/project dirs as well
    5. simplest to use the same user on worker and master if you have shared home dirs. 
4. potentially other workers
    1. if shared installation dir AND same CUDA version AND same ssd path: can use the same worker installation on multiple workers. 
    2. deps are only compiled when you first install on one of the workers
    3. subsequently on other workers you should just do cryosparcw connect
    4. At update time, each worker is updated but they check versions so only the first will actually perform and recompile deps.
5. Make sure basic dependencies are everywhere: gcc >= 4.4, CUDA, etc

#### Master:
1. select a user in which to install cryosparc master
    1. all input data and project directories must be read/writable by this user
    2. all other nodes and clusters must be accessible by this user (ssh keys)
    3. all jobs will run as this user (even on clusters)
    4. not root! for security
2. Select and DB path and have it ready 
3. Select a port number

```
export LICENSE_ID="blah"
curl -L https://get.cryosparc2.com/download/master-latest/$LICENSE_ID > cryosparc2_master.tar.gz
tar -xf cryosparc2_master.tar.gz
cd cryosparc2_master
./install.sh --license $LICENSE_ID --dbpath <path> --port <portnum>
source ~/.bashrc
# now optionally edit your config.sh file to set CRYOSPARC_MASTER_HOSTNAME
cryosparcm start
cryosparcm createuser <email> <password>
```

#### Worker (standalone):

1. Ensure that master is installed and running
2. Ensure that master node can ssh to this node at this user no password
3. Ensure you know where the SSD path is
4. Ensure you know where the CUDA path is 
```
export LICENSE_ID="blah"
curl -L https://get.cryosparc2.com/download/worker-latest/$LICENSE_ID > cryosparc2_worker.tar.gz
tar -xf cryosparc2_worker.tar.gz
cd cryosparc2_worker
./install.sh --license $LICENSE_ID --cudapath <path> --ssdpath <ssdpath>
bin/cryosparcw connect <workerhostname> <masterhostname> <commandport>
```

#### Worker (cluster)

1. Ensure that master is installed and running
2. Ensure master and cluster nodes can access shared FS at same paths for imports and project dirs 
3. ensure you know where SSD is on cluster nodes
4. ensure you know where CUDA path is on cluster nodes
5. decide what the lane is going to represent - single GPU node? multiple GPU nodes?

Log in interactively to a GPU node that will be part of the lane (if no internet do the download elsewhere first into home dir)
```
export LICENSE_ID="blah"
curl -L https://get.cryosparc2.com/download/worker-latest/$LICENSE_ID > cryosparc2_worker.tar.gz
tar -xf cryosparc2_worker.tar.gz
cd cryosparc2_worker
./install.sh --license $LICENSE_ID --cudapath <path> --ssdpath <ssdpath>
```
Then back on the master:
```
cryosparcm clustertemplate pbs
```
Will generate template info and script, that need to be filled out.
Then:
```
cryosparcm connectcluster info.json script.sh
cryosparcm cli verify_cluster('clustername')
```
This should connect the cluster and create the lane and check it.
