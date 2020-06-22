#!/bin/bash

echo "installing cifs-utils"
sudo apt-get update
sudo apt-get install -y cifs-utils
echo

declare -a arr=("//nnlmdpfls02.inn.intel.com/lab_msdk            /mnt/nnlmdpfls02               cifs credentials=/root/.smbcredentials,iocharset=utf8,sec=ntlm,file_mode=0777,dir_mode=0777,vers=1.0 0 0"
                "//nnlmdpfls01.inn.intel.com/MediaSDK            /mnt/nnlmdpfls01               cifs credentials=/root/.smbcredentials,iocharset=utf8,sec=ntlm,file_mode=0777,dir_mode=0777,vers=1.0 0 0"
                "//samba.inn.intel.com/nfs                       /mnt/samba/nfs                 cifs credentials=/root/.smbcredentials,iocharset=utf8,file_mode=0777,dir_mode=0777,vers=1.0          0 0"
                "//nncv05a-cifs.inn.intel.com/msdk_ext4          /mnt/nncv05a-cifs/msdk_ext4    cifs credentials=/root/.smbcredentials,iocharset=utf8,sec=ntlm,file_mode=0777,dir_mode=0777,vers=1.0 0 0"
                )

echo "adding needed shares to /etc/fstab:"
for i in "${arr[@]}"
do
    if grep -qF "$i" /etc/fstab; then
        echo "$i"
    else
        echo "$i" | sudo tee --append /etc/fstab
    fi
done

echo "adding mounting credentials to ~/.smbcredentials"
if [ -f ~/.smbcredentials ]; then
    echo "Removing ~/.smbcredentials and creating it again with"
    rm ~/.smbcredentials
fi

echo "username=lab_msdk" | tee --append ~/.smbcredentials
echo "password=..."
echo "password=pelnq72@" | tee --append ~/.smbcredentials > /dev/null

echo "changing access permissions for ~/.smbcredentials"
echo "chmod 0600 ~/.smbcredentials"
chmod 0600 ~/.smbcredentials

echo "creating directories to mount shares"
for i in "${arr[@]}"
do
    splitted_i=($i)
    echo "mkdir -p ${splitted_i[1]}"
    sudo mkdir -p ${splitted_i[1]}
done
echo

echo "mounting shares"
echo "sudo mount -a"
sudo mount -a
echo
