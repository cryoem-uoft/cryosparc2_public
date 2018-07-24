
# Installation and management guide

## Installation
### Overall setup

CryoSPARC is a backend and frontend software system that provides data processing and image analysis capabilities for single particle cryo-EM, along with a browser based user interface and command line tools.

The cryoSPARC system is designed to run on several system architectures. 
The system is based on a master-worker pattern. The master processes run together on one node (master node) and worker processes can be spawned on any available worker nodes (including the master node if it is also registered as a worker). The master node can also spawn or submit jobs to a cluster scheduler system (SLURM etc). This allows running the program on a single workstation, collection of unmanaged workstations/nodes, cluster of managed nodes (running a cluster scheduler like SLURM/PBS/Torque/etc) or heterogeneous mix of the above. 

The major requirement for installation is that all nodes (including the master) be able to access the same shared file system(s) at the same absolute path. These file systems (typically cluster file systems or NFS mounts) will be used for loading input data into jobs running on various nodes, as well as saving output data from jobs.

The cryoSPARC system is specifically designed not to require root access to install or use. The reason for this is to avoid security vulnerabilities that can occur when a network application (web interface, database, etc) is hosted as the root user. For this reason, the cryoSPARC system must be installed and run as a regular unix user (from now on referred to as `cryosparc_user`), and all input and output file locations *must* be readable and writable as this user. In particular, this means that project input and output directories that are stored within a regular user's home directory need to be accessible by `cryosparc_user`, or else (more commonly) another location on a shared file system must be used for cryosparc project directories. 

If you are installing the cryoSPARC system for use by a number of users (for example within a lab), there are two ways to do so, described below. Each is also described in more detail in the rest of this document.

1) Create a new regular user (`cryosparc_user`) and install and run cryoSPARC as this user. Create a cryoSPARC project directory (on a shared file system) where project data will be stored, and create sub-directories for each lab member. If extra security is necessary, use UNIX group priviledges to make each sub-directory read/writeable only by `cryosparc_user` and the appropriate lab member's UNIX account. Within the cryoSPARC webapp user interface, create a cryosparc user account for each lab member, and have each lab member create their projects within their respective project directories. This method relies on the cryoSPARC webapp for security to limit each user to seeing only their own projects. This is not guaranteed security, and malicious users who try hard enough will be able to modify the system to be able to see the projects and results of other users.
2) If each user must be guaranteed complete isolation and security of their projects, each user must install cryoSPARC independently within their own home directories. Projects can be kept private within user home directories as well, using UNIX permissions. Multiple single-user cryoSPARC master processes can be run on the same master node, and they can all submit jobs to the same cluster scheduler system. This method relies on the UNIX system for security and is more tedious to manage but provides stronger access restrictions. Each user will need to have their own license key in this case.

CryoSPARC worker processes run on worker nodes to actually carry out computational workloads, including all GPU-based jobs. Some job types (interactive jobs, visualization jobs, etc) also run directly on the master node without requiring a separate process to be spawned. 

Worker nodes can be installed with the following options:

* GPU(s) available: at least one worker must have GPUs available to be able to run the complete set of cryoSPARC jobs, but non-GPU workers can also be connected to run CPU-only jobs. Different workers can have different CUDA versions, but installation is simplest if all have the same version.
* SSD scratch space available: SSD space is optional on a per-worker node basis, but highly recommended for worker nodes that will be running refinements and reconstructions using particle images. Nodes reserved for pre-processing (motion correction, particle picking, CTF estimation, etc) do not need to have an SSD. 

### Prerequisites

The cryoSPARC system is pictured below:

```
browser <++++> master |<----> standalone worker 1
                      |<----> standalone worker 2
                      |<----> cluster head <////> cluster node
                      |<=========================
```

The major requirements for networking and infrastructure are:
    
