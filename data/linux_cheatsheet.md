
## File Ownership & Permissions
```bash
ls -l /path/to/directory
sudo chown newowner:newgroup filename
chmod 755 filename
chmod u=rwx,g=rx,o=rx filename
stat filename
getfacl filename
sudo setfacl -m u:alice:r filename
sudo chown -R newowner:newgroup /path/to/directory
sudo chmod -R 755 /path/to/directory
umask 022
```

## Text Processing & Regex
```bash
grep -R --color 'pattern' /path/to/search
grep -E '^(foo|bar)' filename
grep -v 'pattern' filename
sed 's/foo/bar/g' filename
sed -i.bak 's/foo/bar/g' filename
awk '{print $2}' filename
awk '{sum+=$3} END {print sum}' filename
```

## Cron & Scheduling
```bash
crontab -l
crontab -e
# Example cron entries:
0 0 * * * /path/to/script.sh
*/5 * * * * /path/to/script.sh
0 6 * * 1-5 /path/to/script.sh
ls /etc/cron.hourly/
ls /etc/cron.daily/
ls /etc/cron.weekly/
ls /etc/cron.monthly/
```

## Sudoers & Privilege Escalation
```bash
sudo visudo
# In sudoers file (via visudo):
# username ALL=(ALL) NOPASSWD: ALL
# username ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/journalctl
sudo -l
find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -ld {} \; 2>/dev/null
```

## User & Group Management
```bash
sudo adduser newusername
sudo useradd -m newusername
sudo usermod -aG groupname username
sudo groupadd groupname
sudo usermod -a -G groupname username
sudo passwd username
sudo deluser --remove-home username
sudo groupdel groupname
```

## File Handling & Searching
```bash
find /path/to/search -type f -name "filename*"
find /path/to/search -type d -name "dirname*"
find /path/to/search -type f -mtime -7
find /path/to/search -type f -perm 755
find /path/to/search -type f -size +100M
grep -R "search_string" /path/to/directory
find /path/to/search -type f -exec grep -H "pattern" {} \;
cat file1 file2
tail -f logfile
split -l 1000 largefile segment_
```

## Network Tools & Security
```bash
ifconfig -a
ip a
netstat -tulpn
ss -tulpn
nmap -sV target_ip
sudo tcpdump -i eth0
watch -n 1 'netstat -tulpn'
ping target_ip
traceroute target_ip
```

## Advanced Sysadmin & Hacking Tools
```bash
ps aux
top
htop
dmesg | less
df -h
du -sh /path/to/directory/*
free -m
sudo apt update
sudo apt upgrade
sudo apt install package_name
sudo apt remove package_name
nc -v target_ip 80
msfconsole
sudo lynis audit system
hydra -l username -P /path/to/passwordlist.txt ssh://target_ip
sudo tail -f /var/log/syslog
grep -i "error" /var/log/syslog
sudo strace -p PID
```

## Extra Sysadmin Commands (added)
```bash
systemctl status service
systemctl restart service
systemctl enable service
journalctl -u service -f
hostnamectl set-hostname newname

ip route show
curl -I https://example.com
dig example.com +short

mkdir -p /path/to/newdir
rsync -av /src/ /dst/
scp file user@host:/path/
tar -czvf archive.tar.gz /path
unzip file.zip

whoami
id
last
uptime
reboot
shutdown -r now
```

---

## ℹ️ Wanneer gebruik je wat? (quick context + voorbeeld)
- `ls -l` / `stat` → controleren van rechten/eigenaar. Voorbeeld: `ls -l /var/www`.  
- `chown/chmod/setfacl` → rechten aanpassen. Voorbeeld: `sudo chown -R app:app /srv/app`.  
- `grep -R "foo"` / `rg foo` → snel tekst zoeken in bomen.  
- `sed -i.bak 's/foo/bar/g' file` → inline vervangen met back-up.  
- `awk '{sum+=$3} END {print sum}' file` → kolom optellen in log/CSV.  
- `crontab -e` → taak plannen; `0 6 * * 1-5 /path/job.sh` voor werkdags 06:00.  
- `sudo visudo` → sudoers veilig editen; gebruik voor NOPASSWD rules.  
- `find /path -type f -mtime -7` → bestanden gewijzigd in laatste week.  
- `tail -f logfile` → live logs; combineer met `grep -i error`.  
- `ip a` / `ss -tulpn` → netwerkinterfaces en open sockets.  
- `nmap -sV host` → services/versies scannen (alleen waar toegestaan).  
- `top/htop/free -m/df -h` → snelle health check CPU/mem/disk.  
- `systemctl status/restart <svc>` → service controleren/herstarten.  
- `journalctl -u <svc> -f` → live servicelog.  
- `rsync -av /src/ /dst/` → veilige kopie/sync met rechten behoud.  
- `scp file user@host:/path` → eenvoudige kopie tussen hosts.  
- `tar -czvf backup.tar.gz /path` → directory archiveren/comprimeren.  
- `reboot` / `shutdown -r now` → herstart; doe dit niet op productie zonder akkoord.  
