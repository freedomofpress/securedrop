#!/usr/bin/env python3
#
#
#
#
import hashlib
import json
import os
from os.path import join
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET


SCENARIO_NAME = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
SCENARIO_PATH = os.path.dirname(os.path.realpath(__file__))
BOX_BUILD_DIR = join(SCENARIO_PATH, "build")
BOX_METADATA_DIR = join(SCENARIO_PATH, "box_files")
EPHEMERAL_DIRS = {}
TARGET_VERSION_FILE = os.path.join(SCENARIO_PATH, os.path.pardir, "shared", "stable.ver")


class LibVirtPackager(object):

    def __init__(self, vm):
        # type: (str) -> None
        self.cli_prefix = "virsh --connect qemu:///system {}"
        self.vm_name = vm

    def _get_virsh_xml(self, cmd):
        # type: (str) -> ET.Element
        virsh_cmd_str = self.cli_prefix.format(cmd)
        cmd_output = subprocess.check_output(virsh_cmd_str.split())
        return ET.fromstring(cmd_output)

    def vm_xml(self):
        # type: () -> ET.Element
        """ Get XML definition for virtual machine domain
        """
        return self._get_virsh_xml("dumpxml "+self.vm_name)

    def default_image_location(self):
        # type: () -> str
        """
            Get full system path to the default system pool dir
        """
        pool = self._get_virsh_xml("pool-dumpxml default")

        return pool.findall('./target/path')[0].text

    def image_rebase(self, img_location):
        # type: (str) -> None
        """ If an image has a backing store, merge the backing store into the
            target image file
        """
        if self.default_image_location() in img_location:
            raise UserWarning("To prevent catastrophy, will not"
                              " run on image in the default pool. Copy it"
                              " first to someplace else")

        img_info = subprocess.check_output(["qemu-img", "info", img_location])
        rebase_cmd = """qemu-img rebase -b "" {}""".format(img_location)

        if "backing file:" in img_info.decode('utf-8'):
            print("Running rebase now..")
            subprocess.check_call(rebase_cmd, shell=True)
        else:
            print("No rebase necessary")

    def image_store_path(self):
        # type: () -> str
        """ Get location of VM's first storage disk file """
        vm_xml = self.vm_xml()
        return vm_xml.findall('./devices/disk/source')[0].attrib['file']

    def image_sparsify(self, src, dest, tmp_dir, inplace):
        # type: (str, str, str, bool) -> None
        """ Remove blank-space from the image. Note that setting inplace to
            false will get you better bang for your buck but can make system
            unstable. Pushed IO to the max on my machine and caused it to crash
        """
        img_info = subprocess.check_output(["qemu-img", "info", src])

        if "backing file:" in img_info.decode('utf-8'):
            raise UserWarning("Cannot sparsify image w/ backing "
                              "store. Please rebase first.")

        if inplace:
            subprocess.check_call(["virt-sparsify",
                                   "--in-place",
                                   src])
            shutil.move(src, dest)
        else:
            subprocess.check_call(["virt-sparsify", "--tmp",
                                  tmp_dir,
                                  src,
                                  dest])

    def sysprep(self, img_location):
        # type: (str) -> None
        """ Run the virt-sysprep tool over the image to prep the log for
            re-dist. Removes things like logs and user history files
        """
        sysprep_cmd = ("virt-sysprep --no-logfile --operations "
                       "defaults,-ssh-userdir,-ssh-hostkeys,-logfiles -a " +
                       img_location)
        subprocess.check_call(sysprep_cmd.split())

    def vagrant_metadata(self, img_location):
        # type: (str) -> dict
        """ Produce dictionary of necessary vagrant key/values """
        json = {}

        info_output = subprocess.check_output(["qemu-img", "info",
                                               img_location]).decode('utf-8')
        json['virtual_size'] = int((re.search(r"virtual size: (?P<size>\d+)G",
                                    info_output)).group("size"))

        json['format'] = (re.search(r"file format: (?P<format>\w+)",
                                    info_output)).group("format")
        json['provider'] = 'libvirt'

        return json


