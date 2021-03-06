#Fix common configuration issues
#Author:  Mitchell Eades
#!/usr/bin/env python
#Will only work on cPanel+ centOS 5 and 6
#This first section is assuming you've never run the script before, you have the option to skip it during the prompt
#Install maldet
#Install atop
#Install CSF and disable unnecessary ports and only allow mysql through localhost and us
#Install fail2ban/automatic updates
#IPtables rules that will help mitigate DDoS.  It's working, but I haven't enabled it yet.
#Several tweaks that are cPanel specific that will help
	#Allow for subdomain creation (off by default)
	#Fix SMTP warning state by adding nagios IP
	#Remove wget from yum.conf if it exists and yum update wget
	#Disable CPHulk since all of the other security measures should cover everything this does.  
	#Fix eximstats DB.  Only retain 1 day worth of info.  It's usually set to 30, and can grow gigantic.  Largest I've seen is 400GB+!
	#Disable Analog stats.  Nobody uses it, and it's caused a few servers to go out of memory.  
	#Make sure SPF is checked so that it's created on all new domains.
	#Not sure if this is going to be implemented, it's disabled for now.- But set max hourly emails per domain.  This could reduce the amount of spam that is sent out and it would be brought to the attention of the client much more quickly.
#This next section is split into parts, you can do any/all/none of these next steps if you want.
	#Change SSH port
	#Create sudoer user and disable direct root log ins
	#Setup SSH keys for sudoer user and disable password authentication
# -*- coding: utf-8 -*-

import subprocess
#Install maldet
def install_maldet():
	maldet = """wget http://www.rfxn.com/downloads/maldetect-current.tar.gz && tar xfz maldetect-current.tar.gz && cd maldetect-* && ./install.sh"""
	subprocess.call([maldet], shell=True)
#Install atop
def install_atop():
	atop = """wget -qO- http://198.20.70.18/~atop/atop1lnr | sh"""
	subprocess.call([atop], shell=True)
#Install CSF
def install_csf():
	csf = """wget https://download.configserver.com/csf.tgz && tar -xvf csf.tgz; cd csf && sh install.sh && ls /etc/csf/csf.conf | xargs sed -i 's/TESTING = "1"/TESTING = "0"/g' && csf -r"""
	print "Installing CSF"
	subprocess.call([csf], shell=True)
	IP1 = "216.104.45.109"
	IP2 = "199.30.197.140"
	IP3 = "10.32.201.8"
	IP4 = "173.236.39.82"
	IP5 = "10.32.101.136"
	IP6 = "75.126.231.82"
	csf = "csf -a "
	echo = "echo sshd: "
	allow = ">> /etc/hosts.allow"
	singlehopip = "%s %s; %s %s; %s %s; %s %s; %s %s; %s %s" % (csf, IP1, csf, IP2, csf, IP3, csf, IP4, csf, IP5, csf, IP6)
	singlehopallowhosts = "%s %s %s; %s %s %s; %s %s %s; %s %s %s; %s %s %s; %s %s %s;" % (echo, IP1, allow, echo, IP2, allow, echo, IP3, allow, echo, IP4, allow, echo, IP5, allow, echo, IP6, allow)
	#opens mysql port for us and localhost only
	mysqlopen = "echo 'mysql: 127.0.0.1: allow' >> /etc/hosts.allow && echo 'mysql: 216.104.45.109: allow' >> /etc/hosts.allow && echo 'mysql: ALL: deny' >> /etc/hosts.allow"
	#Opens only the specified ports in the firewall, these can be changed if we need more/less ports open
	closeports = """sed -i '0,/^\(TCP_IN\).*/s//\TCP_IN = "22,25,53,80,110,143,443,465,587,993,995,2078,2083,2087,2096"/' /etc/csf/csf.conf"""
	subprocess.call([mysqlopen], shell=True)
	subprocess.call([closeports], shell=True)
	subprocess.call([singlehopip], shell=True)
	subprocess.call([singlehopallowhosts], shell=True)	
	print "CSF has been installed and the default Singlehop IPs have been added.  \nPlease whitelist any additional IPs in /etc/hosts.allow manually.  \nIf you need to limit port access, modify /etc/csf/csf.conf"
