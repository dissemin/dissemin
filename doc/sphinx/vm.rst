.. _page-vm:

Using the Dissemin Virtual Machine
==================================

1. Install VirtualBox
2. Download http://dev.dissem.in/files/DisseminVM.ova
3. Run the VM and login to it with user and pass "dissemin"
4. Go to the local copy, directory "~/dissemin"
5. Update the local copy by running ./pull_and_update.sh
6. Run the server with "./launch.sh"
7. You can see the result on http://localhost:8080/ (from both the VM and the host)

You can also connect to the guest from the host on port 8022. By default, for
security reasons, the SSH server and Web server only listen to connections from
the host.

If you wish to allow other machines to access the SSH or Web server, you can
configure this in VirtualBox: in the contextual menu Devices > Network > Network
Settings..., click "Port Forwarding" and remove "127.0.0.1" from the "Host IP"
columns for services that should listen for connections from other machines.

