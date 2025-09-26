import os
import sys
import io
import requests
import zipfile
import xml.etree.ElementTree as ET
import rich.console
import webbrowser
import time
import random

# not sure if I need to set this dynamically
VERSION = '1_11_2931_2'
VERSION_PTR = '1_11_2931_10'

RELEASE_URI = 'https://github.com/pinesss/HW2-Mod/releases/download/test/HW2.mod.zip'
HW2_HOGAN_PATH = "Packages\\Microsoft.HoganThreshold_8wekyb3d8bbwe\\LocalState"

class ModManager:
	def __init__(self, appData) -> None:
		self.localStateDir = os.path.join(appData, HW2_HOGAN_PATH)
		self.version = VERSION
		self.mod_package = self.get_latest_mod()
		if os.path.isdir(self.localPkgDir(VERSION_PTR)):
			self.version = VERSION_PTR
		
	def localPkgDir(self, version = None):	
		if version:
			return os.path.join(self.localStateDir, f"GTS\\{version}_active")
		return os.path.join(self.localStateDir, f"GTS\\{self.version}_active")
	
	def localPkgPath(self):
		return os.path.join(self.localPkgDir(), 'maethrillian.pkg')
	
	def localManifestPath(self):
		return os.path.join(self.localPkgDir(), f"{self.version}_file_manifest.xml")

	def local_mod_exists(self):
		return (os.path.isfile(self.localPkgPath()) and os.path.isfile(self.localManifestPath()))
			
	def get_latest_mod(self):
		try:
			response = requests.get(RELEASE_URI)
			response.raise_for_status()
		except requests.exceptions.RequestException as err:
			print("Error Occured: ",err)
			return None
		else:
			return zipfile.ZipFile(io.BytesIO(response.content))
		
	def check_mod_version(self):
		"""
		Compares local mod version to remote mod version
		"""
		if self.local_mod_exists():
			tree = ET.parse(self.localManifestPath())
			root = tree.getroot()
			published_utc = int(root.get('published_utc'))
		else:
			print(f"No mod detected in the specified installation directory.\n {self.localPkgDir}")
			return False
		if self.mod_package is not None:
			for name in self.mod_package.namelist():
				if os.path.splitext(name)[1] == '.xml':
					with self.mod_package.open(name) as myfile:
						remote_manifest = myfile.read()
						remote_root = ET.fromstring(remote_manifest)
						remote_published_utc = int(remote_root.get('published_utc'))
						if remote_published_utc > published_utc:
							return False
						else:
							return True
		else:
			print("No latest mod available")
			return False
		print("Unknown error. Try uninstalling and reinstalling mod.")
		return False

	def mod_cleanup(self):
		# need to delete files within the local package directory if any exist
		if os.path.isdir(self.localPkgDir()):
			for file in os.listdir(self.localPkgDir()):
				file_path = os.path.join(self.localPkgDir(), file)
				try:
					if os.path.isfile(file_path):
						os.unlink(file_path)
				except Exception as e:
					print(e)
		return "Mod removed."

	def install_mod(self):
		if self.mod_package is not None:
			os.makedirs(self.localPkgDir(), exist_ok=True)
			for name in self.mod_package.namelist():
				if os.path.splitext(name)[1] == '.pkg':
					mod_w_path = self.localPkgPath()
				else:
					mod_w_path = self.localManifestPath()

				with self.mod_package.open(name) as myfile:
					with open(mod_w_path, 'wb') as f:
						f.write(myfile.read())
			return "Mod installation complete."
		else:
			return "Unable to install mod."

	def status(self):
		if os.path.isdir(self.localPkgDir()):
			pkg_files = [file for file in os.listdir(self.localPkgDir()) if file.endswith('.pkg')]
			manifest_files = [file for file in os.listdir(self.localPkgDir()) if file.endswith('_file_manifest.xml')]
			if len(pkg_files) == 1 and len(manifest_files) == 1 and os.path.isfile(self.localPkgPath()):
				if self.check_mod_version():
					return "Mod is installed and up to date."
				else:
					return "Mod is outdated. Press I to install latest."
			elif os.path.isfile(self.localPkgPath()):
				return "Mod is installed but files are missing or corrupted."
			else:
				return "Mod is not installed."
		else:
			return "HW2 local app data not found."


def	type_write(console: rich.console.Console, text: str, wpm: int = 40, cnsl_style: str = "bright_green"):
	"""
	Slowly writes text to console with a random time interval between each character
	"""
	for char in text:
		console.print(char, end='', style=cnsl_style)
		speed = 60 / (wpm * 6)
		time.sleep(random.uniform(0.25*speed, 1.5*speed))
	time.sleep(0.4)
	console.line()

def print_discord_link(console: rich.console.Console):
	discord_invite = "https://discord.gg/kyS82ZB"		
	type_write(console, f'Opening... {discord_invite}', 60)
	time.sleep(1.5)
	webbrowser.open(discord_invite, new=2)

if __name__ == '__main__':
	
	# print cosole header
	console = rich.console.Console()
	console.print("=========================================", style="bold italic dodger_blue3")
	console.print("=========================================", style="bold italic steel_blue3")
	console.print("=========================================", style="bold italic royal_blue1")
	console.print("=========================================", style="bold italic blue_violet")
	time.sleep(0.8)
	console.print(" .\Maethrillian> ", style="bold italic purple4", end='')
	time.sleep(0.8)
	#type_write(console, " .\Maethrillian> ", 100, "bold italic purple4")
	type_write(console, "start", 60)

	# initialize mod manager
	appData = os.environ.get('LOCALAPPDATA', -1)

	if appData == -1:
		print('Unable to find local appdata')
		input('Press any key to quit...')

	mod_manager = ModManager(appData)
	menu_counter = 0
	
	while True:
		if menu_counter % 4 == 0:
			console.print("\n(I)nstall, (U)ninstall, (S)tatus, (D)iscord, (Q)uit", style="bold dodger_blue3 underline")
		cmdKey = input('Enter key: ')
		menu_counter += 1
		if cmdKey == 'i' or cmdKey == 'I':
			mod_manager.mod_cleanup()
			type_write(console, mod_manager.install_mod(), 100)
		elif cmdKey == 'u' or cmdKey == 'U':
			type_write(console, mod_manager.mod_cleanup(), 100)
		elif cmdKey == 's' or cmdKey == 'S':
			type_write(console, mod_manager.status(), 100)
		elif cmdKey == 'd' or cmdKey == 'D':
			print_discord_link(console)
		elif cmdKey == 'q' or cmdKey == 'Q':
			sys.exit()
		else:
			type_write(console, 'BAD KEY', 100, "red")




