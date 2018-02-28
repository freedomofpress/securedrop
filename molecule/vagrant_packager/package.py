#!/usr/bin/env python3
#
#
#
#
import json
import os
from os.path import join
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET


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
        json['virtual_size'] = int((re.search("virtual size: (?P<size>\d+)G",
                                    info_output)).group("size"))

        json['format'] = (re.search("file format: (?P<format>\w+)",
                                    info_output)).group("format")
        json['provider'] = 'libvirt'

        return json


def main():
    SCENARIO_PATH = os.path.dirname(os.path.realpath(__file__))
    BOX_PATH = join(SCENARIO_PATH, "build")
    EPHEMERAL_DIRS = {}

    for srv in ["app-staging", "mon-staging"]:

        for temp_dir in ["build", "tmp"]:
            try:
                ephemeral_path = join(SCENARIO_PATH, ".molecule",
                                      temp_dir)
                EPHEMERAL_DIRS[temp_dir] = ephemeral_path

                os.mkdir(os.path.join(SCENARIO_PATH, ".molecule", temp_dir))
            except OSError:
                pass

        vm = LibVirtPackager(".molecule_"+srv)

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
        shutil.copyfile(join(SCENARIO_PATH, "box_files", "Vagrantfile."+srv),
                        join(EPHEMERAL_DIRS['build'], 'Vagrantfile'))

        print("Creating tar file")
        box_file = join(BOX_PATH, srv+".box")
        with tarfile.open(box_file, "w|gz") as tar:
            for boxfile in ["box.img", "Vagrantfile", "metadata.json"]:
                tar.add(join(EPHEMERAL_DIRS["build"], boxfile),
                        arcname=boxfile)

        print("Box created at {}".format(box_file))

        print("Clean-up tmp space")
        shutil.rmtree(EPHEMERAL_DIRS['tmp'])


if __name__ == "__main__":
    main()