* Shared file system. All nodes must have access to the same shared file system(s) where input and project directories are stored.
* A reliable (i.e. redundant) file system, not necessarily shared, available on the master node for storage of the cryoSPARC database. 
* HTTP access from user's browser to master node. The master node will run a web application at port 38000 (configurable) that all user machines (laptops, etc) must be able to access via HTTP. For remote access, users can use a VPN into your local network, SSH port tunnelling, or X forwarding (last resort, not recommended).
* SSH access between the master node and each standalone worker node. The `cryosparc_user` account should be set up to be able to SSH without password (using a key-pair) into all non-cluster worker nodes.
* SSH access between the master node and a cluster head node. If the master node itself is allowed to directly run cluster scheduler commands (qsub, etc) then this is not necessary. Otherwise, a cluster head node that can launch jobs must be SSH (without password) accessible for `cryosparc_user` from the master node.
* TCP access between every worker node (standalone or cluster) and the master node on ports 38000-38010 (configurable) for command and database connections.
* Internet access (via HTTPS) from the master node. Note: worker and cluster nodes do not need internet access.
* Every node should have a consistently resolvable hostname on the network (long name is preferred, i.e `hostname.structura.bio` rather than just `hostname`)

All nodes:

* Modern Linux OS
    * CentOS 6 +, Ubuntu 12.04 +, etc 
    * Essentially need GLIBC >= 2.12 and gcc >= 4.4
* bash as the default shell for `cryosparc_user`

The master node:

* Must have 8GB+ RAM, 2+ CPUs
* GPU/SSD not necessary
* Can double as a worker if it also has GPUs/SSD
* Note: on clusters, the master node can be a regular cluster node (or even a login node) if this makes networking requirements easier, but the master processes must be run continuously so if using a regular cluster node, the node probably needs to be requested from your scheduler in interactive mode or for an indefinitely running job. If the master process is started on one cluster node, then stopped, then later started on a different cluster node, everything should run fine. However, you should not attempt to start the same master process (same port number/database/license ID) on multiple nodes simultaneously as this might cause database corruption.

Standalone worker nodes:

* `cryosparc_user` logged in to the master node must be able to SSH to the worker node without a password.  
Note: it is not stricly necessary that the user account name/UID on the worker node be identical to the master node, if the shared-file-system requirement is met, but installation becomes more complex in that case.
* at least one node must have a GPU and preferrably an SSD
* no standalone workers are required if running only on a cluster

Cluster worker nodes:

* SSH access from the master node is not required
* Must be able to directly connect via TCP (HTTP and MongoDB) to the master node, on ports 38000-38010 (configurable)
* must have installed CUDA 8.0+

### Quick Install: Single workstation

The following commands will install cryoSPARC on to a single machine serving as both the master and a worker node. This installation will use all default settings, and enable all GPUs on the workstation. For a more complex or custom installation, or detailed descriptions of the required information (placeholders marked with `< >`), see the guides below.

SSH into the workstation as `cryosparc_user` (the UNIX user that will run all cryosparc processes, could be your personal account). The following assumes bash is your shell.

```bash
cd <install_path>
export LICENSE_ID="<license_id>"
curl -L https://get.cryosparc.com/download/master-latest/$LICENSE_ID > cryosparc2_master.tar.gz
tar -xf cryosparc2_master.tar.gz
cd cryosparc2_master

./install.sh --license $LICENSE_ID --hostname <workstation_hostname>

source ~/.bashrc
cryosparcm start
cryosparcm createuser --email <user_email> --password <user_password>

cd <install_path>
curl -L https://get.cryosparc.com/download/worker-latest/$LICENSE_ID > cryosparc2_worker.tar.gz
tar -xf cryosparc2_worker.tar.gz
cd cryosparc2_worker
./install.sh --license $LICENSE_ID --cudapath <cuda_path>

bin/cryosparcw connect --worker <workstation_hostname> --master <workstation_hostname> --ssdpath <ssd_path>
```

After completing the above, navigate your browser to `https://<workstation_hostname>:38000` to access the cryoSPARC user interface. 

### Installation: Master

Prepare the following items before you start. The name of each item is used as a placeholder in the below commands, and the values given after the equals sign are examples.

