require 'serverspec'

include SpecInfra::Helper::Exec
include SpecInfra::Helper::DetectOS
include Serverspec::Helper::Properties
require 'yaml'

properties = YAML.load_file('../install_files/ansible-base/secureDropConf.yml')

RSpec.configure do |c|
  set_property properties
end
