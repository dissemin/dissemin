module Utility

    # Custom Debian installer for Vbguest
    class DebianCustom < VagrantVbguest::Installers::Debian
    
        # Adds snapshot archive repo to sources
        def install(opts=nil, &block)
            
            cmd = <<~SCRIPT
                cat <<EOF > /etc/apt/sources.list.d/snapshot_archive.list
                deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20190801T025637Z/ stretch main
                deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20190801T025637Z/ stretch/updates main
                EOF
            SCRIPT

            # Uncomment if running a Buster box
            # cmd = <<~SCRIPT
            #     cat <<EOF > /etc/apt/sources.list.d/snapshot_archive.list
            #     deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20190812T140702Z/ buster main
            #     deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20190812T140702Z/ buster/updates main
            #     EOF
            # SCRIPT

            communicate.sudo(cmd, opts, &block)

            super
        end

        def cleanup
            # Uncomment to remove the snapshot archive repo from sources
            # communicate.sudo('rm /etc/apt/sources.list.d/snapshot_archive.list')
            
            super
        end
    end
end
