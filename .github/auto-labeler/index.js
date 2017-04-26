"use strict";

var fs = require('fs');
var readline = require('readline');

var GitHubApi = require('github');
var _ = require('lodash');
var async = require('async');

var config = require('./config');

function get_most_recent_pr(recent_cb){
  fs.readFile(config.state_file, function(err, data){
    if(err){
      fs.writeFile(config.state_file, '0', function(err){
        if(err) return recent_cb(err);
        recent_cb(null, 0);
      });
    } else {
      recent_cb(null, Number(data));
    }
  });
}

function github_process_prs(most_recent_pr_checked, pr_cb){
  var github = new GitHubApi();

  var securedrop = {
    user: config.github_user,
    repo: config.github_repo
  }

  github.authenticate({
    type: "oauth",
    token: config.github_token || process.env.GITHUB_TOKEN
  })

  // Label all PRs which meet the criteria for labelling
  function github_process_pr_page(first_page){
    return function(err, pull_requests){
      if(first_page){
        fs.writeFile(config.state_file, pull_requests[0].number, function(err){
          if(err) return pr_cb(err);
        });
      }

      var file_checks = [];
      _.each(pull_requests, function(pull_request){

        if(pull_request.number > most_recent_pr_checked){

          file_checks.push(function(fc_cb){
            github.pullRequests.getFiles(_.extend(securedrop, {
              number: pull_request.number
            }), function(err, files){
              if(err) return pr_cb(err);

              var labels = new Set();

              _.each(files, function(file){

                if(file.filename.match(/^securedrop\/journalist_templates\//) ||
                  file.filename.match(/^securedrop\/journalist.py$/)){
                  labels.add("journalist_interface");
                }

                if(file.filename.match(/^securedrop\/source_templates\//) ||
                  file.filename.match(/^securedrop\/source.py$/)){
                  labels.add("source_interface");
                }

                if(file.filename.match(/^docs\//)){
                  labels.add("docs");
                }

                if(file.filename.match(/^install_files\//)){
                  labels.add("ops");
                }

                if(file.filename.match(/^snap_ci\//)){
                  labels.add("snap_ci");
                }

                if(file.filename.match(/^spec_tests\//)){
                  labels.add("spec_tests");
                }

                if(file.filename.match(/^securedrop\/tests\//) ||
                  file.filename.match(/^securedrop\/test.sh$/)){
                  labels.add("tests");
                }

              });

              fc_cb(null, {pr: pull_request.number, labels: labels});

            });
          });

        }
      });

      async.parallel(file_checks, function(err, results){
        _.each(results, function(result){
          result.labels.forEach(function(label){
            console.log("Adding label " + label + " to PR #" + result.pr);
	    github.issues.addLabels(_.extend(securedrop, {
	      number: result.pr,
	      body: [label]
	    }), function(err, res){
	      if(err) console.log(err);
	    });
          });
        });
      });

      if(github.hasNextPage(pull_requests)){
        github.getNextPage(pull_requests, github_process_pr_page(false));
      }
    }
  }

  github.pullRequests.getAll(_.extend(securedrop, {
    state: "open",
    per_page: 100
  }), github_process_pr_page(true));
}

async.waterfall([
  get_most_recent_pr,
  github_process_prs
], function(err, result){
  if(err) console.log(err);
});
