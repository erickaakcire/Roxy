from twisted.python import log
import os
import pickle

bl_domains = []
passed = {}
failed = {}
user_bls = {}

def fetch_user_files(folder):
	user_files = []
	
	entries = os.listdir(folder)
	
	for entry in entries:
		path = folder + "/" + entry
		user_files.append(path)
	
	return user_files

def fetch_domain_files(folder):
	domain_files = []
	
	entries = os.listdir(folder)
	
	entries.sort()
	
	for entry in entries:
		
		path = folder + "/" + entry

		if (entry == "domains"):
			domain_files.append(path)
		elif (os.path.isdir(path)):
			for folder_entry in fetch_domain_files(path):
				domain_files.append(folder_entry)
	
	return domain_files

def initialize():
	print("Initializing blacklist...")

	files = fetch_domain_files("blacklists")

	for file in files:
		print(" Ingesting " + file + "...")
	
		f = open(file, "r")

		for line in f:
			line = line.strip()
#			try:
#				bl_domains.index(line)
#			except ValueError:
			bl_domains.append("." + line)
				
		f.close()

	files = fetch_user_files("users")

	for file in files:
		user = file.split("/")[-1]
		
		if (user != ".svn"):
			print(" Ingesting " + file + " (" + user + ")...")
			
			user_bls[user] = pickle.load(open(file))

	print("Blacklist ready.")

def userBlacklist(user):
	bl = None
	
	try:
		bl = user_bls[user]
	except KeyError:
		bl = []
		user_bls[user] = bl
	
	return bl

def addUserBlacklist(user, domain):
	bl = None
	
	try:
		bl = user_bls[user]
	except KeyError:
		bl = []
		user_bls[user] = bl
		
	bl.append(domain)
	
	pickle.dump(bl, open("users/" + user, "w"))

def removeUserBlacklist(user, domain):
	bl = None
	
	try:
		bl = user_bls[user]
	except KeyError:
		bl = []
		user_bls[user] = bl
		
	bl.remove(domain)

	pickle.dump(bl, open("users/" + user, "w"))

def userAllow(user, host):
	bl = None
	
	try:
		bl = user_bls[user]

		for domain in bl:
			try:
				host.index(domain)
				
				return False
			except ValueError:
				pass
	except KeyError:
		pass

	return True

def allow(host):
	try:
		passed[host]
		
		return True
	except KeyError:
		pass

	try:
		failed[host]
		
		return False
	except KeyError:
		pass
	
	index = 0
	
	domain = None
	
	for bl_domain in bl_domains:
		try:
			host.index(bl_domain)
			domain = bl_domain

			break
		except ValueError:
			pass
		
		index = index + 1
	
	if domain is not None:
		print("FAILED: " + host + " matched " + domain + ".")
		
		
		bl_domains.remove(domain)
	
		bl_domains.insert(0, domain)

		failed[host] = True
		
		return False

	passed[host] = True
	
	return True
	