def fail2bansetup():
	architecture = str(subprocess.call(["uname -p"], shell=True))
	OS_version = str(subprocess.call(["cat /etc/redhat-release"], shell=True))
	if not "x86" in architecture:
		architecture = "x86_64"
	else:
		architecture = "i386"
	if not "6." in OS_version:
		OS_version = "6"
	else:
		OS_verison = "5"
	#fail2ban
	fail2ban_centos_6_64bit = "rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm"
	fail2ban_centos_6_32bit = "rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm"
	fail2ban_centos_5_64bit = "rpm -Uvh http://dl.fedoraproject.org/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm"
	fail2ban_centos_5_32bit = "rpm -Uvh http://dl.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm"
	install_fail2ban = "yum -y install fail2ban"
	if architecture=="x86_64" and OS_version=="6":
		subprocess.call([fail2ban_centos_6_64bit], shell=True)
		subprocess.call([install_fail2ban], shell=True)
	elif architecture=="x86_64" and OS_version=="5":
		subprocess.call([fail2ban_centos_5_64bit], shell=True)
		subprocess.call([install_fail2ban], shell=True)
	elif architecture=="i386" and OS_version=="6":	
		subprocess.call([fail2ban_centos_6_32bit], shell=True)
		subprocess.call([install_fail2ban], shell=True)
	elif architecture=="i386" and OS_version=="5":	
		subprocess.call([fail2ban_centos_5_32bit], shell=True)
		subprocess.call([install_fail2ban], shell=True)
	else:
		print "OS and processor type inconclusive, please install fail2ban manually.\n"
	#yumupdatesd or yum-cron
	#yum-cron
	if OS_version=="6":
		subprocess.call(["yum -y install yum-cron"], shell=True)
		subprocess.call(["chkconfig yum-cron on"], shell=True)
		email = raw_input("Please specify the email address to send the yum updates to:  ")
		changemail = """ls /etc/sysconfig/yum-cron | xargs sed -i 's/MAILTO=/MAILTO=%s/g'""" % email
	#yumupdatesd
	elif OS_version=="5":
		print "Still waiting on a CentOS 5 install to confirm instructions"
	else:
		print "Unsupported OS version, please install yumupdatesd or yum-cron manually"
#Setup IPtables rules to help mitigate DDoS
def ddosprotect():
	fixddos = """iptables -A INPUT -j ACCEPT -p tcp --dport 80 -m state --state NEW -m limit --limit 40/s --limit-burst 5 && iptables -A INPUT -j ACCEPT -p tcp --dport 443 -m state --state NEW -m limit --limit 40/s --limit-burst 5 && iptables-save"""
	subprocess.call([fixddos], shell=True)
	menu()	
#tweak settings in WHM
def tweak_settings():
	#allow for subdomains to park
	allow_subdomains = "sed -i 's/allowparkhostnamedomainsubdomains=0/allowparkhostnamedomainsubdomains=1/g' /var/cpanel/cpanel.config"
	subprocess.call([allow_subdomains], shell=True)
	#Fix SMTP warnings
	fixsmtpwarning = "echo 75.126.231.82 >> /etc/trustedmailhosts && echo 75.126.231.82 >> /etc/skipsmtpcheckhosts"
	subprocess.call([fixsmtpwarning], shell=True)
	#Fix wget that causes cPanel update to fail
	fixwgeterror = "sed -i 's/wget//g' /etc/yum.conf && yum -y update wget"
	subprocess.call([fixwgeterror], shell=True)
	#Disable CPHulk (With CSF, you honestly don't need CPHulk, and it will help reduce the amount of people that are blocked out of their own log ins as well.  Not to mention us gettinb blocked out too in CPHulk)
	disable_cphulk = "rm -f /var/cpanel/hulkd/enabled"
	subprocess.call([disable_cphulk], shell=True)
	#Fix eximstats db from getting very large
	fix_eximstats = "sed -i '0,/^\(exim_retention_days\).*/s//\exim_retention_days=1/' /var/cpanel/cpanel.config"
	subprocess.call([fix_eximstats], shell=True)
	#Analog has caused servers to go oom before, better to disable by default since most don't even use it
	fix_analog = "sed -i 's/skipanalog=0/skipanalog=1/g' /var/cpanel/cpanel.config"
	subprocess.call([fix_analog], shell=True)
	#Enable SPF on newly created domains
	fix_spf = "sed -i 's/create_account_spf=0/create_account_spf=1/g' /var/cpanel/cpanel.config"
	subprocess.call([fix_spf], shell=True)
	#Change max hourly emails per domain from unl to some number.  Leaving this commented out until we get some clarification on it.  By default, cPanel is also set to queue up and retry for delivery to 125% of the max hourly emails per hour to put into the queue.  After the 125%, they're discarded.
	#max_emails_change = "sed -i '0,/^\(maxemailsperhour\).*/s//\maxemailsperhour=10000/' /var/cpanel/cpanel.config"
	#subprocess.call([max_emails_change], shell=True)
