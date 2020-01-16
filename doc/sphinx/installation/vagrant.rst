.. _installation_vagrant:

=======
Vagrant
=======

First, install `Vagrant <https://www.vagrantup.com>`_ and one of the supported providers: VirtualBox (should work fine), LXC (tested), libvirt (try it and tell us!).
Then run the following commands:

- ``git clone https://github.com/dissemin/dissemin`` will clone the repository, i.e., download the source code of Dissemin. 
  You should not reuse an existing copy of the repository, otherwise it may cause errors with Vagrant later.
- ``cd dissemin`` to go in the repository
- If using the VirtualBox provider, run `vagrant plugin install vagrant-vbguest` to install the VirtualBox guest additions plugin for Vagrant
- ``vagrant up --provider=your_provider`` will create the VM / container and provision the machine once
- ``vagrant ssh`` will let you poke into the machine and access its services (PostgreSQL, Redis, ElasticSearch)
- A tmux session is running so that you can check out the Celery and Django development server, attach it using: ``tmux attach``.
  It contains a ``bash`` panel, two panels to check on Celery and Django development server and a panel to create a superuser (admin account) for Dissemin, which you can then use from `localhost:8080/admin`.

Dissemin will be available on your host machine at `localhost:8080`.

Note that, when rebooting the Vagrant VM / container, the Dissemin server will not be started automatically.
To do it, once you have booted the machine, run ``vagrant ssh`` and then ``cd /dissemin`` and ``./launch.sh`` and wait for some time until it says that Dissemin has started.
The same holds for other backend services, you can check the ``Vagrantfile`` and ``provisioning/provision.sh`` to find out how to start them.