def main():
    with open(TARGET_VERSION_FILE, 'r') as f:
        TARGET_VERSION = f.read().strip()

    # Default to Xenial as base OS.
    TARGET_DISTRIBUTION = os.environ.get("SECUREDROP_TARGET_DISTRIBUTION", "xenial")

    for srv in ["app-staging", "mon-staging"]:

        for temp_dir in ["build", "tmp"]:
            try:
                ephemeral_path = join(SCENARIO_PATH, ".molecule",
                                      temp_dir)
                EPHEMERAL_DIRS[temp_dir] = ephemeral_path

                os.makedirs(os.path.join(SCENARIO_PATH, ".molecule", temp_dir))
            except OSError:
                pass

        vm = LibVirtPackager("{}_{}".format(SCENARIO_NAME, srv))

        tmp_img_file = join(EPHEMERAL_DIRS["tmp"], "wip.img")
        packaged_img_file = join(EPHEMERAL_DIRS["build"], "box.img")

        print("Copying VM image store locally")
        subprocess.check_output(["sudo", "cp",
                                vm.image_store_path(),  # source
                                tmp_img_file  # dest
                                 ])

        print("Changing file ownership")
        subprocess.check_output(["sudo", "chown", os.environ['USER'],
                                tmp_img_file])

        # Run a sysprep on it
        print("Run an image sysprep")
        vm.sysprep(tmp_img_file)

        print("Rebase Image")
        vm.image_rebase(tmp_img_file)

        # Sparsify the image file
        print("Run sparsi-fication on the image")
        vm.image_sparsify(src=tmp_img_file,
                          dest=packaged_img_file,
                          tmp_dir=EPHEMERAL_DIRS['tmp'],
                          inplace=True)

        # Write out metadata file
        with open(join(EPHEMERAL_DIRS['build'], 'metadata.json'),
                  'w') as mdata:
            json.dump(
                vm.vagrant_metadata(packaged_img_file),
                mdata)

        # Copy in appropriate vagrant file to build dir
        shutil.copyfile(join(BOX_METADATA_DIR, "Vagrantfile."+srv),
                        join(EPHEMERAL_DIRS['build'], 'Vagrantfile'))

        print("Creating tar file")
        box_file = join(
            BOX_BUILD_DIR, "{}-{}_{}.box".format(srv, TARGET_DISTRIBUTION, TARGET_VERSION)
        )
        with tarfile.open(box_file, "w|gz") as tar:
            for boxfile in ["box.img", "Vagrantfile", "metadata.json"]:
                tar.add(join(EPHEMERAL_DIRS["build"], boxfile),
                        arcname=boxfile)

        print("Box created at {}".format(box_file))

        print("Updating box metadata")
        update_box_metadata(srv, box_file, TARGET_DISTRIBUTION, TARGET_VERSION)

        print("Clean-up tmp space")
        shutil.rmtree(EPHEMERAL_DIRS['tmp'])


def sha256_checksum(filepath):
    """
    Returns a SHA256 checksum for a given filepath.
    """
    checksum = hashlib.sha256()
    with open(filepath, 'rb') as f:
        # Read by chunks, to avoid slurping the entire file into memory.
        # Box files range from 500MB to 1.5GB.
        for block in iter(lambda: f.read(checksum.block_size), b''):
            checksum.update(block)
    return checksum.hexdigest()


def update_box_metadata(server_name, box_file, platform, version):
    """
    Updates the JSON file of Vagrant box metadata, including remote URL,
    version number, and SHA256 checksum.
    """
    # Strip off "staging" suffix from box names
    server_name_short = re.sub(r'\-staging$', '', server_name)
    json_file_basename = "{}_{}_metadata.json".format(server_name_short, platform)
    json_file = os.path.join(BOX_METADATA_DIR, json_file_basename)

    # Read in current JSON metadata, so we can append the new info to it.
    with open(json_file, "r") as f:
        metadata_config = json.loads(f.read())

    base_url = "https://dev-bin.ops.securedrop.org/vagrant"
    box_name = os.path.basename(box_file)
    box_url = "{}/{}".format(base_url, box_name)
    box_checksum = sha256_checksum(box_file)
    box_config = dict(
        name="libvirt",
        url=box_url,
        checksum_type="sha256",
        checksum=box_checksum,
    )
    # Creating list of dicts to adhere to JSON format of Vagrant box metadata
    providers_list = []
    providers_list.append(box_config)
    version_config = dict(
        version=version,
        providers=providers_list,
    )
    box_versions = metadata_config['versions']
    box_versions.append(version_config)
    metadata_config['versions'] = box_versions

    # Write out final, modified data. Does not validate for uniqueness,
    # so repeated runs on the same version will duplicate version info,
    # which'll likely break the box fetching. Target file is version-controlled,
    # though, so easy enough to correct in the event of a mistake.
    with open(json_file, "w") as f:
        f.write(json.dumps(metadata_config, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