1. `<master_hostname> = cryoem1.structura.bio`
    * The long-form hostname of the machine that will be acting as the master node.
    * If the machine is consistently identifiable on your network with just the short hostname (in this case `cryoem1`) then that is sufficient.
    * You can usually get the long name using the command: `hostname -f`, and this is the `<master_hostname>` that is used if the `--hostname` option is left out below.
1. `<cryosparc_user> = cryosparc_user`
    * a regular (non-root) UNIX user account selected to run the cryosparc processes.
    * See above for how to decide which user account this should be, depending on your scenario
2. `<install_path> = /home/cryosparc_user/software/cryosparc` 
    * The directory where cryoSPARC code and dependencies will be installed.
2. `<db_path> = /home/cryosparc_user/cryosparc_database`
    * A directory that resides somewhere accessible to the master node, on a reliable (possible shared) file system
    * The cryoSPARC database will be stored here.
4. `<license_id> = 682437fb-d2ae-47b8-870b-b530c587da94`
    * The license ID issued to you 
    * Only a single cryoSPARC master instance can be running per license key.
3. `<port_number> = 38000` [Optional]
    * The base port number for this cryoSPARC instance. Do not install cryosparc master on the same machine multiple times with the same port number - this can cause database errors. 38000 is the default and will be used if the `--port` option is left out below.
4. `<user_email> = someone@structura.bio`
    * login email address for first cryoSPARC webapp account
    * This will become an admin account in the user interface
5. `<user_password> = Password123`
    * password that will be created for the `<user_email>` account

SSH in to the `<master_hostname>` machine as `<cryosparc_user>`, and then run the following commands:

```bash
cd <install_path>
export LICENSE_ID="<license_id>"
curl -L https://get.cryosparc.com/download/master-latest/$LICENSE_ID > cryosparc2_master.tar.gz
tar -xf cryosparc2_master.tar.gz
cd cryosparc2_master

./install.sh --license $LICENSE_ID --hostname <master_hostname> --dbpath <db_path> --port <port_number>

source ~/.bashrc
cryosparcm start
cryosparcm createuser --email <user_email> --password <user_password>
```

More arguments to `install.sh`:
    * `--insecure` : this instructs the installer and the cryosparc master node to ignore SSL certificate errors when connecting to HTTPS endpoints. This is useful if you are behind a enterprise network using SSL injection.
    * `--allowroot` : force allow install as root
    * `--yes` : do not ask for any user input confirmations


### Installation: Standalone worker

Installation of the cryoSPARC worker module can be done once and used by multiple worker nodes, if the installation is done in a shared location. This is helpful when dealing with multiple standalone workers. 

The requirement for multiple standalone workers to share the same copy of cryoSPARC worker installation is that they all have the same CUDA version and location of CUDA library (usually `/usr/local/cuda`). GPUs within each worker can be enabled/disabled independently, in order to limit the cryoSPARC scheduler to only using the available GPUs. Each worker node can also be configured to indicate whether or not is has a local SSD that can be used to cache particle images.

Prepare the following items before you start:

1. Start the cryosparc master process on the master node if not already started
    * `cryosparcm start` (as above)
1. `<master_hostname> = cryoem1.structura.bio`
    * The long-form hostname of the machine that is the master node.
1. `<port_num> = 38000`
    * The port number that was used to install the master process, 38000 by default.
1. `<worker_hostname> = cryoem2.structura.bio`
    * The long-form hostname of the machine that will be running jobs as the worker.
2. Ensure that SSH keys are set up for the `cryosparc_user` account to SSH between the master node and the worker node without a password.
    * Generate an RSA key pair (if not already done)  
    `ssh-keygen -t rsa`  
    (use no passphrase and the default key file location)
    * On most systems you can log into the master node and do  
    `ssh-copy-id <cryosparc_user>@<worker_hostname>`  
3. `<cuda_path> = /usr/local/cuda`
    * Path to the CUDA installation directory on the worker node
    * Note: this path should *not* be the `cuda/bin` directory, but the `cuda` directory that contains both `bin` and `lib64` subdirectories
    * This is optional, and if omitted, also add the `--nogpu` option to indicate that the worker node does not have any GPUs [As of v2.0.20, no-GPU installation is not yet supported. It will be in a future version.]