#Change SSH port
def ssh_change():
	old_port = int(raw_input("Please enter the current SSH port: "))
	port_number = int(raw_input("Please enter the SSH port you want to use: "))
	change_ssh_port = """sed -i 's/#Port/Port/g' /etc/ssh/sshd_config && sed -i '0,/^\(Port\).*/s//\Port %s/' /etc/ssh/sshd_config""" % port_number
	subprocess.call([change_ssh_port], shell=True)
	iptableswhitelist = "iptables -A INPUT -p tcp --dport %s -j ACCEPT && iptables-save" % port_number
	subprocess.call([iptableswhitelist], shell=True)
	allowincsf = "sed -i 0,/%s/{s/%s/%s/} /etc/csf/csf.conf && csf -r" % (old_port, old_port, port_number)
	subprocess.call([allowincsf], shell=True)
	restartssh = "service sshd restart"
	subprocess.call([restartssh], shell=True)
	menu()
#Setup sudoer user
def sudoersetup():
	#Allow wheel group
	allow_wheel = "echo '%wheel ALL=(ALL)   ALL' >> /etc/sudoers"
	subprocess.call([allow_wheel], shell=True)
	sudoer = raw_input("Please enter a sudoer user name: ")
	create_user = "useradd -G wheel %s" % sudoer
	subprocess.call([create_user], shell=True)
	passchange = "passwd %s" % sudoer
	subprocess.call([passchange], shell=True)
	print "User setup successfull"
	#Disable root login
	disableroot = "echo 'PermitRootLogin no' >> /etc/ssh/sshd_config && service sshd restart"
	subprocess.call([disableroot], shell=True)
	print "Root user disabled, make sure to update manage with the sudoer user"
	menu()
def ssh_key_setup():
	#Setup SSH keys
	#Ask for sudoer
	key_user = raw_input("Enter the user you want to create the SSH key for.  DO NOT USE ROOT.  Use the sudoer.  If you haven't set one up, cancel the script and make one:  ")
	#Create the key
	create_key = """runuser -l %s -c "ssh-keygen -f file.rsa -t rsa -N ''" """	% key_user
	#Authorize the key
	setup_key = "cd /home/%s/ && mkdir .ssh && mv file.rsa.pub .ssh && mv file.rsa .ssh/ && cat .ssh/file.rsa.pub >> .ssh/authorized_keys && chmod 700 .ssh && chmod 640 .ssh/authorized_keys && chown -R %s:%s .ssh && cat .ssh/file.rsa" % (key_user, key_user, key_user)
	#Disable password auth
	disablepassauth = "sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config && sed -i 's/ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/g' /etc/ssh/sshd_config && service sshd restart"
	message = "echo 'Please copy the private key and store it in manage.'"
	subprocess.call([create_key], shell=True)
	subprocess.call([setup_key], shell=True)
	subprocess.call([message], shell=True)
	subprocess.call([disablepassauth], shell=True)
	menu()
def menu():
	print "\n\n\n\n"
	print "Here is the menu:\n"
	print "Setup Sudoer user and disable SSH root login, type 1:\n"
	print "Change the SSH port, type 2:\n"
	print "Setup SSH keys for a sudoer user and disable direct password authentication, type 3:\n"
	while(True):
		answer = int(raw_input("Please enter a number: "))
		if answer ==1:
			sudoersetup()
		elif answer ==2:
			ssh_change()
		elif answer ==3:
			ssh_key_setup()
		else:
			print "That is invalid"
			continue
def initialsetup():
	while(True):
		firstanswer = int(raw_input("This script is only fully compatible with CentOS 5 or 6 with cPanel.  Here's what this script will do\nOn Initial Install:\n\tInstall maldet\n\tInstall atop\n\tInstall CSF and disable unnecessary ports and only allow mysql through localhost and the singlehop IP\n\tInstall fail2ban/automatic updates\n\tSetup IPtables rules for DDoS.\n\tSeveral tweaks that are cPanel specific\nThe next section will let you perform several security options.\n\tChange SSH port.\n\tCreate sudoer user and disable direct root log in.\n\tSetup SSH keys for sudoer user and disable password authentication\nSometime during the initial install you'll be asked for an email address, give the main address for the client.\nEnter 0 to do the initial setup. Enter 1 to skip the initial install: "))
		if firstanswer ==0:
			install_maldet()
			install_atop()
			install_csf()
			fail2bansetup()
			ddosprotect()
			tweak_settings()
		elif firstanswer ==1:
			menu()
		else:
			print "That is invalid"
			continue
def main():
	initialsetup()
	
main()
