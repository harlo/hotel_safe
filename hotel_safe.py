import os, json, md5
from sys import argv, exit
from time import sleep
from fabric.api import settings, local
from fabric.operations import prompt
from fabric.context_managers import hide

def setupSafe(pwd=None, manifest=None):
	if manifest is None:
		manifest = {'assets' : []}

		print "What is the FULL PATH to the folder containing your protected assets?"
		
		manifest['safe_dir'] = prompt("folder path (Default %s): " % os.getcwd())
		
		if len(manifest['safe_dir']) == 0:
			manifest['safe_dir'] = os.getcwd()

		print "\nProtect all assets? If no, you will be able to choose which ones to protect."
		protect_all = False if prompt("y or n (Default y): ") == "n" else True

		for _, assets, _ in os.walk(manifest['safe_dir']):
			for asset in assets:
				if protect_all or prompt("\nProtect %s?\ny or n (Default n): " % asset) == "y":
					manifest['assets'].append(os.path.join(manifest['safe_dir'], asset))

			break

		if len(manifest['assets']) == 0:
			print "\nNo assets to protect in folder %s" % manifest['safe_dir']
			return None

	if not os.path.exists(manifest_dir()):
		with settings(hide('everything'), warn_only=True):
			local("mkdir -p %s" % manifest_dir())

	manifest_file = os.path.join(manifest_dir(), ".manifest.%s.json" % md5_hash(manifest['safe_dir']))
	m_gpg = "%s.gpg" % manifest_file

	with open(manifest_file, 'wb+') as m:
		m.write(json.dumps(manifest))

	with settings(hide('everything'), warn_only=True):
		local("echo %s | gpg --passphrase-fd 0 -c -o %s %s" % (pwd, m_gpg, manifest_file))
		local("echo Yes | wipe %s" % manifest_file)
		local("mv %s %s" % (m_gpg, manifest_file))

	if argv[1] in ["setup", "-s"]:
		print "\nManifest Created:\n%s" % manifest

	return manifest

def lockSafe():
	manifest_file = os.path.join(manifest_dir(), ".manifest.%s.json" % md5_hash(os.getcwd()))
	
	print "Locking your assets..."
	pwd = getPwd(perform_check=True)

	if not os.path.exists(manifest_file):
		print "No manifest for this directory yet.  Let's create one!"
		manifest = None
	else:
		with open(manifest_file, 'rb') as m:
			manifest = json.loads(m.read())

	manifest = setupSafe(pwd, manifest=manifest)
	if manifest is None:
		print "Could not create a manifest for this directory"
		failOut()
	
	safe_dir = os.path.join(manifest['safe_dir'], ".hotel_safe")
	zip_ = os.path.join(manifest['safe_dir'], ".hotel_safe.tar.gz")
	gpg_ = "%s.gpg" % zip_

	with settings(hide('everything'), warn_only=True):
		local("mkdir -p %s" % safe_dir)

		for asset in manifest['assets']:
			local("mv %s %s" % (asset, safe_dir))

		local("tar cvzf %s %s" % (zip_, safe_dir))
		local("echo %s | gpg --passphrase-fd 0 -c -o %s %s" % (pwd, gpg_, zip_))

		for cruft in [safe_dir, zip_]:
			sleep(1)
			local("echo Yes | wipe -fcr %s" % cruft, capture=True)

	print "\nASSETS SUCCESSFULLY LOCKED.\n\n"

def unlockSafe():
	manifest_file = os.path.join(manifest_dir(), ".manifest.%s.json" % md5_hash(os.getcwd()))
	m_gpg = "%s.gpg" % manifest_file
	
	print "Unlocking your assets..."
	pwd = getPwd()

	with settings(hide('everything'), warn_only=True):
		local("echo %s | gpg --passphrase-fd 0 -d -o %s %s" % (pwd, m_gpg, manifest_file ))
		local("echo Yes | wipe %s" % manifest_file)
		local("mv %s %s" % (m_gpg, manifest_file))

	try:
		with open(manifest_file, 'rb') as m:
			manifest = json.loads(m.read())
			safe_dir = manifest['safe_dir']
	except Exception as e:
		print "No manifest for this safe."
		failOut()

	with open(manifest_file, 'wb+') as m:
		m.write(json.dumps(manifest))

	zip_ = os.path.join(safe_dir, ".hotel_safe.tar.gz")
	gpg_ = "%s.gpg" % zip_

	with settings(hide('everything'), warn_only=True):
		local("echo %s | gpg --passphrase-fd 0 -d -o %s %s" % (pwd, zip_, gpg_))
		local("tar -xvzf %s -C %s" % (zip_, safe_dir))
	
		archive = os.path.join("%(sd)s%(sd)s" % ({ 'sd' : safe_dir }), ".hotel_safe")

		for _, assets, _ in os.walk(archive):
			for asset in assets:
				local("mv %s %s" % (os.path.join(archive, asset), safe_dir))

			break

		archive_home = [s for s in safe_dir.split("/") if s != ""][0]
		for cruft in [os.path.join(safe_dir, archive_home), zip_, gpg_]:
			sleep(1)
			local("echo Yes | wipe -fcr %s" % cruft, capture=True)

	print "\nASSETS SUCCESSFULLY UNLOCKED.\n\n"
			
def failOut():
	print "usage: hotel_safe [lock|unlock|setup]"
	exit(1)

def getPwd(retries=0, perform_check=False):
	# TODO: prompt should be password-safe
	pwd = prompt("passphrase: ")

	if perform_check:
		failure = None
		check_pwd = prompt("passphrase (again): ")

		if pwd == "":
			failure = "Password cannot be blank"
		elif pwd != check_pwd:
			failure = "Passwords do not match"
		elif len(pwd) <= 6:
			failure = "Password should be greater than %d characters long" % len(pwd)
		
		if failure is not None:
			if retries > 10:
				print "Too many bad tries for generating a password.  Failing."
				failOut()
			
			print "\n%s. Try again!\n" % failure
			return getPwd(retries + 1, perform_check=True)
	
	return pwd

def this_dir(): return os.path.abspath(os.path.join(__file__, os.pardir))

def manifest_dir(): return os.path.join(this_dir(), ".manifests")

def md5_hash(s):
	m = md5.new()
	m.update(s)
	return m.hexdigest()

if __name__ == '__main__':
	if len(argv) != 2: failOut()

	if argv[1] in ["lock", "-l"]: lockSafe()
	elif argv[1] in ["unlock", "-u"]: unlockSafe()
	elif argv[1] in ["setup", "-s"] : setupSafe()
	else: failOut()

	exit(0)