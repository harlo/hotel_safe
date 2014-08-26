import os, json, md5
from sys import argv, exit
from fabric.api import settings, local
from fabric.operations import prompt

def setupSafe():
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

	with open(os.path.join(this_dir(), ".manifest.%s.json" % md5_hash(manifest['safe_dir'])), 'wb+') as m:
		m.write(json.dumps(manifest))

	if argv[1] in ["setup", "-s"]:
		print "\nManifest Created:\n%s" % manifest

	return manifest

def lockSafe():
	try:
		with open(os.path.join(this_dir(), ".manifest.%s.json" % md5_hash(os.getcwd())), 'rb') as m: manifest = json.loads(m.read())
	except Exception as e:
		print e
		manifest = setupSafe()

	print "Locking your assets..."
	
	pwd = getPwd()
	safe_dir = os.path.join(manifest['safe_dir'], ".hotel_safe")
	zip_ = os.path.join(manifest['safe_dir'], ".hotel_safe.tar.gz")
	gpg_ = "%s.gpg" % zip_

	with settings(warn_only=True):
		local("mkdir -p %s" % safe_dir)

		for asset in manifest['assets']:
			local("mv %s %s" % (asset, safe_dir))

		local("tar cvzf %s %s" % (zip_, safe_dir))
		local("echo %s | gpg --passphrase-fd 0 -c -o %s %s" % (pwd, gpg_, zip_))
		
		for cruft in [safe_dir, zip_]:
			local("rm -rf %s" % cruft)

def unlockSafe():
	print "Unlocking your assets..."
	pwd = getPwd()

	try:
		with open(os.path.join(this_dir(), ".manifest.%s.json" % md5_hash(os.getcwd())), 'rb') as m:
			safe_dir = json.loads(m.read())['safe_dir']
	except Exception as e:
		print "No manifest for this safe."
		failOut()

	zip_ = os.path.join(safe_dir, ".hotel_safe.tar.gz")
	gpg_ = "%s.gpg" % zip_

	with settings(warn_only=True):
		local("echo %s | gpg --passphrase-fd 0 -d -o %s %s" % (pwd, zip_, gpg_))
		local("tar -xvzf %s -C %s" % (zip_, safe_dir))
	
		archive = os.path.join("%(sd)s%(sd)s" % ({ 'sd' : safe_dir }), ".hotel_safe")
		print "ARCHIVE AT %s" % archive

		for _, assets, _ in os.walk(archive):
			print assets

			for asset in assets:
				local("mv %s %s" % (os.path.join(archive, asset), safe_dir))

			break

		archive_home = [s for s in safe_dir.split("/") if s != ""][0]
		for cruft in [os.path.join(safe_dir, archive_home), zip_, gpg_]:
			local("rm -rf %s" % cruft)
			
def failOut():
	print "usage: hotel_safe.py [lock|unlock|setup]"
	exit(1)

def getPwd(): return prompt("passphrase: ")

def this_dir(): return os.path.abspath(os.path.join(__file__, os.pardir))

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