3. `<ssd_path> = /scratch/cryosparc_cache`
    * Path on the worker node to a writable directory residing on the local SSD
    * This is optional, and if omitted, also add the `--nossd` option to indicate that the worker node does not have an SSD

SSH in to the worker node `<worker_hostname>` and execute the following commands to install the cryosparc worker binaries:

```bash
cd <install_path>
export LICENSE_ID="<license_id>"
curl -L https://get.cryosparc.com/download/worker-latest/$LICENSE_ID > cryosparc2_worker.tar.gz
tar -xf cryosparc2_worker.tar.gz
cd cryosparc2_worker
./install.sh --license $LICENSE_ID --cudapath <cuda_path>
```

Follow the below instructions on each worker node that will use this worker installation. 

```bash
cd <install_path>/cryosparc2_worker
bin/cryosparcw connect --worker <worker_hostname> --master <master_hostname> --port <port_num> --ssdpath <ssd_path>
```

This will connect the worker node and register it with the master node, allowing it to be used for running jobs. By default, all GPUs will be enabled, the SSD cache will be enabled with no quota/limit, and the new worker node will be added to the default scheduler lane.

For advanced configuration:

```bash
cd <install_path>/cryosparc2_worker
bin/cryosparcw gpulist
```

This will list the available GPUs on the worker node, and their corresponding numbers. Use this list to decide which GPUs you wish to enable using the `--gpus` flag below, or leave this flag out to enable all GPUs.

Use advanced options with the connect command, or use the `--update` flag to update an existing configuration:

```bash
bin/cryosparcw connect 
  --worker <worker_hostname> 
  --master <master_hostname>
  --port <port_num>
  [--update]                       : update an existing worker configuration
  [--sshstr <custom_ssh_string>]   : custom ssh connection string 
                                     like user@hostname
  [--nogpu]                        : connect worker with no GPUs
  [--gpus 0,1,2,3]                 : enable specific GPU devices only
  [--nossd]                        : connect worker with no SSD
  [--ssdpath <ssd_path> ]          : path to directory on local ssd
  [--ssdquota <ssd_quota_mb> ]     : quota of how much SSD space to use (MB)
  [--ssdreserve <ssd_reserve_mb> ] : minimum free space to leave on SSD (MB) 
  [--lane <lane_name>]             : name of lane to add worker to
  [--newlane]                      : force creation of a new lane if 
                                     specified lane does not exist

```

### Installation: Cluster

For a cluster installation, installation of the master node is the same as above. 
Installation of the worker is done only once, and the same worker installation is used by any cluster nodes that run jobs. Thus, all cluster nodes must have the same CUDA version, CUDA path and SSD path (if any). 
Once installed, the cluster must be registered with the master process, including providing template job submission commands and scripts that the master process will use to submit jobs to the cluster scheduler. 

The cluster worker installation needs to be run on a node that either is a cluster worker, or has the same configuration as cluster workers, to ensure that CUDA compilation will be successful at install time. 

To install on a cluster, SSH into one of the cluster worker nodes and execute the following:

```bash
cd <install_path>
export LICENSE_ID="<license_id>"
curl -L https://get.cryosparc.com/download/worker-latest/$LICENSE_ID > cryosparc2_worker.tar.gz
tar -xf cryosparc2_worker.tar.gz
cd cryosparc2_worker
./install.sh --license $LICENSE_ID --cudapath <cuda_path>
```

