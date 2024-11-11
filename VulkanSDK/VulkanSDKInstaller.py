import os
import subprocess

from autopkglib import Processor, ProcessorError

__all__ = ["VulkanSDKInstaller"]


class VulkanSDKInstaller(Processor):
    """This process installs the Vulkan SDK into a temporary folder to be packaged later"""

    description = __doc__
    input_variables = {
        "install_vulkan_app": {
            "required": False,
            "description": "Path to the Vulkan SDK installer app. Defaults to RECIPE_CACHE_DIR/NAME/InstallVulkan.app",
        },
        "root_dir_sdk": {
            "required": False,
            "description": "Root directory of the SDK. Defaults to RECIPE_CACHE_DIR/NAME/installed",
        }
    }
    output_variables = {
        "module_file_path": {"description": "Outputs this module's file path."}
    }

    def main(self):
        install_vulkan_app = self.env.get("install_vulkan_app", os.path.join(self.env["RECIPE_CACHE_DIR"], self.env["NAME"], "InstallVulkan.app"))
        root_dir_sdk = self.env.get("root_dir_sdk", os.path.join(self.env["RECIPE_CACHE_DIR"], self.env["NAME"], "installed"))

        
        print("Running Vulkan SDK Installer:")

        command = [
            os.path.join(install_vulkan_app, 'Contents', 'MacOS', 'InstallVulkan'),
            "--root", root_dir_sdk,
            "--accept-messages",
            "--accept-licenses",
            "--confirm-command", "install"
        ]

        try:
            self.output("Executing command: %s" % " ".join(command))
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as err:
            raise ProcessorError(f"Failed to run Vulkan SDK installer: {err}")

        command = [
            "sed",
            "-i.orig",
            's/\\("Dest": "\\)\\(.*",\\)/\\1..\/macos_root\\2/g',
            os.path.join(root_dir_sdk, "INSTALL_BOM.json")
        ]
        try: 
            self.output("Fixing BOM: %s" % " ".join(command))
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as err:
            raise ProcessorError(f"Failed to fix BOM: {err}")
        command = [
            "sed",
            "-i", ".orig",
            's/\\(^#!\/usr\/bin\/env python\\)$/\\13/;'
            's/\\(shutil\\.copy("uninstall.sh", "\\)\\(.*)\\)/\\1..\/macos_root\\2/g',
            os.path.join(root_dir_sdk, "install_vulkan.py")
        ]
        try: 
            self.output("Fixing Install script: %s" % " ".join(command))
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as err:
            raise ProcessorError(f"Failed to fix BOM: {err}")

        os.mkdir(os.path.join(root_dir_sdk, "..", "macos_root", "usr"))
        os.mkdir(os.path.join(root_dir_sdk, "..", "macos_root", "usr", "local"))
        command = [
            os.path.join(root_dir_sdk, "install_vulkan.py"),
            "--install-json-location",
            os.path.join(root_dir_sdk),
            "--force-install"
        ]
        try:
            self.output("Executing command: %s" % " ".join(command))
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as err:
            raise ProcessorError(f"Failed to run Vulkan SDK installer: {err}")

if __name__ == "__main__":
    PROCESSOR = VulkanSDKInstaller()
    PROCESSOR.execute_shell()