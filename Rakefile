require 'net/http'
require 'json'

desc 'Build RPMs'

DOWNLOAD_SOURCE = "www.ossec.net"
DOWNLOAD_PATH = "files/"

task :default do
  puts "Building packages"
  download_source
  write_vars_file(hashes)

  %x(vagrant up)

  if $?.success?
    %x(vagrant destroy --force)
    puts "Packages built and now available in build/"
    puts %x(ls -ltr build/*.deb)
  else
    message = %q(Vagrant or Ansible playbook has failed.
Run
    vagrant status
and
    vagrant provision
to troubleshoot.
    )
    fail message
  end
end

def version
  ENV['OSSEC_VERSION'] || "2.8.2"
end

def source_filename
  "ossec-hids-#{version}.tar.gz"
end

def download_source
  unless File.exists?("build/#{source_filename}")
    f = open("build/#{source_filename}", "wb")
    begin
      Net::HTTP.start(DOWNLOAD_SOURCE) do |http|
        http.request_get("/#{DOWNLOAD_PATH}#{source_filename}") do |resp|
          resp.read_body do |segment|
            f.write(segment)
          end
        end
      end
    ensure
      f.close()
    end
  end
end

def sha256
  sha256 = Digest::SHA256.file("build/#{source_filename}")
  sha256.hexdigest
end

def hashes
  md5 = ""
  filename = "ossec-hids-#{version}-checksum.txt"

  Net::HTTP.start(DOWNLOAD_SOURCE) do |http|
    response = http.request_get("/#{DOWNLOAD_PATH}#{filename}")
    md5 = /MD5.*= (.*)$/.match(response.body)[1]
  end

  {
    download_checksum_md5: md5,
    download_checksum_sha256: sha256
  }
end

def write_vars_file(ansible_vars)
  ansible_vars[:version] = version
  File.open("ansible_vars.json", "wb") do |f|
    f.write(ansible_vars.to_json)
  end
end