To register the cluster, you will need to provide cryoSPARC with template strings used to construct cluster commands (like `qsub`, `qstat`, `qdel` etc or their equivalents for your system), as well as a template string to construct appropriate cluster submission scripts for your system. 
The [`jinja2`](http://jinja.pocoo.org/docs/2.10) tempate engine is used to generate cluster submission/monitoring commands as well as submission scripts for each job. 

The following fields are required to be defined as template strings in the configuration of a cluster. Examples for PBS are given here, but you can use any command required for your particular cluster scheduler:

```bash
name               :  "cluster1"
# A unique name for the cluster to be connected (multiple clusters can be connected)

worker_bin_path    :   "/path/to/cryosparc2_worker/bin/cryosparcw"
# Path on cluster nodes to the cryosparcw entry point for worker process

cache_path         :   "/path/to/local/SSD/on/cluster/nodes"
# Path on cluster nodes that is a writable location on local SSD on each cluster node. This might be /scratch or similar. This path MUST be the same on all cluster nodes. Note that the installer does not check that this path exists, so make sure it does and is writable. If you plan to use the cluster nodes without SSD, you can leave this blank.

send_cmd_tpl       :   "ssh loginnode {{ command }}"
# Used to send a command to be executed by a cluster node (in case the cryosparc master is not able to directly use cluster commands). If your cryosparc master node is able to directly use cluster commands (like qsub etc) then this string can be just "{{ command }}"

qsub_cmd_tpl       :   "qsub {{ script_path_abs }}"
# The exact command used to submit a job to the cluster, where the job is defined in the cluster script located at {{ script_path_abs }}. This string can also use any of the variables defined below that are available inside the cluster script (num_gpus, num_cpus, etc)

qstat_cmd_tpl      :   "qstat -as {{ cluster_job_id }}"
# Cluster command that will report back the status of cluster job with id {{ cluster_job_id }}. 

qdel_cmd_tpl       :   "qdel {{ cluster_job_id }}"
# Cluter command that will kill and remove {{ cluster_job_id }} from the queue.

qinfo_cmd_tpl      :   "qstat -q"
# General cluster information command

transfer_cmd_tpl   :   "scp {{ src_path }} loginnode:{{ dest_path }}"
# Command that can be used to transfer a file {{ src_path }} on the cryosparc master node to {{ dest_path }} on the cluster nodes. This is used when the master node is remotely updating a cluster worker installation. This is optional - if it is incorrect or omitted, you can manually update the cluster worker installation.
```

Along with the above commands, a complete cluster configuration requires a template cluster submission script. The script should be able to send jobs into your cluster scheduler queue marking them with the appropriate hardware requirements. The cryoSPARC internal scheduler will take care of submitting jobs as their inputs become ready.
The following variables are available to be used within a cluster submisison script template. Examples of templates, for use as a starting point, can be generated with the commands explained below.

```
{{ script_path_abs }}    - the absolute path to the generated submission script
{{ run_cmd }}            - the complete command-line string to run the job
{{ num_cpu }}            - the number of CPUs needed
{{ num_gpu }}            - the number of GPUs needed. 
{{ ram_gb }}             - the amount of RAM needed in GB
{{ job_dir_abs }}        - absolute path to the job directory
{{ project_dir_abs }}    - absolute path to the project dir
{{ job_log_path_abs }}   - absolute path to the log file for the job
{{ worker_bin_path }}    - absolute path to the cryosparc worker command
{{ run_args }}           - arguments to be passed to cryosparcw run
{{ project_uid }}        - uid of the project
{{ job_uid }}            - uid of the job
```

**Note:** The cryoSPARC scheduler does not assume control over GPU allocation when spawning jobs on a cluster. The number of GPUs required is provided as a template variable, but either your submission script, or your cluster scheduler itself is responsible for assigning GPU device indices to each job spawned. The actual cryoSPARC worker processes that use one or more GPUs on a cluster will simply begin using device 0, then 1, then 2, etc. Therefore, the simplest way to get GPUs correctly allocated is to ensure that your cluster scheduler or submission script sets the `CUDA_VISIBLE_DEVICES` environment variable, so that device 0 is always the first GPU that the particular spawned job should use. The example script for `pbs` clusters (generated as below) shows now to check which GPUs are available at runtime, and automatically select the next available device.

To actually create or set a configuration for a cluster in cryoSPARC, use the following commands. the `example`, `dump`, and `connect` commands read two files from the current working directory: `cluster_info.json` and `cluster_script.sh`

```bash
cryosparcm cluster example <cluster_type>
# dumps out config and script template files to current working directory
# examples are available for pbs and slurm schedulers but others should be very similar

cryosparcm cluster dump <name>
# dumps out existing config and script to current working directory

cryosparcm cluster connect 
# connects new or updates existing cluster configuration, reading cluster_info.json and cluster_script.sh from the current directory, using the name from cluster_info.json

cryosparcm cluster remove <name>
# removes a cluster configuration from the scheduler
```

### Optimal setup suggestions

- Disks & compressions
  - Fast disks are a necessity for processing cryo-EM data efficiently. Fast sequential read/write throughput is needed during preprocessing stages where the volume of data is very large (10s of TB) while the amount of computation is relatively low (sequential processing for motion correction, CTF estimation, particle picking etc.)
  - Typically users use spinning disk arrays (RAID) to store large raw data files, and often cluster file systems are used for larger systems. As a rule of thumb, to saturate a 4-GPU machine during preprocessing, sustained sequential read of 1000MB/s is required.
  - Compression can greatly reduce the amount of data stored in movie files, and also greatly speeds up preprocessing because decompression is actually faster than reading uncompressed data straight from disk. Typically, counting-mode movie files are stored in LZW compressed TIFF format _without_ gain correction, so that the gain reference file is stored separately and must be applied on-the-fly during process (which is supported by cryoSPARC). Compressing gain corrected movies can often result in much worse compression ratios than compressing pre-gain corrected (integer count) data. 
  - cryoSPARC supports LZW compressed TIFF format and BZ2 compressed MRC format natively. In either case the gain reference must be supplied as an MRC file. Both TIFF and BZ2 compression are implemented as multicore decompression streams on-the-fly.
- SSDs
  - For classification, refinement, and reconstruction jobs that deal with particles, having local SSDs on worker nodes can significantly speed up computation, as many algorithms rely on random-access patterns and multiple passes though the data, rather than sequentially reading the data once.
  - SSDs of 1TB+ are recommended to be able to store the largest particle stacks.
  - SSD caching can be turned off if desired, for the job types that use it.
  - cryoSPARC manages the SSD cache on each worker node transparently - files are cached, re-used across jobs in the same project, and deleted if more space is needed.
- GPUs, CPUs, RAM
  - Only NVIDIA GPUs are supported, compute capability 3.5+ is required
  - CUDA 6.0 + is required on all worker nodes (CUDA 9.0 is recommended)
  - The GPU RAM in each GPU limits the maximum box size allowed in several processing types
    - Typically, a 12GB GPU can handle a box size up to 700^3
  - Older GPUs can often perform almost equally as well as the newest, fastest GPUs because most computations in cryoSPARC are not bottlenecked by GPU compute speed, but rather by memory bandwidth and disk IO speed. Many of our benchmarks are done on NVIDIA Tesla K40s which are now (2018) almost 5 years old.
  - Multiple CPUs are needed per GPU in each worker system, at least 2 CPUs per GPU, though more is better.
  - System RAM of 32GB per GPU in a system is recommended. Faster RAM (DDR4) can often speed up processing.

## Management & Monitoring

### cryosparcm

The `cryosparcm` command line utility serves as the command line entry point for all administrative and advanced usage tasks. The `cryosparcm` command is available in your `$PATH` if you are logged in as the `<cryosparc_user>` (as mentioned in the installation guide) if the option to modify your `~/.bashrc` was allowed at install time. Otherwise, to use the `cryosparcm` command, navigate to your cryosparc master installation directory, and find the tool at `bin/cryosparcm`. (Note: `cryosparcm` is a bash script with various capabilities)

Some of the general command available are:

* `cryosparcm help` - prints help message
* `cryosparcm env` - prints out a list of environment variables that should be set in a shell to replicate the exact environment used to run cryosparc processes. The typical way to use this command is `eval $(cryosparcm env)` which causes the current shell to execute the output of the `env` command and therefore define all needed variables. This is the way to get access to for example the `python` distribution packed with cryosparc.
* `cryosparcm cli <command> ` - runs the command using the cryosparc cli (more detail below)
* `cryosparcm icli` drops the current shell into an interactive cryosparc shell that connects to the master processes and allows you to interactively run cli commands
* `cryosparcm createuser --email <email_address> --password <password>` - creates a new user account that can be accessed in the graphical web UI.
* `cryosparcm resetpassword --email <email address> --password <password> ` - reset the password for indicated user with the new `<password>` provided
* `cryosparcm downloadtest` - download test data (subset of EMPIAR 10025) to the current working directory.

### Status

The cryoSPARC master process(es) are controlled by a supervisor process that ensures that the correct processes are launched and running at the correct times. The status of the cryoSPARC master system is controlled by the `cryosparcm` command line utility, which also serves as the command line entry point for all administrative and advanced usage tasks.

The commands relating to status are described below:

* `cryosparcm status`  - prints out the current status of the cryosparc master system, including the status of all individual processes (database, webapp, command_core, etc). Also prints out configuration environment variables.
* `cryosparcm start` - starts the cryosparc instance if stopped. This will cause the database, command, webapp etc processes to start up. Once these processes are started, they are run in the background, so the current shell can be closed and the web UI will continue to run, as will jobs that are spawned.  
* `cryosparcm stop` - stops the cryosparc instance if running. This will gracefully kill all the master processes, and will cause any running jobs (potentially on other nodes) to fail. 

### Logs

The cryosparc master system keeps track of several log streams to aid in debugging if anything is not working. You can quickly see the debugging logs for various master processes with the following command:

* `cryosparcm log <process>` - begins tailing the log for `<process>` which can be either `webapp`, `database`, or `command_core`.
* `cryosparcm joblog PX JXX` - begins tailing the job log for job JXX in project PX (this shows the stdout stream from the job, which is different than the log outputs that are displayed in the webapp). 

## Updating
Updates to cryoSPARC are deployed very frequently, approximately every 2 weeks. When a new update is deployed, users will see a new version appear on the changelog in the dashboard of the web UI. Updates can be done using the process described below. Updates are usually seamless, but do require any currently running jobs to be stopped, since the cryosparc instance will be shut down during update.

### Checking for updates

`cryosparcm update --check`

This will check for updates with the cryoSPARC deployment servers, and indicate whether an update is available. You can also use `cryosparcm update --list` to get a full list of available versions (including old versions in case of a downgrade).

### Automatic update

`cryosparcm update`  will begin the standard automatic update process, by default updating to the lastest available version. The cryosparc instance will be shut down, and then new versions of both the master and worker installations will be downloaded. The master installation will be untarred (this can take several minutes on slower disks as there are many files) and will replace the current version. If dependencies have changed, updating may trigger a re-installation of dependencies (automatically). 

Once master update is complete, the new master instance will start up and then each registered standalone worker node will be updated automatically, by transferring (via scp) the downloaded worker installation `.tar.gz` file to the worker node, and then untarring and updating dependencies. If multiple standalone worker nodes are registered that all share the same worker installation, the update will only be applied once.

Cluster installations do not update automatically, because not all clusters have internet access on worker nodes. Once the automatic update above is complete, navigate to the cryosparc master installation directory, inside which you will find a file named `cryosparc2_worker.tar.gz`. This file is the latest downloaded update for worker installations. Copy this file (via scp) inside the directory where the cluster worker installation is installed (so that it sits alongside the `bin` and `deps` folders) and then within that installation directory, run

`bin/cryosparcw update`

This will cause the worker installation at that location to look for the above copied file, untar it, and update itself including dependencies. 

Attempting to run a mismatched version of cryosparc master and workers will cause an error.

### Manual update

You can update to a specific version exactly as described above, but with the command

`cryosparcm update --version=vX.Y.Z`

use `cryosparcm update --list` to see the list of available versions.

## Advanced

Notes:

- master and worker installation directories cannot be moved to a different absolute path once installed. To move the installation, dump the database, install cryoSPARC again in the new location, and restore the database.

## 