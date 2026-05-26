# LINFO2144 TPs Solution

This repo contains mostly my notes and solutions attempt for the different exercices. No TAs or teacher has read them so **it is very likely it contains mistakes**. Note that AI has been used to help me do the exercises, so maybe I may sound confident and still be wrong :) 


Both teacher agreed to share solutions between students. If you see any mistakes or want to improve the solutions, feel free to do a PR. All solutions will be written in markdown for easier work. `.xopp` files comes from the FOSS note taking software *Xournalpp*, thoses files need the associated PDF.


## Tips
For all the exercises that require the use of a VM. I strongly recommend not using the GUI and ssh to the VM in your host terminal. What worked for me with QEMU/KVM :

1. Use the GUI and log into the VM. Carefull keybord is in qwerty. Default credentials are user:`admin`, password:`nimda`. 
2. (optional) launch a terminal and set keyboard to azerty belgium: 
    ```bash
    setxkbmap be
    ```
3. In a terminal, enable the ssh service : 
    ```bash
    sudo systemctl enable ssh
    sudo systemctl start ssh
    # check status, should see "active (running)"
    sudo systemctl status ssh
    ```
4. Now you can ssh from your host to the VM :
    ```bash
    ssh admin@<VM_IP>
    ```
5. Send the files directory you need to the VM :
    ```bash
    scp -rp <your_folder> admin@<VM_IP>:<path_to_send_in_the_VM>
    # for example :
    scp -rp Moodle_files-Tutorial-01/ admin@192.168.122.128:~/TP/tp1
    ```

